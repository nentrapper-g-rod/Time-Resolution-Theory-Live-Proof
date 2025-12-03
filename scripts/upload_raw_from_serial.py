#!/usr/bin/env python3
"""
Read raw voltage data from Arduino serial output and upload to GitHub.
This script collects samples from the serial stream, batches them, and uploads
raw data files that the Arduino itself cannot upload due to memory constraints.
"""

import serial
import time
import json
import base64
import requests
from collections import deque
from datetime import datetime
from config import GITHUB_TOKEN

# Configuration
SERIAL_PORT = '/dev/ttyACM0'  # Current port
BAUD_RATE = 115200
GITHUB_USER = 'nentrapper-g-rod'
GITHUB_REPO = 'Time-Resolution-Theory-Live-Proof'
SAMPLES_PER_UPLOAD = 500
UPLOAD_INTERVAL = 60  # 1 minute (as per user requirement)

# Phase mapping
PHASE_NAMES = {
    0: 'control_off',
    1: 'control_on',
    2: 'sweep_100hz',
    3: 'sweep_1khz',
    4: 'sweep_10khz',
    5: 'sweep_20khz',
    6: 'live_trt'
}

class RawDataUploader:
    def __init__(self):
        self.samples = deque(maxlen=SAMPLES_PER_UPLOAD)
        self.current_phase = 0
        self.current_cycle = 0
        self.last_upload_time = time.time()
        self.total_samples = 0

    def parse_serial_line(self, line):
        """Parse CSV line: timestamp,voltage,cycle,phase"""
        try:
            parts = line.strip().split(',')
            if len(parts) == 4:
                timestamp_s = float(parts[0])
                voltage = float(parts[1])
                cycle = int(parts[2])
                phase = int(parts[3])
                return int(timestamp_s * 1000), voltage, cycle, phase
            elif len(parts) == 2:
                # Fallback for old format (backward compatibility)
                timestamp_s = float(parts[0])
                voltage = float(parts[1])
                return int(timestamp_s * 1000), voltage, None, None
        except:
            pass
        return None

    def upload_to_github(self):
        """Upload collected samples to GitHub with cycle-based appending"""
        if len(self.samples) == 0:
            print("No samples to upload")
            return

        phase_name = PHASE_NAMES.get(self.current_phase, 'unknown')
        file_path = f'data/raw_{phase_name}.json'

        # Build cycle data entry
        cycle_samples = [{'t_ms': t, 'v': v} for t, v, _, _ in self.samples]

        # Get current file content (if exists)
        api_url = f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{file_path}'
        headers = {
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }

        sha = None
        existing_data = {}

        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            file_info = response.json()
            sha = file_info.get('sha')
            print(f"Found existing file SHA: {sha[:8]}...")

            # Decode existing content
            content_b64 = file_info.get('content', '')
            if content_b64:
                try:
                    content = base64.b64decode(content_b64).decode('utf-8')
                    existing_data = json.loads(content)
                except:
                    print("Could not parse existing file, will overwrite")
                    existing_data = {}

        # Add new cycle data (append to existing samples if cycle already exists)
        cycle_key = f'cycle_{self.current_cycle}'
        if cycle_key in existing_data:
            # Append to existing cycle samples
            existing_data[cycle_key].extend(cycle_samples)
            print(f"Appending {len(cycle_samples)} samples to existing {cycle_key}")
        else:
            # Create new cycle entry
            existing_data[cycle_key] = cycle_samples
            print(f"Creating new {cycle_key} with {len(cycle_samples)} samples")

        json_str = json.dumps(existing_data, indent=2)
        print(f"Uploading cycle {self.current_cycle} phase {self.current_phase} ({phase_name})")
        print(f"Total JSON size: {len(json_str)} bytes")

        # Upload file
        content_b64 = base64.b64encode(json_str.encode()).decode()
        payload = {
            'message': f'Cycle {self.current_cycle} raw data for {phase_name}',
            'content': content_b64
        }
        if sha:
            payload['sha'] = sha

        response = requests.put(api_url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print(f"✓ Successfully uploaded to {file_path}")
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(response.text)

    def process_sample(self, timestamp_ms, voltage, cycle=None, phase=None):
        """Process a sample and upload if needed"""
        self.samples.append((timestamp_ms, voltage, cycle, phase))
        self.total_samples += 1

        # Update cycle and phase from Serial data (if provided)
        if cycle is not None and phase is not None:
            # Check for phase change
            if phase != self.current_phase:
                print(f"Phase changed: {self.current_phase} → {phase}")
                # Upload current phase data before switching
                if len(self.samples) > 0:
                    self.upload_to_github()
                    self.samples.clear()
                self.current_phase = phase
                self.last_upload_time = time.time()

            # Check for cycle change
            if cycle != self.current_cycle:
                print(f"Cycle changed: {self.current_cycle} → {cycle}")
                self.current_cycle = cycle

        # Upload periodically (every minute as per user's requirement)
        if time.time() - self.last_upload_time >= UPLOAD_INTERVAL:
            self.upload_to_github()
            self.samples.clear()
            self.last_upload_time = time.time()

def main():
    print("TRT Raw Data Uploader")
    print(f"Connecting to {SERIAL_PORT}...")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for connection
        print("Connected!")

        uploader = RawDataUploader()

        while True:
            try:
                line = ser.readline().decode('utf-8', errors='ignore')
                parsed = uploader.parse_serial_line(line)

                if parsed:
                    if len(parsed) == 4:
                        timestamp_ms, voltage, cycle, phase = parsed
                        uploader.process_sample(timestamp_ms, voltage, cycle, phase)
                    elif len(parsed) == 2:
                        # Old format fallback
                        timestamp_ms, voltage = parsed
                        uploader.process_sample(timestamp_ms, voltage)

                    # Print status every 1000 samples
                    if uploader.total_samples % 1000 == 0:
                        print(f"Collected {uploader.total_samples} samples, cycle {uploader.current_cycle}, phase {uploader.current_phase}")

            except KeyboardInterrupt:
                print("\nStopping...")
                # Upload any remaining samples
                if len(uploader.samples) > 0:
                    uploader.upload_to_github()
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
