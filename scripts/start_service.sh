#!/usr/bin/env bash
# Usage: start_service.sh <command> <health_url> <log_file> [retries] [delay_seconds]
set -eu

CMD="$1"
URL="$2"
LOG_FILE="$3"
RETRIES="${4:-30}"
DELAY="${5:-1}"

eval "nohup $CMD > $LOG_FILE 2>&1 &"
bash "$(dirname "$0")/wait_for_service.sh" "$URL" "$LOG_FILE" "$RETRIES" "$DELAY"
