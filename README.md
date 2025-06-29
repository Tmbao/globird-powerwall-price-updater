# TSLA Powerwall Price Updater

This project aims to update the Tesla Powerwall's price settings based on electricity prices.

## Setup Instructions

To run this project, follow these steps:

### 1. Clone the repository

```bash
git clone https://github.com/your-repo/tsla-pw-price-updater.git
cd tsla-pw-price-updater
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory of the project with the following content:

```
AMBER_API_TOKEN="YOUR_AMBER_ELECTRIC_API_TOKEN"
AMBER_RESOLUTION="YOUR_AMBER_RESOLUTION"
# Example: AMBER_RESOLUTION="30" for 30-minute intervals
```

- **AMBER_API_TOKEN**: Obtain this from your Amber Electric account or API documentation.
- **AMBER_RESOLUTION**: This specifies the interval resolution for price data (e.g., "30" for 30-minute intervals).

### 5. Running the project

Once set up, you can run the main script (e.g., `price_updater.py` or `run.sh` if it exists and is configured for execution).

```bash
# Example if price_updater.py is the main script
python price_updater.py
```

Or if there's a `run.sh` script:

```bash
./run.sh
```

## Project Structure (brief overview)

- `simple_price.py`: Defines the `SimplePrice` dataclass used for price representation.
- `price_updater.py`: (Assumed) Main logic for fetching prices and updating Powerwall.
- `amber_client.py`: (Assumed) Handles communication with the Amber Electric API.
- `requirements.txt`: Lists Python dependencies.
- `.env`: Contains environment variables (not committed to Git).
