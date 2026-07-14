# auth_init.py
import json
from pathlib import Path
from datetime import datetime, timedelta

import requests

TOKEN_PATH = Path.home() / ".qt_tokens.json"

def redeem_manual_token(manual_token: str, practice: bool = False):
    base = "https://practicelogin.questrade.com" if practice else "https://login.questrade.com"
    url = f"{base}/oauth2/token"

    params = {
        "grant_type": "refresh_token",
        "refresh_token": manual_token,
    }

    resp = requests.get(url, params=params, headers={"Accept": "application/json"})
    resp.raise_for_status()
    data = resp.json()

    # data: access_token, refresh_token, api_server, token_type, expires_in, etc.[web:14][web:28]
    data["access_expiry"] = (datetime.utcnow() + timedelta(seconds=data["expires_in"])).isoformat()

    TOKEN_PATH.write_text(json.dumps(data, indent=2))
    print("Saved tokens to", TOKEN_PATH)
    print("API server:", data["api_server"])
    return data

if __name__ == "__main__":
    manual = input("Paste manual token: ").strip()
    redeem_manual_token(manual, practice=False)  # True if you generated it from a practice account