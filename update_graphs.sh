#!/bin/bash
# Auto-generate TRT graphs and push to GitHub
# Runs every 10 minutes via cron

# GitHub credentials - REPLACE WITH YOUR ACTUAL TOKEN
GITHUB_TOKEN="YOUR_GITHUB_TOKEN_HERE"
GITHUB_USER="nentrapper-g-rod"
REPO_DIR="/home/joshuag/Time-Resolution-Theory-Live-Proof"

cd "$REPO_DIR" || exit 1

# Configure git to use token for this session
git config --local credential.helper store
echo "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials

# Pull latest data from GitHub (in case Arduino pushed new JSON)
git pull origin main --no-rebase > /dev/null 2>&1

# Generate graphs using Python script
python3 .github/scripts/make_graphs.py

# Check if any PNG files changed
if git diff --quiet data/*.png 2>/dev/null; then
  echo "$(date): No graph changes"
  exit 0
fi

# Commit and push the new graphs
git add data/*.png
git commit -m "Auto-update TRT graphs (local cron) [skip ci]"
git push origin main

echo "$(date): Graphs updated and pushed to GitHub"
