import yfinance as yf
import schedule
from pushbullet import Pushbullet
import time
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Pushbullet API key for notifications
pb = Pushbullet("o.10x2z9QmmnUy7ZenDoYPMyxlRmn93mdh")

# List registered devices for debugging
devices = pb.devices
for device in devices:
    print(f"Registered device: {device.nickname}")

# Send a test notification to ensure Pushbullet is working
pb.push_note("Test Notification", "This is a test to verify notifications are working.")

# Define the tickers and price limits
tickers = {
    'BTC-USD': 50000, # Bitcoin
    'MSFT': 325, # Microsoft
    'NVDA': 100, # Nvidia
    'AAPL': 185, # Apple
    'DIS': 80, # Disney
    'INST': 20, # Instructure
    'AMD': 100, # AMD
    'AMZN': 150, # Amazon
    'INTC': 17, # Intel
    'VTI': 245, # Vanguard Total Stock Market ETF
    'VXUS': 55, # Vanguard Total International Stock ETF
    'WM': 175, # Waste Management
    'WMT': 50, # Walmart
    'SCHD': 70, # Schwab US Dividend Equity ETF
    'JPM': 175, # JP Morgan Chase
    'V': 200, # Visa
    'AXP': 200, # American Express
    'COIN': 100, # Coinbase
    'KO': 55, # Coca-Cola
    'ETSY': 45, # Etsy
    'DG': 70, # Dollar General
}

# Function to check prices and send notifications
def check_prices():
    data = []
    for ticker, target_price in tickers.items():
        stock = yf.Ticker(ticker)
        current_price = stock.history(period="1d")['Close'][0]
        data.append((ticker, current_price, target_price))
        if current_price <= target_price:
            pb.push_note(f"Price Alert: {ticker}", f"The current price of {ticker} is {current_price}, which is below your target of {target_price}.")
    
    visualize_data(data)

# Function to visualize data
def visualize_data(data):
    df = pd.DataFrame(data, columns=['Ticker', 'Current Price', 'Target Price'])
    df['Percentage Difference'] = ((df['Target Price'] - df['Current Price']) / df['Target Price']) * 100
    
    plt.figure(figsize=(14, 7))
    sns.barplot(x='Ticker', y='Percentage Difference', data=df)
    plt.axhline(0, color='red', linestyle='--')
    plt.title('Percentage Difference Between Current Price and Target Price')
    plt.xlabel('Ticker')
    plt.ylabel('Percentage Difference (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Call the check_prices function immediately
check_prices()
visualize_data()

# Schedule the check_prices function to run at a specific interval
schedule.every().day.at("09:00").do(check_prices)

while True:
    schedule.run_pending()
    time.sleep(1)