#!/usr/bin/env sh
set -eu

: "${MONITOR_URL:=http://nginx/api/health/}"

# Optional: healthchecks.io (or similar) ping URL.
# If set, we will ping it on success; on failure we will call it with /fail.
HEALTHCHECKS_PING_URL="${HEALTHCHECKS_PING_URL:-}"

if curl -fsS --max-time 10 "$MONITOR_URL" >/dev/null; then
  echo "OK: health check passed: $MONITOR_URL"
  if [ -n "$HEALTHCHECKS_PING_URL" ]; then
    curl -fsS --max-time 10 "$HEALTHCHECKS_PING_URL" >/dev/null || true
  fi
  exit 0
fi

echo "ERROR: health check failed: $MONITOR_URL" >&2
if [ -n "$HEALTHCHECKS_PING_URL" ]; then
  curl -fsS --max-time 10 "${HEALTHCHECKS_PING_URL}/fail" >/dev/null || true
fi
exit 1
