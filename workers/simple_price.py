from dataclasses import dataclass
import datetime

from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class PriceType:
    ACTUAL = "ActualInterval"
    CURRENT = "CurrentInterval"
    FORECAST = "ForecastInterval"

    @classmethod
    def is_valid(cls, value):
        return value in (cls.ACTUAL, cls.CURRENT, cls.FORECAST)

@dataclass_json
@dataclass
class SimplePrice:
    """A simple representation of a price with a start time and per kWh cost."""
    start_time: datetime.datetime
    period: datetime.timedelta
    buy_per_kwh: float
    sell_per_kwh: float
    price_type: PriceType

    def start_time_time(self) -> datetime.time:
        """Returns the start time as a Unix timestamp."""
        return self.start_time.time()
