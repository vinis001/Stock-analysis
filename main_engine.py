import feedparser
import yfinance as yf
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import os

# CONFIGURATION
RSS_URL = "https://news.google.com/rss/search?q=when:1d+Indian+stock+market+business&hl=en-IN&gl=IN&ceid=IN:en"

SECTOR_MAP = {
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Auto": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "ADANIGREEN.NS"],
    "Pharma": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS"],
    "FMCG": ["ITC.NS", "HUL.NS", "NESTLEIND.NS"],
    "Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS"]
}

def get_sentiment(text):
    score = TextBlob(text).sentiment.polarity
    return "Bullish" if score > 0.05 else "Bearish" if score < -0.05 else "Neutral"

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        last_price = round(hist['Close'].iloc[-1], 2)
        change = round(((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100, 2)
        trend = "📈 Up" if change > 0 else "📉 Down"
        return last_price, trend
    except:
        return "N/A", "Stable"

def generate_report():
    feed = feedparser.parse(RSS_URL)
    entries = feed.entries[:20]
    
    sector_hits = {}
    analysis_results = []

    for entry in entries:
        headline = entry.title
        sentiment = get_sentiment(headline)
        
        for sector, stocks in SECTOR_MAP.items():
            if sector.lower() in headline.lower() or any(s.split('.')[0].lower() in headline.lower() for s in stocks):
                sector_hits[sector] = sector_hits.get(sector, 0) + 1
                
                # Analyze first stock in that sector for report
                main_stock = stocks[0]
                price, trend = get_stock_data(main_stock)
                
                analysis_results.append({
                    "sector": sector,
                    "headline": headline,
                    "sentiment": sentiment,
                    "stock": main_stock,
                    "price": price,
                    "trend": trend
                })

    # SORT SECTORS BY IMPACT
    top_sectors = sorted(sector_hits.items(), key=lambda x: x[1], reverse=True)[:10]

    # CREATE MARKDOWN FILE (Matching your Image Structure)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_content = f"# Investment Timeliness Sectors - {date_str}\n\n"
    
    report_content += "## Top Most Affected Sectors\n"
    for i, (sec, count) in enumerate(top_sectors, 1):
        report_content += f"{i}. {sec} ({count} major news items)\n"

    report_content += f"\n### 1. NEWS RSS URL\n- {RSS_URL}\n"
    
    report_content += "\n### 2. Sector Map (Logic Used)\n```json\n" + str(SECTOR_MAP).replace("'", '"') + "\n```\n"

    report_content += "\n### 3. Analysis Results\n"
    for res in analysis_results:
        report_content += f"#### {res['sector']} | Impact: {res['sentiment']}\n"
        report_content += f"- **Headline:** {res['headline']}\n"
        report_content += f"- **Top Pick:** `{res['stock']}` | **Price:** ₹{res['price']} | **Trend:** {res['trend']}\n\n"

    os.makedirs("reports", exist_ok=True)
    with open(f"reports/Report_{date_str}.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"✅ Report generated for {date_str}")

if __name__ == "__main__":
    generate_report()
