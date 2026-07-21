"""
Report generation: equity curve / drawdown charts, metrics table, and
the current target portfolio weights (the part you actually act on).
"""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_performance(
    portfolio_cumulative: pd.Series,
    benchmark_cumulative: dict[str, pd.Series],
    drawdown: pd.Series,
    out_path: str,
):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), gridspec_kw={"height_ratios": [2.2, 1]})

    ax1.plot(portfolio_cumulative.index, (portfolio_cumulative - 1) * 100, label="Strategy", linewidth=2, color="#1F3864")
    for name, series in benchmark_cumulative.items():
        aligned = series.reindex(portfolio_cumulative.index).ffill()
        ax1.plot(aligned.index, (aligned / aligned.iloc[0] - 1) * 100, label=name, linewidth=1.4, linestyle="--")
    ax1.set_title("Cumulative Return: Strategy vs. Benchmarks")
    ax1.set_ylabel("Cumulative Return (%)")
    ax1.legend(loc="upper left")
    ax1.grid(alpha=0.25)

    ax2.fill_between(drawdown.index, drawdown * 100, 0, color="#B3261E", alpha=0.4)
    ax2.set_title("Strategy Drawdown")
    ax2.set_ylabel("Drawdown (%)")
    ax2.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def print_summary(metrics: dict, benchmark_metrics: dict[str, dict], final_weights: pd.Series):
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"{'Metric':<22}{'Strategy':>12}", end="")
    for name in benchmark_metrics:
        print(f"{name:>14}", end="")
    print()

    def row(label, key, pct=True):
        val = metrics[key]
        print(f"{label:<22}{val*100 if pct else val:>11.2f}{'%' if pct else '':<1}", end="")
        for name, bm in benchmark_metrics.items():
            v = bm[key]
            print(f"{v*100 if pct else v:>13.2f}{'%' if pct else '':<1}", end="")
        print()

    row("Total Return", "total_return")
    row("CAGR", "cagr")
    row("Annualised Vol", "annualised_vol")
    row("Sharpe Ratio", "sharpe_ratio", pct=False)
    row("Max Drawdown", "max_drawdown")

    print("\n" + "=" * 60)
    print("CURRENT TARGET PORTFOLIO (rebalance-ready weights)")
    print("=" * 60)
    for ticker, w in final_weights.sort_values(ascending=False).items():
        print(f"  {ticker:<10}{w*100:>6.2f}%")
    print("=" * 60 + "\n")
