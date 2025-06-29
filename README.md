# TSLA Powerwall Price Updater

This project aims to update the Tesla Powerwall's price settings based on electricity prices.

## Setup Instructions

To run this project, follow these steps:

### 1. Clone the repository

```bash
git clone https://github.com/tmbao/globird-powerwall-price-updater/
cd globird-powerwall-price-updater
```

### 2. Create a virtual environment (recommended for local development)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory of the project with the following content. These variables are crucial for connecting to Amber Electric and Tesla Powerwall APIs.

```
export AMBER_API_TOKEN="YOUR_AMBER_ELECTRIC_API_TOKEN"
export RESOLUTION="30" # Example: "30" for 30-minute intervals, this value can only be either 5 or 30
export TESLA_CLIENT_ID="YOUR_TESLA_CLIENT_ID"
export TESLA_CLIENT_SECRET="YOUR_TESLA_CLIENT_SECRET"
export AUTH_DIR=/app/auth

### 5. Public Domain and Tesla API Authentication

A public domain is required for the Tesla API authentication callback. Please ensure you have a public domain configured. Follow the official Tesla API documentation for detailed authentication setup: [https://developer.tesla.com/docs/fleet-api/authentication/overview](https://developer.tesla.com/docs/fleet-api/authentication/overview). The `oauth_server.py` script in the `servers/` directory can serve as a starting point for implementing the authentication callback.

### 6. Running the project (Local)

Once set up, you can run the main script locally:

```bash
python workers/price_updater.py
```

### 7. Running with Docker (Recommended for Deployment)

This project is designed to be run within a Docker container for easier deployment and management.

#### Build the Docker image

```bash
docker build -t tsla-pw-price-updater .
```

#### Run the Docker container

```bash
docker run -d --name powerwall-updater --env-file ./.env tsla-pw-price-updater
```

This command will:
- `-d`: Run the container in detached mode (in the background).
- `--name powerwall-updater`: Assign a name to your container.
- `--env-file ./.env`: Pass your environment variables from the `.env` file into the container.

Inside the Docker container, the `run.sh` script executes the `price_updater.py` script, and `supervisord` manages the processes, including a scheduled cron job for regular updates.

## Project Structure

- `crontab`: Defines the cron job schedule for `price_updater.py`.
- `Dockerfile`: Defines the Docker image for the application.
- `requirements.txt`: Lists Python dependencies.
- `run.sh`: Entrypoint script for the Docker container, executes `price_updater.py`.
- `supervisord.conf`: Configuration for `supervisord` to manage processes within the Docker container.
- `.env`: Contains environment variables (not committed to Git).
- `servers/`: Contains server-side components.
    - `oauth_server.py`: Handles OAuth authentication flow for Tesla API.
    - `templates/`: HTML templates for the OAuth server.
- `workers/`: Contains the core logic for price fetching and Powerwall updates.
    - `amber_client.py`: Handles communication with the Amber Electric API.
    - `app_logger.py`: Application logging configuration.
    - `globird_client.py`: (If applicable) Client for Globird energy.
    - `price_updater.py`: Main logic for fetching prices and updating Powerwall settings.
    - `simple_price.py`: Defines the `SimplePrice` dataclass for price representation.
    - `tesla_client.py`: Handles communication with the Tesla API.
    - `tesla_tou_settings.py`: Logic for managing Tesla Time-of-Use (TOU) settings.
    - `test_price_updater.py`: Unit tests for `price_updater.py`.
    - `test_tesla_tou_settings.py`: Unit tests for `tesla_tou_settings.py`.
    - `examples/`: Example JSON files.
        - `amber_forecast.json`: Example Amber forecast data.
        - `tesla_tou.json`: Example Tesla TOU settings.
