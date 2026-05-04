from signals import (
    VALID_LABELS,
    generate_signal,
    score_fundamentals,
    score_news,
    score_technical,
)


def _ind(rsi=50, trend="uptrend", sma20=10, sma50=9, sma200=8, drawdown=-0.05):
    return {
        "rsi": rsi, "trend": trend, "sma20": sma20, "sma50": sma50, "sma200": sma200,
        "drawdown_3m": drawdown, "ret5": 0.01, "ret20": 0.05, "vol20": 0.02,
        "close": 10, "bars": 300, "has_long": sma200 is not None,
    }


def test_score_technical_oversold_lifts():
    s, _, _ = score_technical(_ind(rsi=20, trend="sideways"))
    assert s > 0


def test_score_technical_overbought_drags():
    s, _, _ = score_technical(_ind(rsi=80, trend="downtrend"))
    assert s < 0


def test_score_fundamentals_high_leverage_flagged():
    funds = {"P/B": 1.2, "EV/EBITDA": 8.0, "Debt/Equity": 200, "Current_Ratio": 0.9}
    score, _, risks, _ = score_fundamentals(funds)
    assert score < 0
    assert any("High leverage" in r for r in risks)
    assert any("Weak liquidity" in r for r in risks)


def test_score_fundamentals_all_missing():
    score, ev, risks, dw = score_fundamentals({"P/B": None, "EV/EBITDA": None,
                                               "Debt/Equity": None, "Current_Ratio": None})
    assert score == 0.0
    assert dw and "Missing fundamentals" in dw[0]


def test_score_news_zero_relevant_neutralises():
    score, ev = score_news(0.6, True, 0)
    assert score == 0.0


def test_generate_signal_value_buy_path():
    sig = generate_signal(
        ind=_ind(rsi=25, trend="downtrend"),
        funds={"P/B": 0.7, "EV/EBITDA": 4.0, "Debt/Equity": 30, "Current_Ratio": 1.5},
        news={"avg_sentiment": 0.0, "geo_alert": False, "relevant_count": 3},
    )
    assert sig.label in VALID_LABELS
    assert sig.label == "VALUE BUY"
    assert sig.confidence in {"low", "medium", "high"}


def test_generate_signal_avoid_when_geo_and_weak_momentum():
    sig = generate_signal(
        ind=_ind(rsi=40, trend="downtrend"),
        funds={"P/B": 1.2, "EV/EBITDA": 8.0, "Debt/Equity": 50, "Current_Ratio": 1.2},
        news={"avg_sentiment": -0.2, "geo_alert": True, "relevant_count": 2},
    )
    assert sig.label == "AVOID"
    assert sig.geo_risk is True


def test_generate_signal_returns_subscores_and_warnings_separated():
    sig = generate_signal(
        ind=_ind(rsi=None, trend="unknown", sma20=None, sma50=None, sma200=None),
        funds={"P/B": None, "EV/EBITDA": None, "Debt/Equity": None, "Current_Ratio": None},
        news={"avg_sentiment": 0.0, "geo_alert": False, "relevant_count": 0},
    )
    assert sig.label in VALID_LABELS
    assert sig.confidence == "low"
    assert sig.data_warnings  # something missing
    # Risk warnings list is for risks, not data quality — should be empty here.
    assert all("missing" not in r.lower() for r in sig.risk_warnings)
