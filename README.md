pandas
numpy
statsmodels
yfinance
matplotlib
requests


# Statistical Arbitrage — S&P 500 Pairs Trading System

## Overview

This repository implements an end-to-end pairs trading system for the S&P 500 universe: research and backtesting to discover profitable pairs, and a live paper-trading engine that executes the strategy in real time using the Questrade API.

The pipeline has two stages:

1. **Research (root directory)** — downloads historical prices, finds correlated/cointegrated pairs, backtests a mean-reversion strategy, and ranks candidates by Sharpe ratio.
2. **Live paper trading (`live/`)** — takes the top candidate pairs from research, feeds them live market data every scheduler cycle, and simulates trade execution based on real-time z-score signals.

See `live/README.md` for details on the paper-trading engine specifically.

## Repository Structure

```
├── DataLoader.py # price download, caching, train/test split, pair selection
├── Strategy.py # hedge ratio fitting, residual z-score, signal generation
├── Backtest.py # returns, Sharpe/Sortino/drawdown, plots
├── main.py # orchestrates research pipeline, ranks pairs by Sharpe
├── constituents.csv # S&P 500 ticker universe
├── price_cache.csv # cached historical prices (generated)
├── live/
│ ├── config/
│ │ └── pairs_config.csv # selected pairs + strategy params for live trading
│ ├── engine/
│ │ ├── auth.py # Questrade OAuth2 session management
│ │ ├── auth_init.py # one-time manual token bootstrap
│ │ ├── live_data.py # live quotes + historical candles
│ │ ├── live_trader.py # main paper-trading loop
│ │ ├── strategy_live.py # live z-score/signal computation
│ │ ├── risk.py # position sizing, stop-loss, side mapping
│ │ └── positions.py # position state, trade/PnL logging
│ ├── logs/ # daily_pnl.csv, trades.csv (generated, gitignored)
│ └── README.md # paper-trading engine documentation
└── README.md
```

## Dependencies

```
pandas
numpy
statsmodels
yfinance
matplotlib
requests
```



Install with:

```powershell
pip install -r requirements.txt
```

## Running the Research Pipeline

```powershell
python main.py
```

This downloads (or loads cached) price data, evaluates all candidate pairs, prints the top pairs by Sharpe ratio, and generates performance plots for each.

## Data Caching

`DataLoader.py` writes historical prices to `price_cache.csv` after the first download. If cached data doesn't cover the requested `START_DATE` or is missing tickers, the cache refreshes automatically. Delete it manually to force a full refresh:

```powershell
Remove-Item .\price_cache.csv
python main.py
```

## Customizing Date Ranges

Set in `DataLoader.py`:

```python
START_DATE = "2018-01-01"
split_date = "2023-01-01"
```

`START_DATE` controls how far back price history goes; `split_date` separates training from test data.

## From Research to Live Trading

Once `main.py` identifies strong candidate pairs, transfer their alpha, beta, and entry/exit thresholds into `live/config/pairs_config.csv`. The live engine (`live/engine/live_trader.py`) reads this file every run and applies the same z-score logic used in backtesting, but against live Questrade quotes instead of historical data.

## Troubleshooting

- If Yahoo Finance skips tickers, they may be delisted; this is expected and handled gracefully.
- Stale cache after changing `START_DATE` requires deleting `price_cache.csv`.
- For live trading issues (auth errors, missing data), see `live/README.md`.

## Recommended Next Steps

- Use higher entry/exit z-score thresholds to reduce weak trades.
- Filter candidate pairs by sector or minimum spread volatility.
- Extend live engine with trade-level win-rate and PnL analytics.
