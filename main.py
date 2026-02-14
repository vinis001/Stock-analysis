import pandas as pd
import feedparser
import yfinance as yf
import re
import requests
import io
import os
from datetime import datetime
from textblob import TextBlob
from pptx import Presentation
from pptx.util import Pt

def get_stock_universe():
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        df = pd.read_csv(io.StringIO(response.text))
        # NSE columns are: 'Company Name', 'Symbol', 'Industry'
        return df
    except Exception as e:
        print(f"⚠️ Error fetching universe: {e}")
        return pd.DataFrame()

def get_impact_summary(change, sentiment, sector):
    if change > 1.0:
        return f"Positive momentum in the {sector} space is driving price action. News sentiment is supportive."
    elif change < -1.0:
        return f"The {sector} sector is facing selling pressure. Technicals suggest caution despite current headlines."
    return f"Stable movement in {sector}. Investors are weighing the latest news against broader market trends."

def create_ppt(data_list):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Market Intelligence Report"
    slide.placeholders[1].text = f"15+ Stock Analysis\nGenerated: {datetime.now().strftime('%d %b %Y')}"

    for d in data_list:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = f"{d['name']} ({d['sector']})"
        body = slide.placeholders[1].text_frame
        body.text = f"Price Change: {d['change']}% | Sentiment: {d['sent']}"
        
        p = body.add_paragraph()
        p.text = f"\nNews: {d['headline']}"
        p.font.size = Pt(14)
        
        p = body.add_paragraph()
        p.text = f"Link: {d['link']}"
        p.font.size = Pt(10)

        p = body.add_paragraph()
        p.text = f"\nAnalysis: {d['summary']}"
        p.font.bold = True

    filename = "Market_Report.pptx"
    prs.save(filename)
    return filename

def run_analysis():
    df = get_stock_universe()
    if df.empty: return

    # Use 'Industry' as the key to avoid KeyError
    stock_map = {row['Symbol']: row['Company Name'] for _, row in df.iterrows()}
    sector_map = {row['Symbol']: row.get('Industry', 'General') for _, row in df.iterrows()}

    feed = feedparser.parse("https://news.google.com/rss/search?q=Indian+stock+market+news&hl=en-IN&gl=IN&ceid=IN:en")
    final_data = []
    seen = set()

    for entry in feed.entries[:100]:
        if len(final_data) >= 15: break
        headline = entry.title
        for sym, name in stock_map.items():
            if sym in headline or name.split()[0] in headline:
                ticker = f"{sym}.NS"
                if ticker not in seen:
                    try:
                        s = yf.Ticker(ticker).history(period="2d")
                        change = round(((s['Close'].iloc[-1]-s['Close'].iloc[-2])/s['Close'].iloc[-2])*100, 2)
                        final_data.append({
                            "name": name, "sector": sector_map[sym], "headline": headline,
                            "link": entry.link, "change": change, "sent": "Positive" if change > 0 else "Negative",
                            "summary": get_impact_summary(change, "Neutral", sector_map[sym])
                        })
                        seen.add(ticker)
                        break
                    except: continue

   if final_data:
        # Create a dynamic filename based on current date
        date_str = datetime.now().strftime('%d_%b_%Y')
        filename = f"Market_Report_{date_str}.pptx"
        create_ppt(final_data, filename) # Pass filename to function
def create_ppt(data_list, filename):
    prs = Presentation()
    # ... (keep your existing slide logic) ...
    prs.save(filename)
    print(f"✅ Saved as {filename}")
    
if __name__ == "__main__":
    run_analysis()
