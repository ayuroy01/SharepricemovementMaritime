"""Demo mode + sample data integration tests.

These tests run the FULL pipeline (providers → indicators → signals →
watchlist) against the bundled sample fixtures, with no network access.
They are the closest thing to an end-to-end test we can run in CI.
"""
import importlib

import config
import demo_data
import maritime_data
import providers


def _force_demo(monkeypatch):
    monkeypatch.setattr(config, "APP_MODE", "demo")
    # Clear lru_caches so fixture re-reads pick up any tmp tweaks
    demo_data._watchlist.cache_clear()
    demo_data._fundamentals.cache_clear()
    demo_data._news.cache_clear()


def test_resolve_mode_demo_when_no_key(monkeypatch):
    monkeypatch.setattr(config, "APP_MODE", "auto")
    monkeypatch.setattr(config, "NEWSAPI_KEY", "")
    assert config.resolve_mode() == "demo"


def test_resolve_mode_live_when_key_present(monkeypatch):
    monkeypatch.setattr(config, "APP_MODE", "auto")
    monkeypatch.setenv("NEWSAPI_KEY", "fake-test-value")
    monkeypatch.setattr(config, "NEWSAPI_KEY", "fake-test-value")
    assert config.resolve_mode() == "live"


def test_resolve_mode_explicit_overrides(monkeypatch):
    monkeypatch.setattr(config, "APP_MODE", "demo")
    monkeypatch.setattr(config, "NEWSAPI_KEY", "anything")
    assert config.resolve_mode() == "demo"
    monkeypatch.setattr(config, "APP_MODE", "live")
    assert config.resolve_mode() == "live"


def test_sample_data_files_present():
    assert demo_data.has_sample_data()


def test_provider_returns_demo_data_when_in_demo_mode(monkeypatch):
    _force_demo(monkeypatch)
    df, status = providers.fetch_price_history("ZIM")
    assert status.ok and status.records > 0
    assert "Close" in df.columns

    funds, fstat = providers.fetch_fundamentals("ZIM")
    assert fstat.ok
    assert funds["P/B"] is not None

    news, nstat = providers.fetch_news("ZIM Integrated Shipping", "ZIM")
    assert nstat.ok
    assert news.source == "sample"
    assert news.headlines  # non-empty

    bdi, bstat = providers.fetch_bdi_proxy()
    assert bstat.ok and bdi is not None
    assert bdi.last is not None


def test_build_watchlist_in_demo_mode_returns_full_results(monkeypatch):
    _force_demo(monkeypatch)
    result = maritime_data.build_watchlist(news_hours=72)
    assert result["effective_mode"] == "demo"
    assert result["app_mode"] == "demo"
    assert len(result["rows"]) == len(config.DEFAULT_WATCHLIST)
    assert not result["failures"]
    # Schema completeness
    for row in result["rows"]:
        for key in maritime_data.ROW_SCHEMA:
            assert key in row
        assert row["Action"] != "ERROR"


def test_demo_mode_does_not_print_secrets(capsys, monkeypatch):
    _force_demo(monkeypatch)
    monkeypatch.setattr(config, "NEWSAPI_KEY", "super-secret-do-not-print")
    maritime_data.build_watchlist(news_hours=72)
    captured = capsys.readouterr()
    assert "super-secret-do-not-print" not in captured.out
    assert "super-secret-do-not-print" not in captured.err
