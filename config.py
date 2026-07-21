"""
Walk-forward backtest.

Deliberately walk-forward (re-selects the portfolio at every rebalance
date using only price history available up to that date) rather than
applying today's selection to past prices, to avoid look-ahead bias -
the single most common mistake in home-made backtests.

Known simplification: fundamentals (P/E, ROE) are point-in-time-current
rather than historical, since free data providers don't give historical
fundamentals easily. This means the *equity selection* in early periods
of a long backtest is somewhat optimistic. Documented here rather than
hidden - worth being able to explain this trade-off if asked about it.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from factors import compute_momentum, compute_annualised_volatility, equity_composite_score
from portfolio import inverse_vol_weights


def get_rebalance_dates(index: pd.DatetimeIndex, freq: str) -> list[pd.Timestamp]:
    """First trading day of each period (e.g. month) within the index range."""
    s = pd.Series(index=index, data=index)
    grouped = s.groupby(pd.Grouper(freq=freq)).first()
    return [d for d in grouped.dropna().tolist() if d in index]


def run_backtest(
    equity_prices: pd.DataFrame,
    crypto_prices: pd.DataFrame,
    fundamentals: pd.DataFrame,
    cfg,
) -> dict:
    all_prices = equity_prices.join(crypto_prices, how="outer").sort_index()
    rebalance_dates = get_rebalance_dates(all_prices.index, cfg.REBALANCE_FREQ)

    min_history = max(cfg.MOMENTUM_WINDOW_DAYS, cfg.VOL_WINDOW_DAYS) + 5
    rebalance_dates = [d for d in rebalance_dates if all_prices.index.get_loc(d) >= min_history]

    if len(rebalance_dates) < 2:
        raise ValueError("Not enough price history for even one full rebalance period.")

    daily_returns = all_prices.pct_change()
    portfolio_daily_returns = []
    weights_history = {}

    for i, reb_date in enumerate(rebalance_dates):
        loc = all_prices.index.get_loc(reb_date)
        window_equity = equity_prices.iloc[: loc + 1]
        window_crypto = crypto_prices.iloc[: loc + 1]

        momentum = compute_momentum(window_equity, cfg.MOMENTUM_WINDOW_DAYS)
        scores = equity_composite_score(momentum, fundamentals, cfg.FACTOR_WEIGHTS)
        selected_equities = scores.head(cfg.TOP_N_EQUITIES).index.tolist()
        eq_vol = compute_annualised_volatility(window_equity[selected_equities], cfg.VOL_WINDOW_DAYS)
        eq_weights = inverse_vol_weights(eq_vol) * cfg.EQUITY_SLEEVE_WEIGHT

        crypto_momentum = compute_momentum(window_crypto, cfg.MOMENTUM_WINDOW_DAYS).sort_values(ascending=False)
        selected_crypto = crypto_momentum.head(cfg.TOP_N_CRYPTO).index.tolist()
        cr_vol = compute_annualised_volatility(window_crypto[selected_crypto], cfg.VOL_WINDOW_DAYS)
        cr_weights = inverse_vol_weights(cr_vol) * cfg.CRYPTO_SLEEVE_WEIGHT

        period_weights = pd.concat([eq_weights, cr_weights])
        weights_history[reb_date] = period_weights

        period_end = rebalance_dates[i + 1] if i + 1 < len(rebalance_dates) else all_prices.index[-1]
        period_mask = (all_prices.index > reb_date) & (all_prices.index <= period_end)
        period_returns = daily_returns.loc[period_mask, period_weights.index]
        weighted = (period_returns * period_weights).sum(axis=1)
        portfolio_daily_returns.append(weighted)

    portfolio_returns = pd.concat(portfolio_daily_returns).sort_index()
    portfolio_returns = portfolio_returns[~portfolio_returns.index.duplicated()]

    return {
        "returns": portfolio_returns,
        "weights_history": weights_history,
        "final_weights": weights_history[rebalance_dates[-1]],
    }


def performance_metrics(returns: pd.Series, risk_free_rate: float) -> dict:
    returns = returns.dropna()
    n_days = len(returns)
    cumulative = (1 + returns).cumprod()
    total_return = cumulative.iloc[-1] - 1
    years = n_days / 252
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else float("nan")
    ann_vol = returns.std() * np.sqrt(252)
    sharpe = (cagr - risk_free_rate) / ann_vol if ann_vol > 0 else float("nan")

    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    max_drawdown = drawdown.min()

    return {
        "total_return": total_return,
        "cagr": cagr,
        "annualised_vol": ann_vol,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_drawdown,
        "cumulative_series": cumulative,
        "drawdown_series": drawdown,
    }
