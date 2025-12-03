#!/usr/bin/env python3
"""
Manually create and upload a raw data file from Arduino serial output.
Collects 500 samples and immediately uploads.
"""

import serial
import json
import base64
import requests
import time
from config import GITHUB_TOKEN

SERIAL_PORT = '/dev/ttyACM1'
BAUD_RATE = 115200
GITHUB_USER = 'nentrapper-g-rod'
GITHUB_REPO = 'Time-Resolution-Theory-Live-Proof'
SAMPLES_TO_COLLECT = 500

print("Collecting 500 samples from Arduino...")

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

samples = []
while len(samples) < SAMPLES_TO_COLLECT:
    try:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if ',' in line:
            parts = line.split(',')
            if len(parts) == 2:
                try:
                    timestamp_s = float(parts[0])
                    voltage = float(parts[1])
                    timestamp_ms = int(timestamp_s * 1000)
                    samples.append({'t_ms': timestamp_ms, 'v': voltage})

                    if len(samples) % 100 == 0:
                        print(f"Collected {len(samples)}/{SAMPLES_TO_COLLECT} samples...")
                except:
                    pass
    except:
        pass

ser.close()

print(f"✓ Collected {len(samples)} samples")

# Determine phase based on timestamp
if len(samples) > 0:
    timestamp_ms = samples[-1]['t_ms']
    if timestamp_ms < 300000:
        phase = 0
        phase_name = 'control_off'
    elif timestamp_ms < 600000:
        phase = 1
        phase_name = 'control_on'
    elif timestamp_ms < 900000:
        phase = 2
        phase_name = 'sweep_100hz'
    elif timestamp_ms < 1200000:
        phase = 3
        phase_name = 'sweep_1khz'
    elif timestamp_ms < 1500000:
        phase = 4
        phase_name = 'sweep_10khz'
    elif timestamp_ms < 1800000:
        phase = 5
        phase_name = 'sweep_20khz'
    else:
        phase = 6
        phase_name = 'live_trt'
else:
    phase = 0
    phase_name = 'control_off'

print(f"Phase detected: {phase} ({phase_name})")

# Build JSON
json_data = {
    'timestamp_ms': int(time.time() * 1000),
    'total_samples_collected': len(samples),
    'sample_count': len(samples),
    'sampling_rate_hz': 1000,
    'phase': phase,
    'phase_name': phase_name,
    'raw_samples': samples
}

json_str = json.dumps(json_data, indent=2)
print(f"JSON size: {len(json_str)} bytes")

# Upload to GitHub
file_path = f'data/raw_{phase_name}.json'
api_url = f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{file_path}'
headers = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# Get existing file SHA
print(f"Uploading to {file_path}...")
sha = None
response = requests.get(api_url, headers=headers)
if response.status_code == 200:
    sha = response.json().get('sha')
    print(f"Found existing file SHA: {sha[:8]}...")

# Upload
content_b64 = base64.b64encode(json_str.encode()).decode()
payload = {
    'message': f'Manual upload of raw {phase_name} data',
    'content': content_b64
}
if sha:
    payload['sha'] = sha

response = requests.put(api_url, headers=headers, json=payload)
if response.status_code in [200, 201]:
    print(f"✅ Successfully uploaded {len(samples)} samples to {file_path}")
else:
    print(f"❌ Upload failed: {response.status_code}")
    print(response.text)
