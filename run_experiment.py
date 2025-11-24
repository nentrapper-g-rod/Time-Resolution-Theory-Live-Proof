# Time-Resolution-Theory-Live-Proof — Python logger
# Reads serial, applies three Δt resolutions, pushes JSON to repo

import serial, time, json, numpy as np
from scipy.ndimage import gaussian_filter1d
import requests

# --- CONFIG ---
SERIAL_PORT = "COM3"          # Windows → change to your port
# SERIAL_PORT = "/dev/ttyUSB0"  # Linux/Mac
BAUD = 115200
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # ← your PAT
REPO = "nentrapper-g-rod/Time-Resolution-Theory-Live-Proof"
FILE_PATH = "data/latest.json"
# ----------------

ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

print("TRT Live Proof — recording...")

while True:
    samples = []
    start = time.time()
    while time.time() - start < 60:               # collect 60 seconds
        line = ser.readline().decode('utf-8').strip()
        if line and ',' in line:
            _, voltage = line.split(',')
            samples.append(float(voltage))
    data = np.array(samples)

    result = {}
    for dt_ms, label in [(100, "100ms"), (10, "10ms"), (1, "1ms")]:
        sigma = dt_ms / 2.355
        blurred = gaussian_filter1d(data, sigma)
        result[label] = {
            "mean": round(float(np.mean(blurred)), 6),
            "variance": round(float(np.var(blurred)), 6)
        }
    result["timestamp"] = int(time.time())

    # Push to GitHub
    payload = {
        "message": "Live TRT data update",
        "content": json.dumps(result, indent=2)
    }
    r = requests.put(url, headers=headers, json=payload)
    print(f"[{time.strftime('%H:%M:%S')}] Updated — coarse Δt mean ≈ {result['100ms']['mean']:.6f}")

    time.sleep(1)
