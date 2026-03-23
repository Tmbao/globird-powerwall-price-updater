#!/usr/bin/dash
set -eu

start_services() {
  mkdir -p /var/log
  /app/lxc-services.sh >>/var/log/container-init.log 2>&1 &
  child=$!

  cleanup() {
    kill "$child" 2>/dev/null || true
    wait "$child" 2>/dev/null || true
    exit 0
  }

  trap cleanup INT TERM HUP
  wait "$child"
}

case "${LXC_INIT_MODE:-services}" in
  shell)
    exec /usr/bin/dash
    ;;
  sleep)
    while true; do
      sleep 3600
    done
    ;;
  services)
    start_services
    ;;
  *)
    echo "Unsupported LXC_INIT_MODE: ${LXC_INIT_MODE}" >&2
    exit 1
    ;;
esac
