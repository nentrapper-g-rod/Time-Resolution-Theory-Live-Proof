#!/usr/bin/env python3
"""
TRT Arduino to GitHub Poster
Fetches data from Arduino web server and posts to GitHub
"""

import requests
import json
import base64
from datetime import datetime
import re
import sys
from config import ARDUINO_IP, GITHUB_TOKEN, GITHUB_REPO, GITHUB_FILE

def fetch_arduino_data():
    """Fetch current data from Arduino"""
    try:
        response = requests.get(f"{ARDUINO_IP}/", timeout=5)
        html = response.text

        # Extract data from HTML (simple regex parsing)
        data = {}

        # Extract samples
        match = re.search(r"Samples Collected:</span><span.*?>(\d+)</span>", html)
        if match:
            data['samples'] = int(match.group(1))

        # Extract runtime
        match = re.search(r"Runtime:</span><span.*?>(\d+) seconds</span>", html)
        if match:
            data['runtime'] = int(match.group(1))

        # More extraction logic here...
        data['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        return data
    except Exception as e:
        print(f"Error fetching Arduino data: {e}")
        return None

def post_to_github(data):
    """Post data to GitHub"""
    if not data:
        return False

    # Get current file
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_data = response.json()
            sha = file_data['sha']
        else:
            sha = None  # File doesn't exist yet

        # Prepare new content
        content = json.dumps(data, indent=2)
        encoded_content = base64.b64encode(content.encode()).decode()

        # Update file
        payload = {
            "message": f"TRT data update - {data.get('samples', 0)} samples",
            "content": encoded_content
        }
        if sha:
            payload['sha'] = sha

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"✓ Posted to GitHub: {data.get('samples', 0)} samples")
            return True
        else:
            print(f"✗ GitHub error: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error posting to GitHub: {e}")
        return False

def fetch_boot_log():
    """Fetch boot log from Arduino"""
    try:
        response = requests.get(f"{ARDUINO_IP}/bootlog", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Boot log fetch failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching boot log: {e}")
        return None

def post_boot_log_to_github(boot_data):
    """Post boot log to GitHub"""
    if not boot_data:
        return False

    file_path = "data/boot_log.json"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_data = response.json()
            sha = file_data['sha']
        else:
            sha = None  # File doesn't exist yet

        # Prepare new content
        content = json.dumps(boot_data, indent=2)
        encoded_content = base64.b64encode(content.encode()).decode()

        # Update file
        payload = {
            "message": f"Boot log update - {boot_data.get('boot_timestamp', 'unknown')}",
            "content": encoded_content
        }
        if sha:
            payload['sha'] = sha

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"✓ Posted boot log to GitHub")
            return True
        else:
            print(f"✗ Boot log GitHub error: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error posting boot log to GitHub: {e}")
        return False

if __name__ == "__main__":
    # Post live data
    data = fetch_arduino_data()
    if data:
        post_to_github(data)
    else:
        sys.exit(1)

    # Post boot log (once per run)
    boot_data = fetch_boot_log()
    if boot_data:
        post_boot_log_to_github(boot_data)
