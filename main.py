import os
import time
import threading
import numpy as np
import cv2
import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1115 import ADS1115

# --- ADC SETUP ---
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
chan = AnalogIn(ads, 0)  # Channel 0 (A0)

# --- Constants ---
TH_TIME = 3  # Seconds threshold must persist before triggering
DISPLAY_DURATION = 1800  # 30 minutes
SAMPLERATE = 100  # Not used for FFT, just for buffer trimming

# --- Thresholds (dB) ---
AmberTH = 85
RedTH = 100
BlackTH = 115
ExtremeTH = 120

# --- Paths ---
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "Images")

images = {
    "amber": cv2.imread(os.path.join(IMAGE_PATH, "amber.png")),
    "red": cv2.imread(os.path.join(IMAGE_PATH, "red.png")),
    "black": cv2.imread(os.path.join(IMAGE_PATH, "black.png")),
    "extreme": cv2.imread(os.path.join(IMAGE_PATH, "extreme.png"))
}

# --- Globals ---
current_image = None
last_threshold_time = None
last_threshold_reached = None
max_threshold_reached = None
image_lock = threading.Lock()

# --- Convert ADC Voltage to dBA ---
def get_noise_level():
    voltage = chan.voltage
    db = (voltage - 0.6) * 100 / (2.6 - 0.6) + 30
    db = max(0, min(db, 130))  # Clamp range
    print(f"Voltage: {voltage:.3f} V → dBA: {db:.2f}")
    return db

# --- Match dBA to image and level ---
def get_image_for_noise(noise_level):
    thresholds = {
        ExtremeTH: "extreme",
        BlackTH: "black",
        RedTH: "red",
        AmberTH: "amber"
    }
    for threshold, image_key in sorted(thresholds.items(), reverse=True):
        if noise_level >= threshold:
            return images[image_key], threshold
    return None, None

# --- Display Reset Thread ---
def reset_display():
    global current_image, max_threshold_reached
    while True:
        time.sleep(DISPLAY_DURATION)
        with image_lock:
            current_image = None
            max_threshold_reached = None

# --- Start Reset Thread ---
threading.Thread(target=reset_display, daemon=True).start()

# --- Main Loop ---
while True:
    noise_level = get_noise_level()
    new_image, threshold_reached = get_image_for_noise(noise_level)

    if threshold_reached is not None:
        if last_threshold_reached != threshold_reached:
            last_threshold_reached = threshold_reached
            last_threshold_time = time.time()
        elif time.time() - last_threshold_time >= TH_TIME:
            if max_threshold_reached is None or threshold_reached > max_threshold_reached:
                with image_lock:
                    current_image = new_image
                    max_threshold_reached = threshold_reached
    else:
        last_threshold_reached = None
        last_threshold_time = None

    with image_lock:
        if current_image is not None:
            cv2.imshow("Noise Level Display", current_image)
        else:
            cv2.imshow("Noise Level Display", np.zeros((240, 320, 3), dtype=np.uint8))

    if cv2.waitKey(100) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
