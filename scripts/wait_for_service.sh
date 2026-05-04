#!/usr/bin/env bash
# Usage: wait_for_service.sh <url> <log_file> [retries] [delay_seconds]
set -euo pipefail

URL="$1"
LOG_FILE="$2"
RETRIES="${3:-30}"
DELAY="${4:-1}"

echo "Waiting for $URL..."
for i in $(seq 1 "$RETRIES"); do
  if curl -sf "$URL" > /dev/null; then
    echo "Service ready at $URL"
    exit 0
  fi
  echo "  attempt $i/$RETRIES..."
  sleep "$DELAY"
done
echo "Service failed to start. Logs:"
cat "$LOG_FILE"
exit 1
