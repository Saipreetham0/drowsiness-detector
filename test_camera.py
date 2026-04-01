#!/usr/bin/env python3
# test_camera.py — Headless camera test, saves 5 snapshots

import cv2
import time
from picamera2 import Picamera2

SAVE_DIR = "image_data"
NUM_SHOTS = 5

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()
time.sleep(1)  # let sensor settle

print(f"[INFO] Camera started (OV5647 640x480). Saving {NUM_SHOTS} snapshots to {SAVE_DIR}/")

for i in range(NUM_SHOTS):
    frame = picam2.capture_array()
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    path = f"{SAVE_DIR}/test_{i+1}.jpg"
    cv2.imwrite(path, bgr)
    h, w = bgr.shape[:2]
    print(f"  Saved {path}  ({w}x{h})")
    time.sleep(0.5)

picam2.stop()
print("[INFO] Done. Check image_data/test_1.jpg … test_5.jpg")
