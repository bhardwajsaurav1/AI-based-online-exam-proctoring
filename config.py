"""
Configuration settings for AI-Based Online Exam Proctoring System.
Author: Sole Contributor / Creator
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Model File Paths
SHAPE_PREDICTOR_PATH = MODELS_DIR / "shape_predictor_68_face_landmarks.dat"
YOLO_CONFIG_PATH = MODELS_DIR / "yolov3-tiny.cfg"
YOLO_WEIGHTS_PATH = MODELS_DIR / "yolov3-tiny.weights"
YOLO_CLASSES_PATH = MODELS_DIR / "coco.names"

# Camera Settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_FPS = 30

# Computer Vision Proctoring Thresholds
BLINK_EAR_THRESHOLD = 0.22      # Eye Aspect Ratio threshold for blink detection
MOUTH_AR_THRESHOLD = 0.65       # Mouth Aspect Ratio threshold for open mouth/speech
GAZE_RATIO_LEFT_THRESH = 0.85   # Ratio determining looking left
GAZE_RATIO_RIGHT_THRESH = 1.25  # Ratio determining looking right
HEAD_PITCH_THRESHOLD = 20.0     # Degrees up/down deviation limit
HEAD_YAW_THRESHOLD = 25.0       # Degrees left/right deviation limit

# Audio Monitoring Thresholds
AUDIO_CHUNK = 1024
AUDIO_RATE = 44100
AUDIO_THRESHOLD = 2000          # RMS Amplitude intensity limit
AUDIO_ALERT_FREQUENCY = 2500    # Hertz (Auditory beep warning)
AUDIO_ALERT_DURATION = 1000     # Milliseconds

# Object Detection Classes (Prohibited Items to Flag)
PROHIBITED_OBJECTS = [
    "cell phone",
    "laptop",
    "tv",
    "book",
    "tablet",
    "remote"
]

# Database Settings
DATABASE_TYPE = os.getenv("DB_TYPE", "sqlite")  # 'sqlite' or 'mysql'
SQLITE_DB_PATH = BASE_DIR / "proctoring.db"

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "root"),
    "database": os.getenv("MYSQL_DB", "quizo"),
    "port": int(os.getenv("MYSQL_PORT", 3306))
}

# Web Server Settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
DEBUG_MODE = True
SECRET_KEY = os.getenv("SECRET_KEY", "proctor-super-secure-key-2026")

# Audit File Paths
ACTIVITY_LOG_TXT = BASE_DIR / "activity.txt"
ACTIVITY_LOG_JSON = LOGS_DIR / "activity.json"
