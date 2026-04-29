# SharepricemovementMaritime

## The Strategy: A Multi-Factor Approach
The shipping industry is highly cyclical and volatile. To survive, this algorithm requires three strict conditions to be met before generating a "BUY" signal:

### 1. Fundamental Valuation (Company Health)
The model actively scans for underpriced companies while strictly avoiding **Value Traps** (stocks that look cheap but are actually failing). It evaluates:
* **Debt-to-Equity (D/E):** It filters out over-leveraged companies (>150% D/E) to ensure the business can survive industry downturns. 
* **Price-to-Book (P/B) & EV/EBITDA:** It looks for companies trading below their true asset value, essentially trying to "buy the cargo ships for less than scrap value."

### 2. Technical Momentum (Price Action)
The algorithm refuses to "catch a falling knife." It uses price history math to confirm the market is actually buying the stock:
* **Simple Moving Averages (SMA):** It calculates the 50-day average price to ensure the stock is in a confirmed macro **Uptrend**.
* **Relative Strength Index (RSI):** It monitors the speed of price changes to avoid buying **Overbought** stocks (where buyers are exhausted) and looks for **Oversold** opportunities (where panic has driven the price artificially low).

### 3. Event-Driven Sentiment (The News)
In shipping, real-world events instantly disrupt supply chains. The model uses **Natural Language Processing (NLP)** to mathematically score the last 72 hours of news headlines. If it detects geopolitical panic keywords (e.g., "tariffs", "Suez", "embargo"), it triggers a hard veto and halts trading to avoid unpredictable macro risks.

## Risk Management & Backtesting
A strategy means nothing without capital protection. This suite includes a **Backtesting Engine** that runs the strategy against years of historical data to validate its edge. 

It utilizes an **Asymmetric Risk/Reward** model via automated **Bracket Orders**:
* **Take-Profit (+15%):** Automatically locks in cash when the stock surges.
* **Hard Stop-Loss (-5%):** Automatically cuts the cord if the trade goes bad, taking a small paper cut to prevent a catastrophic portfolio loss.
* *The Result:* By risking $5 to make $15, the algorithm can be wrong on the majority of its trades and still generate a positive net return.

## Tech Stack
* **Python** (Pandas, NumPy) for data engineering.
* **Backtrader** for the event-driven backtesting engine.
* **yfinance** for live market data routing.
* **vaderSentiment** for NLP sentiment scoring.

## How to Run It
1. Clone this repository.
2. Install the required libraries: `pip install -r requirements.txt`
3. Run the master pipeline: `python main.py`
