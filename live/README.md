
# Live Paper Trading Engine

## Overview

This module runs the pairs trading strategy in real time as **paper trades** (no real orders are sent) using live quotes and historical candles from the Questrade API. It's designed to run on a schedule (e.g., every 15 minutes during market hours) via Windows Task Scheduler or cron.

## Architecture

```
live/
├── config/
│ └── pairs_config.csv # Pair, Stock1, Stock2, Alpha, Beta,
│ Entry Threshold, Exit Threshold, Window Length
├── engine/
│ ├── auth.py # OAuth2 session + atomic refresh-token rotation
│ ├── auth_init.py # one-time manual token setup
│ ├── live_data.py # symbol resolution, live quotes, historical candles
│ ├── live_trader.py # main loop: signal → risk check → open/close/hold
│ ├── strategy_live.py # residual z-score computation on live data
│ ├── risk.py # position sizing, stop-loss, z-score-to-side mapping
│ └── positions.py # position persistence, trade + PnL logging
└── logs/
├── daily_pnl.csv # per-pair PnL snapshot, every run
├── trades.csv # open/close trade log
└── positions.json # current open positions state
```



## How It Works

1. `get_session()` authenticates with Questrade, redeeming the stored refresh token for a new access token and **immediately** persisting the new refresh token atomically (single-use rotation — losing this breaks the chain).
2. `get_latest_quotes()` and `get_history()` pull live bid/ask prices and enough daily candles to satisfy each pair's `Window Length`.
3. For each configured pair, `strategy_live.py` computes the current residual z-score against the fitted alpha/beta from research.
4. `risk.py` maps the z-score to a desired side (long spread / short spread / flat) and applies stop-loss/drawdown checks against any open position.
5. `positions.py` opens, holds, or closes positions accordingly, logging every trade to `trades.csv` and every PnL snapshot to `daily_pnl.csv`.
6. A file lock (`~/.qt_trader.lock`) prevents overlapping runs from corrupting the token or position state.

## Setup

### 1. Bootstrap authentication (one-time)

Get a manual refresh token from your Questrade app portal, then run:

```powershell
python -m live.engine.auth_init
```

This writes `~/.qt_tokens.json`, which `auth.py` will rotate automatically on every subsequent run.

### 2. Configure pairs

Populate `live/config/pairs_config.csv` with pairs selected from the research pipeline (`main.py` output), including fitted `Alpha`, `Beta`, `Entry Threshold`, `Exit Threshold`, and `Window Length`.

### 3. Run manually to verify

```powershell
python -m live.engine.live_trader
```

Check `live/logs/daily_pnl.csv` for a new row per pair.

### 4. Schedule it

Set up a scheduled task (Mon–Fri, every 15 minutes, market hours) to run:

```powershell
python -m live.engine.live_trader
```

Do not run manually while the scheduler is active — concurrent runs can race on the refresh token and break the auth chain.

## Token Rotation Notes

Questrade access tokens expire every 30 minutes; refresh tokens are single-use and rotate on every redemption. `auth.py` handles this automatically:

- Refresh token is redeemed and the new one saved atomically (`os.replace`) before anything else executes.
- If a run crashes *after* redemption but *before* saving, the chain breaks and you must regenerate manually via `auth_init.py`.

## Troubleshooting

| Symptom                                              | Likely cause                                                                                  |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `401 Unauthorized` on first run                    | Manual token expired/invalid; rerun`auth_init.py`                                           |
| `401 Unauthorized` only after first successful run | Refresh token not persisted (crash between redeem and save); check`auth.py` for exceptions  |
| Pairs skipped with no z-score logged                 | `lookback_days` insufficient for `Window Length`; increase buffer in `get_history` call |
| `daily_pnl.csv` not updating                       | Check for silent exceptions inside the pair loop; add debug prints per pair                   |
| "Another instance appears to be running"             | Stale lock file from a crashed run; delete`~/.qt_trader.lock` manually                      |

## Files Excluded from Git

Tokens, lock files, and generated logs/state are gitignored — see root `.gitignore`. Never commit `~/.qt_tokens.json` or any file matching `*.qt_tokens*`.
