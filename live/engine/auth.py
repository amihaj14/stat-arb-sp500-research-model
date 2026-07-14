# auth.py
import json
import os
from pathlib import Path
import time
import requests

TOKEN_PATH = Path.home() / ".qt_tokens.json"

def _load_tokens():
    if not TOKEN_PATH.exists():
        raise RuntimeError("Token file not found; run auth_init.py with a manual token first.")
    with open(TOKEN_PATH, "r") as f:
        return json.load(f)


def _save_tokens_atomic(data):
    tmp_path = TOKEN_PATH.with_name(TOKEN_PATH.name + ".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    os.replace(tmp_path, TOKEN_PATH)


def get_session():
    tokens = _load_tokens()
    refresh_token = tokens["refresh_token"]

    url = f"https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token={refresh_token}"
    r = requests.get(url)
    r.raise_for_status()
    payload = r.json()

    new_tokens = {
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "api_server": payload["api_server"],
        "issued_at": time.time(),
    }

    _save_tokens_atomic(new_tokens)

    return new_tokens["api_server"], new_tokens["access_token"]