"""Generate deterministic synthetic sample data for DEMO mode.

Run from the repo root:  python3 sample_data/generate.py

The output is committed to the repo so cloners can run the dashboard
with no network access. All values are CLEARLY synthetic. Nothing here
should be interpreted as real market data.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent

# Watchlist mirrors config.DEFAULT_WATCHLIST so the demo "feels real" while
# being labelled as synthetic in the UI.
WATCHLIST = {
    "A.P. Moller - Maersk": "MAERSK-B.CO",
    "Hapag-Lloyd": "HLAG.DE",
    "ZIM Integrated Shipping": "ZIM",
    "Frontline Ltd.": "FRO",
    "Star Bulk Carriers": "SBLK",
    "Wallenius Wilhelmsen": "WAWI.OL",
}

# Per-ticker generation parameters chosen to produce a varied set of
# regimes (uptrend, downtrend, range) so every signal label can fire.
PARAMS = {
    "MAERSK-B.CO": dict(start=12000, drift=0.0006, vol=0.018, seed=11),
    "HLAG.DE":     dict(start=130,   drift=-0.0004, vol=0.022, seed=12),
    "ZIM":         dict(start=22,    drift=-0.0012, vol=0.030, seed=13),
    "FRO":         dict(start=20,    drift=0.0010, vol=0.025, seed=14),
    "SBLK":        dict(start=18,    drift=0.0009, vol=0.022, seed=15),
    "WAWI.OL":     dict(start=110,   drift=0.0002, vol=0.020, seed=16),
}

FUNDAMENTALS = {
    "MAERSK-B.CO": {"P/B": 0.65, "EV/EBITDA": 5.4, "Debt/Equity": 35,
                    "Current_Ratio": 1.45, "Market_Cap": 25e9, "Shares_Out": 1.7e9},
    "HLAG.DE":     {"P/B": 1.1, "EV/EBITDA": 9.8, "Debt/Equity": 40,
                    "Current_Ratio": 1.30, "Market_Cap": 22e9, "Shares_Out": 1.7e8},
    "ZIM":         {"P/B": 0.8, "EV/EBITDA": 7.5, "Debt/Equity": 165,
                    "Current_Ratio": 0.95, "Market_Cap": 2.5e9, "Shares_Out": 1.2e8},
    "FRO":         {"P/B": 2.4, "EV/EBITDA": 6.1, "Debt/Equity": 120,
                    "Current_Ratio": 1.10, "Market_Cap": 8.0e9, "Shares_Out": 2.2e8},
    "SBLK":        {"P/B": 1.0, "EV/EBITDA": 4.8, "Debt/Equity": 55,
                    "Current_Ratio": 1.40, "Market_Cap": 2.8e9, "Shares_Out": 1.1e8},
    "WAWI.OL":     {"P/B": 1.5, "EV/EBITDA": 5.9, "Debt/Equity": 80,
                    "Current_Ratio": 1.20, "Market_Cap": 5.0e9, "Shares_Out": 4.3e8},
}

# Synthetic, fictional headlines. No copyrighted text. Mix of relevant,
# geopolitical, and mildly off-topic items so the relevance filter has
# something to do.
SYNTHETIC_NEWS = {
    "MAERSK-B.CO": [
        ("Maersk reports stronger container freight rates on transpacific routes (sample)",
         "Sample Maritime Wire", 0.5, ["shipping", "freight"]),
        ("Red Sea diversions continue to add days to Asia-Europe shipping schedules (sample)",
         "Sample Trade Daily", -0.4, ["red sea", "shipping"]),
        ("Maersk announces fleet renewal program, cargo capacity to expand (sample)",
         "Sample Industry Report", 0.6, ["fleet", "cargo"]),
    ],
    "HLAG.DE": [
        ("Hapag-Lloyd posts mixed quarterly volumes amid weaker spot freight market (sample)",
         "Sample Maritime Wire", -0.1, ["freight"]),
        ("European port congestion eases as container ship arrivals normalise (sample)",
         "Sample Trade Daily", 0.3, ["port", "container"]),
    ],
    "ZIM": [
        ("ZIM's spot rate exposure highlights volatility in container shipping (sample)",
         "Sample Maritime Wire", -0.3, ["shipping"]),
        ("Houthi activity in Red Sea raises insurance premiums for tanker operators (sample)",
         "Sample Geopolitics Brief", -0.6, ["houthi", "red sea"]),
        ("Industry sentiment improves on easing Suez canal disruptions (sample)",
         "Sample Trade Daily", 0.4, ["suez", "canal"]),
    ],
    "FRO": [
        ("Frontline benefits from elevated tanker freight rates this quarter (sample)",
         "Sample Maritime Wire", 0.5, ["tanker", "freight"]),
        ("Sanctions on shadow fleet redirect crude trade routes (sample)",
         "Sample Geopolitics Brief", -0.2, ["sanction"]),
    ],
    "SBLK": [
        ("Star Bulk reports fleet utilisation rising as bulk carrier demand picks up (sample)",
         "Sample Maritime Wire", 0.4, ["fleet", "bulk carrier"]),
    ],
    "WAWI.OL": [
        ("Wallenius Wilhelmsen sees steady demand for vehicle carrier capacity (sample)",
         "Sample Industry Report", 0.2, ["vessel", "cargo"]),
        ("Trade-war tariff talk weighs on automotive shipping outlook (sample)",
         "Sample Geopolitics Brief", -0.3, ["tariff", "trade war"]),
    ],
}


def _gen_prices(start: float, drift: float, vol: float, seed: int, n: int = 180) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, n)
    closes = start * np.cumprod(1 + rets)
    opens = np.r_[closes[:1], closes[:-1]] * (1 + rng.normal(0, 0.001, n))
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, 0.004, n)))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, 0.004, n)))
    vols = rng.integers(2_000_000, 10_000_000, n)
    end = date(2026, 4, 30)  # fixed reference so output is deterministic
    idx = pd.bdate_range(end=end, periods=n)
    df = pd.DataFrame({
        "Date": idx, "Open": opens.round(2), "High": highs.round(2),
        "Low": lows.round(2), "Close": closes.round(2), "Volume": vols,
    })
    return df


def _gen_bdry(seed: int = 99, n: int = 90) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    closes = 18 * np.cumprod(1 + rng.normal(-0.0008, 0.025, n))
    end = date(2026, 4, 30)
    idx = pd.bdate_range(end=end, periods=n)
    return pd.DataFrame({"Date": idx, "Close": closes.round(2)})


def main() -> None:
    (ROOT / "prices").mkdir(parents=True, exist_ok=True)

    # Watchlist
    (ROOT / "watchlist.json").write_text(json.dumps(WATCHLIST, indent=2) + "\n")

    # Prices
    for ticker, p in PARAMS.items():
        df = _gen_prices(**p)
        df.to_csv(ROOT / "prices" / f"{ticker}.csv", index=False)

    # BDRY proxy
    _gen_bdry().to_csv(ROOT / "prices" / "BDRY.csv", index=False)

    # Fundamentals
    (ROOT / "fundamentals.json").write_text(json.dumps(FUNDAMENTALS, indent=2) + "\n")

    # News (with deterministic decreasing timestamps from the fixed reference)
    base = pd.Timestamp("2026-04-30T12:00:00Z")
    news = {}
    for ticker, items in SYNTHETIC_NEWS.items():
        rows = []
        for i, (title, source, sentiment_hint, geo) in enumerate(items):
            published = (base - pd.Timedelta(hours=6 * (i + 1))).isoformat()
            rows.append({
                "title": title,
                "source": source,
                "url": f"https://example.com/sample/{ticker.lower()}/{i}",
                "publishedAt": published,
                "description": "",
                "sample_geo_hint": geo,
                "sample_sentiment_hint": sentiment_hint,
            })
        news[ticker] = rows
    (ROOT / "news.json").write_text(json.dumps(news, indent=2) + "\n")

    print(f"Wrote sample data to {ROOT}")


if __name__ == "__main__":
    main()
