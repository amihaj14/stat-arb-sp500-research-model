from pathlib import Path
from research.Strategy import lin_reg, z_score, generate_signals
import numpy as np
import pandas as pd

def _load_pair_config(pair, config_path=None) :
    if config_path is None:
        config_path = Path(__file__).resolve().parents[1] / "config" / "pairs_config.csv"

    if not Path(config_path).exists():
        return {}

    config_df = pd.read_csv(config_path)
    row = config_df[config_df["Pair"] == pair]
    if row.empty:
        return {}

    row = row.iloc[0].to_dict()
    return {
        key: (float(value) if isinstance(value, str) and value.replace(".", "", 1).lstrip("-").isdigit() else value)
        for key, value in row.items()
    }


def _prepare_window(prices, stock1, stock2, window_length):
    if prices is None:
        raise ValueError("prices cannot be None")

    if isinstance(prices, pd.DataFrame):
        frame = prices[[stock1, stock2]].dropna()
    else:
        frame = pd.DataFrame(prices, columns=[stock1, stock2]).dropna()

    if frame.empty:
        return frame, None, None

    if window_length and window_length > 0:
        frame = frame.tail(int(window_length))

    return frame, frame[stock1], frame[stock2]


def compute_live_spread(prices, stock1, stock2, beta=None, window_length=None):
    window, x_series, y_series = _prepare_window(prices, stock1, stock2, window_length)
    if window.empty or x_series is None or y_series is None:
        return pd.Series(dtype=float), np.nan, np.nan, np.nan

    if beta is None:
        alpha, beta, _ = lin_reg(y_series, x_series)
    else:
        beta = float(beta)
        alpha = float(np.mean(y_series - beta * x_series))

    residuals = y_series - (alpha + beta * x_series)
    if hasattr(y_series, "index"):
        residuals = pd.Series(residuals, index=y_series.index)

    return residuals, alpha, beta, residuals.iloc[-1] if not residuals.empty else np.nan


def get_live_strategy_signal(prices, pair=None, stock1=None, stock2=None, config=None, beta=None):
    if config is None:
        config = _load_pair_config(pair) if pair else {}

    entry_threshold = config.get("Entry Threshold", 2.5)
    exit_threshold = config.get("Exit Threshold", 0.5)
    window_length = config.get("Window Length", 60)

    if beta is None:
        beta = config.get("Beta")

    window, x_series, y_series = _prepare_window(prices, stock1, stock2, window_length)
    if window.empty or x_series is None or y_series is None:
        return {
            "residual_series": pd.Series(dtype=float),
            "latest_residual": np.nan,
            "latest_z_score": np.nan,
            "spread_side": "flat",
            "signal": 0,
            "alpha": np.nan,
            "beta": beta,
        }

    residuals, alpha, beta, latest_residual = compute_live_spread(
        window,
        stock1,
        stock2,
        beta=beta,
        window_length=None,
    )
    zscore = z_score(residuals, window=int(window_length))
    signals = generate_signals(zscore, entry_threshold=float(entry_threshold), exit_threshold=float(exit_threshold))
    latest_signal = int(signals.iloc[-1]) if not signals.empty else 0

    if latest_signal == 1:
        spread_side = "long"
    elif latest_signal == -1:
        spread_side = "short"
    else:
        spread_side = "flat"

    return {
        "residual_series": residuals,
        "latest_residual": latest_residual,
        "latest_z_score": float(zscore.iloc[-1]) if not zscore.empty else np.nan,
        "spread_side": spread_side,
        "signal": latest_signal,
        "alpha": alpha,
        "beta": beta,
    }
