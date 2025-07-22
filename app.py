from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging

import yfinance as yf
from flask import Flask, render_template, jsonify
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)

# ─── Ticker & Alert Configuration ──────────────────────────────────────────────
tickers = {
    'VTI':   245,
    'VXUS':   55,
    'VOO':   490,
    'AMD':    90,
    'INTC':   18,
    'WMT':    80,
    'KO':     55,
    'WM':    175,
    'BRK-B': 475,
    'GOOGL': 165,
    'META':  450,
    'AMZN':  150,
    'AAPL':  185,
    'NVDA':  100,
    'MSFT':  325,
    'TSLA':  300,
}

# ─── Logging Configuration ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_one(symbol_target):
    """
    Fetches latest close, 52-week High/Low, all-time High/Low,
    and 30-day close history for a single ticker.
    Returns a dict or None on failure.
    """
    symbol, target = symbol_target
    try:
        ticker = yf.Ticker(symbol)

        # 1. Latest price (close of most recent daily bar)
        recent = ticker.history(period="5d", interval="1d")
        if recent.empty:
            logger.warning(f"No recent data for {symbol}")
            return None
        current = recent["Close"].iloc[-1]

        # 2. 52-week high/low (intraday)
        year_hist   = ticker.history(period="1y", interval="1d")
        week52_high = year_hist["High"].max()
        week52_low  = year_hist["Low"].min()

        # 3. All-time high/low (intraday)
        full_hist      = ticker.history(period="max", interval="1d")
        all_time_high  = full_hist["High"].max()
        all_time_low   = full_hist["Low"].min()

        # 4. 30-day close history
        hist30 = ticker.history(period="30d", interval="1d")
        dates  = [d.strftime("%Y-%m-%d") for d in hist30.index]
        prices = hist30["Close"].tolist()

        result = {
            "ticker":        symbol,
            "current_price": current,
            "week52_low":    week52_low,
            "week52_high":   week52_high,
            "all_time_low":  all_time_low,
            "all_time_high": all_time_high,
            "history": {
                "dates":  dates,
                "prices": prices
            }
        }

        if current <= target:
            logger.info(f"ALERT: {symbol} is at {current} (≤ target {target})")

        return result

    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return None


def fetch_ticker_data_concurrent(max_workers=8):
    """
    Uses ThreadPoolExecutor to fetch all tickers in parallel.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_one, item): item[0] for item in tickers.items()}
        for future in as_completed(futures):
            data = future.result()
            if data:
                results.append(data)
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data_route():
    return jsonify(fetch_ticker_data_concurrent())

if __name__ == "__main__":
    # Run Flask without reloader (to avoid duplicate threads)
    app.run(debug=False, use_reloader=False)
