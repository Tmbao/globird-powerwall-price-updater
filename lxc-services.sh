#!/usr/bin/dash
set -eu

mkdir -p /app/auth /var/log
: > /var/log/cron.log

cleanup() {
  status=$?
  for pid in ${OAUTH_PID:-} ${CRON_PID:-}; do
    if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
      wait "${pid}" 2>/dev/null || true
    fi
  done
  exit "$status"
}

trap cleanup INT TERM HUP

cd /app

echo "Starting OAuth server on port ${PORT:-9090}"
python3 /app/servers/oauth_server.py &
OAUTH_PID=$!

echo "Starting cron in foreground mode"
/usr/sbin/cron -f &
CRON_PID=$!

while true; do
  for pid in "$OAUTH_PID" "$CRON_PID"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid"
      exit $?
    fi
  done
  sleep 1
done

