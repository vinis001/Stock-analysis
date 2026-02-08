import pandas as pd
import feedparser
import yfinance as yf
import os
import smtplib
import re
from datetime import datetime
from textblob import TextBlob
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict

# --- STEP 1: LOAD A WIDE LIST OF STOCKS (NIFTY 500) ---
def get_nifty_500():
    try:
        # Fetching Nifty 500 list from a reliable source
        url = "https://raw.githubusercontent.com/senthilthyagarajan/nifty-indices-components/master/nifty500.csv"
        df = pd.read_csv(url)
        # Create a dictionary of {Company Name: Ticker}
        # We clean the names to make matching easier (e.g., removing 'Ltd', 'Limited')
        stock_dict = {}
        for _, row in df.iterrows():
            clean_name = re.sub(r' (Ltd|Limited|Industries|Bank|Finance|Services|Corporation)', '', row['Company Name'], flags=re.I).strip()
            stock_dict[clean_name] = row['Symbol'] + ".NS"
            stock_dict[row['Symbol']] = row['Symbol'] + ".NS" # Also match the symbol itself
        return stock_dict
    except Exception as e:
        print(f"⚠️ Failed to fetch Nifty 500: {e}")
        return {"Reliance": "RELIANCE.NS", "TCS": "TCS.NS"}

# --- STEP 2: EXTRACT STOCKS FROM TEXT ---
def extract_stocks_from_news(headline, stock_dict):
    found_tickers = []
    # Tokenize headline and check against our 500+ stock names
    for name, ticker in stock_dict.items():
        if len(name) > 3: # Avoid matching very short words
            if re.search(r'\b' + re.escape(name) + r'\b', headline, re.I):
                found_tickers.append((name, ticker))
    return list(set(found_tickers)) # Remove duplicates

# --- STEP 3: MARKET ANALYSIS LOGIC ---
def get_stock_metrics(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="2d")
        if len(hist) < 2: return "Stable", 0
        change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
        trend = "🚀 Bullish" if change > 0.5 else "🔻 Bearish" if change < -0.5 else "➖ Neutral"
        return trend, round(hist['Close'].iloc[-1], 2), round(change, 2)
    except:
        return "N/A", 0, 0

def send_email(subject, body):
    sender = os.environ.get('EMAIL_ADDRESS')
    password = os.environ.get('EMAIL_PASSWORD')
    receiver = os.environ.get('RECEIVER_EMAIL')
    if not all([sender, password, receiver]): return
    msg = MIMEMultipart(); msg['From'], msg['To'], msg['Subject'] = sender, receiver, subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(sender, password); server.send_message(msg); server.quit()
        print("📧 Email Sent!")
    except Exception as e: print(f"Email Error: {e}")

# --- MAIN EXECUTION ---
def run_analysis():
    stock_dict = get_nifty_500()
    rss_url = "https://news.google.com/rss/search?q=when:1d+Indian+stock+market+business&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    
    analyzed_stocks = {} # Store analysis for stocks found in news

    print(f"🔍 Scanning {len(feed.entries)} headlines for {len(stock_dict)} stocks...")

    for entry in feed.entries[:40]: # Scan top 40 news items
        headline = entry.title
        found = extract_stocks_from_news(headline, stock_dict)
        
        sentiment_score = TextBlob(headline).sentiment.polarity
        sentiment = "Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral"

        for name, ticker in found:
            if ticker not in analyzed_stocks:
                trend, price, change = get_stock_metrics(ticker)
                analyzed_stocks[ticker] = {
                    "name": name,
                    "headline": headline,
                    "sentiment": sentiment,
                    "trend": trend,
                    "price": price,
                    "change": change
                }

    # Build the report
    date_str = datetime.now().strftime("%d %b %Y")
    report = f"📰 STOCKS IN THE NEWS: {date_str}\n" + "="*40 + "\n\n"
    
    if not analyzed_stocks:
        report += "No specific Nifty 500 stocks identified in today's top headlines."
    else:
        for ticker, data in analyzed_stocks.items():
            report += f"🏢 STOCK: {data['name']} ({ticker})\n"
            report += f"🗞️ News: {data['headline']}\n"
            report += f"🧠 Sentiment: {data['sentiment']}\n"
            report += f"📊 Trend: {data['trend']} | Price: ₹{data['price']} ({data['change']}%)\n"
            report += "-"*20 + "\n\n"

    send_email(f"Daily Stocks-in-News Analysis: {date_str}", report)

if __name__ == "__main__":
    run_analysis()
