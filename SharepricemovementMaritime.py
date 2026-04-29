import warnings
import yfinance as yf
import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Suppress warnings for cleaner terminal output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# ======================================================
# 1. GLOBAL CONFIGURATION
# ======================================================
shipping_companies = {
    "A.P. Moller - Maersk": "MAERSK-B.CO",
    "Hapag-Lloyd": "HLAG.DE",
    "ZIM Integrated Shipping": "ZIM",
    "Frontline Ltd.": "FRO",
    "Star Bulk Carriers": "SBLK",
    "Wallenius Wilhelmsen": "WAWI.OL"
}

GEO_KEYWORDS = [
    "houthi", "red sea", "suez", "canal", "tariffs", "trade war", 
    "sanctions", "black sea", "drought", "piracy", "embargo", "hormuz"
]

analyzer = SentimentIntensityAnalyzer()

# ======================================================
# 2. PART A: LIVE MARKET DASHBOARD (DATA ACQUISITION)
# ======================================================
def get_technical_data(ticker_symbol):
    """Fetches price history and calculates technical indicators."""
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="6mo")
    
    if df.empty:
        return None
        
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).ewm(com=13, min_periods=14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=13, min_periods=14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df.iloc[-1]

def get_fundamental_data(ticker_symbol):
    """Fetches critical valuation and solvency ratios."""
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    
    fundamentals = {
        'P/B': info.get('priceToBook', None),
        'EV/EBITDA': info.get('enterpriseToEbitda', None),
        'Debt/Equity': info.get('debtToEquity', None),
        'Current_Ratio': info.get('currentRatio', None)
    }
    return fundamentals

def get_news_signals(ticker_symbol):
    """Parses recent news for sentiment and geopolitical triggers."""
    try:
        stock = yf.Ticker(ticker_symbol)
        news_items = stock.news 
        if not news_items:
            return 0.0, False

        cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
        recent_news = [
            item for item in news_items 
            if datetime.fromtimestamp(item.get('providerPublishTime', 0), tz=timezone.utc) >= cutoff
        ]
        
        recent_news = recent_news if recent_news else news_items[:5]
        
        sentiments = []
        geo_detected = False

        for item in recent_news:
            title = item.get('title', '')
            if not title: continue
                
            sentiments.append(analyzer.polarity_scores(title)['compound'])
            if any(keyword in title.lower() for keyword in GEO_KEYWORDS):
                geo_detected = True

        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        return avg_sentiment, geo_detected
    except Exception:
        return 0.0, False

def evaluate_fundamentals(funds):
    """Scores fundamentals to flag Value Traps or High Risk."""
    score = 0
    warnings = []
    
    pb = funds['P/B']
    de = funds['Debt/Equity']
    ev_eb = funds['EV/EBITDA']
    
    if de is not None:
        if de > 150:
            warnings.append("High Leverage")
            score -= 1
        elif de < 50:
            score += 1

    if pb is not None:
        if pb < 1.0:
            score += 1
        elif pb > 2.5:
            warnings.append("Overvalued (P/B)")
            score -= 1
            
    if ev_eb is not None:
        if ev_eb < 5:
            score += 1
            
    return score, warnings

def generate_composite_signal(tech, funds, sentiment, geo_alert):
    """Aggregates data into a strict execution command."""
    fund_score, fund_warnings = evaluate_fundamentals(funds)
    rsi = tech['RSI']
    uptrend = tech['SMA_20'] > tech['SMA_50']
    
    if geo_alert and rsi < 50: return "AVOID", "Geopolitical risk in weak momentum"
    if "High Leverage" in fund_warnings and rsi < 40: return "STRONG SELL", "Falling knife + Solvency risk"
    if rsi < 35 and fund_score >= 1 and sentiment > -0.1: return "VALUE BUY", "Oversold with strong fundamentals"
    if uptrend and rsi < 65 and fund_score >= 0: return "MOMENTUM BUY", "Trend confirmed, acceptable valuation"
    if rsi > 70 and fund_score < 0: return "PROFIT TAKE", "Overbought and fundamentally expensive"
    if not uptrend and fund_score < 0: return "SELL", "Downtrend + Weak fundamentals"

    return "HOLD", "Mixed signals"

def run_live_dashboard():
    """Executes the Live Market Scanner."""
    print("\n" + "=" * 125)
    print(" PHASE 1: LIVE QUANTITATIVE EXECUTION DASHBOARD (MARITIME EQUITIES)")
    print("=" * 125)
    print(f"{'Ticker':<10} | {'Price':<8} | {'P/B':<5} | {'EV/EBIT':<7} | {'D/E %':<6} | {'RSI':<5} | {'Sent':<5} | {'Geo':<4} | {'Action':<15} | {'Rationale'}")
    print("-" * 125)

    for name, ticker in shipping_companies.items():
        try:
            tech = get_technical_data(ticker)
            if tech is None or pd.isna(tech['RSI']): continue
                
            funds = get_fundamental_data(ticker)
            sentiment, geo_alert = get_news_signals(ticker)
            action, rationale = generate_composite_signal(tech, funds, sentiment, geo_alert)
            
            price = tech['Close']
            pb_str = f"{funds['P/B']:.1f}" if funds['P/B'] else "N/A"
            ev_str = f"{funds['EV/EBITDA']:.1f}" if funds['EV/EBITDA'] else "N/A"
            de_str = f"{funds['Debt/Equity']:.0f}" if funds['Debt/Equity'] else "N/A"
            geo_str = "YES" if geo_alert else "NO"
            
            print(f"{ticker:<10} | {price:>8.2f} | {pb_str:>5} | {ev_str:>7} | {de_str:>6} | {tech['RSI']:>5.1f} | {sentiment:>5.2f} | {geo_str:<4} | {action:<15} | {rationale}")
        except Exception as e:
            print(f"{ticker:<10} | Pipeline Error: {e}")
    print("-" * 125 + "\n")

# ======================================================
# 3. PART B: ALGORITHMIC BACKTESTING STRATEGY
# ======================================================
class ProfitBracketStrategy(bt.Strategy):
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.sma50 = bt.indicators.SimpleMovingAverage(self.datas[0], period=50)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return 

        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                print(f"🟢 BOUGHT  | Price: ${self.buyprice:.2f} | Cost: ${order.executed.value:.2f}")
            elif order.issell():
                profit = order.executed.price - self.buyprice
                if profit > 0:
                    print(f"🎯 TAKE PROFIT (+15%) | Sold at: ${order.executed.price:.2f} | Profit/Share: +${profit:.2f}")
                else:
                    print(f"🛡️ STOP LOSS (-5%)    | Sold at: ${order.executed.price:.2f} | Loss/Share: ${profit:.2f}")
                self.buyprice = None
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.buyprice = None
        self.order = None

    def next(self):
        if len(self) < 50: return
        if self.order: return

        if not self.position:
            r0 = (self.dataclose[0] - self.dataclose[-1]) / self.dataclose[-1]
            r1 = (self.dataclose[-1] - self.dataclose[-2]) / self.dataclose[-2]
            
            if self.dataclose[0] > self.sma50[0] and (r0 + r1) >= 0.02:
                print(f"\n🚀 UPTREND BREAKOUT | Date: {self.datas[0].datetime.date(0)}")
                self.order = self.buy()
        else:
            take_profit_target = self.buyprice * 1.15
            stop_loss_target = self.buyprice * 0.95
            
            if self.dataclose[0] >= take_profit_target or self.dataclose[0] <= stop_loss_target:
                self.order = self.sell()

def run_backtest(target_ticker="ZIM"):
    """Executes the Historical Validation Engine."""
    print("=" * 125)
    print(f" PHASE 2: HISTORICAL VALIDATION ENGINE ({target_ticker})")
    print("=" * 125)
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(ProfitBracketStrategy)

    print(f"Fetching historical data for {target_ticker} from Yahoo Finance...")
    stock_data = yf.Ticker(target_ticker)
    data_df = stock_data.history(start="2021-01-01", end="2023-12-31")
    
    # Bulletproof Data Sanitizer
    if isinstance(data_df.columns, pd.MultiIndex):
        data_df.columns = data_df.columns.get_level_values(0)
    data_df.columns = [str(col) for col in data_df.columns]
    
    if data_df.index.tz is not None:
        data_df.index = data_df.index.tz_localize(None)
        
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    data_df = data_df[[col for col in required_columns if col in data_df.columns]]

    data = bt.feeds.PandasData(dataname=data_df)
    cerebro.adddata(data)

    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001) 
    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)

    print("-" * 60)
    print(f"STARTING PORTFOLIO VALUE: ${cerebro.broker.getvalue():.2f}")
    print("-" * 60)

    cerebro.run()

    print("-" * 60)
    print(f"FINAL PORTFOLIO VALUE: ${cerebro.broker.getvalue():.2f}")
    print("-" * 60)

# ======================================================
# 4. MASTER EXECUTION
# ======================================================
if __name__ == '__main__':
    # 1. Run the Live Market Scanner
    run_live_dashboard()
    
    # 2. Run the Historical Backtest (Defaulting to ZIM)
    run_backtest(target_ticker="ZIM")