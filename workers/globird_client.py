import datetime
import os
from datetime import timedelta
from typing import List
from dateutil import tz

from simple_price import SimplePrice, PriceType


class GlobirdClient:
    """
    A dummy client for Globird Electricity prices.
    Globird electricity prices are as follows:
     - Buy prices:
        - From 6PM to 8PM: $AU1.50 per kWh
        - From 4PM to 11PM (outside of 6PM to 8PM): $AU0.46 per kWh
        - From 11AM to 2PM: $AU0.0 per kWh
        - Other times: $AU0.31 per kWh
     - Sell prices:
        - From 6PM to 8PM: $AU0.15 per kWh
        - From 4PM to 9PM (outside of 6PM to 8PM): $AU0.9 per kWh
        - From 11AM to 2PM: $AU0.0 per kWh
        - Other times: $AU0.05 per kWh
     - Resolution: 30 minutes
    """

    def __init__(self):
        pass

    def _get_buy_price(self, time: datetime.time) -> float:
        if datetime.time(18, 0) <= time < datetime.time(20, 0):
            return 1.50
        elif datetime.time(16, 0) <= time < datetime.time(23, 0):
            return 0.46
        elif datetime.time(11, 0) <= time < datetime.time(14, 0):
            return 0.0
        else:
            return 0.31

    def _get_sell_price(self, time: datetime.time) -> float:
        if datetime.time(18, 0) <= time < datetime.time(20, 0):
            return 0.15
        elif datetime.time(16, 0) <= time < datetime.time(21, 0):
            return 0.09
        elif datetime.time(11, 0) <= time < datetime.time(14, 0):
            return 0.0
        elif datetime.time(10, 0) <= time < datetime.time(15, 0):
            return 0.01
        else:
            return 0.05

    def get_prices(self) -> List[SimplePrice]:
        """
        Simulates prices from the Globird for the specified time range.
        This method generates prices for a full day (00:00 to 23:55) based on the
        Globird pricing rules, with a resolution determined by the RESOLUTION
        environment variable (defaulting to 5 minutes).
        """
        prices: List[SimplePrice] = []
        today = datetime.date.today()

        resolution_minutes = int(os.environ.get("RESOLUTION", 5))
        if resolution_minutes not in [5, 30]:
            raise ValueError("RESOLUTION must be 5 or 30 minutes.")

        current_time = datetime.datetime.combine(
            today, datetime.time(0, 0, tzinfo=tz.tzlocal())
        )
        end_time = datetime.datetime.combine(today, datetime.time(23, 55, tzinfo=tz.tzlocal()))

        while current_time <= end_time:
            buy_price = self._get_buy_price(current_time.time())
            sell_price = self._get_sell_price(current_time.time())
            prices.append(
                SimplePrice(
                    start_time=current_time,
                    period=timedelta(minutes=resolution_minutes),
                    buy_per_kwh=buy_price,
                    sell_per_kwh=sell_price,
                    price_type=PriceType.ACTUAL,
                )
            )
            current_time += timedelta(minutes=resolution_minutes)

        return prices
