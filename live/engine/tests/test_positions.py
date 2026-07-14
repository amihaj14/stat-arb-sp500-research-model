import pandas as pd

from live.engine import positions


def test_load_positions_returns_only_open_positions(tmp_path, monkeypatch):
    path = tmp_path / "positions.csv"
    pd.DataFrame(
        [
            {
                "pair_id": "pair_a",
                "status": "open",
                "s1": "AAPL",
                "s2": "MSFT",
                "qty_s1": 1.0,
                "qty_s2": -1.0,
            },
            {
                "pair_id": "pair_b",
                "status": "closed",
                "s1": "AAPL",
                "s2": "MSFT",
                "qty_s1": 2.0,
                "qty_s2": -2.0,
            },
        ]
    ).to_csv(path, index=False)

    monkeypatch.setattr(positions, "POSITION_PATH", path)

    loaded = positions.load_positions()

    assert list(loaded.keys()) == ["pair_a"]
    assert loaded["pair_a"]["status"] == "open"
    assert loaded["pair_a"]["s1"] == "AAPL"


def test_save_positions_writes_csv_to_position_path(tmp_path, monkeypatch):
    path = tmp_path / "positions.csv"
    monkeypatch.setattr(positions, "POSITION_PATH", path)

    positions.save_positions(
        {
            "pair_a": {"pair_id": "pair_a", "status": "open", "qty_s1": 1.0},
            "pair_b": {"pair_id": "pair_b", "status": "open", "qty_s1": 2.0},
        }
    )

    saved = pd.read_csv(path)
    assert list(saved["pair_id"]) == ["pair_a", "pair_b"]
    assert list(saved["status"]) == ["open", "open"]


def test_open_spread_builds_expected_position_for_long_spread():
    pair_cfg = {"pair_id": "pair_a", "s1": "AAPL", "s2": "MSFT", "beta": 0.5}
    latest_prices = {"AAPL": 100.0, "MSFT": 200.0}

    pos = positions.open_spread(pair_cfg, latest_prices, side="long_spread", size_notional=1000.0)

    assert pos["pair_id"] == "pair_a"
    assert pos["side"] == "long_spread"
    assert pos["qty_s1"] == -10.0
    assert pos["qty_s2"] == 5.0
    assert pos["status"] == "open"
    assert pos["realized_pnl"] == 0.0


def test_close_spread_marks_position_closed_and_returns_pnl():
    pair_cfg = {"pair_id": "pair_a", "s1": "AAPL", "s2": "MSFT", "beta": 0.5}
    latest_prices = {"AAPL": 100.0, "MSFT": 200.0}
    position = positions.open_spread(pair_cfg, latest_prices, side="long_spread", size_notional=1000.0)

    exit_prices = {"AAPL": 110.0, "MSFT": 190.0}
    closed_position, pnl = positions.close_spread(position, exit_prices)

    assert closed_position["status"] == "closed"
    assert closed_position["exit_time"] is not None
    assert pnl == -150.0
    assert closed_position["realized_pnl"] == -150.0
