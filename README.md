# Driver Drowsiness Detector

A real-time drowsiness and distraction detection system built for the **Raspberry Pi 4B** using a Pi Camera Module and an active buzzer. No internet connection or cloud service required — everything runs locally on the Pi.

Live preview is accessible from any device on the same WiFi network via browser at `http://<pi-ip>:8080`.

---

## How It Works

The system captures frames from the Pi Camera, detects the driver's face using OpenCV Haar cascades, and analyses the eye region to determine eye state and gaze direction.

Two alert rules run continuously:

| Rule | Trigger | Action |
|------|---------|--------|
| Drowsiness | Eyes closed for 20 consecutive frames | Buzzer sounds for 2 seconds |
| Distraction | Gaze locked left or right for 15 consecutive frames | Buzzer sounds for 2 seconds |

A live MJPEG stream with on-screen status overlay runs in the background and is viewable from any browser on the local network.

---

## Hardware

| Component | Model | Notes |
|-----------|-------|-------|
| Microcontroller | Raspberry Pi 4B | Any RAM variant |
| Camera | 5MP Pi Camera Module (OV5647) Rev 1.3 | Connected via CSI ribbon cable |
| Buzzer | TMB12A12 | 12V active buzzer |
| Transistor | BC547 NPN | Drives the 12V buzzer from 3.3V GPIO |
| Resistor | 1 kΩ | Base resistor for BC547 |
| Power supply | 9–12V DC | For the buzzer circuit |

### Wiring

**Camera** — connect to the CSI camera port on the Pi (ribbon cable, blue side toward USB ports).

**Buzzer circuit** (GPIO 23 → BC547 → TMB12A12):

```
Pi GPIO 23 (pin 16) ──[1kΩ]──► BC547 BASE   (middle pin, flat face toward you)
                               BC547 EMITTER (right pin)  ──► GND (Pi pin 14)
                               BC547 COLLECTOR (left pin) ──► Buzzer (−) short leg

9–12V supply (+) ──► Buzzer (+) long leg
9–12V supply (−) ──► GND rail (same as Pi GND)
```

> **Note:** GPIO outputs only 3.3V. The BC547 transistor is required to switch the 12V needed by the TMB12A12. Do not connect the buzzer directly to a GPIO pin.

---

## Project Structure

```
drowsiness-detector/
├── main.py            # Main detection loop + MJPEG stream server
├── eye_game.py        # Face + eye detection and gaze analysis
├── config.py          # Tunable parameters
├── test_camera.py     # Standalone camera test (saves snapshots)
├── test_buzzer.py     # Standalone buzzer test (5 beeps)
├── setup.sh           # One-time system setup script
├── run.sh             # Launch script
├── requirements.txt   # Python dependencies
├── image_data/        # Runtime frame storage (auto-created, git-ignored)
└── known_faces/       # Reserved for future face recognition
```

---

## Setup

Run once after cloning:

```bash
chmod +x setup.sh run.sh
./setup.sh
```

This installs system packages (`python3-opencv`, `opencv-data`), creates a virtual environment, and installs `RPi.GPIO` and `picamera2`.

---

## Running

```bash
python3 main.py
```

Or using the launch script:

```bash
./run.sh
```

On startup you will see:

```
[INFO] Live preview → http://192.168.1.x:8080
[INFO] Starting — press Ctrl+C to quit.
```

Open the URL in any browser on the same WiFi to watch the live feed.

Press **Ctrl+C** to stop — camera and GPIO shut down cleanly.

---

## Live Preview

The stream runs on port **8080** and is accessible from any device on the same network:

```
http://<raspberry-pi-ip>:8080
```

**Status overlay colours:**

| Colour | Meaning |
|--------|---------|
| Green `CENTER` | Eyes open, looking forward — normal |
| Red `CLOSED 45%` | Eyes closing — percentage toward drowsiness alert |
| Orange `GAZE LEFT 80%` | Looking away — percentage toward distraction alert |
| Grey `NO FACE` | No face detected in frame |

A green rectangle is drawn around the detected face in real time.

---

## Testing Components Individually

**Camera** — captures 5 snapshots to `image_data/`:

```bash
python3 test_camera.py
```

**Buzzer** — sounds 5 beeps (1 second each):

```bash
python3 test_buzzer.py
```

---

## Configuration

Edit `config.py` to tune detection sensitivity:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `BUZZER_PIN` | `23` | BCM GPIO pin connected to BC547 base |
| `EAR_CONSEC_FRAMES` | `20` | Frames with closed eyes before drowsiness alert |
| `SAME_DIR_CONSEC_FRAMES` | `15` | Frames with fixed off-centre gaze before distraction alert |
| `FRAME_SCALE` | `0.25` | Frame downscale factor for face detection (lower = faster) |
| `BUZZER_DURATION` | `2.0` | Seconds the buzzer stays on per alert |

---

## Dependencies

- `python3-opencv` — face and eye detection via Haar cascades
- `picamera2` — Pi Camera Module (OV5647) interface via libcamera
- `RPi.GPIO` — GPIO control for buzzer transistor circuit

Haar cascade XML files are read from `/usr/share/opencv4/haarcascades/` (installed with `opencv-data`).

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Device or resource busy` | Another process holds the camera | Run `sudo fuser /dev/video0` and kill the process |
| Blue tint in stream | Colour format mismatch | Already fixed — `RGB888` format used, no conversion |
| No face detected | Poor lighting or distance | Sit 30–60 cm from camera in good light |
| Buzzer silent | Wiring or voltage issue | Check BC547 pinout (C–B–E flat side), verify 9–12V supply |
| Stream not loading | Firewall or wrong IP | Check Pi IP with `hostname -I`, ensure port 8080 is open |
| libcamera logs in terminal | Normal info messages | Run with `python3 main.py 2>/dev/null` to suppress |
