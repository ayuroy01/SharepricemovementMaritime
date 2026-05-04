"""Tests for the provider layer using mocks. No live API calls."""
from unittest.mock import patch

import pandas as pd
import pytest

import providers
from providers import (
    NewsResult,
    ProviderStatus,
    _build_query,
    _dedupe,
    _relevance,
    _sanitise_error,
    _score_one,
    fetch_news,
)


def test_sanitise_error_redacts_apikey():
    exc = RuntimeError("connect failed url=https://x?apiKey=SECRET&q=foo")
    msg = _sanitise_error(exc)
    assert "SECRET" not in msg
    assert "[redacted]" in msg
    assert "RuntimeError" in msg


def test_relevance_zero_for_unrelated():
    assert _relevance("Apple unveils new MacBook with M5 chip") == 0.0


def test_relevance_positive_for_maritime_geo():
    r = _relevance("Houthi missile strike disrupts Red Sea shipping containers")
    assert r > 0.5


def test_dedupe_by_url_and_title():
    items = [
        {"title": "A", "url": "u1"},
        {"title": "B", "url": "u1"},     # dup url
        {"title": "a", "url": "u2"},     # dup title (case-insensitive)
        {"title": "C", "url": "u3"},
    ]
    out = _dedupe(items)
    titles = [i["title"] for i in out]
    assert "A" in titles and "C" in titles
    assert len(out) == 2


def test_score_one_attaches_fields():
    item = {"title": "Suez canal blocked, freight rates surge", "description": "shipping"}
    s = _score_one(item)
    assert "sentiment" in s and "relevance" in s and "geo_keywords" in s
    assert "suez" in s["geo_keywords"] or "canal" in s["geo_keywords"]


def test_build_query_omits_ambiguous_ticker():
    # ZIM is ambiguous (ZIP/ZIM/ZIM connector etc.) — bare ticker should not appear
    q = _build_query("ZIM Integrated Shipping", "ZIM")
    assert '"ZIM Integrated Shipping"' in q
    # No bare ticker token
    assert " ZIM " not in q.replace("(", " ").replace(")", " ")


def test_build_query_includes_unambiguous_ticker():
    q = _build_query("A.P. Moller - Maersk", "MAERSK-B.CO")
    assert "MAERSK-B.CO" in q


def test_fetch_news_falls_back_to_yfinance(monkeypatch):
    # Force NEWSAPI_KEY off for this test, and ensure live mode (not demo).
    monkeypatch.setattr(providers.cfg, "APP_MODE", "live")
    monkeypatch.setattr(providers.cfg, "NEWSAPI_KEY", "")

    fake_yf = [
        {"title": "Maersk container ship rerouted via Cape of Good Hope", "url": "u1",
         "source": "Reuters", "publishedAt": ""},
        {"title": "Unrelated tech news", "url": "u2", "source": "X", "publishedAt": ""},
    ]
    with patch("providers._yfinance_news", return_value=fake_yf):
        result, status = fetch_news("Maersk", "MAERSK-B.CO", hours=72)
    assert isinstance(result, NewsResult)
    assert result.source == "yfinance"
    assert result.fallback_used is True
    # Relevant filter should keep maritime headline, drop tech
    assert result.relevant_count >= 1
    assert status.ok


def test_fetch_news_handles_total_failure_falls_back_to_sample(monkeypatch):
    """When NewsAPI is absent and yfinance returns nothing, the provider
    should substitute bundled sample data and label it as a fallback."""
    monkeypatch.setattr(providers.cfg, "APP_MODE", "live")  # bypass demo short-circuit
    monkeypatch.setattr(providers.cfg, "NEWSAPI_KEY", "")
    with patch("providers._yfinance_news", return_value=[]):
        result, status = fetch_news("ZIM Integrated Shipping", "ZIM", hours=72)
    assert result.source == "sample"
    assert result.fallback_used is True
    assert "sample fallback" in (status.provider or "")
