#!/usr/bin/env python3
"""
TRT GitHub Posting Web Server
Shows logs, posted files, and allows config editing
"""

from flask import Flask, render_template_string, request, jsonify
import json
from pathlib import Path
from datetime import datetime
import os

app = Flask(__name__)

# Paths
REPO_DIR = Path("/home/joshuag/Time-Resolution-Theory-Live-Proof")
SCRIPTS_DIR = REPO_DIR / "scripts"
CONFIG_FILE = SCRIPTS_DIR / "config.json"
LOG_FILE = SCRIPTS_DIR / "auto_update.log"
ACTIVITY_LOG = SCRIPTS_DIR / "activity.json"

def load_config():
    """Load configuration"""
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    """Save configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_activity_log():
    """Load activity log"""
    try:
        with open(ACTIVITY_LOG) as f:
            return json.load(f)
    except:
        return {"pushes": [], "stats": {"total_pushes": 0, "total_files": 0}}

def get_recent_logs(lines=100):
    """Get recent log entries"""
    try:
        with open(LOG_FILE) as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except:
        return "No logs available"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>TRT GitHub Posting Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #000;
            color: #0ff;
            margin: 0;
            padding: 20px;
        }
        h1 {
            color: #0ff;
            text-align: center;
            border-bottom: 2px solid #0ff;
            padding-bottom: 10px;
        }
        h2 {
            color: #ff0;
            margin-top: 30px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: #001a33;
            border: 2px solid #0ff;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-box {
            background: #003;
            border: 1px solid #0ff;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-value {
            font-size: 32px;
            color: #0f0;
            font-weight: bold;
        }
        .stat-label {
            color: #fff;
            margin-top: 5px;
        }
        .log-box {
            background: #000;
            border: 1px solid #0ff;
            padding: 15px;
            border-radius: 5px;
            max-height: 400px;
            overflow-y: auto;
            font-size: 12px;
            white-space: pre-wrap;
            color: #0f0;
        }
        .push-entry {
            background: #002;
            border-left: 3px solid #0f0;
            padding: 10px;
            margin: 10px 0;
            border-radius: 3px;
        }
        .push-time {
            color: #ff0;
            font-weight: bold;
        }
        .push-files {
            color: #0ff;
            margin-top: 5px;
        }
        .config-editor {
            background: #001;
            border: 1px solid #0ff;
            padding: 15px;
            border-radius: 5px;
        }
        .config-field {
            margin: 15px 0;
        }
        .config-field label {
            display: block;
            color: #ff0;
            margin-bottom: 5px;
        }
        .config-field input {
            width: 100%;
            padding: 8px;
            background: #000;
            border: 1px solid #0ff;
            color: #0f0;
            font-family: 'Courier New', monospace;
            border-radius: 3px;
        }
        button {
            background: #0a0;
            color: #000;
            border: 2px solid #0f0;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 6px;
            margin: 10px 5px;
        }
        button:hover {
            background: #0f0;
        }
        .refresh-btn {
            background: #00a;
            color: #0ff;
            border-color: #0ff;
        }
        .refresh-btn:hover {
            background: #00f;
        }
        .status-running {
            color: #0f0;
        }
        .status-stopped {
            color: #f00;
        }
    </style>
    <script>
        function refreshLogs() {
            location.reload();
        }

        function saveConfig() {
            const config = {
                arduino_ip: document.getElementById('arduino_ip').value,
                update_interval: parseInt(document.getElementById('update_interval').value),
                repo_dir: document.getElementById('repo_dir').value,
                data_dir: document.getElementById('data_dir').value,
                github_enabled: document.getElementById('github_enabled').checked,
                max_history_points: parseInt(document.getElementById('max_history_points').value),
                web_server_port: parseInt(document.getElementById('web_server_port').value),
                web_server_host: document.getElementById('web_server_host').value
            };

            fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                alert('Configuration saved! Restart auto_update.py to apply changes.');
            });
        }

        // Auto-refresh every 30 seconds
        setTimeout(refreshLogs, 30000);
    </script>
</head>
<body>
    <div class="container">
        <h1>⚡ TRT GITHUB POSTING DASHBOARD ⚡</h1>

        <!-- Statistics -->
        <div class="card">
            <h2>📊 Statistics</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value">{{ stats.total_pushes }}</div>
                    <div class="stat-label">Total Pushes</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{{ stats.total_files }}</div>
                    <div class="stat-label">Files Posted</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{{ config.update_interval }}s</div>
                    <div class="stat-label">Update Interval</div>
                </div>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="card">
            <h2>📝 Recent Push Activity</h2>
            <button class="refresh-btn" onclick="refreshLogs()">🔄 Refresh</button>
            <div style="margin-top: 15px;">
                {% for push in recent_pushes %}
                <div class="push-entry">
                    <div class="push-time">{{ push.timestamp }}</div>
                    <div class="push-files">
                        {% for file in push.files %}
                        <div>✓ {{ file }}</div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
                {% if not recent_pushes %}
                <p style="color: #888;">No pushes yet. Waiting for first update...</p>
                {% endif %}
            </div>
        </div>

        <!-- Live Logs -->
        <div class="card">
            <h2>📋 Live Logs</h2>
            <div class="log-box">{{ logs }}</div>
        </div>

        <!-- Configuration -->
        <div class="card">
            <h2>⚙️ Configuration</h2>
            <div class="config-editor">
                <div class="config-field">
                    <label>Arduino IP:</label>
                    <input type="text" id="arduino_ip" value="{{ config.arduino_ip }}">
                </div>
                <div class="config-field">
                    <label>Update Interval (seconds):</label>
                    <input type="number" id="update_interval" value="{{ config.update_interval }}">
                </div>
                <div class="config-field">
                    <label>Repository Directory:</label>
                    <input type="text" id="repo_dir" value="{{ config.repo_dir }}">
                </div>
                <div class="config-field">
                    <label>Data Directory:</label>
                    <input type="text" id="data_dir" value="{{ config.data_dir }}">
                </div>
                <div class="config-field">
                    <label>Max History Points:</label>
                    <input type="number" id="max_history_points" value="{{ config.max_history_points }}">
                </div>
                <div class="config-field">
                    <label>Web Server Port:</label>
                    <input type="number" id="web_server_port" value="{{ config.web_server_port }}">
                </div>
                <div class="config-field">
                    <label>Web Server Host:</label>
                    <input type="text" id="web_server_host" value="{{ config.web_server_host }}">
                </div>
                <div class="config-field">
                    <label>
                        <input type="checkbox" id="github_enabled" {% if config.github_enabled %}checked{% endif %}>
                        Enable GitHub Pushing
                    </label>
                </div>
                <button onclick="saveConfig()">💾 Save Configuration</button>
            </div>
        </div>

        <div style="text-align: center; color: #888; margin-top: 30px; padding: 20px;">
            Auto-refreshes every 30 seconds | Last updated: {{ current_time }}
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Main dashboard"""
    config = load_config()
    activity = load_activity_log()
    logs = get_recent_logs(100)

    return render_template_string(
        HTML_TEMPLATE,
        config=config,
        stats=activity.get('stats', {'total_pushes': 0, 'total_files': 0}),
        recent_pushes=activity.get('pushes', [])[-10:][::-1],  # Last 10, reversed
        logs=logs,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Config API endpoint"""
    if request.method == 'POST':
        config = request.json
        save_config(config)
        return jsonify({'success': True})
    else:
        return jsonify(load_config())

@app.route('/api/activity')
def api_activity():
    """Activity API endpoint"""
    return jsonify(load_activity_log())

@app.route('/api/logs')
def api_logs():
    """Logs API endpoint"""
    lines = request.args.get('lines', 100, type=int)
    return jsonify({'logs': get_recent_logs(lines)})

if __name__ == '__main__':
    config = load_config()
    port = config.get('web_server_port', 5000)
    host = config.get('web_server_host', '0.0.0.0')

    print("=" * 60)
    print("TRT GITHUB POSTING WEB SERVER")
    print("=" * 60)
    print(f"Dashboard: http://localhost:{port}")
    print(f"Network: http://{host}:{port}")
    print("=" * 60)

    app.run(host=host, port=port, debug=False)
