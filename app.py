from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
import os
import shutil
from pathlib import Path
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    from yahooquery import Ticker as YQTicker
    YAHOOQUERY_AVAILABLE = True
except ImportError:
    YAHOOQUERY_AVAILABLE = False

from flask import Flask, render_template, jsonify
from flask_bootstrap import Bootstrap
import pandas as pd

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_yfinance_cache():
    """
    Clears the yfinance cache to fix database corruption issues.
    """
    try:
        # Clear the Windows-specific cache location
        cache_dir = Path.home() / "AppData" / "Local" / "py-yfinance"
        if cache_dir.exists():
            logger.info(f"Clearing cache directory: {cache_dir}")
            shutil.rmtree(cache_dir)
            logger.info("Successfully cleared yfinance cache")
        else:
            logger.info("No yfinance cache found to clear")
            
        # Also clear any other potential locations
        other_locations = [
            Path.home() / ".cache" / "py-yfinance",
            Path.home() / ".yfinance",
        ]
        
        for location in other_locations:
            if location.exists():
                logger.info(f"Clearing additional cache: {location}")
                shutil.rmtree(location)
                
    except Exception as e:
        logger.warning(f"Could not clear yfinance cache: {e}")
    
    # Force clear any existing yfinance modules from memory
    import sys
    modules_to_remove = [key for key in sys.modules.keys() if 'yfinance' in key.lower()]
    for module in modules_to_remove:
        try:
            del sys.modules[module]
        except:
            pass

def validate_data(data, symbol):
    """
    Validates that the data is reasonable and not corrupted.
    """
    if data is None or data.empty:
        return False
    
    # Check for reasonable price ranges (shouldn't be negative or extremely high)
    if hasattr(data, 'min') and hasattr(data, 'max'):
        min_val = data.min()
        max_val = data.max()
        if min_val <= 0 or max_val > 100000:  # Reasonable upper bound
            logger.warning(f"Suspicious data for {symbol}: min={min_val}, max={max_val}")
            return False
    
    return True

