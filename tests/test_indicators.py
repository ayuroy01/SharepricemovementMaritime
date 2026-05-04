import numpy as np
import pandas as pd

from indicators import compute_indicators, rsi


def _synthetic(n=300, seed=0):
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0005, 0.02, n)
    prices = 100 * np.cumprod(1 + rets)
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "Open": prices, "High": prices * 1.01, "Low": prices * 0.99,
        "Close": prices, "Volume": rng.integers(1e5, 1e6, n),
    }, index=idx)


def test_rsi_bounded_0_100():
    df = _synthetic(200)
    r = rsi(df["Close"]).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_compute_indicators_full_history():
    df = _synthetic(300)
    out = compute_indicators(df)
    assert out["bars"] == 300
    assert out["close"] is not None
    assert out["sma20"] is not None
    assert out["sma50"] is not None
    assert out["sma200"] is not None
    assert out["has_long"]
    assert out["rsi"] is not None
    assert out["trend"] in {
        "strong_uptrend", "uptrend", "sideways", "downtrend", "strong_downtrend"
    }


def test_compute_indicators_short_history_is_safe():
    df = _synthetic(30)
    out = compute_indicators(df)
    assert out["sma200"] is None
    assert out["has_long"] is False
    # No crash, schema intact
    for k in ("close", "sma20", "rsi", "trend", "bars"):
        assert k in out


def test_compute_indicators_empty_df():
    out = compute_indicators(pd.DataFrame())
    assert out["close"] is None
    assert out["bars"] == 0
    assert out["trend"] == "unknown"
