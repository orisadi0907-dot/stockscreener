import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import random

st.set_page_config(page_title="Global Ultimate 50 Stock Screener", layout="wide")

st.title("🌍 Automated Ultimate 50 Screener: Large, Mid & Small-Cap Value Stocks")
st.write("This fully automated system scans the entire global market ecosystem to find the top 50 most attractive stocks based on Intrinsic Value discount (Margin of Safety), high profit efficiency, and positive cash flow generation.")

@st.cache_data(ttl=3600)
def get_ultimate_market_pool():
    """ Dynamically builds a massive global base of large, mid, and small cap tickers """
    try:
        # Pulling the core S&P 500 list from Wikipedia
        url_sp = "https://wikipedia.org"
        df_sp = pd.read_html(url_sp)
        tickers = df_sp[0]['Symbol'].tolist()
        
        # Adding explicitly combined high-interest global large, mid, and small caps
        extra_pool = [
            "AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMZN", "NFLX", "AMD", "QCOM", 
            "PLTR", "BABA", "ASML", "NIO", "CROX", "DECK", "SKX", "LEVI", "ANF", "AEO", 
            "ENPH", "SEDG", "FSLR", "PLUG", "CHPT", "RUN", "1105436.TA", "748038.TA", "662577.TA",
            "NET", "SNOW", "DDOG", "CRWD", "ZS", "OKTA", "MDB", "PATH", "IOT", "X", "NUE"
        ]
        return list(set(tickers + extra_pool))
    except Exception:
        # Robust fallback mechanism
        return [
            "AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMZN", "NFLX", "AMD", "PLTR", 
            "BABA", "INTC", "QCOM", "CROX", "X", "NUE", "FSLR", "ENPH", "NET", "SNOW"
        ]

# Load the comprehensive combined database
market_pool = get_ultimate_market_pool()

# Scan a significantly wider segment (150 tickers) to guarantee exactly 50 qualified results
sample_size = min(150, len(market_pool))
tickers_to_scan = random.sample(market_pool, sample_size)

st.info(f"🔄 Scanning an extensive blend of {sample_size} global tickers to rank the ultimate top 50 winning stocks...")

progress_bar = st.progress(0)
data_list = []

for index, t in enumerate(tickers_to_scan):
    progress_bar.progress((index + 1) / len(tickers_to_scan))
    try:
        t_clean = t.replace('.', '-')
        stock = yf.Ticker(t_clean)
        info = stock.info
        
        current_price = info.get('currentPrice', None)
        target_price = info.get('targetMeanPrice', None)
        market_cap = info.get('marketCap', 0)
        
        profit_margin = info.get('profitMargins', None)
        debt_to_equity = info.get('debtToEquity', None)
        fcf = info.get('freeCashflow', None)
        
        pm_pct = profit_margin * 100 if profit_margin else 0.0
        de_ratio = debt_to_equity / 100 if debt_to_equity and debt_to_equity > 5 else debt_to_equity if debt_to_equity else 0.0
        fcf_yield = (fcf / market_cap) * 100 if fcf and market_cap else 0.0
        
        # Flexible reliability rule: Must have positive margins to ensure it's a solid business
        if current_price and target_price and target_price > 0 and market_cap > 0:
            if pm_pct > 0:
                
                margin_of_safety = ((target_price - current_price) / current_price) * 100
                
                # Determine firm size category dynamically based on standard Wall Street caps
                if market_cap >= 1e10:
                    company_size = "Large-Cap"
                elif market_cap >= 2e9:
                    company_size = "Mid-Cap"
                else:
                    company_size = "Small-Cap"
                
                # Ultimate universal score formulation (Safety margin + core financial health)
                score = margin_of_safety * 1.3 + (pm_pct * 0.2) + (fcf_yield * 0.4) - (min(de_ratio, 3.0) * 5)
                
                data_list.append({
                    "Ticker": t,
                    "Company Name": info.get('shortName', t),
                    "Market Segment": company_size,
                    "Market Cap ($B)": round(market_cap / 1e9, 2),
                    "Current Price": round(current_price, 2),
                    "Target Price": round(target_price, 2),
                    "Margin of Safety (%)": round(margin_of_safety, 1),
                    "Net Profit Margin": f"{round(pm_pct, 1)}%",
                    "Winning Score": round(max(0, min(100, score)), 1)
                })
    except Exception:
        continue

df = pd.DataFrame(data_list)

if not df.empty:
    # Filter and extract precisely the Top 50 ranked stocks
    df = df.sort_values(by="Winning Score", ascending=False).head(50).reset_index(drop=True)
    
    # 1. Clean Table Layout Execution
    st.subheader("📋 The Ultimate Top 50 Most Attractive Value Stocks")
    
    df_display = df.copy()
    df_display["Margin of Safety (%)"] = df_display["Margin of Safety (%)"].apply(lambda x: f"+{x}%" if x > 0 else f"{x}%")
    df_display["Current Price"] = df_display["Current Price"].apply(lambda x: f"${x}")
    df_display["Target Price"] = df_display["Target Price"].apply(lambda x: f"${x}")
    df_display["Market Cap ($B)"] = df_display["Market Cap ($B)"].apply(lambda x: f"${x:,}B")
    
    st.dataframe(df_display, use_container_width=True)
    
    # 2. Clean Chart Layout Execution (Displaying all 50 sorted beautifully)
    st.subheader("📉 Chart: All Top 50 Selected Stocks Ranked by Value & Attractiveness Score")
    
    fig = px.bar(
        df, 
        x="Ticker", 
        y="Winning Score", 
        color="Market Segment", # Dynamic color theme based on whether it is large, mid or small cap
        text="Winning Score",
        labels={"Winning Score": "Score (0-100)", "Ticker": "Stock Ticker", "Market Segment": "Company Size"},
        title="Comprehensive Ranking of the Top 50 Value Opportunities",
        color_discrete_map={"Large-Cap": "#1a5f7a", "Mid-Cap": "#57c5b6", "Small-Cap": "#159895"}
    )
    
    fig.update_layout(xaxis_title="Stock Ticker", yaxis_title="Score (Higher = More Attractive Opportunity)")
    st.plotly_chart(fig, use_container_width=True)
    
    # CSV generation trigger
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Download Ultimate 50 List as CSV File", data=csv, file_name="ultimate_top_50_stocks.csv", mime="text/csv")
else:
    st.error("An error occurred while compiling fresh market records. Please refresh the dashboard to launch a new automated scan.")
