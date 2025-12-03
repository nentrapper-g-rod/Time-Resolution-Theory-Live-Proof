#!/usr/bin/env python3
"""
Accumulate historical data points from JSON files.
Appends current values to a history array so graphs show trends over time.
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")

# Files to track
tracked_files = [
    "control_off.json",
    "control_on.json",
    "sweep_100hz.json",
    "sweep_1khz.json",
    "sweep_10khz.json",
    "sweep_20khz.json",
    "live_trt.json"
]

history_file = DATA_DIR / "history.json"

# Load existing history
history = {}
if history_file.exists():
    with open(history_file) as f:
        history = json.load(f)

# Append current values to history
for filename in tracked_files:
    filepath = DATA_DIR / filename
    if not filepath.exists():
        continue

    try:
        with open(filepath) as f:
            current_data = json.load(f)

        # Initialize history for this file if needed
        if filename not in history:
            history[filename] = []

        # Append current snapshot with timestamp
        history[filename].append({
            'timestamp': datetime.now().isoformat(),
            'timestamp_ms': current_data.get('timestamp_ms', 0),
            'delta_t_100ms': current_data.get('delta_t_100ms', {}),
            'delta_t_10ms': current_data.get('delta_t_10ms', {}),
            'delta_t_1ms': current_data.get('delta_t_1ms', {}),
            'sample_count': current_data.get('sample_count', 0)
        })

        # Keep last 1000 data points per file (limit history size)
        if len(history[filename]) > 1000:
            history[filename] = history[filename][-1000:]

        print(f"✓ Added data point to {filename} history ({len(history[filename])} points total)")

    except Exception as e:
        print(f"✗ Error processing {filename}: {e}")

# Save updated history
with open(history_file, 'w') as f:
    json.dump(history, f, indent=2)

print(f"\n✅ History file updated: {history_file}")
