# test_live_quotes.py
from live.engine.live_data import get_latest_quotes

def main():
    tickers = ["MSFT", "AAPL", "SPY"]
    quotes = get_latest_quotes(tickers)

    print("Quotes DataFrame:")
    print(quotes)

    # quick sanity checks
    assert not quotes.empty, "quotes DataFrame is empty"
    for col in ["bidPrice", "askPrice", "lastTradePriceTrHrs", "lastTradeTime"]:
        assert col in quotes.columns, f"Missing column {col}"

    print("\nSUCCESS: live_data.get_latest_quotes is returning valid data.")

if __name__ == "__main__":
    main()