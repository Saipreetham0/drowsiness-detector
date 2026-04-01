# eye_game.py — Eye state and gaze detection using OpenCV Haar cascades
# No external model downloads required — cascades are bundled with OpenCV.

import cv2
import numpy as np

_CASCADE_DIR = "/usr/share/opencv4/haarcascades/"
_face_cascade = cv2.CascadeClassifier(_CASCADE_DIR + "haarcascade_frontalface_default.xml")
_eye_cascade  = cv2.CascadeClassifier(_CASCADE_DIR + "haarcascade_eye.xml")


def _pupil_direction(eye_gray):
    """Return LEFT / RIGHT / CENTER by finding where the dark pupil sits."""
    if eye_gray.size == 0:
        return "CENTER"
    # Isolate dark pupil/iris via inverse threshold
    blurred = cv2.GaussianBlur(eye_gray, (7, 7), 0)
    _, thresh = cv2.threshold(blurred, 45, 255, cv2.THRESH_BINARY_INV)

    h, w = thresh.shape
    left_mass  = cv2.countNonZero(thresh[:, : w // 2])
    right_mass = cv2.countNonZero(thresh[:, w // 2 :])
    total = left_mass + right_mass
    if total == 0:
        return "CENTER"

    ratio = left_mass / total   # >0.5 means pupil skewed left
    if ratio < 0.35:
        return "RIGHT"
    if ratio > 0.65:
        return "LEFT"
    return "CENTER"


def get_eyeball_direction(image_path):
    """
    Analyse a saved frame and return one of:
      'CLOSED'  — no eyes detected (drowsy / blinking)
      'LEFT'    — gaze to the left
      'RIGHT'   — gaze to the right
      'CENTER'  — normal forward gaze
      'Unknown' — no face detected in the image
    """
    frame = cv2.imread(image_path)
    if frame is None:
        return "Unknown"

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)   # improve detection in low light

    faces = _face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    if len(faces) == 0:
        return "Unknown"

    # Use the largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]

    # Only search the upper half of the face (eye region)
    face_roi = gray[y : y + h // 2, x : x + w]

    eyes = _eye_cascade.detectMultiScale(
        face_roi, scaleFactor=1.1, minNeighbors=8, minSize=(20, 20)
    )

    if len(eyes) == 0:
        return "CLOSED"

    # Determine gaze from up to 2 detected eyes
    directions = []
    for ex, ey, ew, eh in eyes[:2]:
        roi = face_roi[ey : ey + eh, ex : ex + ew]
        directions.append(_pupil_direction(roi))

    if "LEFT"  in directions:
        return "LEFT"
    if "RIGHT" in directions:
        return "RIGHT"
    return "CENTER"
