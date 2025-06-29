import requests
import os

from tesla_tou_settings import TimeOfUseSettings
from app_logger import logger

AUDIENCE = "https://fleet-api.prd.na.vn.cloud.tesla.com"
CALLBACK_URL = "https://pow.coldzee.win/oauth_redirect"
TOKEN_EXCHANGE_URL = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token"


class TeslaClient:

    def __init__(self):
        """
        Initializes the TeslaClient instance.
        Reads TESLA_CLIENT_ID and TESLA_CLIENT_SECRET from environment variables.
        """
        self.client_id = os.getenv("TESLA_CLIENT_ID")
        self.client_secret = os.getenv("TESLA_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "TESLA_CLIENT_ID and TESLA_CLIENT_SECRET must be set in environment variables."
            )

        self.auth_dir = os.getenv("AUTH_DIR", "/app/auth")

    def read_file(self, file_path: str) -> str:
        """
        Reads the content of a file.
        :param file_path: Path to the file to read.
        :return: Content of the file as a string.
        """
        try:
            with open(file_path, "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            raise RuntimeError(f"File not found: {file_path}")
        except IOError as e:
            raise RuntimeError(f"Error reading file {file_path}: {e}")

    def write_file(self, file_path: str, content: str):
        """
        Writes content to a file.
        :param file_path: Path to the file to write.
        :param content: Content to write to the file.
        """
        try:
            with open(file_path, "w") as file:
                file.write(content)
        except IOError as e:
            raise RuntimeError(f"Error writing to file {file_path}: {e}")

    def update(self, time_of_use_settings: TimeOfUseSettings):
        """
        Updates the time of use settings for Tesla's energy site.
        :param time_of_use_settings: TimeOfUseSettings object containing the settings to update.
        :return: Response from the API or None if an error occurs.
        """

        products = self.get_products()
        logger.debug(f"Products: {products}")

        energy_site_id = self.find_energy_site_id(products)
        logger.debug(f"Energy site ID: {energy_site_id}")

        self.post_time_of_use_settings(time_of_use_settings, energy_site_id)
        logger.info("Successfully updated time of use settings.")

    def find_energy_site_id(self, products: list) -> str:
        for product in products:
            if product.get("device_type") == "energy":
                energy_site_id = product.get("energy_site_id")
                if energy_site_id:
                    logger.debug(f"Found energy site ID: {energy_site_id}")
                    return energy_site_id

    def get_products(self):
        """
        Retrieves products from Tesla's API.
        :return: List of products or None if an error occurs.
        """
        access_token = self.exchange_tokens()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{AUDIENCE}/api/1/products"

        try:
            response = requests.get(url, headers=headers)
            logger.debug(
                f"Retrieved products: {response.status_code} - {response.text}"
            )

            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving products: {e}")
            return None

    def post_time_of_use_settings(
        self,
        time_of_use_settings: TimeOfUseSettings,
        energy_site_id: str,
    ) -> dict | None:
        """
        Posts time of use settings to Tesla's API.
        :param time_of_use_settings: Dictionary containing time of use settings.
        :return: Response from the API.
        """
        access_token = self.exchange_tokens()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{AUDIENCE}/api/1/energy_sites/{energy_site_id}/time_of_use_settings"

        tou_settings_json = {
            "tou_settings": {"tariff_content_v2": time_of_use_settings.to_dict()}
        }
        logger.debug(f"Posting time of use settings: {tou_settings_json}")

        try:
            response = requests.post(url, headers=headers, json=tou_settings_json)
            logger.debug(
                f"Posted time of use settings: {response.status_code} - {response.text}"
            )
            response.raise_for_status()  # Raise an exception for HTTP errors

            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error posting time of use settings: {e}")
            return None

    def exchange_tokens(self) -> tuple[str, str]:
        """
        Exchanges the authorization code for access and refresh tokens.
        Reads the authorization code from /app/auth/tesla_refresh_token.txt
        and makes a POST request to Tesla's OAuth2 token endpoint.
        Extracts access_token and refresh_token from the response.
        """
        logger.debug("Exchanging tokens")
        auth_code = self.read_file(
            os.path.join(self.auth_dir, "tesla_refresh_token.txt")
        )
        access_token, refresh_token = self.exchange_refresh_token(auth_code)

        self.write_file(
            os.path.join(self.auth_dir, "tesla_refresh_token.txt"), refresh_token
        )
        return access_token

    def exchange_refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Exchanges the authorization code for access and refresh tokens.
        Reads the authorization code from /app/auth/tesla_refresh_token.txt
        and makes a POST request to Tesla's OAuth2 token endpoint.
        Extracts access_token and refresh_token from the response.
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": refresh_token,
        }
        logger.debug(f"Exchanging for tokens with data: {data} and headers: {headers}")

        try:
            response = requests.post(TOKEN_EXCHANGE_URL, headers=headers, data=data)
            logger.debug(f"Exchanged tokens: {response.status_code} - {response.text}")
            response.raise_for_status()  # Raise an exception for HTTP errors
            token_data = response.json()

            print("Successfully exchanged code for tokens.")
            return token_data.get("access_token"), token_data.get("refresh_token")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Error during token exchange: {e} - {e.response.text if e.response else ''}"
            )
        except ValueError:
            raise RuntimeError("Error: Could not decode JSON response.")


if __name__ == "__main__":
    # Example usage
    try:
        tesla_client = TeslaClient()
        # Assuming you have a TimeOfUseSettings object to pass
        tesla_client.update(None)  # Replace None with actual TimeOfUseSettings object
    except Exception as e:
        print(f"An error occurred: {e}")
