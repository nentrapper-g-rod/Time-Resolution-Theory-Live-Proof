#!/usr/bin/env python3
"""
TRT Auto-Update Script
Pulls data from Arduino, generates graphs, and pushes to GitHub
"""

import requests
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Paths
REPO_DIR = Path("/home/joshuag/Time-Resolution-Theory-Live-Proof")
SCRIPTS_DIR = REPO_DIR / "scripts"
CONFIG_FILE = SCRIPTS_DIR / "config.json"
ACTIVITY_LOG = SCRIPTS_DIR / "activity.json"

def load_config():
    """Load configuration"""
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except:
        return {
            "arduino_ip": "http://192.168.1.91",
            "update_interval": 30,
            "repo_dir": str(REPO_DIR),
            "data_dir": "data",
            "github_enabled": True,
            "max_history_points": 200
        }

def load_activity():
    """Load activity log"""
    try:
        with open(ACTIVITY_LOG) as f:
            return json.load(f)
    except:
        return {"pushes": [], "stats": {"total_pushes": 0, "total_files": 0}}

def save_activity(activity):
    """Save activity log"""
    with open(ACTIVITY_LOG, 'w') as f:
        json.dump(activity, f, indent=2)

def log_push(files):
    """Log a GitHub push"""
    activity = load_activity()
    activity["pushes"].append({
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "files": files
    })
    # Keep last 100 pushes
    activity["pushes"] = activity["pushes"][-100:]
    activity["stats"]["total_pushes"] += 1
    activity["stats"]["total_files"] += len(files)
    save_activity(activity)

def fetch_arduino_data(arduino_ip):
    """Fetch current data from Arduino"""
    try:
        response = requests.get(f"{arduino_ip}/data", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Arduino returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching Arduino data: {e}")
        return None

def save_data(data, filename, data_dir):
    """Save data to JSON file"""
    filepath = REPO_DIR / data_dir / filename
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
            ["python3", str(REPO_DIR / ".github" / "scripts" / "make_graphs.py")],
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

def get_changed_files():
    """Get list of changed files"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in result.stdout.split('\n') if f.strip()]
    except:
        return []

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
            # Get list of files being committed
            changed_files = get_changed_files()

            # Commit
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            commit_msg = f"Auto-update TRT data and graphs - {timestamp}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=REPO_DIR,
                check=True
            )

            # Pull before pushing (in case of remote changes)
            pull_result = subprocess.run(
                ["git", "pull", "origin", "main", "--no-rebase"],
                cwd=REPO_DIR,
                capture_output=True,
                text=True
            )

            # Check for merge conflicts
            if pull_result.returncode != 0 and "CONFLICT" in pull_result.stdout:
                print("⚠️  Merge conflict detected, resolving...")

                # Fetch latest data from Arduino to resolve conflict
                config = load_config()
                data = fetch_arduino_data(config['arduino_ip'])
                if data:
                    # Write latest data to resolve conflict
                    conflict_file = REPO_DIR / "live_data" / "trt_live_data.json"
                    with open(conflict_file, 'w') as f:
                        json.dump(data, f, indent=2)

                    # Add resolved file and commit
                    subprocess.run(["git", "add", str(conflict_file)], cwd=REPO_DIR, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", f"Resolve merge conflict with latest Arduino data\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"],
                        cwd=REPO_DIR,
                        check=True
                    )
                    print("✓ Conflict resolved")

            # Push
            subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
            print(f"✓ Pushed to GitHub ({len(changed_files)} files)")

            # Log the push
            log_push(changed_files)
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
    config = load_config()

    print("=" * 60)
    print("TRT AUTO-UPDATE SCRIPT")
    print("=" * 60)
    print(f"Arduino: {config['arduino_ip']}")
    print(f"Update interval: {config['update_interval']} seconds")
    print(f"Data directory: {config['data_dir']}")
    print(f"GitHub pushing: {'Enabled' if config['github_enabled'] else 'Disabled'}")
    print("=" * 60)
    print()

    iteration = 0

    while True:
        # Reload config each iteration (allows live updates)
        config = load_config()

        iteration += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{timestamp}] Iteration #{iteration}")
        print("-" * 60)

        # Step 1: Fetch data from Arduino
        print("1. Fetching data from Arduino...")
        data = fetch_arduino_data(config['arduino_ip'])

        if data:
            print(f"   ✓ Received data: {data.get('samples', '?')} samples, phase {data.get('phase', '?')}")

            # Step 2: Save data locally
            print("2. Saving data locally...")
            save_data(data, "live_trt.json", config['data_dir'])

            # Also save to live_data directory for compatibility
            live_data_dir = "live_data"
            (REPO_DIR / live_data_dir).mkdir(exist_ok=True)
            save_data(data, "trt_live_data.json", live_data_dir)

            # Step 3: Generate graphs
            print("3. Generating graphs...")
            generate_graphs()

            # Step 4: Push to GitHub (if enabled)
            if config['github_enabled']:
                print("4. Pushing to GitHub...")
                push_to_github()
            else:
                print("4. GitHub pushing disabled (skipping)")

            print(f"✅ Cycle complete")
        else:
            print("⚠️  Skipping this cycle (no data)")

        # Wait for next iteration
        print(f"\n⏳ Waiting {config['update_interval']} seconds until next update...")
        time.sleep(config['update_interval'])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user (Ctrl+C)")
        print("Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        raise
