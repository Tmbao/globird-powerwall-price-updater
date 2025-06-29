#!/usr/bin/env python3
"""
TSLA Price Updater - A cron job to update electricity prices every 5 minutes for Tesla Powerwall.

This script fetches electricity prices from Globird and Amber Electric, and updates the Tesla Powerwall
with the latest prices. It is designed to run as a cron job, updating prices every 5 minutes.
"""

import os
from datetime import datetime, timedelta, date, time
from typing import List
from dateutil import tz
from amber_client import AmberClient
from app_logger import logger
from globird_client import GlobirdClient
from simple_price import SimplePrice
from tesla_tou_settings import (
    TouPeriod,
    TouPeriodContainer,
    Season,
    EnergyChargesSeason,
    DailyCharge,
    SellTariff,
    TimeOfUseSettings,
    DemandChargesSeason,
)
from tesla_client import TeslaClient


class PowerwallPriceUpdater:
    def __init__(self, globird_client, amber_client, tesla_client):
        self.globird_client = globird_client
        self.amber_client = amber_client
        self.tesla_client = tesla_client

    def _generate_prices(self):
        """Generates electricity prices from both Globird and Amber clients."""
        globird_prices: List[SimplePrice] = self.globird_client.get_prices()
        amber_prices: List[SimplePrice] = self.amber_client.get_forecast()

        logger.info(
            f"Globird prices: {len(globird_prices)} entries, Amber prices: {len(amber_prices)} entries"
        )
        logger.debug(
            f"---\nGlobird prices: {globird_prices}\n---\nAmber prices: {amber_prices}\n---"
        )

        if not globird_prices:
            logger.warning("No prices returned from Globird client.")
        if not amber_prices:
            logger.warning("No prices returned from Amber client.")

        globird_prices_map: dict[datetime, SimplePrice] = {
            p.start_time_time(): p for p in globird_prices
        }
        amber_prices_map: dict[datetime, SimplePrice] = {
            p.start_time_time(): p for p in amber_prices
        }

        prices: List[SimplePrice] = []
        today = date.today()
        current_time = time(0, 0, tzinfo=tz.tzlocal())
        resolution_minutes = int(os.environ.get("RESOLUTION", 5))
        if resolution_minutes not in [5, 30]:
            raise ValueError("RESOLUTION must be 5 or 30 minutes.")
        sell_threshold = 1.5

        for _ in range(int(24 * 60 / resolution_minutes)):
            globird_price = globird_prices_map.get(current_time)
            amber_price = amber_prices_map.get(current_time)

            if not globird_price:
                raise RuntimeError(
                    f"Globird price not found for time {current_time.isoformat()}"
                )

            # Default to Globird sell price
            final_buy_price = globird_price.buy_per_kwh
            final_sell_price = globird_price.sell_per_kwh

            if amber_price and amber_price.sell_per_kwh > sell_threshold:
                final_sell_price = 1
                final_buy_price += 1
                # Use Amber's price type if its sell price is used
                price_type = amber_price.price_type
                logger.info(f"Price spike detected at {current_time.strftime("%H%M")}: ")
            else:
                # Otherwise use Globird's price type
                price_type = globird_price.price_type

            prices.append(
                SimplePrice(
                    start_time=current_time,
                    period=timedelta(minutes=resolution_minutes),
                    buy_per_kwh=final_buy_price,
                    sell_per_kwh=final_sell_price,
                    price_type=price_type,
                )
            )

            current_time = (
                datetime.combine(today, current_time)
                + timedelta(minutes=resolution_minutes)
            ).time()

        return prices

    def _build_time_of_use_settings(
        self, prices: List[SimplePrice]
    ) -> TimeOfUseSettings:
        """
        Builds the time-of-use settings for the Tesla Powerwall.
          - version: 1
          - utility: "Globird"
          - code: "ZEROHERO"
          - name: "Globird ZEROHERO VPP"
          - currency: "USD"
          - daily charge: 1.1
          - seasons: ALL (all year round)
            - fromDay 1 to 31 (all days of the month)
            - tou_periods: from 00:00 to 23:55 use the RESOLUTION environment variable
              - Use the name format HHMM for each period
              - All weekdays (0 to 6)
              - fromHour and toHour correspond to the start and end of the period
          - energy_charges: Extract from SimplePrice objects (use buy price) for all the periods above
          - sell_tariffs: Extract from SimplePrice objects (use sell price) for all the periods above
        """
        resolution_minutes = int(os.environ.get("RESOLUTION", 5))
        if resolution_minutes not in [5, 30]:
            raise ValueError("RESOLUTION must be 5 or 30 minutes.")

        tou_periods: dict[str, List[TouPeriod]] = {}
        tou_periods_list: List[TouPeriod] = []
        buy_rates_dict: dict[str, float] = {}
        sell_rates_dict: dict[str, float] = {}

        today = datetime.now()

        for price in prices:
            start_time_str = price.start_time.strftime("%H%M")
            end_time = (datetime.combine(today, price.start_time) + price.period).time()

            tou_periods[start_time_str] = TouPeriodContainer(
                periods=[
                    TouPeriod(
                        fromDayOfWeek=0,  # All weekdays
                        toHour=end_time.hour,
                        toDayOfWeek=6,  # All weekdays
                        fromHour=price.start_time.hour,
                        fromMinute=price.start_time.minute,
                        toMinute=end_time.minute,
                    )
                ]
            )
            buy_rates_dict[start_time_str] = price.buy_per_kwh
            sell_rates_dict[start_time_str] = price.sell_per_kwh

        main_season = Season(
            fromMonth=1,
            fromDay=1,
            toMonth=12,
            toDay=31,
            tou_periods=tou_periods,
        )

        main_energy_charges_season = EnergyChargesSeason(rates=buy_rates_dict)
        main_energy_charges = {"ALL": main_energy_charges_season}

        sell_energy_charges_season = EnergyChargesSeason(rates=sell_rates_dict)
        sell_energy_charges = {"ALL": sell_energy_charges_season}

        daily_charge = DailyCharge(name="Daily Charge", amount=1.1)

        # Default DemandChargesSeason for SellTariff
        default_demand_charges_season = DemandChargesSeason(rates={})
        default_demand_charges = {"ALL": default_demand_charges_season}

        sell_tariff = SellTariff(
            min_applicable_demand=0.0,
            monthly_minimum_bill=0.0,
            monthly_charges=0.0,
            max_applicable_demand=0.0,
            utility="Globird",
            demand_charges=default_demand_charges,
            daily_charges=[daily_charge],
            seasons={"ALL": main_season},  # Assuming sell tariff uses the same seasons
            code="ZEROHERO",
            energy_charges=sell_energy_charges,
            daily_demand_charges={},
            currency="USD",
            name="Globird ZEROHERO VPP",
        )

        return TimeOfUseSettings(
            version=1,
            monthly_minimum_bill=0.0,
            min_applicable_demand=0.0,
            max_applicable_demand=0.0,
            monthly_charges=0.0,
            utility="Globird",
            code="ZEROHERO",
            name="Globird ZEROHERO VPP",
            currency="USD",
            daily_charges=[daily_charge],
            daily_demand_charges={},
            demand_charges=default_demand_charges,
            energy_charges=main_energy_charges,
            seasons={"ALL": main_season},
            sell_tariff=sell_tariff,
        )

    def run(self):
        """Main execution method for the cron job."""
        logger.info("Starting electricity price update job")

        prices = self._generate_prices()
        logger.info(f"Generated {len(prices)} prices")
        logger.debug(f"Prices: {prices}")

        time_of_use_settings = self._build_time_of_use_settings(prices)
        logger.info("Built TimeOfUseSettings")
        logger.debug(f"TimeOfUseSettings: {time_of_use_settings}")

        self.tesla_client.update(time_of_use_settings=time_of_use_settings)


def main():
    """Entry point for the script."""
    updater = PowerwallPriceUpdater(
        globird_client=GlobirdClient(),
        amber_client=AmberClient(),
        tesla_client=TeslaClient(),
    )
    updater.run()


if __name__ == "__main__":
    main()
