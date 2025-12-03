#!/usr/bin/env python3
"""
Reset TRT Experiment Data
Deletes all JSON data files from GitHub /data/ directory
"""

import requests
import sys
from config import GITHUB_TOKEN

GITHUB_USER = 'nentrapper-g-rod'
GITHUB_REPO = 'Time-Resolution-Theory-Live-Proof'

# Files to delete
DATA_FILES = [
    'control_off.json',
    'control_on.json',
    'sweep_100hz.json',
    'sweep_1khz.json',
    'sweep_10khz.json',
    'sweep_20khz.json',
    'live_trt.json',
    'raw_control_off.json',
    'raw_control_on.json',
    'raw_sweep_100hz.json',
    'raw_sweep_1khz.json',
    'raw_sweep_10khz.json',
    'raw_sweep_20khz.json',
    'raw_live_trt.json',
    'cycle_history.json',
    'cycle_tests.json',
    'history.json',
    'latest.json'
]

def delete_file(filename):
    """Delete a file from GitHub"""
    api_url = f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/data/{filename}'
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get file SHA
    response = requests.get(api_url, headers=headers)
    if response.status_code == 404:
        print(f"  {filename} - doesn't exist (skipping)")
        return True
    elif response.status_code != 200:
        print(f"  {filename} - error getting file: {response.status_code}")
        return False

    sha = response.json().get('sha')
    if not sha:
        print(f"  {filename} - couldn't get SHA")
        return False

    # Delete file
    payload = {
        'message': f'Reset experiment: delete {filename}',
        'sha': sha
    }

    response = requests.delete(api_url, headers=headers, json=payload)
    if response.status_code in [200, 204]:
        print(f"  {filename} - deleted ✓")
        return True
    else:
        print(f"  {filename} - delete failed: {response.status_code}")
        return False

def main():
    print("=" * 60)
    print("TRT EXPERIMENT DATA RESET")
    print("=" * 60)
    print()
    print("This will DELETE all experiment data files from GitHub.")
    print()

    # Ask for confirmation
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Reset cancelled.")
        return 0

    print()
    print("Deleting data files from GitHub...")
    print()

    success_count = 0
    for filename in DATA_FILES:
        if delete_file(filename):
            success_count += 1

    print()
    print("=" * 60)
    print(f"Reset complete: {success_count}/{len(DATA_FILES)} files processed")
    print("=" * 60)
    print()
    print("The Arduino will create new data files automatically.")
    print("Cycle count will reset to 0 on next Arduino reboot.")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
