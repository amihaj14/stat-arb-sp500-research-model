# wrappers for yfinance / Polygon / Questrade
import requests
import pandas as pd
from live.engine.auth import get_session
from datetime import datetime, timedelta, timezone

def _headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "pairs-trading-sp500/0.1",
    }

def get_history(tickers, api_server, token, interval="OneDay", lookback_days=120):
    id_map = resolve_symbols(tickers, api_server, token)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)
    start_str = start.isoformat(timespec="seconds")
    end_str = end.isoformat(timespec="seconds")

    frames = []
    base = api_server.rstrip("/")
    for sym, sid in id_map.items():
        url = f"{base}/v1/markets/candles/{sid}"
        params = {"interval": interval, "startTime": start_str, "endTime": end_str}
        r = requests.get(url, headers=_headers(token), params=params)
        r.raise_for_status()
        candles = r.json()["candles"]
        if not candles:
            continue
        df = pd.DataFrame(candles)
        df["time"] = pd.to_datetime(df["start"], utc=True)
        df["symbol"] = sym
        frames.append(df[["time", "close", "symbol"]])

    if not frames:
        return pd.DataFrame()
    big = pd.concat(frames, ignore_index=True)
    return big.pivot(index="time", columns="symbol", values="close").sort_index()

def resolve_symbols(tickers, api_server, token):
    base = api_server.rstrip("/")  # <-- FIX: strip trailing slash here
    url = f"{base}/v1/symbols"
    params = {"names": ",".join(tickers)}
    r = requests.get(url, headers=_headers(token), params=params)
    r.raise_for_status()
    symbols = r.json()["symbols"]
    return {s["symbol"]: s["symbolId"] for s in symbols}


def get_latest_quotes(tickers, api_server, token):
    base = api_server.rstrip("/")
    id_map = resolve_symbols(tickers, api_server, token)
    ids = ",".join(str(i) for i in id_map.values())
    url = f"{base}/v1/markets/quotes"
    params = {"ids": ids}
    r = requests.get(url, headers=_headers(token), params=params)
    r.raise_for_status()
    quotes = r.json()["quotes"]

    df = pd.DataFrame(quotes)
    inv = {v: k for k, v in id_map.items()}
    df["symbol"] = df["symbolId"].map(inv)
    df.set_index("symbol", inplace=True)
    return df[["bidPrice", "askPrice", "lastTradePriceTrHrs", "lastTradeTime"]]