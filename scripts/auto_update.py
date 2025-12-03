#!/usr/bin/env python3
"""
TRT Auto-Update Script
Pulls data from Arduino every 30 seconds, generates graphs, and pushes to GitHub
"""

import requests
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Configuration
ARDUINO_IP = "http://192.168.1.91"
UPDATE_INTERVAL = 30  # seconds
REPO_DIR = Path("/home/joshuag/Time-Resolution-Theory-Live-Proof")
DATA_DIR = REPO_DIR / "data"
SCRIPTS_DIR = REPO_DIR / ".github" / "scripts"

def fetch_arduino_data():
    """Fetch current data from Arduino"""
    try:
        response = requests.get(f"{ARDUINO_IP}/data", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Arduino returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching Arduino data: {e}")
        return None

def save_data(data, filename):
    """Save data to JSON file"""
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return False

def generate_graphs():
    """Run the graph generation script"""
    try:
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "make_graphs.py")],
            cwd=REPO_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Graphs generated")
            return True
        else:
            print(f"❌ Graph generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error generating graphs: {e}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        # Add all changes
        subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)

        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=REPO_DIR
        )

        if result.returncode != 0:  # There are changes
            # Commit
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            commit_msg = f"Auto-update TRT data and graphs - {timestamp}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=REPO_DIR,
                check=True
            )

            # Push
            subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
            print("✓ Pushed to GitHub")
            return True
        else:
            print("• No changes to push")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error pushing to GitHub: {e}")
        return False

def main():
    """Main loop"""
    print("=" * 60)
    print("TRT AUTO-UPDATE SCRIPT")
    print("=" * 60)
    print(f"Arduino: {ARDUINO_IP}")
    print(f"Update interval: {UPDATE_INTERVAL} seconds")
    print(f"Data directory: {DATA_DIR}")
    print("=" * 60)
    print()

    iteration = 0

    while True:
        iteration += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{timestamp}] Iteration #{iteration}")
        print("-" * 60)

        # Step 1: Fetch data from Arduino
        print("1. Fetching data from Arduino...")
        data = fetch_arduino_data()

        if data:
            print(f"   ✓ Received data: {data.get('samples', '?')} samples, phase {data.get('phase', '?')}")

            # Step 2: Save data locally
            print("2. Saving data locally...")
            save_data(data, "live_trt.json")

            # Also save to live_data directory for compatibility
            live_data_dir = REPO_DIR / "live_data"
            live_data_dir.mkdir(exist_ok=True)
            save_data(data, "../live_data/trt_live_data.json")

            # Step 3: Generate graphs
            print("3. Generating graphs...")
            generate_graphs()

            # Step 4: Push to GitHub
            print("4. Pushing to GitHub...")
            push_to_github()

            print(f"✅ Cycle complete")
        else:
            print("⚠️  Skipping this cycle (no data)")

        # Wait for next iteration
        print(f"\n⏳ Waiting {UPDATE_INTERVAL} seconds until next update...")
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user (Ctrl+C)")
        print("Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        raise
