from flask import Flask, render_template_string
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

app = Flask(__name__)

PNL_PATH = Path("live/logs/daily_pnl.csv")
TRADES_PATH = Path("live/logs/trades.csv")
POSITIONS_PATH = Path("live/logs/positions.csv")

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>Pairs Trader Dashboard</title>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, Segoe UI, Roboto, sans-serif;
    background: #0f1115;
    color: #e6e6e6;
    margin: 0;
    padding: 20px;
  }
  h1 {
    font-size: 22px;
    margin-bottom: 4px;
  }
  .timestamp {
    color: #888;
    font-size: 13px;
    margin-bottom: 24px;
  }
  .summary-row {
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
    flex-wrap: wrap;
  }
  .card {
    background: #1a1d24;
    border: 1px solid #2a2e38;
    border-radius: 10px;
    padding: 14px 18px;
    flex: 1;
    min-width: 140px;
  }
  .card .label {
    font-size: 12px;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .card .value {
    font-size: 24px;
    font-weight: 600;
    margin-top: 4px;
  }
  .positive { color: #3ecf8e; }
  .negative { color: #ef5b5b; }
  .neutral { color: #e6e6e6; }
  section {
    background: #15171c;
    border: 1px solid #2a2e38;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 20px;
  }
  section h2 {
    font-size: 15px;
    margin: 0 0 12px 0;
    color: #ccc;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  th, td {
    text-align: left;
    padding: 8px 10px;
    border-bottom: 1px solid #23262e;
    white-space: nowrap;
  }
  th {
    color: #999;
    font-weight: 500;
    font-size: 11px;
    text-transform: uppercase;
  }
  tr:hover td { background: #1c1f26; }
  .empty-msg {
    color: #666;
    font-style: italic;
    padding: 8px 0;
  }
  .status-open { color: #3ecf8e; font-weight: 600; }
  .status-closed { color: #888; }
  .action-open { color: #3ecf8e; }
  .action-close { color: #ef5b5b; }
</style>
</head>
<body>
  <h1>Pairs Trader — Live Status</h1>
  <div class="timestamp">Last refreshed: {{ now }} (auto-refreshes every 60s)</div>

  <div class="summary-row">
    <div class="card">
      <div class="label">Open Positions</div>
      <div class="value neutral">{{ open_count }}</div>
    </div>
    <div class="card">
      <div class="label">Total Realized PnL</div>
      <div class="value {{ realized_class }}">${{ realized_pnl }}</div>
    </div>
    <div class="card">
      <div class="label">Total Unrealized PnL</div>
      <div class="value {{ unrealized_class }}">${{ unrealized_pnl }}</div>
    </div>
    <div class="card">
      <div class="label">Trades Today</div>
      <div class="value neutral">{{ trades_today }}</div>
    </div>
  </div>

  <section>
    <h2>Open Positions</h2>
    {{ positions|safe }}
  </section>

  <section>
    <h2>Recent Trades</h2>
    {{ trades|safe }}
  </section>

  <section>
    <h2>Latest PnL</h2>
    {{ pnl|safe }}
  </section>
</body>
</html>
"""


def safe_read_df(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(path)
        return df if not df.empty else None
    except pd.errors.EmptyDataError:
        return None


def style_table(df: pd.DataFrame, status_col=None, action_col=None) -> str:
    if df is None:
        return '<div class="empty-msg">No data yet.</div>'

    html = df.to_html(index=False, classes="styled", border=0, escape=False)
    return html


@app.route("/")
def home():
    pos_df = safe_read_df(POSITIONS_PATH)
    trades_df = safe_read_df(TRADES_PATH)
    pnl_df = safe_read_df(PNL_PATH)

    open_count = 0
    if pos_df is not None and "status" in pos_df.columns:
        open_count = (pos_df["status"] == "open").sum()

    realized_pnl = 0.0
    unrealized_pnl = 0.0
    if pnl_df is not None:
        if "realized_pnl" in pnl_df.columns:
            realized_pnl = pnl_df["realized_pnl"].sum()
        if "unrealized_pnl" in pnl_df.columns:
            unrealized_pnl = pnl_df["unrealized_pnl"].iloc[-len(pos_df):].sum() if pos_df is not None else pnl_df["unrealized_pnl"].sum()

    trades_today = 0
    if trades_df is not None and "timestamp" in trades_df.columns:
        today = datetime.now(timezone.utc).date()
        trades_df["_date"] = pd.to_datetime(trades_df["timestamp"]).dt.date
        trades_today = (trades_df["_date"] == today).sum()
        trades_df = trades_df.drop(columns=["_date"]).tail(20)

    if pnl_df is not None:
        pnl_df = pnl_df.tail(20)

    return render_template_string(
        TEMPLATE,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        positions=style_table(pos_df),
        trades=style_table(trades_df),
        pnl=style_table(pnl_df),
        open_count=open_count,
        realized_pnl=f"{realized_pnl:,.2f}",
        unrealized_pnl=f"{unrealized_pnl:,.2f}",
        realized_class="positive" if realized_pnl > 0 else ("negative" if realized_pnl < 0 else "neutral"),
        unrealized_class="positive" if unrealized_pnl > 0 else ("negative" if unrealized_pnl < 0 else "neutral"),
        trades_today=trades_today,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)