def fetch_one(symbol_target):
    """
    Fetches latest close, 52-week High/Low, all-time High/Low,
    and 30-day close history for a single ticker.
    Returns a dict or None on failure.
    """
    symbol, target = symbol_target
    logger.info(f"Starting fetch for {symbol}")
    
    # Try yahooquery first (more reliable)
    if YAHOOQUERY_AVAILABLE:
        try:
            logger.info(f"Trying yahooquery for {symbol}")
            ticker = YQTicker(symbol)
            
            # Get price data
            hist_data = ticker.history(period="1y")
            if hist_data is not None and not hist_data.empty:
                # Get current price (most recent)
                current = float(hist_data['close'].iloc[-1])
                logger.info(f"Got current price for {symbol}: ${current}")
                
                # Get 52-week high/low
                week52_high = float(hist_data['high'].max())
                week52_low = float(hist_data['low'].min())
                
                # Get 30-day history
                recent_30d = hist_data.tail(30)
                dates = [d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d)[:10] for d in recent_30d.index]
                prices = [float(p) for p in recent_30d['close'].tolist()]
                
                # Try to get all-time data
                try:
                    all_time_hist = ticker.history(period="max")
                    if all_time_hist is not None and not all_time_hist.empty:
                        all_time_high = float(all_time_hist['high'].max())
                        all_time_low = float(all_time_hist['low'].min())
                    else:
                        all_time_high = week52_high
                        all_time_low = week52_low
                except:
                    all_time_high = week52_high
                    all_time_low = week52_low
                
                # Calculate additional metrics
                price_change_24h = None
                price_change_pct_24h = None
                if len(prices) >= 2:
                    price_change_24h = current - prices[-2] if len(prices) > 1 else 0
                    price_change_pct_24h = (price_change_24h / prices[-2] * 100) if prices[-2] != 0 else 0

                # Distance from 52-week high/low
                distance_from_52w_high = ((current - week52_high) / week52_high * 100)
                distance_from_52w_low = ((current - week52_low) / week52_low * 100)

                result = {
                    "ticker": symbol,
                    "current_price": round(current, 2),
                    "week52_low": round(week52_low, 2),
                    "week52_high": round(week52_high, 2),
                    "all_time_low": round(all_time_low, 2),
                    "all_time_high": round(all_time_high, 2),
                    "target_price": target,
                    "price_change_24h": round(price_change_24h, 2) if price_change_24h else None,
                    "price_change_pct_24h": round(price_change_pct_24h, 2) if price_change_pct_24h else None,
                    "distance_from_52w_high": round(distance_from_52w_high, 2),
                    "distance_from_52w_low": round(distance_from_52w_low, 2),
                    "alert_triggered": current <= target,
                    "history": {
                        "dates": dates,
                        "prices": prices
                    },
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "data_source": "yahooquery"
                }

                if current <= target:
                    logger.info(f"🚨 ALERT: {symbol} is at ${current} (≤ target ${target})")

                return result
                
        except Exception as e:
            logger.warning(f"yahooquery failed for {symbol}: {e}")
    
    # Fallback to yfinance if yahooquery fails
    if YFINANCE_AVAILABLE:
        try:
            logger.info(f"Trying yfinance for {symbol}")
            # Create ticker with error handling
            ticker = yf.Ticker(symbol)
            
            # Add retry mechanism for data fetching
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Fetching recent data for {symbol} (attempt {attempt + 1})")
                    # 1. Latest price (close of most recent daily bar)
                    recent = ticker.history(period="5d", interval="1d")
                    if recent.empty or not validate_data(recent["Close"], symbol):
                        if attempt < max_retries - 1:
                            logger.warning(f"Attempt {attempt + 1} failed for {symbol}, retrying...")
                            time.sleep(1)  # Brief delay before retry
                            continue
                        else:
                            logger.warning(f"No valid recent data for {symbol} after {max_retries} attempts")
                            return None
                    
                    current = float(recent["Close"].iloc[-1])
                    logger.info(f"Got current price for {symbol}: ${current}")
                    break
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {e}, retrying...")
                        time.sleep(1)
                        continue
                    else:
                        raise e

            # 2. 52-week high/low (intraday)
            year_hist = ticker.history(period="1y", interval="1d")
            if year_hist.empty or not validate_data(year_hist["High"], symbol):
                logger.warning(f"No valid 52-week data for {symbol}")
                week52_high = week52_low = None
            else:
                week52_high = float(year_hist["High"].max())
                week52_low = float(year_hist["Low"].min())

            # 3. All-time high/low (intraday) - FIXED LOGIC
            # Use a longer period if "max" fails, and add validation
            try:
                full_hist = ticker.history(period="max", interval="1d")
                if full_hist.empty or not validate_data(full_hist["High"], symbol):
                    # Fallback to 10 years if max fails
                    logger.info(f"Using 10-year fallback for all-time data for {symbol}")
                    full_hist = ticker.history(period="10y", interval="1d")
                
                if not full_hist.empty and validate_data(full_hist["High"], symbol):
                    all_time_high = float(full_hist["High"].max())
                    all_time_low = float(full_hist["Low"].min())
                else:
                    logger.warning(f"No valid all-time data for {symbol}")
                    all_time_high = all_time_low = None
                    
            except Exception as e:
                logger.warning(f"Error fetching all-time data for {symbol}: {e}")
                all_time_high = all_time_low = None

            # 4. 30-day close history
            hist30 = ticker.history(period="30d", interval="1d")
            if hist30.empty or not validate_data(hist30["Close"], symbol):
                logger.warning(f"No valid 30-day history for {symbol}")
                dates = []
                prices = []
            else:
                dates = [d.strftime("%Y-%m-%d") for d in hist30.index]
                prices = [float(p) for p in hist30["Close"].tolist()]

            # Calculate additional metrics
            price_change_24h = None
            price_change_pct_24h = None
            if len(prices) >= 2:
                price_change_24h = current - prices[-2] if len(prices) > 1 else 0
                price_change_pct_24h = (price_change_24h / prices[-2] * 100) if prices[-2] != 0 else 0

            # Distance from 52-week high/low
            distance_from_52w_high = None
            distance_from_52w_low = None
            if week52_high and week52_low:
                distance_from_52w_high = ((current - week52_high) / week52_high * 100)
                distance_from_52w_low = ((current - week52_low) / week52_low * 100)

            result = {
                "ticker": symbol,
                "current_price": round(current, 2),
                "week52_low": round(week52_low, 2) if week52_low else None,
                "week52_high": round(week52_high, 2) if week52_high else None,
                "all_time_low": round(all_time_low, 2) if all_time_low else None,
                "all_time_high": round(all_time_high, 2) if all_time_high else None,
                "target_price": target,
                "price_change_24h": round(price_change_24h, 2) if price_change_24h else None,
                "price_change_pct_24h": round(price_change_pct_24h, 2) if price_change_pct_24h else None,
                "distance_from_52w_high": round(distance_from_52w_high, 2) if distance_from_52w_high else None,
                "distance_from_52w_low": round(distance_from_52w_low, 2) if distance_from_52w_low else None,
                "alert_triggered": current <= target,
                "history": {
                    "dates": dates,
                    "prices": prices
                },
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "yfinance"
            }

            if current <= target:
                logger.info(f"🚨 ALERT: {symbol} is at ${current} (≤ target ${target})")

            return result

        except Exception as e:
            logger.error(f"yfinance also failed for {symbol}: {e}")
    
    logger.error(f"All data sources failed for {symbol}")
    return None


