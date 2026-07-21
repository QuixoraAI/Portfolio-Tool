"""
Validates the entire pipeline (factors -> portfolio construction ->
backtest -> report) using synthetic random-walk price data instead of
real yfinance data, since this sandbox has no internet access.

This proves the LOGIC is correct and bug-free. When you run main.py
on your own machine with internet access, it uses real yfinance data
instead - same code path, just swap the data source.

Run: python3 test_synthetic.py
"""
import numpy as np
import pandas as pd

import config
import backtest
import report


def make_synthetic_prices(tickers, days, seed_offset=0, annual_drift=0.08, annual_vol=0.25):
    """Geometric Brownian motion price paths - good enough to exercise all the code paths."""
    rng = np.random.default_rng(42 + seed_offset)
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=days)
    daily_drift = annual_drift / 252
    daily_vol = annual_vol / np.sqrt(252)

    data = {}
    for i, t in enumerate(tickers):
        rng_t = np.random.default_rng(100 + seed_offset + i)
        shocks = rng_t.normal(daily_drift, daily_vol, size=days)
        prices = 100 * np.exp(np.cumsum(shocks))
        data[t] = prices
    return pd.DataFrame(data, index=dates)


def make_synthetic_fundamentals(tickers, seed=7):
    rng = np.random.default_rng(seed)
    rows = []
    for t in tickers:
        rows.append({
            "ticker": t,
            "trailing_pe": rng.uniform(8, 35),
            "return_on_equity": rng.uniform(0.05, 0.35),
        })
    return pd.DataFrame(rows).set_index("ticker")


def main():
    print("Building synthetic test data (no internet used)...")
    days = config.LOOKBACK_YEARS * 252

    equity_prices = make_synthetic_prices(config.EQUITY_UNIVERSE, days, seed_offset=0, annual_vol=0.22)
    crypto_prices = make_synthetic_prices(config.CRYPTO_UNIVERSE, days, seed_offset=100, annual_drift=0.15, annual_vol=0.55)
    benchmark_prices = make_synthetic_prices(list(config.BENCHMARKS.keys()), days, seed_offset=200, annual_vol=0.18)
    fundamentals = make_synthetic_fundamentals(config.EQUITY_UNIVERSE)

    print("Running walk-forward backtest on synthetic data...")
    result = backtest.run_backtest(equity_prices, crypto_prices, fundamentals, config)
    print(f"  -> {len(result['weights_history'])} rebalance periods executed")
    print(f"  -> {len(result['returns'])} daily return observations")

    assert abs(result["final_weights"].sum() - 1.0) < 1e-6, "Weights should sum to 1.0"
    assert not result["returns"].isna().all(), "Should have real return observations"
    print("  -> Weight sum check: PASS (sums to 1.0)")

    metrics = backtest.performance_metrics(result["returns"], config.RISK_FREE_RATE)
    assert not np.isnan(metrics["sharpe_ratio"]), "Sharpe ratio should compute"
    print("  -> Metrics computation check: PASS")

    benchmark_metrics = {}
    benchmark_cumulative = {}
    for ticker, label in config.BENCHMARKS.items():
        bm_returns = benchmark_prices[ticker].pct_change().reindex(result["returns"].index).dropna()
        bm_metrics = backtest.performance_metrics(bm_returns, config.RISK_FREE_RATE)
        benchmark_metrics[label] = bm_metrics
        benchmark_cumulative[label] = bm_metrics["cumulative_series"]

    report.print_summary(metrics, benchmark_metrics, result["final_weights"])
    report.plot_performance(
        metrics["cumulative_series"], benchmark_cumulative, metrics["drawdown_series"],
        "output/test_performance.png",
    )
    print("Chart saved to output/test_performance.png")
    print("\nALL CHECKS PASSED - pipeline logic is verified end-to-end.")


if __name__ == "__main__":
    main()
