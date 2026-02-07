import feedparser
import yfinance as yf
import json
import os
from datetime import datetime
from textblob import TextBlob

# 1. Configuration: Sector to Stocks Mapping
SECTOR_MAP = {
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "Auto": ["TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "EICHERMOT.NS", "BAJAJ-AUTO.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "ADANIGREEN.NS", "POWERGRID.NS", "BPCL.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS"],
    "Consumer": ["HUL.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TITAN.NS"],
    "Telecom": ["BHARTIARTL.NS", "IDEA.NS", "INDUSTOWER.NS"],
    "Real Estate": ["DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS"],
    "Cement": ["ULTRACEMCO.NS", "GRASIM.NS", "SHREECEM.NS"]
}

def get_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.1: return "Positive"
    elif analysis.sentiment.polarity < -0.1: return "Negative"
    return "Neutral"

def get_stock_prediction(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="5d")
        if len(hist) < 2: return "Stable", "N/A"
        
        last_close = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        trend = "Upward" if last_close > prev_close else "Downward"
        return trend, round(last_close, 2)
    except:
        return "Unknown", "N/A"

def run_pipeline():
    print("📡 Fetching Live Indian Business News...")
    rss_url = "https://news.google.com/rss/search?q=when:1d+Indian+stock+market+business&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    
    report_data = []
    
    for entry in feed.entries[:10]: # Analyze top 10 news items
        title = entry.title
        sentiment = get_sentiment(title)
        
        # Identify Sector
        detected_sector = "General"
        for sector in SECTOR_MAP:
            if sector.lower() in title.lower():
                detected_sector = sector
                break
        
        # Get Stock Recommendations
        recommendations = []
        stocks_to_check = SECTOR_MAP.get(detected_sector, ["^NSEI"]) # Default to Nifty 50
        for s in stocks_to_check:
            trend, price = get_stock_prediction(s)
            recommendations.append({"ticker": s, "trend": trend, "price": price})
        
        report_data.append({
            "headline": title,
            "sentiment": sentiment,
            "sector": detected_sector,
            "stocks": recommendations,
            "timeframe": "Intraday/Short-term"
        })

    # Save Markdown Report
    os.makedirs('reports', exist_ok=True)
    filename = f"reports/Analysis_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(filename, 'w') as f:
        f.write(f"# 📈 Indian Market Prediction: {datetime.now().strftime('%d %b %Y')}\n\n")
        for item in report_data:
            f.write(f"### 📰 {item['headline']}\n")
            f.write(f"- **Sector:** {item['sector']} | **Sentiment:** {item['sentiment']}\n")
            for s in item['stocks']:
                f.write(f"  - 🏷️ `{s['ticker']}`: {s['trend']} (Last: ₹{s['price']})\n")
            f.write("\n---\n")
    
    print(f"✅ Report created: {filename}")

if __name__ == "__main__":
    run_pipeline()
