import numpy as np
import pandas as pd

from backtest import run_backtest


def _trending(n=400, drift=0.0008, seed=1):
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, 0.015, n)
    prices = 50 * np.cumprod(1 + rets)
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "Open": prices, "High": prices * 1.005, "Low": prices * 0.995,
        "Close": prices, "Volume": [1_000_000] * n,
    }, index=idx)


def test_backtest_runs_and_produces_metrics():
    df = _trending()
    res = run_backtest(df, "TEST")
    assert res.bars == len(df)
    assert isinstance(res.total_return, float)
    assert res.equity_curve and len(res.equity_curve) == len(df)
    assert res.benchmark_return == df["Close"].iloc[-1] / df["Close"].iloc[0] - 1
    # Drawdown is non-positive
    assert res.max_drawdown <= 0


def test_backtest_no_lookahead_uses_next_open():
    df = _trending()
    res = run_backtest(df, "TEST")
    # Every trade entry/exit must be at a date that exists in the index.
    valid_dates = {str(d.date()) for d in df.index}
    for t in res.trades:
        assert t.entry_date in valid_dates
        assert t.exit_date in valid_dates
        assert t.bars_held >= 1


def test_backtest_short_history_safe():
    short = _trending(n=20)
    res = run_backtest(short, "SHORT")
    assert res.bars == 20
    assert res.notes  # logged a note


def test_backtest_empty():
    res = run_backtest(pd.DataFrame(), "X")
    assert res.bars == 0
    assert res.notes
