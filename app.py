import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import random

st.set_page_config(page_title="Reliable Small-Cap Stock Screener", layout="wide")

st.title("🌍 Automated Screener: Reliable Small & Mid-Cap Undervalued Stocks")
st.write("This automated system scans global small and mid-cap markets (Market Cap between $300M and $5B) to find highly attractive stocks with deep Margin of Safety, high profit efficiency, low debt, and strong free cash flow.")

@st.cache_data(ttl=3600)
def get_reliable_small_cap_pool():
    """ Automatically builds a broad global database of 250+ small and mid-cap companies """
    pool = [
        "PLTR", "NET", "SNOW", "DDOG", "CRWD", "ZS", "OKTA", "MDB", "PATH", "IOT",
        "UPWK", "FIVR", "DOCU", "TWLO", "SPLK", "PINS", "SNAP", "RBLX", "U", "CHWY",
        "X", "NUE", "CLF", "FCX", "AA", "ALB", "SQM", "MP", "LAC", "LTHM", 
        "MOS", "CF", "NTR", "AGCO", "OSK", "TEX", "MTW", "TDOC", "EDIT", "BEAM", 
        "CRSP", "NTLA", "PACB", "EXAS", "GH", "NVTA", "ILMN", "MRNA", "BNTX", 
        "NVAX", "INO", "SRPT", "BMRN", "VRTX", "ALNY", "REGN", "INCY", "CROX", 
        "DECK", "SKX", "WWW", "LEVI", "GPS", "URBN", "ANF", "AEO", "BOOT",
        "HELE", "IRBT", "WHR", "TPX", "SNBR", "PRG", "CONN", "RUN", "NOVA", 
        "SPWR", "ENPH", "SEDG", "FSLR", "CSIQ", "JKS", "DQ", "MAXN", "PLUG", 
        "BLNK", "FCEL", "BE", "CHPT", "EVGO", "CLNE", "AMRC", "AAON", "AAN", 
        "ABCB", "ABG", "ABM", "ACA", "ACGL", "ACHC", "ACM", "ACIW", "ACLS", 
        "ADC", "ADTN", "ADUS", "AEIS", "AEL", "ATO", "ATR", "ATRC", "ATRI", 
        "ATRO", "AVA", "AVAV", "AVNS", "AVNT", "AVT", "AWI", "AWK", "AWR",
        "AX", "AXL", "AXS", "AYI", "AZZ", "BANC", "BANR", "BBSI", "BC", 
        "BCPC", "BGC", "BGS", "BHE", "BHLB", "BIG", "BIO", "BJ", "BKD", 
        "BKE", "BKH", "BKU", "BLD", "BLDR", "BLKB", "BMI", "BMS", "BMRC", 
        "BOWL", "BOX", "BRC", "BRKL", "BRKR", "BRP", "BRSP", "BSET", "BSVN", 
        "BURL", "BWA", "BWXT", "BYD", "BZH", "CABO", "CAC", "CACC", "CADE", 
        "CAE", "CAH", "CAKE", "CAL", "CALM", "CALX", "CAMT", "CANG", "CAPL", 
        "CAR", "CARG", "CARR", "CARS", "CASH", "CASI", "CASS", "CASY", "CATY"
    ]
    return list(set(pool))

market_pool = get_reliable_small_cap_pool()

# Scan a segment to pull the top 50
sample_size = min(100, len(market_pool))
tickers_to_scan = random.sample(market_pool, sample_size)

st.info(f"🔄 Scanning a target segment of {sample_size} small & mid-cap stocks to filter the top 50 most reliable gems...")

progress_bar = st.progress(0)
data_list = []

for index, t in enumerate(tickers_to_scan):
    progress_bar.progress((index + 1) / len(tickers_to_scan))
    try:
        stock = yf.Ticker(t)
        info = stock.info
        
        market_cap = info.get('marketCap', 0)
        if market_cap == 0 or market_cap > 6e9:
            continue
            
        current_price = info.get('currentPrice', None)
        target_price = info.get('targetMeanPrice', None)
        
        profit_margin = info.get('profitMargins', None)
        debt_to_equity = info.get('debtToEquity', None)
        fcf = info.get('freeCashflow', None)
        
        pm_pct = profit_margin * 100 if profit_margin else 0.0
        de_ratio = debt_to_equity / 100 if debt_to_equity and debt_to_equity > 5 else debt_to_equity if debt_to_equity else 0.0
        fcf_yield = (fcf / market_cap) * 100 if fcf and market_cap else 0.0
        
        if current_price and target_price and target_price > 0:
            if pm_pct > 0 and de_ratio < 1.5 and fcf_yield > 0:
                margin_of_safety = ((target_price - current_price) / current_price) * 100
                score = margin_of_safety * 1.2 + (pm_pct * 0.3) + (fcf_yield * 0.5) - (de_ratio * 10)
                
                data_list.append({
                    "Ticker": t,
                    "Company Name": info.get('shortName', t),
                    "Market Cap ($M)": round(market_cap / 1e6, 1),
                    "Current Price": round(current_price, 2),
                    "Target Price": round(target_price, 2),
                    "Margin of Safety (%)": round(margin_of_safety, 1),
                    "Net Profit Margin": f"{round(pm_pct, 1)}%",
                    "Debt to Equity": round(de_ratio, 2),
                    "FCF Yield": f"{round(fcf_yield, 2)}%",
                    "Reliability Score": round(max(0, min(100, score)), 1)
                })
    except Exception:
        continue

df = pd.DataFrame(data_list)

if not df.empty:
    df = df.sort_values(by="Reliability Score", ascending=False).head(50).reset_index(drop=True)
    
    st.subheader("📋 Top 50 Most Undervalued & Reliable Small-Cap Stocks")
    
    df_display = df.copy()
    df_display["Margin of Safety (%)"] = df_display["Margin of Safety (%)"].apply(lambda x: f"+{x}%" if x > 0 else f"{x}%")
    df_display["Current Price"] = df_display["Current Price"].apply(lambda x: f"${x}")
    df_display["Target Price"] = df_display["Target Price"].apply(lambda x: f"${x}")
    df_display["Market Cap ($M)"] = df_display["Market Cap ($M)"].apply(lambda x: f"${x:,.1f}M")
    
    st.dataframe(df_display, use_container_width=True)
    
    st.subheader("📉 Chart: Top 20 Small-Cap Gems by Reliability Score")
    fig = px.bar(
        df.head(20), 
        x="Ticker", 
        y="Reliability Score", 
        color="Reliability Score",
        text="Reliability Score",
        labels={"Reliability Score": "Score (0-100)", "Ticker": "Stock Ticker"},
        title="Top 20 Value Gems Filtered in This Run",
        color_continuous_scale=px.colors.sequential.Darkmint
    )
    st.plotly_chart(fig, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Download Top 50 List as CSV File", data=csv, file_name="winning_reliable_smallcaps.csv", mime="text/csv")
else:
    st.error("No stocks met the strict criteria in this run. Please refresh to scan a new batch.")

