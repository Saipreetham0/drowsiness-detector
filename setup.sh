#!/bin/bash
# setup.sh — One-time setup for Drowsiness Detector on Raspberry Pi 4B (Debian trixie)

set -e
cd "$(dirname "$0")"

echo "=== Installing system packages ==="
sudo apt-get update -y
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-opencv \
    python3-numpy \
    opencv-data

echo ""
echo "=== Creating virtual environment ==="
python3 -m venv venv --system-site-packages

echo ""
echo "=== Installing Python packages (fast — no compilation) ==="
venv/bin/pip install --upgrade pip
venv/bin/pip install RPi.GPIO picamera2

echo ""
echo "=== Creating required directories ==="
mkdir -p image_data

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Run the detector:"
echo "  ./run.sh"
