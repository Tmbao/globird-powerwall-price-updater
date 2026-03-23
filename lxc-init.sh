#!/usr/bin/dash
set -eu

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
    exec /app/lxc-services.sh
    ;;
  *)
    echo "Unsupported LXC_INIT_MODE: ${LXC_INIT_MODE}" >&2
    exit 1
    ;;
esac
