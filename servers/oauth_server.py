import uuid
from flask import Flask, request, render_template, send_from_directory
import os
from datetime import datetime, timedelta

import requests

app = Flask(__name__)

CACHE = {}
CACHE_LIMMIT = 1000  # Limit the number of states in the cache

AUTH_DIR = os.environ.get("AUTH_DIR", "/app/auth")
## Get the current working directory of the file
KEYS_DIR = f"{os.path.dirname(__file__)}/.keys"  # Assuming .keys is in the current working directory of the app

AUDIENCE = "https://fleet-api.prd.na.vn.cloud.tesla.com"
CALLBACK_URL = "https://pow.coldzee.win/oauth_redirect"
TOKEN_EXCHANGE_URL = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token"


@app.route("/oauth_redirect")
def oauth_redirect():
    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return "Missing code or state parameter", 400
    if state not in CACHE or datetime.now() > CACHE[state]["expiration"]:
        return "Invalid or expired state parameter", 400

    print(f"Received OAuth code: {code}")

    refresh_token, _ = exchange_refresh_token(code)

    if code:
        file_path = os.path.join(AUTH_DIR, "tesla_refresh_token.txt")
        try:
            with open(file_path, "w") as f:
                f.write(refresh_token)
            return "OAuth redirect successful! Token saved."
        except IOError as e:
            return f"Error saving code: {e}", 500
    return "OAuth redirect successful! No code received.", 400


@app.route("/.well-known/appspecific/com.tesla.3p.public-key.pem")
def serve_public_key():
    try:
        return read_file(os.path.join(KEYS_DIR, "public_key.pem"))
    except FileNotFoundError:
        return "Public key file not found", 404
    except Exception as e:
        return f"Error serving public key", 500


@app.route("/")
def home():
    client_id = os.environ.get("TESLA_CLIENT_ID")
    state = uuid.uuid4().hex
    CACHE[state] = {
        "expiration": datetime.now() + timedelta(minutes=15),
    }
    # Evict oldest state if cache limit is reached
    while len(CACHE) > CACHE_LIMMIT:
        oldest_state = min(CACHE.keys(), key=lambda k: CACHE[k]["expiration"])
        del CACHE[oldest_state]

    return render_template(
        "index.html", client_id=client_id, redirect_uri=CALLBACK_URL, state=state
    )


def read_file(file_path: str) -> str:
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


def exchange_refresh_token(auth_code: str) -> tuple[str, str]:
    """
    Exchanges the authorization code for access and refresh tokens.
    Reads the authorization code from /app/auth/tesla_oauth_code.txt
    and makes a POST request to Tesla's OAuth2 token endpoint.
    Extracts access_token and refresh_token from the response.
    """

    client_id = os.environ.get("TESLA_CLIENT_ID")
    client_secret = os.environ.get("TESLA_CLIENT_SECRET")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "audience": AUDIENCE,
        "redirect_uri": CALLBACK_URL,
    }
    print(f"Exchanging code for tokens with data: {data} and headers: {headers}")

    try:
        response = requests.post(TOKEN_EXCHANGE_URL, headers=headers, data=data)
        print(f"Exchanging code for tokens: {response.status_code} - {response.text}")
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 9090)))
