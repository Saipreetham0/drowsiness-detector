#!/usr/bin/env python3
# test_buzzer.py — Buzzer diagnostic on GPIO 23

import time
import RPi.GPIO as GPIO

BUZZER_PIN = 23

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.output(BUZZER_PIN, GPIO.LOW)

print("=== Buzzer diagnostic on GPIO 23 (BCM) = physical pin 16 ===")
print("Sending 5 long beeps (1 second each)...\n")

for i in range(5):
    print(f"  ON  — beep {i + 1}")
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(1.0)
    print(f"  OFF — beep {i + 1}")
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(0.5)

GPIO.cleanup()
print("\nDone.")
print("If you heard nothing, check:")
print("  1. Buzzer + wire → GPIO 23 (physical pin 16)")
print("  2. Buzzer - wire → any GND pin (e.g. physical pin 14)")
print("  3. Active buzzers need + on positive leg (longer leg)")
print("  4. If buzzer still silent, try wiring it to a 5V pin instead")
print("     (GPIO only outputs 3.3V — some buzzers need 5V)")
