import os
from concurrent.futures import ThreadPoolExecutor

import matplotlib.pyplot as plt
import DataLoader
import Backtest
import Strategy
import pandas as pd

# Keep the full S&P 500 universe, but avoid expensive plotting during the scan.
beta_lookup = {(row.Stock1, row.Stock2): row.BetaValue for row in DataLoader.stockCombi_df.itertuples(index=False)}

pairs = list(DataLoader.stockCombi_df.itertuples(index=False))
print(f"Running backtest on {len(pairs)} candidate pairs using up to {min(8, os.cpu_count() or 1)} threads...")


def evaluate_pair(row):
    s1, s2 = row.Stock1, row.Stock2
    beta = row.BetaValue

    test_pair = DataLoader.testPrices[[s1, s2]].dropna()
    if test_pair.shape[0] < 100:
        return None

    _, _, residuals = Strategy.lin_reg(test_pair[s1], test_pair[s2])
    zscore = Strategy.z_score(residuals, 60)
    signals = Strategy.generate_signals(zscore)

    _, _, metrics = Backtest.backtest(test_pair, signals, beta, residuals, show_plots=False)
    metrics["Pair"] = f"{s1}-{s2}"
    return metrics


def plot_summary(results_df):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    top10 = results_df.head(10)
    axes[0, 0].barh(top10["Pair"][::-1], top10["Sharpe"][::-1], color="tab:blue")
    axes[0, 0].set_title("Top 10 Pairs by Sharpe Ratio")
    axes[0, 0].set_xlabel("Sharpe Ratio")

    axes[0, 1].hist(results_df["Sharpe"].dropna(), bins=30, color="tab:green", edgecolor="black")
    axes[0, 1].set_title("Sharpe Ratio Distribution")
    axes[0, 1].set_xlabel("Sharpe")
    axes[0, 1].set_ylabel("Count")

    axes[1, 0].scatter(results_df["Sharpe"], results_df["CAGR"], alpha=0.6)
    axes[1, 0].set_title("Sharpe vs CAGR")
    axes[1, 0].set_xlabel("Sharpe")
    axes[1, 0].set_ylabel("CAGR")

    axes[1, 1].scatter(results_df["Sharpe"], results_df["Max Drawdown"], alpha=0.6, color="tab:red")
    axes[1, 1].set_title("Sharpe vs Max Drawdown")
    axes[1, 1].set_xlabel("Sharpe")
    axes[1, 1].set_ylabel("Max Drawdown")

    fig.suptitle("Backtest Summary for Candidate Pairs", fontsize=16, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


def plot_top_pairs(best_pairs):
    fig, axes = plt.subplots(len(best_pairs), 3, figsize=(18, 5 * len(best_pairs)))
    if len(best_pairs) == 1:
        axes = [axes]

    for row_index, row in enumerate(best_pairs.itertuples(index=False)):
        pair = row.Pair
        s1, s2 = pair.split("-")
        pair_test = DataLoader.testPrices[[s1, s2]].dropna()

        _, cumulative, _ = Backtest.backtest(
            pair_test,
            Strategy.generate_signals(Strategy.z_score(Strategy.lin_reg(pair_test[s1], pair_test[s2])[2], window=60)),
            beta_lookup[(s1, s2)],
            Strategy.lin_reg(pair_test[s1], pair_test[s2])[2],
            show_plots=False,
        )
        residuals = Strategy.lin_reg(pair_test[s1], pair_test[s2])[2]
        zscore = Strategy.z_score(residuals, window=60)
        signals = Strategy.generate_signals(zscore)

        drawdown = cumulative / cumulative.cummax() - 1

        ax_cum = axes[row_index][0] if len(best_pairs) > 1 else axes[0]
        ax_dd = axes[row_index][1] if len(best_pairs) > 1 else axes[1]
        ax_spread = axes[row_index][2] if len(best_pairs) > 1 else axes[2]

        ax_cum.plot(cumulative, color="tab:blue")
        ax_cum.set_title(f"{pair} Cumulative Return")
        ax_cum.set_ylabel("Cumulative Value")

        ax_dd.plot(drawdown, color="tab:red")
        ax_dd.set_title(f"{pair} Drawdown")
        ax_dd.set_ylabel("Drawdown")

        ax_spread.plot(residuals, label="Residuals", color="tab:purple")
        ax_spread.plot(residuals[signals == 1], "rv", label="Short", markersize=6)
        ax_spread.plot(residuals[signals == -1], "g^", label="Long", markersize=6)
        ax_spread.set_title(f"{pair} Residuals + Signals")
        ax_spread.legend(loc="upper left")

    plt.tight_layout()
    plt.show()


worker_count = min(8, os.cpu_count() or 1)
with ThreadPoolExecutor(max_workers=worker_count) as executor:
    results = list(executor.map(evaluate_pair, pairs))

results = [r for r in results if r is not None]
results_df = pd.DataFrame(results)
if results_df.empty:
    print("No valid pairs found")
    raise SystemExit

results_df.sort_values("Sharpe", ascending=False, inplace=True)

print("\nTop 10 pairs by Sharpe:")
print(results_df.head(10).reset_index(drop=True).to_string(index=False))

best_pairs = results_df.head(3).copy()
print("\nBest 3 pairs by Sharpe:")
print(best_pairs[["Pair", "Sharpe", "CAGR", "Total Return", "Max Drawdown"]].to_string(index=False))

plot_summary(results_df)
plot_top_pairs(best_pairs)
