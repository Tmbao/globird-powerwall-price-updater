import os
from amberelectric.api import amber_api
from datetime import datetime, timedelta

class AmberClient:
    def __init__(self):
        configuration = amber_api.Configuration(
            access_token=os.environ.get("AMBER_API_TOKEN")
        )
        self.api_instance = amber_api.AmberApi(amber_api.ApiClient(configuration))
        self.postcode = os.environ.get("POSTCODE")

    def get_forecast(self):
        try:
            # Get the site id
            sites = self.api_instance.get_sites(postcode=self.postcode)
            if not sites:
                raise ValueError(f"No site found for postcode {self.postcode}")
            site_id = sites[0].id

            # Get the forecast
            end_date = datetime.now() + timedelta(hours=16)
            forecasts = self.api_instance.get_prices(site_id, end_date=end_date)
            return [f.to_dict() for f in forecasts]
        except amber_api.ApiException as e:
            print("Exception when calling AmberApi->get_prices: %s\n" % e)
            return []

if __name__ == '__main__':
    # Example usage:
    # Make sure to set the AMBER_API_TOKEN and POSTCODE environment variables
    client = AmberClient()
    forecast_data = client.get_forecast()
    if forecast_data:
        print(f"Successfully fetched {len(forecast_data)} forecast points.")
        # print(forecast_data)
