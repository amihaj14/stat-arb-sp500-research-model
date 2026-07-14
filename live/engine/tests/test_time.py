# test_time.py
import requests
from live.engine.auth import get_session

def main():
    api_server, access_token = get_session(practice=False)
    url = f"{api_server}/v1/time"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "User-Agent": "pairs-trading-sp500/0.1",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    print(resp.json())

if __name__ == "__main__":
    main()