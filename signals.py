"""Rule-based signal engine.

Takes the indicator panel, fundamentals dict, and news summary; returns a
SignalResult dataclass with sub-scores, label, confidence, evidence, and
two distinct warning lists (risk vs. data quality).

The thresholds live in config.py — change them there, not here.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

import config as cfg


VALID_LABELS = {
    "VALUE BUY", "MOMENTUM BUY", "HOLD", "PROFIT TAKE",
    "SELL", "STRONG SELL", "AVOID",
}


@dataclass
class SignalResult:
    label: str
    rationale: str
    signal_score: float          # -1 .. +1
    confidence: str              # low | medium | high
    technical_score: float       # -1 .. +1
    fundamental_score: float     # -1 .. +1
    news_score: float            # -1 .. +1 (sentiment weighted by relevance)
    risk_score: float            # 0 .. 1 (higher = riskier)
    geo_risk: bool
    evidence: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)
    data_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def score_technical(ind: Dict[str, Any]) -> tuple[float, List[str], List[str]]:
    """Return (score in [-1,1], evidence, data_warnings)."""
    evidence: List[str] = []
    warns: List[str] = []
    score = 0.0
    n = 0

    rsi = ind.get("rsi")
    if rsi is None:
        warns.append("RSI unavailable")
    else:
        n += 1
        if rsi < cfg.RSI_OVERSOLD:
            score += 0.5
            evidence.append(f"RSI {rsi:.1f} oversold")
        elif rsi > cfg.RSI_OVERBOUGHT:
            score -= 0.5
            evidence.append(f"RSI {rsi:.1f} overbought")
        elif rsi < cfg.RSI_NEUTRAL_LOW:
            score -= 0.1
        else:
            score += 0.1

    trend = ind.get("trend", "unknown")
    if trend != "unknown":
        n += 1
        contrib = {
            "strong_uptrend": 0.5, "uptrend": 0.3,
            "sideways": 0.0, "downtrend": -0.3, "strong_downtrend": -0.5,
        }.get(trend, 0.0)
        score += contrib
        evidence.append(f"Trend: {trend}")
    else:
        warns.append("Trend unknown (insufficient SMA data)")

    dd = ind.get("drawdown_3m")
    if dd is not None:
        n += 1
        if dd < -0.20:
            score -= 0.2
            evidence.append(f"3m drawdown {dd*100:.1f}%")
        elif dd > -0.05:
            score += 0.1

    if n == 0:
        return 0.0, evidence, warns
    # normalise loosely into [-1, 1]
    return max(-1.0, min(1.0, score)), evidence, warns


def score_fundamentals(funds: Dict[str, Any]) -> tuple[float, List[str], List[str], List[str]]:
    """Return (score, evidence, risk_warnings, data_warnings)."""
    evidence: List[str] = []
    risks: List[str] = []
    data_warns: List[str] = []
    score = 0.0
    seen = 0

    pb = funds.get("P/B")
    de = funds.get("Debt/Equity")
    ev = funds.get("EV/EBITDA")
    cr = funds.get("Current_Ratio")

    missing = [k for k, v in [("P/B", pb), ("Debt/Equity", de), ("EV/EBITDA", ev), ("Current_Ratio", cr)] if v is None]
    if missing:
        data_warns.append(f"Missing fundamentals: {', '.join(missing)}")

    if de is not None:
        seen += 1
        if de > cfg.DEBT_EQUITY_HIGH:
            score -= 0.4
            risks.append(f"High leverage (D/E {de:.0f})")
        elif de < cfg.DEBT_EQUITY_LOW:
            score += 0.2
            evidence.append(f"Low leverage (D/E {de:.0f})")
    if pb is not None:
        seen += 1
        if pb < cfg.PB_CHEAP:
            score += 0.3
            evidence.append(f"Cheap on book (P/B {pb:.2f})")
        elif pb > cfg.PB_EXPENSIVE:
            score -= 0.3
            risks.append(f"Expensive on book (P/B {pb:.2f})")
    if ev is not None:
        seen += 1
        if ev < 0:
            risks.append(f"Negative EV/EBITDA ({ev:.1f})")
            score -= 0.2
        elif ev < cfg.EV_EBITDA_CHEAP:
            score += 0.2
            evidence.append(f"Cheap on EV/EBITDA ({ev:.1f})")
    if cr is not None:
        seen += 1
        if cr < cfg.CURRENT_RATIO_WEAK:
            risks.append(f"Weak liquidity (Current Ratio {cr:.2f})")
            score -= 0.2

    if seen == 0:
        return 0.0, evidence, risks, data_warns
    return max(-1.0, min(1.0, score)), evidence, risks, data_warns


def score_news(avg_sentiment: float, geo_alert: bool, n_relevant: int) -> tuple[float, List[str]]:
    evidence: List[str] = []
    if n_relevant == 0:
        return 0.0, ["No relevant headlines in window"]
    score = max(-1.0, min(1.0, avg_sentiment))
    evidence.append(f"News sentiment {score:+.2f} over {n_relevant} relevant headlines")
    if geo_alert:
        evidence.append("Geopolitical keyword detected")
    return score, evidence


def _confidence(tech_n: int, fund_n: int, news_n: int, data_warnings: int) -> str:
    score = tech_n + fund_n + news_n - data_warnings
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def generate_signal(
    ind: Dict[str, Any],
    funds: Dict[str, Any],
    news: Dict[str, Any],
) -> SignalResult:
    """Build a SignalResult from indicator/fundamental/news inputs.

    `news` expects keys: avg_sentiment (float), geo_alert (bool),
    relevant_count (int).
    """
    tech_score, tech_ev, tech_dw = score_technical(ind)
    fund_score, fund_ev, fund_risks, fund_dw = score_fundamentals(funds or {})
    news_score, news_ev = score_news(
        float(news.get("avg_sentiment", 0.0)),
        bool(news.get("geo_alert", False)),
        int(news.get("relevant_count", 0)),
    )

    composite = 0.45 * tech_score + 0.35 * fund_score + 0.20 * news_score
    geo = bool(news.get("geo_alert", False))

    risk = 0.0
    if any("High leverage" in r for r in fund_risks):
        risk += 0.4
    if any("Weak liquidity" in r for r in fund_risks):
        risk += 0.2
    if any("Negative EV" in r for r in fund_risks):
        risk += 0.2
    if geo:
        risk += 0.3
    risk = min(1.0, risk)

    rsi = ind.get("rsi")
    trend = ind.get("trend", "unknown")
    uptrend = trend in ("uptrend", "strong_uptrend")

    label, rationale = _label_from_scores(
        tech_score, fund_score, news_score, composite,
        rsi=rsi, uptrend=uptrend, geo=geo, fund_risks=fund_risks,
    )

    confidence = _confidence(
        tech_n=len(tech_ev),
        fund_n=len(fund_ev),
        news_n=int(news.get("relevant_count", 0)),
        data_warnings=len(tech_dw) + len(fund_dw),
    )

    return SignalResult(
        label=label,
        rationale=rationale,
        signal_score=round(composite, 3),
        confidence=confidence,
        technical_score=round(tech_score, 3),
        fundamental_score=round(fund_score, 3),
        news_score=round(news_score, 3),
        risk_score=round(risk, 3),
        geo_risk=geo,
        evidence=tech_ev + fund_ev + news_ev,
        risk_warnings=fund_risks + (["Geopolitical risk flag"] if geo else []),
        data_warnings=tech_dw + fund_dw,
    )


def _label_from_scores(
    tech: float, fund: float, news: float, composite: float,
    *, rsi: Optional[float], uptrend: bool, geo: bool, fund_risks: List[str],
) -> tuple[str, str]:
    high_lev = any("High leverage" in r for r in fund_risks)
    if geo and (rsi is None or rsi < cfg.RSI_NEUTRAL_LOW):
        return "AVOID", "Geopolitical risk in weak/uncertain momentum"
    if high_lev and rsi is not None and rsi < 40:
        return "STRONG SELL", "Falling momentum + solvency risk"
    if rsi is not None and rsi < cfg.RSI_OVERSOLD and fund >= 0.1 and news > -0.2:
        return "VALUE BUY", "Oversold with supportive fundamentals"
    if uptrend and rsi is not None and rsi < cfg.RSI_NEUTRAL_HIGH and fund >= 0.0:
        return "MOMENTUM BUY", "Trend confirmed, acceptable valuation"
    if rsi is not None and rsi > cfg.RSI_OVERBOUGHT and fund < 0:
        return "PROFIT TAKE", "Overbought and fundamentally expensive"
    if not uptrend and fund < 0:
        return "SELL", "Downtrend with weak fundamentals"
    return "HOLD", "Mixed signals"
