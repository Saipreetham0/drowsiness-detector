#!/usr/bin/env python3
# main.py — Driver Drowsiness Detector (pure OpenCV, no dlib/face_recognition)
# Raspberry Pi 4B  |  picamera2 + OpenCV + RPi.GPIO

import sys
import time
import signal
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


def run():
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(1)  # let sensor settle

    # clean shutdown on Ctrl+C
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

    while True:
        frame_rgb = picam2.capture_array()
        frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        if process_frame:
            small = cv2.resize(frame, (0, 0), fx=FRAME_SCALE, fy=FRAME_SCALE)
            gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            gray  = cv2.equalizeHist(gray)
            faces = _face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )

            face_detected = len(faces) > 0

            if face_detected:
                cv2.imwrite(CAPTURE_FILE, small)
                direction = eye_game.get_eyeball_direction(CAPTURE_FILE)
                print(f"[INFO] Eye state: {direction}")

                # ── Rule 1: eyes closed too long ─────────────────────────────
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

                # ── Rule 2: gaze locked off-centre ───────────────────────────
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
                print("[INFO] No face detected")

        process_frame = not process_frame

    picam2.stop()
    GPIO.cleanup()
    print("[INFO] Shutdown complete.")


if __name__ == "__main__":
    run()
