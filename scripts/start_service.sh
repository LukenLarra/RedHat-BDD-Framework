#!/usr/bin/env bash
# Usage: start_service.sh <command> <health_url> <log_file> [retries] [delay_seconds]
set -euo pipefail

CMD="$1"
URL="$2"
LOG_FILE="$3"
RETRIES="${4:-30}"
DELAY="${5:-1}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# shellcheck disable=SC2086 -- intentional word-splitting to support multi-word commands
nohup $CMD > "$LOG_FILE" 2>&1 &
bash "$SCRIPT_DIR/wait_for_service.sh" "$URL" "$LOG_FILE" "$RETRIES" "$DELAY"
