# Globird Powerwall Price Updater

This project aims to update the Tesla Powerwall's price settings to take advantage of Critical Events. Globird Energy does not yet support Tesla Powerwall so this project is a workaround.

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/tmbao/globird-powerwall-price-updater/
cd globird-powerwall-price-updater
```

### 2. Create a virtual environment (optional for local development)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory of the project with the required values:

```sh
export AMBER_API_TOKEN="YOUR_AMBER_ELECTRIC_API_TOKEN"
export RESOLUTION="30"
export TESLA_CLIENT_ID="YOUR_TESLA_CLIENT_ID"
export TESLA_CLIENT_SECRET="YOUR_TESLA_CLIENT_SECRET"
export AUTH_DIR="/app/auth"
export SELL_THRESHOLD="1.2"
```

### 4. Tesla API authentication callback

A public domain is required for the Tesla API authentication callback. Follow the Tesla Fleet API authentication documentation and use `servers/oauth_server.py` as the callback service.

### 5. Run locally

Run the updater once:

```bash
python workers/price_updater.py
```

Run the callback server:

```bash
python servers/oauth_server.py
```

## Docker / Proxmox deployment

This image now uses `/sbin/init` as the container entrypoint so it works cleanly after Docker-to-LXC conversion for Proxmox.

Build the normal image:

```bash
docker build -t tsla-pw-price-updater .
```

Build a debug image that opens a shell as PID 1:

```bash
docker build --build-arg LXC_INIT_MODE=shell -t tsla-pw-price-updater:debug .
```

Build a debug image that simply stays alive:

```bash
docker build --build-arg LXC_INIT_MODE=sleep -t tsla-pw-price-updater:sleep .
```

Example Proxmox CT creation command for a LAN-accessible container on `vmbr0`:

```bash
pct create 120 local:vztmpl/globird-price-updater.tar.xz \
  --hostname globird-price \
  --rootfs wdcdata:1.5 \
  --memory 1024 \
  --cores 1 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.4.24/24,gw=192.168.4.1 \
  --unprivileged 1 \
  --start 1
```

This keeps the CT directly on the `192.168.4.0/24` LAN so it is reachable from the rest of the network without extra NAT or routing rules.

You can also automate the build, upload, and CT recreation flow from WSL with:

```bash
./scripts/deploy-proxmox-ct.sh 192.168.4.16 192.168.4.24 120
```

The script rebuilds `build/globird-rootfs.tar.xz`, uploads it to Proxmox, destroys any existing CT with the same ID, and recreates it on `vmbr0`.


In normal mode the container init script starts `lxc-services.sh` as a child process, waits on it as PID 1, starts the Flask OAuth server on port `9090`, starts cron in foreground mode, and keeps container logs in `/var/log/container-init.log`.

The cron job defined in `crontab` runs `/app/run.sh`, which executes `workers/price_updater.py` and appends output to `/var/log/cron.log`.

## Project Structure

- `Dockerfile`: Container build with LXC-friendly init support.
- `lxc-init.sh`: PID 1 entrypoint for Proxmox/LXC and Docker.
- `lxc-services.sh`: Starts and monitors cron plus the OAuth server.
- `crontab`: Schedule for the price updater job.
- `run.sh`: Wrapper that loads `.env` and runs the updater worker.
- `servers/oauth_server.py`: Tesla OAuth callback server.
- `workers/price_updater.py`: Main price update workflow.

## Native Proxmox LXC Build With distrobuilder

This repository includes `globird-distrobuilder.yaml` for building a native Debian rootfs for Proxmox without converting from Docker.

Install distrobuilder and build a root filesystem tarball:

```bash
sudo distrobuilder build-dir --with-post-files globird-distrobuilder.yaml rootfs
sudo tar -C rootfs -caf globird-rootfs.tar.xz .
```

You can also build an LXC image layout directly:

```bash
sudo distrobuilder build-lxc globird-distrobuilder.yaml
```

That usually produces `rootfs.tar.xz` plus LXC metadata. For Proxmox, the plain rootfs tarball is typically the most convenient artifact.

Example Proxmox import flow:

```bash
scp globird-rootfs.tar.xz root@YOUR-PROXMOX:/var/lib/vz/template/cache/
pct create 121 local:vztmpl/globird-rootfs.tar.xz --hostname globird --rootfs local-lvm:8
pct start 121
```

If you want a debug CT that always stays alive, edit `/etc/profile.d/globird-init-mode.sh` in the built rootfs or set `LXC_INIT_MODE=sleep` before starting `/sbin/init`.

Note: the distrobuilder image does not require `.env` to be baked in. You can copy `/app/.env` into the CT after creation if you prefer to keep secrets out of the rootfs tarball.




