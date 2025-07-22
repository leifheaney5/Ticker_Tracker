# Ticker Tracker – Real-Time Market Clarity Without the Clutter

**Ticker Tracker** is a lightweight, locally‑run dashboard that fetches live market data. 
  - It runs in parallel, renders both bar‑ and multi‑line charts, and displays a high‑contrast, dark‑mode‑friendly table. 
  - Optional Pushbullet integration lets you know the moment a ticker hits your target price
  - Track your stocks in real‑time with charts and notifications—no fluff.

---

## Contact Info

### Developer: Leif Heaney
### Contact: leif@leifheaney.com
### Portfolio: https://leifheaney.com/
### GitHub: https://github.com/leifheaney5
### Created On: 2024-09-09
### Last Updated: 2025-07-22

---

### Important Info about yfinance API: 

- yfinance API has had issues lately with updates; as such, upon installation if you experience an errors fetching tickers that you are positive have not been delisted, 
pip install a prior version of finance, using the following command: 'pip install yfinance==0.1.63'

- this script is meant to run locally and securely. however, functionality has been put in place to allow for PushBullet API to execute automatically if desired. 
As such, incorporate this feature if you would like using your own custom-generated API key here: https://docs.pushbullet.com/
<img width="1061" height="1193" alt="TickerTracker-Screenshot" src="https://github.com/user-attachments/assets/47692e15-0e52-4f0c-b185-a055eeb54950" />
<img width="1342" height="846" alt="TickerTracker-Table-Screenshot" src="https://github.com/user-attachments/assets/eac81432-dbde-407d-b814-01966592ede2" />
---

![Dashboard](images/1c300a31-a5fe-4c9f-9fc9-497981506fab.png)  
![Line Chart](images/f16e5378-c5b1-48fb-ac66-180f2ebd3614.png)  
![Pushbullet Setup](images/fee7e5e1-d2ad-4c72-80aa-a8f4ba347a77.png)  

---

## Features

- **Fast, parallel fetching** of live prices via `yfinance`  
- **Real‑time bar & multi‑line charts** (30‑day history) with Chart.js  
- **High‑contrast, dark‑mode‑friendly table** for easy reading  
- **Optional Pushbullet alerts** for price targets  

---

## Installation

### Prerequisites

- Python 3.7+  
- `pip`

```bash
git clone https://github.com/yourusername/ticker-tracker.git
cd ticker-tracker
pip install -r requirements.txt
```
---

### Usage

```bash
python app.py
```

Then open your browser to: [http://localhost:5000](http://localhost:5000)

---

### Pushbullet Notifications (Optional)

    Create or log in to Pushbullet → grab your API Key:
    https://docs.pushbullet.com/

    Export your key as an environment variable:

export PUSHBULLET_API_KEY="o.xxxxxxYOURKEYxxxxxx"

In app.py, uncomment/configure the Pushbullet section. Alerts will fire automatically when a symbol hits your target.

---

Changelog
v1.2.0 – Front‑end Enhancements

Enhance front‑end dashboard with 30‑day multi‑line chart and high‑contrast table

        Add lineChart canvas + JS logic to plot a separate line per ticker

        Pull 30‑day history.dates and history.prices from /data JSON

        Build one dataset per symbol with randomized HSL border colors

        Auto‑update chart on each fetch

        Refactor barChart logic (no behavior change, cleaned up names & flow)

        Overhaul table styling for readability

        Solid purple header, alternating RGBA row stripes

        Hover states brighten row & text

        Lightened borders & adjusted padding

        .toFixed(2) formatting on all numeric cells

        Preserve dark‑mode support across charts & table

v1.1.0 – Back‑end Improvements

Improve ticker‑data pipeline with parallel fetching and 30‑day history support

        Refactor fetch_one() to:

          Use yf.Ticker.history() for recent, 1y, max, and 30d windows

          Compute 52‑week & all‑time highs/lows from High/Low columns

          Extract 30‑day closing‑price history (dates + prices)

      Introduce fetch_ticker_data_concurrent() via ThreadPoolExecutor (8 workers)

      Simplify Flask routes to a single / and /data endpoint

      Remove duplicate __main__ blocks & set use_reloader=False to avoid threading issues
    
