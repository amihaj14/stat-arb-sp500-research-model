import os
from concurrent.futures import ThreadPoolExecutor

import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint
import Strategy

CACHE_PATH = "price_cache.csv"
MAX_CANDIDATE_PAIRS = 2500
CORRELATION_THRESHOLD = 0.92

# Load the S&P 500 universe from the CSV file.
tickers_df = pd.read_csv("constituents.csv")
tickers = tickers_df["Symbol"].dropna().astype(str).str.strip().tolist()

# Mapping for tickers Yahoo Finance uses differently.
ticker_map = {"BRK.B": "BRK-B", "BF.B": "BF-B"}
tickers_yf = [ticker_map.get(t, t) for t in tickers]

if os.path.exists(CACHE_PATH):
    print(f"Loading cached price data from {CACHE_PATH}...")
    prices = pd.read_csv(CACHE_PATH, index_col=0, parse_dates=True)
else:
    print(f"Downloading price data for {len(tickers_yf)} symbols...")
    df = yf.download(
        tickers_yf,
        start="2015-01-01",
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="column",
    )

    if isinstance(df.columns, pd.MultiIndex):
        prices = df["Close"]
    else:
        prices = df

    prices = prices.dropna(axis=1, how="all").astype(float)
    prices.to_csv(CACHE_PATH)

split_date = "2020-01-01"
train_prices = prices.loc[:split_date]
test_prices = prices.loc[split_date:]

# Fast screening: compute price-level correlations once, then only evaluate pairs above the threshold.
correlation_matrix = train_prices.corr().abs()
triangular_mask = np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
correlated_pairs = correlation_matrix.where(triangular_mask).stack()
correlated_pairs = correlated_pairs[correlated_pairs > CORRELATION_THRESHOLD].sort_values(ascending=False)
correlated_pairs = correlated_pairs.head(MAX_CANDIDATE_PAIRS)

stockCombi_df = pd.DataFrame(
    [(stock1, stock2, float(corr)) for (stock1, stock2), corr in correlated_pairs.items()],
    columns=["Stock1", "Stock2", "Correlation"],
)
print(f"Evaluating {len(stockCombi_df)} correlated pairs...")

def _evaluate_pair(args):
    s1, s2, training_pair = args
    if training_pair.shape[0] < 100:
        return s1, s2, np.nan, np.nan

    x = training_pair[s1]
    y = training_pair[s2]

    _, p_val, _ = coint(x, y)
    _, beta, _ = Strategy.lin_reg(y, x)
    return s1, s2, p_val, beta


# The Engle-Granger two-step cointegration test.
pair_inputs = []
for row in stockCombi_df.itertuples(index=False):
    s1, s2, _ = row
    training_pair = train_prices[[s1, s2]].dropna()
    pair_inputs.append((s1, s2, training_pair))

worker_count = min(8, max(1, os.cpu_count() or 1))
with ThreadPoolExecutor(max_workers=worker_count) as executor:
    results = list(executor.map(_evaluate_pair, pair_inputs))

stockCombi_df[["Coint PVal", "BetaValue"]] = pd.DataFrame(
    results, columns=["Stock1", "Stock2", "Coint PVal", "BetaValue"]
)[["Coint PVal", "BetaValue"]]
stockCombi_df = stockCombi_df[stockCombi_df["Coint PVal"] < 0.05]

print(stockCombi_df.head(20))

# Export the prepared datasets for the rest of the pipeline.
trainPrices = train_prices
testPrices = test_prices