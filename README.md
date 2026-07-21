# Quantitative Portfolio Construction & Backtesting Tool

A factor-based, risk-weighted portfolio construction tool covering equities and crypto,
with a walk-forward backtest against S&P 500 and Bitcoin benchmarks.

Built to do two things at once: generate an actual, rebalance-ready portfolio I can act on,
and demonstrate an end-to-end quantitative investing workflow (factor scoring → risk-based
weighting → walk-forward backtesting → performance evaluation).

## Methodology

**Universe**: a curated list of ~30 liquid, well-known equities across sectors, plus 7 major
cryptoassets (configurable in `config.py`).

**Equity selection**: a composite z-score combining three factors, equally weighted:
- **Value** — inverse trailing P/E (cheaper is better)
- **Quality** — return on equity
- **Momentum** — trailing 6-month total return

The top 10 equities by composite score are selected each rebalance.

**Crypto selection**: top 4 assets by trailing 6-month momentum (crypto has no P/E or ROE,
so momentum is the only sensible cross-sectional factor here).

**Weighting**: inverse-volatility ("risk parity-lite") within each sleeve — lower-volatility
assets get a larger weight, higher-volatility assets get a smaller one. Sleeves are then
blended at a fixed 80% equity / 20% crypto policy split, reflecting crypto's much higher
volatility relative to equities.

**Backtest**: walk-forward, monthly rebalance. At every rebalance date, the model re-selects
and re-weights the portfolio using *only* price history available up to that date — it does
not use future information to make past decisions. This is the single most common mistake in
home-built backtests (using today's winners to "predict" the past) and this tool is built
specifically to avoid it.

## Known limitations (worth being upfront about)

- **Fundamentals are point-in-time-current, not historical.** Free data providers don't
  make historical P/E/ROE easy to access, so every rebalance in the backtest uses today's
  fundamentals rather than what was actually known at that historical date. This makes the
  equity selection in early backtest periods somewhat optimistic. A production version would
  need a proper point-in-time fundamentals database.
- **Survivorship bias**: the universe is a fixed, curated list of companies that exist today,
  not a historically accurate index constituent list.
- **No transaction costs or slippage** are modelled.
- **Small universe** (~30 equities): chosen deliberately for speed and reliable data, at the
  cost of being a much narrower opportunity set than a real factor fund would use.

None of this invalidates the exercise — it's standard practice to document a backtest's
limitations rather than pretend it's more rigorous than it is.

## Usage

```bash
pip install -r requirements.txt
python main.py
```

This will:
1. Pull ~3 years of daily prices for the configured universe (needs internet — uses yfinance)
2. Fetch current fundamentals for the equity universe
3. Run the walk-forward backtest
4. Print a performance summary (strategy vs. SPY vs. BTC) and the current target portfolio
5. Save a performance chart to `output/performance.png`

## Testing without internet access

`test_synthetic.py` runs the entire pipeline against synthetic (random-walk) price data
instead of live market data, to verify the logic is correct independent of any data
connectivity. Useful for CI, or for verifying changes without burning API calls:

```bash
python test_synthetic.py
```

## Project structure

```
config.py      — universe, strategy parameters (edit this to change behaviour)
data.py        — yfinance data access layer
factors.py     — value / quality / momentum / volatility calculations
portfolio.py   — factor scores -> target portfolio weights
backtest.py    — walk-forward backtest engine + performance metrics
report.py      — charts and summary output
main.py        — orchestrates the full pipeline
test_synthetic.py — end-to-end pipeline test using synthetic data
```

## Disclaimer

Built for educational / portfolio purposes. Not investment advice. Past (simulated)
performance is not indicative of future results.
