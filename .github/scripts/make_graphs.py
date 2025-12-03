#!/usr/bin/env python3
"""
Generate TRT validation graphs from JSON data
Auto-runs via GitHub Actions every 10 minutes
"""

import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# File mappings: (json_file, png_file, title, color)
files = [
    ("control_off.json",    "control_off.png",    "CONTROL: LED OFF",     "#FF0000"),
    ("control_on.json",     "control_on.png",     "CONTROL: LED 100% ON", "#00FF00"),
    ("sweep_100hz.json",    "sweep_100hz.png",    "100 Hz Sweep",         "#FFFF00"),
    ("sweep_1khz.json",     "sweep_1khz.png",     "1 kHz Sweep",          "#00FFFF"),
    ("sweep_10khz.json",    "sweep_10khz.png",    "10 kHz Sweep",         "#FF00FF"),
    ("sweep_20khz.json",    "sweep_20khz.png",    "20 kHz Sweep",         "#FFFFFF"),
    ("live_trt.json",       "live_trt.png",       "TRT LIVE PROOF",       "#00FFFF"),
]

# Load history file if it exists
history_file = DATA_DIR / "history.json"
history_data = {}
if history_file.exists():
    with open(history_file) as f:
        history_data = json.load(f)

for json_file, png_file, title, color in files:
    path = DATA_DIR / json_file
    if not path.exists():
        print(f"Skipping {json_file} (not found)")
        continue

    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_file}: {e}")
        continue

    # Build accumulated history
    history_key = json_file.replace('.json', '_history')
    if history_key not in history_data:
        history_data[history_key] = []

    # Add current data point to history
    if "history" in data:
        # Already has history, use it
        history_data[history_key] = data["history"][-200:]
    else:
        # Single data point - append to accumulated history
        history_data[history_key].append(data)
        history_data[history_key] = history_data[history_key][-200:]  # Keep last 200

    # Extract data from history
    times = []
    mean100 = []
    var100 = []
    mean10 = []
    var10 = []
    mean1 = []

    entries = history_data[history_key]

    for i, entry in enumerate(entries):
        # Use index as time if no timestamp
        t = entry.get("timestamp_ms", i * 1000) / 1000.0  # Convert to seconds
        times.append(t)

        # Extract mean values
        mean100.append(entry.get("delta_t_100ms", {}).get("mean", 0))
        var100.append(entry.get("delta_t_100ms", {}).get("variance", 0))
        mean10.append(entry.get("delta_t_10ms", {}).get("mean", 0))
        var10.append(entry.get("delta_t_10ms", {}).get("variance", 0))
        mean1.append(entry.get("delta_t_1ms", {}).get("mean", 0))

    if len(times) < 1:
        print(f"No data points for {json_file}")
        continue

    # Create figure with 2 subplots: Mean and Variance
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.patch.set_facecolor('#1a1a1a')

    # Plot 1: Mean values
    ax1.set_facecolor('#2a2a2a')
    ax1.plot(times, mean100, 'o-', label='Δt = 0.1s', color='#1f77b4', linewidth=2, markersize=4)
    ax1.plot(times, mean10, 's-', label='Δt = 0.01s', color='#ff7f0e', linewidth=2, markersize=4)
    ax1.plot(times, mean1, 'd-', label='Δt = 0.001s', color='#2ca02c', linewidth=2, markersize=4)
    ax1.axhline(0.5, color='red', linestyle='--', linewidth=2, label='Expected 0.500', alpha=0.7)
    ax1.set_xlabel('Time (seconds)', color='white', fontsize=12)
    ax1.set_ylabel('Mean Intensity', color='white', fontsize=12)
    ax1.set_title(f'{title} - Mean Values', fontsize=16, fontweight='bold', color='white')
    ax1.legend(facecolor='#2a2a2a', edgecolor='white', labelcolor='white')
    ax1.grid(True, alpha=0.3, color='white')
    ax1.tick_params(colors='white')
    ax1.set_ylim(-0.1, 1.1)

    # Plot 2: Variance
    ax2.set_facecolor('#2a2a2a')
    ax2.plot(times, var100, 'o-', label='Variance (Δt = 0.1s)', color='#FFFF00', linewidth=2, markersize=4)
    ax2.plot(times, var10, 's-', label='Variance (Δt = 0.01s)', color='#00FFFF', linewidth=2, markersize=4)
    ax2.set_xlabel('Time (seconds)', color='white', fontsize=12)
    ax2.set_ylabel('Variance', color='white', fontsize=12)
    ax2.set_title('Variance Over Time', fontsize=14, color='white')
    ax2.legend(facecolor='#2a2a2a', edgecolor='white', labelcolor='white')
    ax2.grid(True, alpha=0.3, color='white')
    ax2.tick_params(colors='white')
    ax2.set_ylim(bottom=0)

    # Add timestamp
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    fig.text(0.99, 0.01, f'Generated: {timestamp}', ha='right', va='bottom',
             fontsize=8, color='#888888')

    plt.tight_layout()
    output_path = DATA_DIR / png_file
    plt.savefig(output_path, dpi=200, facecolor='#1a1a1a', edgecolor='none')
    plt.close()
    print(f"✓ Generated {png_file}")

# Save accumulated history for next run
with open(history_file, 'w') as f:
    json.dump(history_data, f, indent=2)
print(f"✓ Saved history ({len(history_data)} datasets)")

print("\n✅ All TRT graphs updated!")
