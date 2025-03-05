import yfinance as yf
import schedule
from pushbullet import Pushbullet
import time
import pandas as pd
from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
import threading
import logging
import asyncio

app = Flask(__name__)
Bootstrap(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pushbullet API 
#pb = Pushbullet("YOUR_API_KEY")
#pb.push_note("Test Notification", "This is a test notification from the ticker tracker.")

# List all registered devices for debugging
#devices = pb.devices
#for device in devices:
#    print(f"Registered device: {device.nickname}")

# Define the tickers and price limits
tickers = {
    'BTC-USD': 80000, # Bitcoin
    'ETH-USD': 2200, # Ethereum
    'COIN': 100, # Coinbase
    'MSFT': 325, # Microsoft
    'NVDA': 100, # Nvidia
    'TSM': 125, # TSMC
    'AAPL': 185, # Apple
    'DIS': 80, # Disney
    'AMD': 90, # AMD
    'AMZN': 150, # Amazon
    'INTC': 18, # Intel
    'VTI': 245, # Vanguard Total Stock Market ETF
    'VXUS': 55, # Vanguard Total International Stock ETF
    'VOO': 490, # Vanguard S&P 500 ETF
    'WM': 175, # Waste Management
    'WMT': 50, # Walmart
    'KO': 55, # Coca-Cola
    'SCHD': 25, # Schwab US Dividend Equity ETF
    'GOOGL': 165, # Google
    'META': 450, # Meta
}

# fetch ticker data, log, and send notifications
def fetch_ticker_data():
    data = []
    for ticker, target_price in tickers.items():
        try:
            stock = yf.Ticker(ticker) # create a Ticker object
            hist = stock.history(period="max") # period set to max to get all availabke data in order to accurately calculate all-time high and low
            if hist.empty:
                logger.warning(f"No data found for {ticker}") # set yfinance to a previous version to avoid this error; pip install yfinance==0.1.63 if needed 
                continue

            current_price = hist['Close'].iloc[-1]

            # Calculate the 52-week high and low
            year_hist = yf.Ticker(ticker).history(period="1y")
            week52_high = year_hist['Close'].max() if not year_hist.empty else None
            week52_low = year_hist['Close'].min() if not year_hist.empty else None

            # Calculate all-time high and low
            max_hist = yf.Ticker(ticker).history(period="max")
            all_time_high = max_hist['Close'].max() if not max_hist.empty else None
            all_time_low = max_hist['Close'].min() if not max_hist.empty else None

            data.append({
                'ticker': ticker,
                'current_price': current_price,
                'week52_low': week52_low,
                'week52_high': week52_high,
                'all_time_low': all_time_low,
                'all_time_high': all_time_high
            })

            if current_price <= target_price:
                print(f"Price Alert: {ticker} - The current price of {ticker} is {current_price}, which is below your target of {target_price}.")
                #pb.push_note(f"Price Alert: {ticker}", f"The current price of {ticker} is {current_price}, which is below your target of {target_price}.")

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")

        time.sleep(0)  # add a delay between requests if desired

    return data


@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/data')
def data():
    data = fetch_ticker_data()
    return jsonify(data)

if __name__ == '__main__':
    fetch_ticker_data()
    app.run(debug=False, use_reloader=True)