def fetch_ticker_data_concurrent(max_workers=5):
    """
    Uses ThreadPoolExecutor to fetch all tickers in parallel.
    Includes error handling and data validation.
    """
    logger.info("Starting ticker data fetch...")
    
    # Clear cache before fetching to prevent database corruption
    clear_yfinance_cache()
    
    results = []
    failed_tickers = []
    
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            logger.info(f"Submitting {len(tickers)} ticker jobs...")
            futures = {executor.submit(fetch_one, item): item[0] for item in tickers.items()}
            
            for future in as_completed(futures):
                ticker_symbol = futures[future]
                try:
                    data = future.result(timeout=45)  # 45 second timeout per ticker
                    if data:
                        results.append(data)
                        logger.info(f"Successfully fetched {ticker_symbol}")
                    else:
                        failed_tickers.append(ticker_symbol)
                        logger.warning(f"No data returned for {ticker_symbol}")
                except Exception as e:
                    logger.error(f"Timeout or error for {ticker_symbol}: {e}")
                    failed_tickers.append(ticker_symbol)
    except Exception as e:
        logger.error(f"Error in concurrent execution: {e}")
        return {
            "tickers": [],
            "error": str(e),
            "summary": {
                "total_tickers": len(tickers),
                "successful": 0,
                "failed": len(tickers),
                "failed_tickers": list(tickers.keys()),
                "alerts_triggered": [],
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    
    # Log summary
    logger.info(f"Successfully fetched {len(results)} tickers, {len(failed_tickers)} failed")
    if failed_tickers:
        logger.warning(f"Failed tickers: {', '.join(failed_tickers)}")
    
    # Sort results by ticker symbol for consistent ordering
    results.sort(key=lambda x: x['ticker'])
    
    return {
        "tickers": results,
        "summary": {
            "total_tickers": len(tickers),
            "successful": len(results),
            "failed": len(failed_tickers),
            "failed_tickers": failed_tickers,
            "alerts_triggered": [r for r in results if r.get('alert_triggered', False)],
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data')
def data_route():
    try:
        return jsonify(fetch_ticker_data_concurrent())
    except Exception as e:
        logger.error(f"Error in data route: {e}")
        return jsonify({
            "error": "Failed to fetch ticker data",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tickers": len(tickers)
    })


if __name__ == "__main__":
    logger.info("Starting Ticker Tracker application...")
    logger.info(f"Monitoring {len(tickers)} tickers")
    
    # Clear cache on startup
    clear_yfinance_cache()
    
    # Run Flask without reloader (to avoid duplicate threads)
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)
