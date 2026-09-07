"""
Forensic Audit & Telemetry Logger.
Author: Sole Contributor / Creator
Writes real-time activity events to activity.txt and structured JSON logs.
"""

import json
import threading
from datetime import datetime
import config

class ForensicLogger:
    def __init__(self, txt_path=config.ACTIVITY_LOG_TXT, json_path=config.ACTIVITY_LOG_JSON):
        self.txt_path = txt_path
        self.json_path = json_path
        self.lock = threading.Lock()
        self.events = []

    def log_record(self, raw_vector, telemetry_dict=None):
        """
        Appends a frame's log vector to activity.txt and logs/activity.json in a thread-safe manner.
        """
        with self.lock:
            # 1. Write to activity.txt (Standard reference format)
            try:
                with open(self.txt_path, "a", encoding="utf-8") as f:
                    f.write(str(raw_vector) + "\n")
            except Exception as e:
                print(f"[Error] Failed writing to activity.txt: {e}")

            # 2. Write to activity.json (Structured time-series)
            if telemetry_dict:
                self.events.append(telemetry_dict)
                try:
                    with open(self.json_path, "w", encoding="utf-8") as f:
                        json.dump(self.events[-500:], f, indent=2)
                except Exception:
                    pass

    def get_recent_violations(self, limit=50):
        """Retrieves recently recorded violation events."""
        with self.lock:
            return [e for e in self.events if e.get("is_violation")][-limit:]
