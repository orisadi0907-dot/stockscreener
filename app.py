import streamlit as st
import subprocess
import sys
import random

# Automatic package installation layer to prevent errors
def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_and_import('yfinance')
install_and_import('pandas')
install_and_import('plotly')

import yfinance as yf
import pandas as pd
import plotly.express as px

# Setting standard left-to-right alignment for clean English display
st.set_page_config(page_title="Automated Value Stock Screener", layout="wide")

st.title("🌍 Automated Global Stock Screener: Intrinsic Value vs Market Price")
st.write("This system scans global markets to find undervalued stocks where the estimated fair value is significantly higher than the current market price (Margin of Safety).")

@st.cache_data(ttl=3600)
def get_market_pool():
    """ Automatically fetches a comprehensive pool of tickers from the web """
    try:
        url_sp = "https://wikipedia.org"
        df_sp = pd.read_html(url_sp)
        sp_tickers = df_sp['Symbol'].tolist()
        
        global_pool = [
            "AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMZN", "NFLX", "AMD", 
            "QCOM", "PLTR", "BABA", "ASML", "1105436.TA", "748038.TA", "662577.TA"
        ]
        return list(set(sp_tickers + global_pool))
    except Exception:
        return ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMZN", "NFLX", "AMD", "PLTR", "BABA"]

# Fetch pool and draw a random sample to maintain speed and bypass rate-limits
all_tickers = get_market_pool()
sample_size = min(30, len(all_tickers))
tickers_to_scan = random.sample(all_tickers, sample_size)

st.info(f"🔄 Scanning and analyzing {sample_size} stocks from the web pool. Please wait...")

progress_bar = st.progress(0)
data_list = []

# Main scanning loop
for index, t in enumerate(tickers_to_scan):
    progress_bar.progress((index + 1) / len(tickers_to_scan))
    try:
        t_clean = t.replace('.', '-')
        stock = yf.Ticker(t_clean)
        info = stock.info
        
        current_price = info.get('currentPrice', None)
        target_price = info.get('targetMeanPrice', None) # Fair value estimated by analysts
        
        profit_margin = info.get('profitMargins', None)
        fcf = info.get('freeCashflow', None)
        market_cap = info.get('marketCap', None)
        
        if current_price and target_price and target_price > 0:
            # Calculate the Margin of Safety percentage
            margin_of_safety = ((target_price - current_price) / current_price) * 100
            
            pm_pct = profit_margin * 100 if profit_margin else 0.0
            fcf_yield = (fcf / market_cap) * 100 if fcf and market_cap else 0.0
            
            # Attractiveness multi-factor score (discount weighted heavily + quality metrics)
            score = margin_of_safety * 1.5 + (pm_pct * 0.2) + (fcf_yield * 0.3)
            
            data_list.append({
                "Ticker": t,
                "Company Name": info.get('shortName', t),
                "Current Price": round(current_price, 2),
                "Estimated Fair Value": round(target_price, 2),
                "Margin of Safety (%)": round(margin_of_safety, 1),
                "Net Profit Margin": f"{round(pm_pct, 1)}%",
                "FCF Yield": f"{round(fcf_yield, 2)}%",
                "Winning Score": round(max(0, min(100, score)), 1)
            })
    except Exception:
        continue

df = pd.DataFrame(data_list)

if not df.empty:
    # Sorting by the highest score (most undervalued/attractive stocks first)
    df = df.sort_values(by="Winning Score", ascending=False).reset_index(drop=True)
    
    # 1. Clean Table Presentation
    st.subheader("📋 Screener Results: Top Undervalued Value Stocks")
    
    # Adding a visual layout indicator for user readability without altering mathematical sorting
    df_display = df.copy()
    df_display["Margin of Safety (%)"] = df_display["Margin of Safety (%)"].apply(lambda x: f"+{x}%" if x > 0 else f"{x}%")
    
    # Format prices with dollar signs for presentation
    df_display["Current Price"] = df_display["Current Price"].apply(lambda x: f"${x}")
    df_display["Estimated Fair Value"] = df_display["Estimated Fair Value"].apply(lambda x: f"${x}")
    
    st.dataframe(df_display, use_container_width=True)
    
    # 2. Clean Chart Presentation
    st.subheader("📉 Chart: Top Stocks by Attractiveness & Valuation Score")
    
    fig = px.bar(
        df.head(15), 
        x="Ticker", 
        y="Winning Score", 
        color="Winning Score",
        text="Winning Score",
        labels={"Winning Score": "Attractiveness Score (0-100)", "Ticker": "Stock Ticker"},
        title="Top 15 Most Attractive Stocks Found in Current Run",
        color_continuous_scale=px.colors.sequential.Darkmint
    )
    
    fig.update_layout(xaxis_title="Stock Ticker", yaxis_title="Score (Higher = More Undervalued)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Export options
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Download Data as CSV File", data=csv, file_name="undervalued_stocks_screener.csv", mime="text/csv")
else:
    st.error("Failed to fetch fresh data from the web pool. Please refresh the page to retry.")
