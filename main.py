import pandas as pd
import feedparser
import yfinance as yf
import re
import requests
import io
from datetime import datetime
from textblob import TextBlob
from pptx import Presentation
from pptx.util import Inches, Pt

def get_stock_universe():
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        df = pd.read_csv(io.StringIO(response.text))
        stock_dict = {re.sub(r' (Ltd|Limited|Bank|Finance|Industries|Services)', '', row['Company Name'], flags=re.I).strip(): row['Symbol'] + ".NS" for _, row in df.iterrows()}
        return stock_dict
    except:
        return {"Reliance": "RELIANCE.NS", "TCS": "TCS.NS"}

def create_ppt_report(found_data):
    prs = Presentation()
    date_str = datetime.now().strftime("%d %b %Y")
    
    # Title Slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Daily Market Analysis"
    slide.placeholders[1].text = f"Generated on: {date_str}\nAutomated by Gemini Bot"

    # Data Slides
    for ticker, d in found_data.items():
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = f"{d['name']} ({ticker})"
        
        content = slide.placeholders[1].text_frame
        content.text = f"Market Trend: {d['trend']}"
        
        p = content.add_paragraph()
        p.text = f"Current Price: ₹{d['price']} ({d['change']}%)"
        
        p = content.add_paragraph()
        p.text = f"Sentiment: {d['sent']}"
        
        p = content.add_paragraph()
        p.text = f"\nLatest News:\n{d['headline']}"

    filename = f"Market_Report_{datetime.now().strftime('%Y%m%d')}.pptx"
    prs.save(filename)
    print(f"✅ PPT created: {filename}")
    return filename

def run_analysis():
    stocks = get_stock_universe()
    rss_url = "https://news.google.com/rss/search?q=when:1d+Indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    found_data = {}

    for entry in feed.entries[:25]:
        headline = entry.title
        for name, ticker in stocks.items():
            if len(name) > 3 and re.search(r'\b' + re.escape(name) + r'\b', headline, re.I):
                if ticker not in found_data:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="2d")
                    change = round(((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100, 2)
                    found_data[ticker] = {
                        "name": name, "headline": headline, 
                        "sent": "Positive" if TextBlob(headline).sentiment.polarity > 0.1 else "Neutral",
                        "trend": "🚀 Bullish" if change > 0 else "🔻 Bearish",
                        "price": round(hist['Close'].iloc[-1], 2), "change": change
                    }
    
    create_ppt_report(found_data)

if __name__ == "__main__":
    run_analysis()
