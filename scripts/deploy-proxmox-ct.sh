#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/deploy-proxmox-ct.sh <proxmox_host_ip> <ct_ip> [ct_id]

Example:
  ./scripts/deploy-proxmox-ct.sh 192.168.4.16 192.168.4.24 120

This script:
  1. Builds the Proxmox rootfs tarball with distrobuilder.
  2. Copies the tarball to the Proxmox host.
  3. Stops and destroys an existing CT with the same ID if it exists.
  4. Creates and starts a new CT on vmbr0 with the requested static IP.

Requirements:
  - Run from WSL/Linux.
  - Passwordless SSH access to root@<proxmox_host_ip>.
  - distrobuilder installed locally.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 1
fi

PROXMOX_HOST_IP="$1"
CT_IP="$2"
CT_ID="${3:-120}"

CT_HOSTNAME="${CT_HOSTNAME:-globird-price}"
CT_MEMORY_MB="${CT_MEMORY_MB:-512}"
CT_CORES="${CT_CORES:-1}"
CT_ROOTFS_STORAGE="${CT_ROOTFS_STORAGE:-wdcdata}"
CT_ROOTFS_SIZE_GB="${CT_ROOTFS_SIZE_GB:-1.5}"
CT_GATEWAY="${CT_GATEWAY:-192.168.4.1}"
CT_TEMPLATE_NAME="${CT_TEMPLATE_NAME:-globird-price-updater.tar.xz}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"
ROOTFS_DIR="/tmp/globird-price-lxc"
LOCAL_TARBALL="${BUILD_DIR}/globird-rootfs.tar.xz"
REMOTE_TARBALL="/var/lib/vz/template/cache/${CT_TEMPLATE_NAME}"

mkdir -p "${BUILD_DIR}"
rm -rf "${ROOTFS_DIR}"

echo "Building rootfs with distrobuilder..."
sudo distrobuilder build-dir --with-post-files "${REPO_ROOT}/globird-distrobuilder.yaml" "${ROOTFS_DIR}"
sudo tar -C "${ROOTFS_DIR}" -caf "${LOCAL_TARBALL}" .

echo "Uploading rootfs tarball to ${PROXMOX_HOST_IP}..."
scp "${LOCAL_TARBALL}" "root@${PROXMOX_HOST_IP}:${REMOTE_TARBALL}"

echo "Recreating CT ${CT_ID} on ${PROXMOX_HOST_IP}..."
ssh "root@${PROXMOX_HOST_IP}" bash <<EOF
set -euo pipefail

if pct status "${CT_ID}" >/dev/null 2>&1; then
  if pct status "${CT_ID}" | grep -q 'status: running'; then
    pct stop "${CT_ID}" || true
  fi
  pct destroy "${CT_ID}" --purge || pct destroy "${CT_ID}"
fi

pct create "${CT_ID}" "local:vztmpl/${CT_TEMPLATE_NAME}" \
  --hostname "${CT_HOSTNAME}" \
  --rootfs "${CT_ROOTFS_STORAGE}:${CT_ROOTFS_SIZE_GB}" \
  --memory "${CT_MEMORY_MB}" \
  --cores "${CT_CORES}" \
  --net0 "name=eth0,bridge=vmbr0,ip=${CT_IP}/24,gw=${CT_GATEWAY}" \
  --unprivileged 1 \
  --start 1

sleep 3
pct status "${CT_ID}"
pct exec "${CT_ID}" -- sh -lc 'ip addr show eth0; echo; ip route'
EOF

echo "Deployment complete."
echo "CT ${CT_ID} should now be reachable at ${CT_IP}."
