import os
from typing import List
import amberelectric
from amberelectric.rest import ApiException
from datetime import datetime, timedelta
from dateutil import tz
from app_logger import logger
from simple_price import PriceType, SimplePrice
from amberelectric.models.interval import Interval


class AmberClient:
    def __init__(self):
        """Initializes the Amber API client with the required configuration."""
        self._configuration = amberelectric.Configuration(
            access_token=os.environ.get("AMBER_API_TOKEN")
        )
        self._resolution = os.environ.get("RESLUTION", 5)

    def _get_site_id(self) -> str:
        """Retrieves the site ID for the configured postcode."""
        with amberelectric.ApiClient(self._configuration) as api_client:
            api_instance = amberelectric.AmberApi(api_client)
            sites = api_instance.get_sites()
            if not sites:
                raise ValueError(f"No site found for postcode {{self.postcode}}")
            logger.info(f"Using site ID: {sites[0].id}")
            return sites[0].id

    def get_forecast(self) -> List[SimplePrice]:
        """Fetches the electricity price forecast for the site."""
        try:
            site_id = self._get_site_id()
            # Get the simple prices for the site, and filter out ActualInterval
            simple_prices = self._get_simple_prices(site_id)
            if not simple_prices:
                logger.warning("No forecast data available for the site.")
                return []
            now = datetime.now(tz=tz.tzlocal())
            # Filter out ActualInterval prices and forcasted prices further than 24 hours
            forecasted_prices = [
                price
                for price in simple_prices
                if price.price_type != PriceType.ACTUAL
                and price.start_time < now + timedelta(days=1)
            ]
            return forecasted_prices
        except ApiException as e:
            print("Exception when calling AmberApi->get_forecast: %s\n" % e)
            return []
        except ValueError as e:
            print(f"Error: {e}")
            return []

    def _get_simple_prices(self, site_id: str) -> List[SimplePrice]:
        """Fetches the forecast data for the given site ID."""
        with amberelectric.ApiClient(self._configuration) as api_client:
            api_instance = amberelectric.AmberApi(api_client)
            start_date = datetime.now()
            end_date = datetime.now() + timedelta(days=1)
            prices: List[Interval] = api_instance.get_prices(
                site_id, start_date=start_date, end_date=end_date, resolution=5
            )
            simple_prices: List[SimplePrice] = []
            for price in prices:
                price_instance = price.actual_instance
                simple_prices.append(
                    SimplePrice(
                        start_time=price_instance.start_time.astimezone(
                            tz=tz.tzlocal()
                        ),
                        period=timedelta(minutes=price_instance.duration),
                        buy_per_kwh=price_instance.per_kwh / 100.0,
                        sell_per_kwh=price_instance.spot_per_kwh / 100.0,
                        price_type=price_instance.type,
                    )
                )
            return simple_prices
