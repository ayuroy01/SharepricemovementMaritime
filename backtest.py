"""Vectorised technical-only backtest.

Strategy (deliberately simple, fully transparent):
  - Long-only.
  - Entry signal at close of bar T:  SMA20[T] > SMA50[T]  AND  RSI14[T] in (40, 65).
  - Exit signal at close of bar T:   SMA20[T] < SMA50[T]  OR   RSI14[T] > 75.
  - Orders execute at the NEXT bar's open. This eliminates lookahead bias
    (we never trade on a price we haven't observed yet).
  - Each side pays commission_bps + slippage_bps relative to the fill price.

Fundamentals and news are intentionally NOT used in the backtest because
historical fundamentals snapshots and historical news sentiment are
unavailable from free sources without leakage. A live signal in the
dashboard uses all three; a backtest evaluates only the technical
component honestly.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

import config as cfg
from indicators import rsi as rsi_series


@dataclass
class Trade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    bars_held: int
    pnl_pct: float


@dataclass
class BacktestResult:
    ticker: str
    period_start: str
    period_end: str
    bars: int
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    equity_dates: List[str] = field(default_factory=list)
    total_return: float = 0.0
    cagr: Optional[float] = None
    max_drawdown: float = 0.0
    sharpe: Optional[float] = None
    win_rate: Optional[float] = None
    avg_holding_bars: Optional[float] = None
    benchmark_return: float = 0.0
    n_trades: int = 0
    notes: List[str] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        d = asdict(self)
        # Drop heavy series for compact display.
        d["equity_curve"] = None
        d["equity_dates"] = None
        d["trades"] = [asdict(t) for t in self.trades]
        return d


def _entry_signal(df: pd.DataFrame) -> pd.Series:
    sma20 = df["Close"].rolling(cfg.SMA_SHORT).mean()
    sma50 = df["Close"].rolling(cfg.SMA_MED).mean()
    rsi = rsi_series(df["Close"])
    return (sma20 > sma50) & (rsi > 40) & (rsi < cfg.RSI_NEUTRAL_HIGH)


def _exit_signal(df: pd.DataFrame) -> pd.Series:
    sma20 = df["Close"].rolling(cfg.SMA_SHORT).mean()
    sma50 = df["Close"].rolling(cfg.SMA_MED).mean()
    rsi = rsi_series(df["Close"])
    return (sma20 < sma50) | (rsi > 75)


def run_backtest(
    df: pd.DataFrame,
    ticker: str,
    *,
    initial_cash: float = cfg.BT_INITIAL_CASH,
    commission_bps: float = cfg.BT_COMMISSION_BPS,
    slippage_bps: float = cfg.BT_SLIPPAGE_BPS,
    risk_free: float = cfg.BT_RISK_FREE_RATE,
) -> BacktestResult:
    """Run a vectorised backtest. df must be daily OHLC with a DatetimeIndex."""
    notes: List[str] = []
    if df is None or df.empty:
        return BacktestResult(ticker=ticker, period_start="", period_end="", bars=0,
                              notes=["No price data."])
    df = df.copy()
    if "Open" not in df.columns or "Close" not in df.columns:
        return BacktestResult(ticker=ticker, period_start="", period_end="", bars=0,
                              notes=["Missing Open/Close columns."])
    df = df.dropna(subset=["Close", "Open"])
    if len(df) < cfg.SMA_MED + 5:
        return BacktestResult(ticker=ticker, period_start=str(df.index.min().date()) if len(df) else "",
                              period_end=str(df.index.max().date()) if len(df) else "",
                              bars=len(df), notes=["Insufficient history for SMA50 + warmup."])

    enter = _entry_signal(df).fillna(False)
    exit_ = _exit_signal(df).fillna(False)

    cost_per_side = (commission_bps + slippage_bps) / 10_000.0
    cash = float(initial_cash)
    shares = 0.0
    entry_price = 0.0
    entry_idx = -1
    trades: List[Trade] = []
    equity: List[float] = []

    opens = df["Open"].values
    closes = df["Close"].values
    dates = list(df.index)

    in_pos = False
    pending: Optional[str] = None  # "BUY" or "SELL", queued at close of T-1, fills at open of T

    for i in range(len(df)):
        # Execute pending order at today's open
        if pending == "BUY" and not in_pos:
            fill = opens[i] * (1 + cost_per_side)
            shares = cash / fill
            cash = 0.0
            entry_price = fill
            entry_idx = i
            in_pos = True
        elif pending == "SELL" and in_pos:
            fill = opens[i] * (1 - cost_per_side)
            cash = shares * fill
            pnl = fill / entry_price - 1.0
            trades.append(Trade(
                entry_date=str(dates[entry_idx].date()),
                exit_date=str(dates[i].date()),
                entry_price=float(entry_price),
                exit_price=float(fill),
                bars_held=i - entry_idx,
                pnl_pct=float(pnl),
            ))
            shares = 0.0
            in_pos = False
        pending = None

        # Mark-to-market at today's close
        equity.append(cash + shares * closes[i])

        # Decide tomorrow's order based on today's close-of-bar signal
        if not in_pos and enter.iloc[i]:
            pending = "BUY"
        elif in_pos and exit_.iloc[i]:
            pending = "SELL"

    # Close any open position at final close (no future bar to fill against)
    if in_pos:
        fill = closes[-1] * (1 - cost_per_side)
        cash = shares * fill
        pnl = fill / entry_price - 1.0
        trades.append(Trade(
            entry_date=str(dates[entry_idx].date()),
            exit_date=str(dates[-1].date()),
            entry_price=float(entry_price),
            exit_price=float(fill),
            bars_held=len(df) - 1 - entry_idx,
            pnl_pct=float(pnl),
        ))
        equity[-1] = cash
        notes.append("Final position force-closed at last close.")

    eq = np.array(equity, dtype=float)
    total_return = eq[-1] / initial_cash - 1.0

    bench_return = float(closes[-1] / closes[0] - 1.0)

    days = (dates[-1] - dates[0]).days
    years = days / 365.25 if days > 0 else 0.0
    cagr = (eq[-1] / initial_cash) ** (1 / years) - 1 if years >= 0.5 else None

    # Daily returns for Sharpe / drawdown
    eq_series = pd.Series(eq, index=dates)
    rets = eq_series.pct_change().dropna()
    sharpe: Optional[float] = None
    if len(rets) >= 30 and rets.std() > 0:
        excess = rets - (risk_free / cfg.TRADING_DAYS_PER_YEAR)
        sharpe = float(np.sqrt(cfg.TRADING_DAYS_PER_YEAR) * excess.mean() / rets.std())

    running_max = eq_series.cummax()
    dd = (eq_series / running_max - 1.0).min()
    max_dd = float(dd) if pd.notna(dd) else 0.0

    win_rate = None
    avg_hold = None
    if trades:
        wins = sum(1 for t in trades if t.pnl_pct > 0)
        win_rate = wins / len(trades)
        avg_hold = sum(t.bars_held for t in trades) / len(trades)

    return BacktestResult(
        ticker=ticker,
        period_start=str(dates[0].date()),
        period_end=str(dates[-1].date()),
        bars=len(df),
        trades=trades,
        equity_curve=[float(x) for x in eq.tolist()],
        equity_dates=[str(d.date()) for d in dates],
        total_return=float(total_return),
        cagr=cagr,
        max_drawdown=max_dd,
        sharpe=sharpe,
        win_rate=win_rate,
        avg_holding_bars=avg_hold,
        benchmark_return=bench_return,
        n_trades=len(trades),
        notes=notes,
    )
