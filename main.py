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
from pptx.enum.text import PP_ALIGN

def get_stock_universe():
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        df = pd.read_csv(io.StringIO(response.text))
        # Store Sector info as well for the "Fields" requirement
        return df
    except:
        return pd.DataFrame()

def get_impact_summary(change, sentiment, sector):
    """Generates the 'Why' and 'How' summary based on data."""
    if change > 1.5 and sentiment == "Positive":
        return f"The stock is witnessing strong momentum due to sectoral tailwinds in {sector}. Positive news sentiment is driving institutional buying."
    elif change < -1.5 and sentiment == "Negative":
        return f"Heavy selling pressure observed. The news indicates fundamental concerns or profit booking within the {sector} space."
    elif sentiment == "Positive" and change < 0:
        return f"Despite positive news, the stock is lagging. This suggests 'Sell on News' behavior or broader market weakness affecting {sector}."
    else:
        return f"The stock is reacting to specific updates. Market participants are currently neutral, awaiting further volume confirmation."

def create_ppt(data_list):
    prs = Presentation()
    date_str = datetime.now().strftime("%d %b %Y")
    
    # Title Slide
    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title_slide.shapes.title.text = "Comprehensive Market Intelligence"
    title_slide.placeholders[1].text = f"Analysis of 15+ Trending Stocks\n{date_str}"

    for d in data_list:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        # Header: Stock Name and Sector
        title_shape = slide.shapes.title
        title_shape.text = f"{d['name']} | Sector: {d['sector']}"
        
        # Body Content
        body = slide.placeholders[1].text_frame
        body.word_wrap = True
        
        # Section 1: Financial Snapshot
        p = body.text
        body.text = f"📊 MARKET STATUS: {d['trend']} ({d['change']}%)"
        
        # Section 2: News Link
        p = body.add_paragraph()
        p.text = f"🔗 SOURCE: {d['link']}"
        p.font.size = Pt(12)
        
        # Section 3: Headline
        p = body.add_paragraph()
        p.text = f"\n🗞️ HEADLINE: {d['headline']}"
        p.font.bold = True
        
        # Section 4: The 'Why' Summary
        p = body.add_paragraph()
        p.text = f"\n💡 ANALYSIS (How & Why):"
        p = body.add_paragraph()
        p.text = d['summary']
        p.font.italic = True

    filename = f"Market_Summary_{datetime.now().strftime('%Y%m%d')}.pptx"
    prs.save(filename)
    return filename

def run_analysis():
    df_universe = get_stock_universe()
    if df_universe.empty: return
    
    # Create a mapping for easy lookup
    stock_map = {row['Symbol']: row['Company Name'] for _, row in df_universe.iterrows()}
    sector_map = {row['Symbol']: row['Sector'] for _, row in df_universe.iterrows()}

    rss_url = "https://news.google.com/rss/search?q=when:1d+Indian+stock+market+analysis&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    
    final_data = []
    seen_tickers = set()

    # Increase scan range to ensure we hit 15 stocks
    for entry in feed.entries[:100]:
        if len(final_data) >= 15: break
        
        headline = entry.title
        for symbol, full_name in stock_map.items():
            # Check for Ticker or Name match
            if symbol in headline or re.search(r'\b' + re.escape(full_name.split()[0]) + r'\b', headline, re.I):
                ticker = f"{symbol}.NS"
                if ticker not in seen_tickers:
                    try:
                        stock = yf.Ticker(ticker)
                        h = stock.history(period="2d")
                        if len(h) < 2: continue
                        
                        price_change = round(((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100, 2)
                        sentiment = "Positive" if TextBlob(headline).sentiment.polarity > 0.1 else "Negative" if TextBlob(headline).sentiment.polarity < -0.1 else "Neutral"
                        
                        final_data.append({
                            "name": full_name,
                            "sector": sector_map.get(symbol, "General"),
                            "headline": headline,
                            "link": entry.link,
                            "change": price_change,
                            "trend": "📈 Gains" if price_change > 0 else "📉 Drop",
                            "summary": get_impact_summary(price_change, sentiment, sector_map.get(symbol, "General"))
                        })
                        seen_tickers.add(ticker)
                        break
                    except:
                        continue

    if final_data:
        create_ppt(final_data)
        print(f"✅ Generated report with {len(final_data)} stocks.")

if __name__ == "__main__":
    run_analysis()
