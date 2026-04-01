# config.py — Tunable parameters for drowsiness detector

# GPIO
BUZZER_PIN = 23          # BCM pin number for buzzer

# Detection thresholds
EAR_THRESHOLD = 0.22     # Eye Aspect Ratio below this → eyes considered closed
EAR_CONSEC_FRAMES = 20   # Consecutive frames with closed eyes before alert
SAME_DIR_CONSEC_FRAMES = 15  # Consecutive frames with same gaze direction before alert

# Camera
CAMERA_INDEX = 0
FRAME_SCALE = 0.25       # Downscale factor for face recognition (faster on Pi)

# Buzzer
BUZZER_DURATION = 2.0    # Seconds the buzzer stays on per alert

# Known faces
KNOWN_FACES_DIR = "known_faces"
FACE_MATCH_TOLERANCE = 0.6   # Lower = stricter matching
