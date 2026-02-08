import pandas as pd
import feedparser
import yfinance as yf
import os
import smtplib
import re
import requests
import io
from datetime import datetime
from textblob import TextBlob
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
def get_stock_universe():
    """Fetch the official Nifty 500 list from NiftyIndices/NSE."""
    # Official URL for the Nifty 500 constituents
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    
    # We must use headers, otherwise the website blocks the request!
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Check for 404 or other errors
        
        # Load the CSV content into a DataFrame
        df = pd.read_csv(io.StringIO(response.text))
        
        stock_dict = {}
        for _, row in df.iterrows():
            # Standardize name for better matching (removing 'Ltd', 'Bank' etc.)
            clean_name = re.sub(r' (Ltd|Limited|Bank|Finance|Industries|Services|Corp|Enterprises)', '', row['Company Name'], flags=re.I).strip()
            ticker = row['Symbol'] + ".NS"
            stock_dict[clean_name] = ticker
            stock_dict[row['Symbol']] = ticker # Also map the symbol itself
            
        print(f"✅ Successfully loaded {len(df)} stocks from Nifty 500.")
        return stock_dict

    except Exception as e:
        print(f"⚠️ Error fetching Nifty 500: {e}. Using critical fallback list.")
        # Fallback if NSE is down or URL changes
        return {"Reliance": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC": "HDFCBANK.NS", "Infosys": "INFY.NS", "ICICI": "ICICIBANK.NS"}

def get_stock_metrics(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="2d")
        if len(hist) < 2: return "Stable", 0, 0
        change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
        trend = "🚀 Bullish" if change > 0.5 else "🔻 Bearish" if change < -0.5 else "➖ Neutral"
        return trend, round(hist['Close'].iloc[-1], 2), round(change, 2)
    except:
        return "N/A", 0, 0

def send_self_email(subject, body):
    my_email = os.environ.get('EMAIL_ADDRESS')
    my_password = os.environ.get('EMAIL_PASSWORD')
    
    if not my_email or not my_password:
        print("❌ Error: Secrets 'EMAIL_ADDRESS' or 'EMAIL_PASSWORD' not set in GitHub.")
        return

    msg = MIMEMultipart()
    msg['From'] = my_email
    msg['To'] = my_email # SEND TO SELF
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(my_email, my_password)
        server.send_message(msg)
        server.quit()
        print(f"📧 Report sent to {my_email}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def run_analysis():
    stocks = get_stock_universe()
    # Google News RSS for Indian Business News
    rss_url = "https://news.google.com/rss/search?q=when:1d+Indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    
    found_data = {}
    for entry in feed.entries[:35]:
        headline = entry.title
        sentiment_val = TextBlob(headline).sentiment.polarity
        sentiment = "Positive" if sentiment_val > 0.1 else "Negative" if sentiment_val < -0.1 else "Neutral"
        
        for name, ticker in stocks.items():
            # Check if stock name appears as a full word in the headline
            if len(name) > 3 and re.search(r'\b' + re.escape(name) + r'\b', headline, re.I):
                if ticker not in found_data:
                    trend, price, change = get_stock_metrics(ticker)
                    found_data[ticker] = {
                        "name": name, "headline": headline, "sent": sentiment,
                        "trend": trend, "price": price, "change": change
                    }

    date_str = datetime.now().strftime("%d %b %Y")
    report = f"📬 PERSONAL MARKET SCAN: {date_str}\n" + "="*40 + "\n\n"
    
    if not found_data:
        report += "No major Nifty 500 stocks detected in today's news headlines."
    else:
        for ticker, d in found_data.items():
            report += f"🔹 {d['name']} ({ticker})\n"
            report += f"   Live: ₹{d['price']} ({d['change']}% {d['trend']})\n"
            report += f"   News: {d['headline']}\n"
            report += f"   Sentiment: {d['sent']}\n" + "-"*30 + "\n"

    send_self_email(f"Market Report: {date_str}", report)

if __name__ == "__main__":
    run_analysis()
