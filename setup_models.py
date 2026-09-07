"""
Model Downloader & Setup Utility.
Author: Sole Contributor / Creator
Automatically downloads required weights and models for face landmarks and YOLOv3-tiny.
"""

import os
import sys
import urllib.request
import bz2
from pathlib import Path
import config

MODELS_INFO = {
    "shape_predictor_68_face_landmarks.dat": {
        "url": "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2",
        "is_bz2": True,
        "target": config.SHAPE_PREDICTOR_PATH
    },
    "yolov3-tiny.cfg": {
        "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg",
        "is_bz2": False,
        "target": config.YOLO_CONFIG_PATH
    },
    "yolov3-tiny.weights": {
        "url": "https://pjreddie.com/media/files/yolov3-tiny.weights",
        "is_bz2": False,
        "target": config.YOLO_WEIGHTS_PATH
    },
    "coco.names": {
        "url": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names",
        "is_bz2": False,
        "target": config.YOLO_CLASSES_PATH
    }
}

def download_progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100, int((downloaded / total_size) * 100))
        sys.stdout.write(f"\rDownloading: {percent}% [{downloaded}/{total_size} bytes]")
        sys.stdout.flush()

def setup_models():
    print("=" * 60)
    print("AI Proctoring System - Model Setup & Verification")
    print("=" * 60)

    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for filename, info in MODELS_INFO.items():
        target_path = info["target"]
        if target_path.exists() and target_path.stat().st_size > 0:
            print(f"[OK] {filename} is already present ({target_path.stat().st_size} bytes).")
            continue

        print(f"\n[DOWNLOAD] Fetching {filename} from {info['url']}...")
        try:
            req = urllib.request.Request(
                info["url"],
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            if info["is_bz2"]:
                temp_bz2 = target_path.with_suffix(".bz2")
                with urllib.request.urlopen(req) as response, open(temp_bz2, 'wb') as out_file:
                    total_size = int(response.info().get('Content-Length', -1))
                    downloaded = 0
                    while True:
                        buffer = response.read(8192)
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        out_file.write(buffer)
                        if total_size > 0:
                            percent = min(100, int((downloaded / total_size) * 100))
                            sys.stdout.write(f"\rDownloading: {percent}% [{downloaded}/{total_size} bytes]")
                            sys.stdout.flush()

                print(f"\n[EXTRACT] Extracting {temp_bz2.name}...")
                with bz2.BZ2File(temp_bz2, 'rb') as f_in, open(target_path, 'wb') as f_out:
                    f_out.write(f_in.read())
                if temp_bz2.exists():
                    temp_bz2.unlink()
            else:
                with urllib.request.urlopen(req) as response, open(target_path, 'wb') as out_file:
                    total_size = int(response.info().get('Content-Length', -1))
                    downloaded = 0
                    while True:
                        buffer = response.read(8192)
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        out_file.write(buffer)
                        if total_size > 0:
                            percent = min(100, int((downloaded / total_size) * 100))
                            sys.stdout.write(f"\rDownloading: {percent}% [{downloaded}/{total_size} bytes]")
                            sys.stdout.flush()

            print(f"\n[OK] Successfully saved {filename} ({target_path.stat().st_size} bytes)")
        except Exception as e:
            print(f"\n[ERROR] Failed downloading {filename}: {e}")

    print("\n" + "=" * 60)
    print("Model Setup Verification Finished.")
    print("=" * 60)

if __name__ == "__main__":
    setup_models()
