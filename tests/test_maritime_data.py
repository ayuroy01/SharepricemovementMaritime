"""Watchlist row normalisation: the dashboard relies on a stable schema."""
from unittest.mock import patch

import pandas as pd

import maritime_data as md
from providers import NewsResult, ProviderStatus


def _ok_price():
    idx = pd.date_range("2024-01-01", periods=260, freq="B")
    return pd.DataFrame({
        "Open": range(260), "High": range(260), "Low": range(260),
        "Close": [100 + i * 0.1 for i in range(260)],
        "Volume": [1_000_000] * 260,
    }, index=idx), ProviderStatus("yfinance:price", ok=True, records=260)


def test_build_watchlist_row_schema_complete_on_success():
    funds = ({"P/B": 1.2, "EV/EBITDA": 8.0, "Debt/Equity": 60, "Current_Ratio": 1.5,
              "Market_Cap": 1e9, "Shares_Out": 1e8},
             ProviderStatus("yfinance:fundamentals", ok=True, records=4))
    news = (NewsResult(headlines=[], avg_sentiment=0.0, geo_alert=False,
                       relevant_count=0, source="none", fallback_used=False),
            ProviderStatus("news:no provider", ok=False, error="no key"))
    with patch("maritime_data.fetch_price_history", return_value=_ok_price()), \
         patch("maritime_data.fetch_fundamentals", return_value=funds), \
         patch("maritime_data.fetch_news", return_value=news):
        row, statuses = md.build_watchlist_row("Maersk", "MAERSK-B.CO")
    for k in md.ROW_SCHEMA:
        assert k in row, f"missing key: {k}"
    assert row["Action"] != "ERROR"
    assert isinstance(statuses, list) and len(statuses) >= 3


def test_build_watchlist_row_price_failure_does_not_crash():
    bad_price = (pd.DataFrame(), ProviderStatus("yfinance:price", ok=False, error="boom"))
    with patch("maritime_data.fetch_price_history", return_value=bad_price):
        row, statuses = md.build_watchlist_row("ZIM", "ZIM")
    assert row["Action"] == "ERROR"
    assert "boom" in row["Rationale"]
    # Schema still complete
    for k in md.ROW_SCHEMA:
        assert k in row


def test_build_watchlist_one_failure_does_not_break_others():
    def fake_price(ticker, period="6mo"):
        if ticker == "ZIM":
            return pd.DataFrame(), ProviderStatus("yfinance:price", ok=False, error="rate limited")
        return _ok_price()

    funds = ({"P/B": 1.0, "EV/EBITDA": 5.0, "Debt/Equity": 40, "Current_Ratio": 1.4,
              "Market_Cap": 1e9, "Shares_Out": 1e8},
             ProviderStatus("yfinance:fundamentals", ok=True, records=4))
    news = (NewsResult(headlines=[], avg_sentiment=0.0, geo_alert=False,
                       relevant_count=0, source="none", fallback_used=False),
            ProviderStatus("news:none", ok=False))
    bdi = (None, ProviderStatus("yfinance:BDRY", ok=False, error="no data"))

    with patch("maritime_data.fetch_price_history", side_effect=fake_price), \
         patch("maritime_data.fetch_fundamentals", return_value=funds), \
         patch("maritime_data.fetch_news", return_value=news), \
         patch("maritime_data.fetch_bdi_proxy", return_value=bdi):
        result = md.build_watchlist(watchlist={"Maersk": "MAERSK-B.CO", "ZIM": "ZIM"})
    assert "ZIM" in result["failures"]
    assert len(result["rows"]) == 2
    actions = {r["Ticker"]: r["Action"] for r in result["rows"]}
    assert actions["ZIM"] == "ERROR"
    assert actions["MAERSK-B.CO"] != "ERROR"
