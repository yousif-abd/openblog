#!/bin/bash
# Auto-process new webinars from Google Drive
# This script is meant to be run by cron/launchd
# It checks for new videos and transcribes them automatically

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="$SCRIPT_DIR/data/webinar_cron.log"
mkdir -p "$SCRIPT_DIR/data"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting webinar auto-process..." >> "$LOG_FILE"

python3 -m webinar.process_webinars --folder-id "$(grep GOOGLE_DRIVE_WEBINAR_FOLDER .env | cut -d'"' -f2)" >> "$LOG_FILE" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - Done." >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
