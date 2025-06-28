#!/usr/bin/env python3
"""
TSLA Price Updater - A cron job to update Tesla stock prices every 5 minutes
"""

import os
import sys
import logging


class PowerwallPriceUpdater:
    def __init__(self):
        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Configure logging for the application."""
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "price_updater.log")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Main execution method for the cron job."""
        self.logger.info("Starting electricity price update job")


def main():
    """Entry point for the script."""
    updater = PowerwallPriceUpdater()
    updater.run()


if __name__ == "__main__":
    main()
