#!/usr/bin/env python3
# main.py — Driver Drowsiness Detector (pure OpenCV, no dlib/face_recognition)
# Raspberry Pi 4B  |  picamera2 + OpenCV + RPi.GPIO
# Live preview → http://<pi-ip>:8080

import sys
import time
import signal
import threading
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import cv2
import numpy as np
import RPi.GPIO as GPIO
from picamera2 import Picamera2

import eye_game
from config import (
    BUZZER_PIN, EAR_CONSEC_FRAMES, SAME_DIR_CONSEC_FRAMES,
    FRAME_SCALE, BUZZER_DURATION,
)

CAPTURE_FILE = "image_data/frame.jpg"
STREAM_PORT  = 8080

# ── Shared frame buffer ───────────────────────────────────────────────────────
_frame_lock  = threading.Lock()
_jpeg_buffer = b""


def _set_frame(bgr_frame):
    global _jpeg_buffer
    _, jpg = cv2.imencode(".jpg", bgr_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    with _frame_lock:
        _jpeg_buffer = jpg.tobytes()


def _get_frame():
    with _frame_lock:
        return _jpeg_buffer


# ── MJPEG HTTP server ─────────────────────────────────────────────────────────
class _StreamHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silence request logs

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <html><head><title>Drowsiness Detector</title>
            <style>body{background:#000;display:flex;justify-content:center;
            align-items:center;height:100vh;margin:0;}
            img{max-width:100%;border:2px solid #0f0;}</style></head>
            <body><img src="/stream"></body></html>
            """)
        elif self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while True:
                    jpg = _get_frame()
                    if jpg:
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                        self.wfile.write(jpg)
                        self.wfile.write(b"\r\n")
                    time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                pass


def _start_stream_server():
    server = HTTPServer(("0.0.0.0", STREAM_PORT), _StreamHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "192.168.1.7"
    print(f"[INFO] Live preview → http://{ip}:{STREAM_PORT}")


# ── GPIO setup ───────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.output(BUZZER_PIN, GPIO.LOW)

# ── Face detector ────────────────────────────────────────────────────────────
_face_cascade = cv2.CascadeClassifier(
    "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
)


def alert(message):
    print(f"[ALERT] {message}")
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(BUZZER_DURATION)
    GPIO.output(BUZZER_PIN, GPIO.LOW)


def _draw_status(frame, direction, closed_count, same_dir_count, face_detected):
    h, w = frame.shape[:2]

    if not face_detected:
        label, color = "NO FACE", (100, 100, 100)
    elif direction == "CLOSED":
        pct = int(closed_count / EAR_CONSEC_FRAMES * 100)
        label, color = f"CLOSED {pct}%", (0, 0, 255)
    elif direction in ("LEFT", "RIGHT"):
        pct = int(same_dir_count / SAME_DIR_CONSEC_FRAMES * 100)
        label, color = f"GAZE {direction} {pct}%", (0, 165, 255)
    else:
        label, color = direction, (0, 255, 0)

    cv2.rectangle(frame, (0, 0), (w, 36), (0, 0, 0), -1)
    cv2.putText(frame, label, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


def run():
    _start_stream_server()

    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(1)

    def _shutdown(sig, frame):
        print("\n[INFO] Interrupted — shutting down.")
        picam2.stop()
        GPIO.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)

    print("[INFO] Starting — press Ctrl+C to quit.")

    closed_count   = 0
    same_dir_count = 0
    prev_direction = None
    process_frame  = True
    direction      = "Unknown"
    face_detected  = False

    while True:
        frame = picam2.capture_array()

        if process_frame:
            small = cv2.resize(frame, (0, 0), fx=FRAME_SCALE, fy=FRAME_SCALE)
            gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            gray  = cv2.equalizeHist(gray)
            faces = _face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )

            face_detected = len(faces) > 0

            if face_detected:
                # draw face box on full frame
                scale = int(1 / FRAME_SCALE)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame,
                                  (x * scale, y * scale),
                                  ((x + w) * scale, (y + h) * scale),
                                  (0, 255, 0), 2)

                cv2.imwrite(CAPTURE_FILE, small)
                direction = eye_game.get_eyeball_direction(CAPTURE_FILE)
                print(f"[INFO] Eye state: {direction}")

                if direction == "CLOSED":
                    closed_count += 1
                    same_dir_count = 0
                    prev_direction = None
                    print(f"  CLOSED frame {closed_count}/{EAR_CONSEC_FRAMES}")
                    if closed_count >= EAR_CONSEC_FRAMES:
                        alert("DROWSINESS DETECTED — eyes closed too long!")
                        closed_count = 0
                else:
                    closed_count = 0

                if direction not in ("CLOSED", "Unknown"):
                    if direction == prev_direction and direction != "CENTER":
                        same_dir_count += 1
                        print(f"  Gaze {direction} locked — frame {same_dir_count}/{SAME_DIR_CONSEC_FRAMES}")
                        if same_dir_count >= SAME_DIR_CONSEC_FRAMES:
                            alert("DISTRACTION DETECTED — driver not watching road!")
                            same_dir_count = 0
                    else:
                        same_dir_count = 0
                        prev_direction = direction
            else:
                direction = "Unknown"
                print("[INFO] No face detected")

        _draw_status(frame, direction, closed_count, same_dir_count, face_detected)
        _set_frame(frame)

        process_frame = not process_frame

    picam2.stop()
    GPIO.cleanup()
    print("[INFO] Shutdown complete.")


if __name__ == "__main__":
    run()
