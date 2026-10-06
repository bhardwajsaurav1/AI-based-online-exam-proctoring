"""
AI-Based Online Exam Proctoring System - Main Flask Application Server.
Author: Sole Contributor / Creator
"""

import cv2
import time
import os
from datetime import datetime
from flask import Flask, render_template, Response, request, redirect, url_for, session, flash, jsonify, send_file, send_from_directory
from flask_cors import CORS
import config
from backend.database import Database
from backend.logger import ForensicLogger
from backend.question_bank import generate_random_exam
from core.proctor_engine import ProctorEngine
from webauthn_routes import bp as webauthn_bp
from backend import webauthn_store

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, 'static'),
    static_url_path='/static',
    template_folder=os.path.join(BASE_DIR, 'templates')
)
app.secret_key = config.SECRET_KEY
CORS(app)

# Register WebAuthn / FIDO2 biometric authentication blueprint
app.register_blueprint(webauthn_bp)

# Initialize Database, Logger, and AI Proctoring Engine
db = Database()
logger = ForensicLogger()
engine = ProctorEngine()

# Global Camera Stream Handler
global_cam = None
latest_telemetry = {
    "face_status": "Normal",
    "face_count": 1,
    "blink_status": "No Blink",
    "gaze_direction": "center",
    "mouth_status": "Mouth Close",
    "head_looking_away": False,
    "detected_objects": [("person", 0.95)],
    "audio_status": "Quiet / Normal",
    "is_violation": False,
    "warning_count": 0
}

def get_camera():
    global global_cam
    if global_cam is None or not global_cam.isOpened():
        global_cam = cv2.VideoCapture(config.CAMERA_INDEX)
        global_cam.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        global_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    return global_cam

