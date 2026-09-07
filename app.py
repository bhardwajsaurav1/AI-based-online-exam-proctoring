"""
AI-Based Online Exam Proctoring System - Main Flask Application Server.
Author: Sole Contributor / Creator
"""

import cv2
import time
import os
from flask import Flask, render_template, Response, request, redirect, url_for, session, flash, jsonify, send_file
from flask_cors import CORS
import config
from backend.database import Database
from backend.logger import ForensicLogger
from core.proctor_engine import ProctorEngine

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
CORS(app)

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
            session['user'] = user
            flash('Login successful! Welcome to the examination portal.', 'success')
            return redirect(url_for('exam'))
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
            flash('Account created successfully! Please sign in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Username or email may already be registered.', 'error')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/exam')
def exam():
    if 'user' not in session:
        flash('Please login to access the examination.', 'error')
        return redirect(url_for('login'))
    return render_template('exam.html')

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

    # Answer Key Evaluation
    CORRECT_ANSWERS = {
        'q1': 'B',
        'q2': 'A',
        'q3': 'B',
        'q4': 'A'
    }

    score = 0
    total_q = len(CORRECT_ANSWERS)
    for q_id, correct_opt in CORRECT_ANSWERS.items():
        if request.form.get(q_id) == correct_opt:
            score += 1

    session['exam_score'] = score
    session['total_questions'] = total_q
    session['total_violations'] = engine.warning_count

    return redirect(url_for('results'))

@app.route('/results')
def results():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Read last 15 lines from activity.txt for display
    recent_logs = []
    if config.ACTIVITY_LOG_TXT.exists():
        try:
            with open(config.ACTIVITY_LOG_TXT, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_logs = [line.strip() for line in lines[-15:]]
        except Exception:
            recent_logs = ["[activity.txt initialized]"]

    return render_template(
        'results.html',
        score=session.get('exam_score', 0),
        total_questions=session.get('total_questions', 4),
        total_violations=session.get('total_violations', engine.warning_count),
        recent_logs=recent_logs
    )

@app.route('/download_log')
def download_log():
    if config.ACTIVITY_LOG_TXT.exists():
        return send_file(config.ACTIVITY_LOG_TXT, as_attachment=True, download_name="activity.txt")
    flash('Activity log is empty.', 'error')
    return redirect(url_for('results'))

if __name__ == '__main__':
    print(f"[✓] Starting AI Proctoring Web Server on http://localhost:{config.SERVER_PORT}")
    app.run(host=config.SERVER_HOST, port=config.SERVER_PORT, debug=config.DEBUG_MODE)
