# TRT Services Management

## Overview

Two systemd services are running to automate data collection and provide a web dashboard:

1. **trt-auto-update.service** - Automatically pulls data from Arduino every 30 seconds, generates graphs, and pushes to GitHub
2. **trt-web-dashboard.service** - Web dashboard for monitoring GitHub posting activity and editing configuration

## Web Dashboard Access

**Local access:**
```
http://localhost:5000
```

**Network access:**
```
http://<your-ip>:5000
```

## Service Commands

### Check Status
```bash
sudo systemctl status trt-auto-update.service
sudo systemctl status trt-web-dashboard.service
```

### Start Services
```bash
sudo systemctl start trt-auto-update.service
sudo systemctl start trt-web-dashboard.service
```

### Stop Services
```bash
sudo systemctl stop trt-auto-update.service
sudo systemctl stop trt-web-dashboard.service
```

### Restart Services
```bash
sudo systemctl restart trt-auto-update.service
sudo systemctl restart trt-web-dashboard.service
```

### View Logs
```bash
# Live tail of auto-update logs
tail -f scripts/auto_update.log

# Live tail of web dashboard logs
tail -f scripts/web_server.log

# View systemd journal
sudo journalctl -u trt-auto-update.service -f
sudo journalctl -u trt-web-dashboard.service -f
```

### Disable Services (stop auto-start on boot)
```bash
sudo systemctl disable trt-auto-update.service
sudo systemctl disable trt-web-dashboard.service
```

### Enable Services (auto-start on boot)
```bash
sudo systemctl enable trt-auto-update.service
sudo systemctl enable trt-web-dashboard.service
```

## Configuration

Edit the configuration file at:
```
scripts/config.json
```

Or use the web dashboard interface at http://localhost:5000

### Configuration Options

- **arduino_ip**: IP address of the Arduino (default: http://192.168.1.91)
- **update_interval**: Seconds between updates (default: 30)
- **github_enabled**: Enable/disable automatic GitHub pushes (default: true)
- **max_history_points**: Number of data points to keep in history (default: 200)
- **web_server_port**: Web dashboard port (default: 5000)
- **web_server_host**: Web dashboard bind address (default: 0.0.0.0)

After editing config.json, the auto-update service will reload it on the next cycle (no restart needed).

## Log Files

- **scripts/auto_update.log** - Auto-update service output
- **scripts/web_server.log** - Web dashboard service output
- **scripts/activity.json** - GitHub push activity log (viewable in dashboard)
- **scripts/config.json** - Service configuration (editable in dashboard)

## Troubleshooting

### Service Won't Start
```bash
# Check service status for errors
sudo systemctl status trt-auto-update.service
sudo journalctl -u trt-auto-update.service -n 50
```

### Merge Conflicts
The auto-update service now automatically resolves merge conflicts by fetching the latest data from the Arduino. Check logs if issues persist.

### Dashboard Not Accessible
```bash
# Check if service is running
sudo systemctl status trt-web-dashboard.service

# Check if port is in use
sudo netstat -tulpn | grep 5000
```

### Stop Both Services Temporarily
```bash
sudo systemctl stop trt-auto-update.service trt-web-dashboard.service
```

### Restart Both Services
```bash
sudo systemctl restart trt-auto-update.service trt-web-dashboard.service
```

## Service Files Location

Service definitions are located at:
- `/etc/systemd/system/trt-auto-update.service`
- `/etc/systemd/system/trt-web-dashboard.service`

After modifying service files, reload systemd:
```bash
sudo systemctl daemon-reload
```
