import pandas as pd
import feedparser
import yfinance as yf
import os
import io
import requests
from datetime import datetime
from pptx import Presentation
from pptx.util import Pt

def get_detailed_analysis(sector, change):
    # Deep-dive sectoral intelligence for 2026
    logic = {
        "Financial Services": {
            "time": "6-12 Months",
            "upside": "12-15%",
            "reason": "Credit growth remains robust; NBFCs are seeing cleaner balance sheets and rising retail AUM."
        },
        "Healthcare": {
            "time": "12-24 Months",
            "upside": "20%",
            "reason": "Expansion of digital health infrastructure and high demand for specialized therapies post-2025."
        },
        "Energy": {
            "time": "3-5 Years",
            "upside": "25%+",
            "reason": "Massive shift toward Green Hydrogen and ammonia terminals; government capex is at an all-time high."
        },
        "Capital Goods": {
            "time": "18-36 Months",
            "upside": "18%",
            "reason": "PLI schemes for advanced manufacturing are hitting peak production cycles."
        }
    }
    
    info = logic.get(sector, {"time": "12 Months", "upside": "10-12%", "reason": "Tracking broader Nifty index recovery and steady earnings."})
    sentiment = "Bullish" if change > 0 else "Consolidating"
    
    return (f"Outlook: {sentiment}\n"
            f"Expected Growth: {info['upside']} over {info['time']}\n"
            f"Why: {info['reason']}")

def create_ppt(data_list, filename):
    # Ensure the folder exists
    os.makedirs("reports", exist_ok=True)
    filepath = os.path.join("reports", filename)
    
    prs = Presentation()
    # Title Slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Sectoral Growth Intelligence"
    slide.placeholders[1].text = f"Deep Dive Analysis\n{datetime.now().strftime('%d %b %Y')}"

    for d in data_list:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = f"{d['name']} - {d['sector']}"
        body = slide.placeholders[1].text_frame
        
        # Summary Section
        p1 = body.paragraphs[0]
        p1.text = f"Current Movement: {d['change']}%"
        p1.font.bold = True
        
        # Detailed Summary (No links)
        p2 = body.add_paragraph()
        p2.text = f"\nMarket Context:\n{d['headline']}"
        p2.font.size = Pt(12)

        p3 = body.add_paragraph()
        p3.text = f"\nDeep-Dive Analysis:\n{d['summary']}"
        p3.font.size = Pt(14)

    prs.save(filepath)
    print(f"✅ File saved to: {filepath}")

def run_analysis():
    # ... (Universe fetching logic remains same) ...
    # Assume final_data is collected here
    
    if final_data:
        date_str = datetime.now().strftime('%d_%b_%Y')
        filename = f"Analysis_{date_str}.pptx"
        create_ppt(final_data, filename)

if __name__ == "__main__":
    run_analysis()
