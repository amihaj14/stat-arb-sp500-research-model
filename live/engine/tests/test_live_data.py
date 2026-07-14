# test_live_data_full.py
import requests
from live.engine.auth import get_session

def headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "pairs-trading-sp500/0.1",
    }

def test_time_and_accounts():
    api_server, token = get_session(practice=False)
    print(f"Session OK. api_server={api_server}")

    # /v1/time
    time_url = f"{api_server}/v1/time"
    r_time = requests.get(time_url, headers=headers(token))
    print("\n/time status:", r_time.status_code)
    print("time body:", r_time.text)

    # /v1/accounts (sample call in Questrade docs)[web:14]
    acct_url = f"{api_server}/v1/accounts"
    r_acct = requests.get(acct_url, headers=headers(token))
    print("\n/accounts status:", r_acct.status_code)
    print("accounts body:", r_acct.text)

    return api_server, token, r_time.status_code, r_acct.status_code

def test_symbols(api_server: str, token: str):
    tickers = ["MSFT", "AAPL", "SPY"]
    names_param = ",".join(tickers)

    # NOTE: single slash before /v1
    sym_url = f"{api_server}/v1/symbols"
    params = {"names": names_param}
    r_sym = requests.get(sym_url, headers=headers(token), params=params)
    print("\n/symbols status:", r_sym.status_code)
    print("symbols url:", r_sym.url)
    print("symbols body:", r_sym.text)

if __name__ == "__main__":
    api_server, token, st_time, st_acct = test_time_and_accounts()
    if st_time != 200:
        print("\nERROR: /time failed; token or server is not valid.")
    if st_acct != 200:
        print("\nERROR: /accounts failed; token is not authorized for this account.")
    test_symbols(api_server, token)