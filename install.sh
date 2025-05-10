#!/bin/bash

echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "Installing required system packages..."
sudo apt install -y python3 python3-pip python3-venv \
    python3-opencv libatlas-base-dev portaudio19-dev \
    i2c-tools python3-pil libjpeg-dev

echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

echo "Installing Python libraries..."
pip3 install numpy sounddevice opencv-python \
    adafruit-circuitpython-ads1x15 matplotlib

echo "Checking available I2C devices..."
i2cdetect -y 1

echo "Creating autostart service..."
SERVICE_NAME=noise-monitor
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME.service

sudo bash -c "cat > $SERVICE_PATH" <<EOF
[Unit]
Description=Noise Monitor Display
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/noise-monitor/main.py
WorkingDirectory=/home/pi/noise-monitor
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo "Installation complete."
echo "Your program will now run on boot. Rebooting..."
sudo reboot
