#!/usr/bin/env python3
"""
Generate TRT Validation Chart from JSON data
"""

import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Read the latest JSON data
with open('data/latest.json', 'r') as f:
    data = json.load(f)

# Read or create history file
history_file = 'data/history.json'
if os.path.exists(history_file):
    with open(history_file, 'r') as f:
        history = json.load(f)
else:
    history = {
        'timestamps': [],
        'var_100ms': [],
        'var_10ms': [],
        'var_1ms': []
    }

# Append current data to history (limit to last 100 points)
history['timestamps'].append(data['timestamp_iso'])
history['var_100ms'].append(data['delta_t_100ms']['variance'])
history['var_10ms'].append(data['delta_t_10ms']['variance'])
history['var_1ms'].append(data['delta_t_1ms']['variance'])

# Keep only last 100 data points
max_points = 100
if len(history['timestamps']) > max_points:
    history['timestamps'] = history['timestamps'][-max_points:]
    history['var_100ms'] = history['var_100ms'][-max_points:]
    history['var_10ms'] = history['var_10ms'][-max_points:]
    history['var_1ms'] = history['var_1ms'][-max_points:]

# Save updated history
with open(history_file, 'w') as f:
    json.dump(history, f, indent=2)

# Create the chart
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#1a1a1a')
ax.set_facecolor('#2a2a2a')

# Plot the data
x = range(len(history['timestamps']))
ax.plot(x, history['var_100ms'], color='#ffff00', linewidth=2, label='Δt = 0.1s', marker='o', markersize=3)
ax.plot(x, history['var_10ms'], color='#00ffff', linewidth=2, label='Δt = 0.01s', marker='s', markersize=3)
ax.plot(x, history['var_1ms'], color='#ff00ff', linewidth=2, label='Δt = 0.001s', marker='^', markersize=3)

# Styling
ax.set_xlabel('Sample Number', color='white', fontsize=12)
ax.set_ylabel('Variance', color='white', fontsize=12)
ax.set_title('Time Resolution Theory — Variance Trends', color='white', fontsize=16, fontweight='bold')
ax.tick_params(colors='white')
ax.grid(True, alpha=0.3, color='white', linestyle='--')
ax.legend(facecolor='#2a2a2a', edgecolor='white', labelcolor='white', fontsize=10)

# Add current values text
textstr = f'Latest Values:\n'
textstr += f'Δt=0.1s: {data["delta_t_100ms"]["variance"]:.8f}\n'
textstr += f'Δt=0.01s: {data["delta_t_10ms"]["variance"]:.8f}\n'
textstr += f'Δt=0.001s: {data["delta_t_1ms"]["variance"]:.8f}\n'
textstr += f'Timestamp: {data["timestamp_iso"]}'

props = dict(boxstyle='round', facecolor='#2a2a2a', edgecolor='white', alpha=0.8)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=props, color='white')

plt.tight_layout()
plt.savefig('data/trt_validation.png', dpi=150, facecolor='#1a1a1a')
print("Chart generated successfully: data/trt_validation.png")
