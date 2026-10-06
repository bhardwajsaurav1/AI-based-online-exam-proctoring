"""
Audio & Microphone Noise Monitoring Module.
Author: Sole Contributor / Creator
Captures real-time PCM audio and flags noise levels exceeding calibrated threshold.
"""

import threading
import numpy as np
import config

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

class AudioMonitor:
    def __init__(self, threshold=config.AUDIO_THRESHOLD):
        self.threshold = threshold
        self.is_running = False
        self.latest_volume = 0
        self.is_suspicious_sound = False
        self.thread = None

    def start(self):
        if not HAS_PYAUDIO:
            print("[Warning] AudioMonitor: PyAudio is not installed. Audio monitoring is simulated.")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.thread.start()
        print("[OK] AudioMonitor: Background audio listening stream started.")

    def _audio_loop(self):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=config.AUDIO_RATE,
                input=True,
                frames_per_buffer=config.AUDIO_CHUNK
            )
            while self.is_running:
                try:
                    data = stream.read(config.AUDIO_CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    peak_vol = int(np.max(np.abs(audio_data)))
                    self.latest_volume = peak_vol
                    self.is_suspicious_sound = (peak_vol > self.threshold)
                except Exception:
                    continue
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"[Warning] AudioMonitor stream error: {e}")
        finally:
            p.terminate()

    def get_audio_status(self):
        return {
            "volume": self.latest_volume,
            "is_suspicious": self.is_suspicious_sound,
            "status": "Suspicious Audio / Noise" if self.is_suspicious_sound else "Quiet / Normal"
        }

    def stop(self):
        self.is_running = False
