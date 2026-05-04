"""Config + .env loading. Must never expose secret VALUES."""
import os
from pathlib import Path

import config


def test_dotenv_loader_handles_missing_file(tmp_path):
    bogus = tmp_path / "nope.env"
    config.load_dotenv(bogus)  # should not raise


def test_dotenv_loader_does_not_overwrite_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_KEY_X", "preset")
    p = tmp_path / ".env"
    p.write_text("FAKE_KEY_X=fromfile\nNEW_KEY_Y=loaded\n")
    config.load_dotenv(p)
    assert os.environ["FAKE_KEY_X"] == "preset"
    assert os.environ["NEW_KEY_Y"] == "loaded"


def test_has_key_is_bool_only():
    assert isinstance(config.has_key("DEFINITELY_NOT_SET_XYZ"), bool)
    assert config.has_key("DEFINITELY_NOT_SET_XYZ") is False


def test_thresholds_are_sane():
    assert config.RSI_OVERSOLD < config.RSI_OVERBOUGHT
    assert config.SMA_SHORT < config.SMA_MED < config.SMA_LONG
    assert 0 < config.MIN_RELEVANCE < 1
    assert config.DEBT_EQUITY_LOW < config.DEBT_EQUITY_HIGH
