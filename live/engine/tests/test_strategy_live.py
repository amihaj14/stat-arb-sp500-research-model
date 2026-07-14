import pandas as pd

from live.engine.strategy_live import get_live_strategy_signal


def test_get_live_strategy_signal_returns_expected_fields():
    prices = pd.DataFrame(
        {
            "MSCI": [100.0, 101.0, 102.0, 103.0],
            "SHW": [100.0, 100.5, 103.0, 104.0],
        },
        index=pd.date_range("2024-01-01", periods=4, freq="D"),
    )

    result = get_live_strategy_signal(
        prices,
        pair="MSCI-SHW",
        stock1="MSCI",
        stock2="SHW",
        config={
            "Beta": 1.0,
            "Entry Threshold": 2.5,
            "Exit Threshold": 0.5,
            "Window Length": 4,
        },
    )

    assert "residual_series" in result
    assert "latest_residual" in result
    assert "latest_z_score" in result
    assert "spread_side" in result
    assert result["spread_side"] in {"long", "short", "flat"}
    assert result["latest_residual"] is not None
