# AI-Based Online Exam Proctoring System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel%20Production-blueviolet?style=for-the-badge&logo=vercel)](https://ai-exam-proctoring-system-five.vercel.app)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green.svg)](https://opencv.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

## 📖 About The Project

An automated, real-time AI-powered invigilation and online examination monitoring platform developed to safeguard academic integrity and prevent cheating during remote examinations.

- 🌐 **Live Vercel Deployment**: [https://ai-exam-proctoring-system-five.vercel.app](https://ai-exam-proctoring-system-five.vercel.app)
- 👤 **Author & Creator**: [bhardwajsaurav1](https://github.com/bhardwajsaurav1)
- 📝 **Live Exam Demo**: Instant access with credentials `student1` / `password123` or create an account via Registration.

---

## 🌟 Key Features

- 👤 **Face Presence & Multi-Face Verification**: Tracks candidate attendance and alerts when zero or multiple individuals enter the camera frame using **Dlib**.
- 👁️ **Eye Gaze & Pupil Tracking**: Segments eye contours and calculates sclera/pupil non-zero pixel ratios to detect off-screen glances.
- ⏱️ **Liveness & Blink Detection**: Computes Eye Aspect Ratio (EAR) across 6 facial landmark pairs to verify candidate liveness and prevent static photo spoofing attacks.
- 📐 **3D Head Pose Estimation**: Estimates 3D rotation vectors (Yaw, Pitch, Roll) using the **Perspective-n-Point (`solvePnP`)** algorithm to flag excessive head movement.
- 👄 **Mouth Tracking & Speech Detection**: Calculates vertical lip separation to detect talking, whispering, or dictating answers.
- 📱 **Unauthorized Object Detection**: Scans the testing environment for prohibited devices (cell phones, laptops, books) using **YOLOv3-Tiny**.
- 🎙️ **Acoustic Noise & Speech Surveillance**: Samples ambient microphone audio in real time to detect verbal assistance.
- 📝 **Forensic Activity Logging**: Outputs time-series incident vectors directly to `activity.txt` and `activity.json` for post-exam review.
- 🌐 **Interactive Web Examination Portal**: Full-featured **Flask** application with candidate authentication, timer, real-time proctoring HUD, and score reporting.

---

## 🏗️ Architecture & Flowchart

```
Candidate Video & Audio Streams
           │
           ├──▶ Dlib 68-Landmark Predictor ──▶ Face Count, Gaze Ratio, EAR Blink, Head Pose, Mouth State
           ├──▶ YOLOv3-Tiny Neural Network ──▶ Cell Phones, Laptops, Books, Secondary Persons
           └──▶ PyAudio Stream Analyzer    ──▶ Amplitude Spikes & Background Speech
           │
           ▼
Master Decision Engine (ProctorEngine)
           ├──▶ Real-Time Warning Alert (Audio Beep & Visual HUD Warning)
           ├──▶ Append Frame Telemetry to 'activity.txt'
           └──▶ Update Exam Dashboard & PostgreSQL/MySQL/SQLite Database
```

---

## 📂 Project Structure

```text
ai-exam-proctoring-system/
├── app.py                     # Main Flask Application Server
├── standalone_proctor.py      # Standalone Desktop Monitor (Direct OpenCV View)
├── config.py                  # Centralized Thresholds & Settings
├── setup_models.py            # Automated Weights & Landmarks Downloader
├── requirements.txt           # Python Package Dependencies
├── activity.txt               # Raw Forensic Audit Log
│
├── core/                      # Multi-Modal AI Detection Engines
│   ├── face_detector.py       # Face presence & count
│   ├── eye_tracker.py         # Sclera/pupil gaze tracking
│   ├── blink_detector.py      # EAR liveness verification
│   ├── head_pose.py           # 3D-to-2D solvePnP head pose
│   ├── mouth_tracker.py       # Lip displacement & speech detection
│   ├── object_detector.py     # YOLOv3-Tiny prohibited object detection
│   ├── audio_monitor.py       # Real-time microphone monitoring
│   └── proctor_engine.py      # Master orchestrator & alert triggers
│
├── backend/                   # Database & Auditing
│   ├── database.py            # SQLite & MySQL database adapter
│   └── logger.py              # Forensic activity logger
│
├── static/                    # CSS & Client Scripts
│   ├── css/style.css
│   ├── css/exam.css
│   ├── js/main.js
│   └── js/exam.js
│
├── templates/                 # Web HTML Templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── exam.html
│   └── results.html
│
└── models/                    # Model Weights & Face Predictors
    ├── shape_predictor_68_face_landmarks.dat
    ├── yolov3-tiny.cfg
    ├── yolov3-tiny.weights
    └── coco.names
```

---

## 🚀 Getting Started

### 1. Clone or Open the Repository
```bash
cd ai-exam-proctoring-system
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download AI Model Weights
Run the automated downloader to retrieve the Dlib shape predictor and YOLOv3-tiny model weights:
```bash
python setup_models.py
```

### 4. Run the Web Application
```bash
python app.py
```
Open your browser and navigate to: **`http://localhost:5000`**

- **Demo Login**: `student1` / `password123`
- Or register a new candidate account via the **Register** tab.

### 5. (Optional) Run in Standalone Desktop Mode
To run the computer vision proctoring engine in a dedicated OpenCV window without opening a browser:
```bash
python standalone_proctor.py
```

---

## 📊 Forensic Activity Log Format

Each analyzed frame writes a structured telemetry vector to `activity.txt`:
```python
['21:37:04.612195', 'Face detecting properly.', 'No Blink', 'center', 'Mouth Close', [('person', 0.95)], -1]
```
- **Field 1**: Timestamp (`HH:MM:SS.microseconds`)
- **Field 2**: Face Presence State (`Face detecting properly.` / `No face detected` / `Multiple faces detected`)
- **Field 3**: Blink / Liveness Status (`Blink` / `No Blink`)
- **Field 4**: Gaze Direction (`center` / `left` / `right`)
- **Field 5**: Mouth Activity (`Mouth Close` / `Mouth Open`)
- **Field 6**: Detected Objects (`[('cell phone', 0.88), ...]`)
- **Field 7**: Head Pose Deviation Metric

---

## 👤 Author & Contributor

- **Sole Contributor / Creator**: Sole Project Author & Developer

---

## 📄 License
This project is licensed under the MIT License.