def generate_video_stream():
    """Generates JPEG stream with real-time AI HUD annotation."""
    global latest_telemetry
    cam = get_camera()

    while True:
        success, frame = cam.read()
        if not success:
            # Fallback frame if camera disconnected
            placeholder = 50 * np.ones((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Camera Unavailable", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', placeholder)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.1)
            continue

        annotated_frame, telemetry, raw_vector = engine.process_frame(frame)
        latest_telemetry = telemetry

        # Forensic Audit Logging
        logger.log_record(raw_vector, telemetry)

        # Encode Frame to JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ----------------- HTTP Routes -----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.authenticate_user(username, password)
        if user:
            from webauthn_routes import username_of
            uname = username_of(user)
            if webauthn_store.has_credentials(uname):
                # Has biometrics enrolled → require biometric MFA step
                session['pending_mfa'] = {'user': user, 't': time.time()}
                next_url = request.args.get('next', url_for('exam'))
                return redirect(url_for('webauthn.mfa_page', next=next_url))
            else:
                # No biometrics yet → log in but prompt to set up biometrics
                session['user'] = user
                session['show_biometric_setup'] = True
                return redirect(url_for('webauthn.security_page'))
        else:
            flash('Invalid username/email or password.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        success = db.register_user(email, username, password)
        if success:
            # Auto-login the new user and redirect straight to biometric setup
            user = db.authenticate_user(username, password)
            if user:
                session['user'] = user
                session['show_biometric_setup'] = True
            return redirect(url_for('webauthn.security_page'))
        else:
            flash('Registration failed. Username or email may already be registered.', 'error')
    return render_template('signup.html')

@app.route('/skip_biometric_setup')
def skip_biometric_setup():
    """Allow users to bypass biometric setup and go straight to the exam."""
    session.pop('show_biometric_setup', None)
    if 'user' not in session:
        return redirect(url_for('login'))
    flash('You can set up biometrics anytime from the Security tab.', 'success')
    return redirect(url_for('exam'))

@app.route('/clear_setup_flag', methods=['POST'])
def clear_setup_flag():
    """AJAX endpoint to clear the one-time biometric setup banner flag."""
    session.pop('show_biometric_setup', None)
    return jsonify(ok=True)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/precheck')
def precheck():
    """Pre-exam system check page — mic, cam, fullscreen, screen-share, AI warm-up."""
    if 'user' not in session:
        flash('Please login to access the examination.', 'error')
        return redirect(url_for('login'))
    return render_template('precheck.html')

@app.route('/exam')
def exam():
    if 'user' not in session:
        flash('Please login to access the examination.', 'error')
        return redirect(url_for('login'))

    # Generate a fresh randomized set of questions for this session
    questions, answer_key = generate_random_exam(num_questions=4)
    session['exam_questions'] = questions
    session['exam_answer_key'] = answer_key
    session['violation_history'] = []
    session['is_disqualified'] = False
    session['exam_score'] = 0
    engine.warning_count = 0

    return render_template('exam.html', questions=questions)


@app.route('/video_feed')
def video_feed():
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/telemetry')
def telemetry():
    global latest_telemetry
    return jsonify(latest_telemetry)

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    if 'user' not in session:
        return redirect(url_for('login'))

    answer_key = session.get('exam_answer_key', {})
    score = 0
    total_q = len(answer_key) if answer_key else 4

    for q_id, correct_opt in answer_key.items():
        if request.form.get(q_id) == correct_opt:
            score += 1

    session['exam_score'] = score
    session['total_questions'] = total_q
    session['total_violations'] = engine.warning_count

    return redirect(url_for('results'))

@app.route('/log_violation', methods=['POST'])
def log_violation():
    data = request.get_json(silent=True) or {}
    violation_type = data.get('type', 'Proctoring Anomaly')
    time_str = datetime.now().strftime("%H:%M:%S")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    engine.warning_count += 1

    v_list = session.get('violation_history', [])
    v_list.append({"type": violation_type, "time": time_str, "warning_num": engine.warning_count})
    session['violation_history'] = v_list

    log_line = f"[{timestamp_str}] [VIOLATION] Type: {violation_type} | Warnings: {engine.warning_count}"
    logger.log_record(log_line, {
        "timestamp": timestamp_str,
        "violation_type": violation_type,
        "is_violation": True,
        "warning_count": engine.warning_count
    })
    return jsonify({"status": "ok", "warning_count": engine.warning_count})

@app.route('/disqualify_exam', methods=['POST'])
def disqualify_exam():
    data = request.get_json(silent=True) or {}
    reason = data.get('reason', 'Exceeded maximum violation warnings (5 / 5 Warnings).')
    if 'user' in session:
        session['is_disqualified'] = True
        session['exam_score'] = 0
        session['total_questions'] = 4
        session['total_violations'] = engine.warning_count
        session['disqualification_reason'] = reason

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp_str}] [DISQUALIFIED] Candidate exceeded warning threshold ({reason}). Examination terminated."
        logger.log_record(log_line, {
            "timestamp": timestamp_str,
            "disqualified": True,
            "warning_count": engine.warning_count
        })
    return jsonify({"status": "disqualified", "redirect_url": url_for('results')})

@app.route('/results')
def results():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template(
        'results.html',
        score=session.get('exam_score', 0),
        total_questions=session.get('total_questions', 4),
        total_violations=session.get('total_violations', engine.warning_count),
        is_disqualified=session.get('is_disqualified', False),
        disqualification_reason=session.get('disqualification_reason', ''),
        violations=session.get('violation_history', [])
    )

@app.route('/download_log')
def download_log():
    if config.ACTIVITY_LOG_TXT.exists():
        return send_file(config.ACTIVITY_LOG_TXT, as_attachment=True, download_name="activity.txt")
    flash('Activity log is empty.', 'error')
    return redirect(url_for('results'))

if __name__ == '__main__':
    print(f"[OK] Starting AI Proctoring Web Server on http://localhost:{config.SERVER_PORT}")
    app.run(host=config.SERVER_HOST, port=config.SERVER_PORT, debug=config.DEBUG_MODE)
