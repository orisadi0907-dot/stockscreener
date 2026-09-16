import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

# הגדרת תצורת העמוד
st.set_page_config(page_title="סורק מניות גלובלי בזמן אמת", layout="wide")

# מנגנון רענון אוטומטי של העמוד בכל 10 דקות (600,000 מילי-שניות)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=600000, key="datarefresh")
except ImportError:
    pass

st.title("📊 סורק מניות מנצחות: יחס שווי שוק מול ערך מקורי")
st.caption("🔄 המערכת מתעדכנת אוטומטית בכל 10 דקות ומחשבת מחדש את דירוג המניות והמחירים בזמן אמת.")

# רשימת מניות מגוונת (גדולות, בינוניות וקטנות)
tickers = [
    # Mega & Large Caps
    "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "JPM", "BAC", "WFC", "C",
    # Mid Caps
    "JXN", "BHF", "GNW", "NWLI", "MET", "PRU", "MFC", "LNC", "AEL", "VOYA", "SLF", "GL", "PRI",
    "PBR", "VALE", "AIG", "HIG", "ALL", "CB", "TRV", "STLA", "FCX", "NUE", "CLF",
    # Small & Micro Caps
    "INSW", "DAC", "GSL", "SBLK", "GNK", "ARCH", "AMR", "CEIX", "ARLP", "FLNG",
    "JAKK", "BBW", "HVT", "VIR", "SXC", "BXC", "PLAB", "WIRE", "PRDO", "MHO",
    "CCS", "TPH", "GRBK", "VHI", "GENC", "ZEUS", "BOOT", "CAL", "FL", "BHE"
]

# שמירה בזיכרון מטמון ל-10 דקות בלבד (ttl=600)
@st.cache_data(ttl=600)
def scan_market(symbol_list):
    results = []
    daily_summaries = {}
    
    # הגדרת אזור זמן ישראל המדויק
    israel_tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(israel_tz)
    current_date_str = now.strftime("%d/%m/%Y")
    current_time_str = now.strftime("%H:%M:%S")
    
    for symbol in symbol_list:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="5d")
            
            market_cap = info.get("marketCap")
            book_value = info.get("bookValue")
            shares = info.get("sharesOutstanding")
            name = info.get("shortName", symbol)
            
            if market_cap and book_value and shares and not hist.empty:
                total_book_value = book_value * shares
                
                # סינון: רק מניות שבהן שווי השוק עולה על הערך בספרים
                if market_cap > total_book_value and total_book_value > 0:
                    pb_ratio = market_cap / total_book_value
                    
                    last_close = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else last_close
                    day_change_pct = ((last_close - prev_close) / prev_close) * 100
                    volume = hist['Volume'].iloc[-1]
                    
                    if market_cap >= 10e9:
                        cap_type = "Large Cap"
                    elif market_cap >= 2e9:
                        cap_type = "Mid Cap"
                    else:
                        cap_type = "Small/Micro Cap"
                    
                    results.append({
                        "סימול": symbol,
                        "שם החברה": name,
                        "סוג חברה": cap_type,
                        "מחיר עדכני ($)": round(last_close, 2),
                        "שווי שוק ($B)": round(market_cap / 1e9, 2),
                        "ערך בספרים ($B)": round(total_book_value / 1e9, 2),
                        "יחס P/B": round(pb_ratio, 2),
                        "שינוי יומי (%)": round(day_change_pct, 2)
                    })
                    
                    direction = "עלה" if day_change_pct >= 0 else "ירד"
                    summary_text = (
                        f"בתאריך **{current_date_str}** (עדכון שעון ישראל: {current_time_str}), מניית **{name} ({symbol})** נסחרה במחיר עדכני של **${round(last_close, 2)}**. "
                        f"מחיר המנייה **{direction} ב-{abs(round(day_change_pct, 2))}%** לעומת מחיר הסגירה הקודם, עם נפח מסחר של **{int(volume):,}** מניות. "
                        f"נכון לרגע זה, שווי השוק עומד על **${round(market_cap / 1e9, 2)}B** לעומת ערך מקורי/מאזני בספרים של **${round(total_book_value / 1e9, 2)}B** (יחס P/B של **{round(pb_ratio, 2)}**)."
                    )
                    daily_summaries[symbol] = summary_text
        except Exception:
            continue
            
    df = pd.DataFrame(results)
    if not df.empty:
        # מיון מחדש לפי שווי השוק העדכני להיום
        df = df.sort_values(by="שווי שוק ($B)", ascending=False).head(50).reset_index(drop=True)
        # הוספת עמודת מיקום עדכנית
        df.insert(0, "מיקום בטבלה", range(1, len(df) + 1))
        
    return df, daily_summaries, current_date_str, current_time_str

with st.spinner("סורק את השוק ומעדכן מחירים ומיקומים בזמן אמת..."):
    df_top50, summaries, date_str, time_str = scan_market(tickers)

if not df_top50.empty:
    st.subheader(f"🏆 Top 50 מניות מנצחות (עדכון שעון ישראל: {date_str} | שעה: {time_str})")
    
    # הצגת הטבלה הדינמית
    st.dataframe(df_top50, use_container_width=True)
    
    # הצגת הגרף בתיאום מלא עם הטבלה
    st.subheader("📈 גרף השוואתי: יחס P/B עבור המניות המובילות בטבלה")
    fig, ax = plt.subplots(figsize=(14, 5))
    
    # לקחת בדיוק את 15 המניות הראשונות בטבלה לפי המיקום שלהן
    df_chart = df_top50.head(15)
    
    bars = ax.bar(df_chart["סימול"], df_chart["יחס P/B"], color="#4A7BB0", width=0.45)
    
    # הדגשת המניה הראשונה (מיקום 1 בטבלה) בירוק
    if len(bars) > 0:
        bars[0].set_color("#72B063")
        
    avg_pb = df_chart["יחס P/B"].mean()
    ax.axhline(y=avg_pb, color="red", linestyle="--", linewidth=1.5, label=f"תמחור ממוצע ({round(avg_pb, 2)})")
    
    ax.set_ylabel("יחס P/B (שווי שוק / ערך מאזני)")
    ax.set_title(f"יחס P/B של 15 המניות המובילות בטבלה - נכון ל-{date_str} בשעה {time_str}")
    ax.legend()
    plt.xticks(rotation=0, fontweight="bold", fontsize=10)
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    
    st.pyplot(fig)
    
    # פירוט יומי מורחב לכל מנייה בטבלה
    st.subheader(f"📝 ניתוח אירועים ועדכון מחירים עבור כל מנייה (נכון ל-{date_str})")
    for idx, row in df_top50.iterrows():
        symbol = row["סימול"]
        if symbol in summaries:
            st.markdown(f"**מיקום #{row['מיקום בטבלה']} - {row['שם החברה']} ({symbol})**")
            st.write(summaries[symbol])
            st.divider()
else:
    st.error("לא נשלפו נתונים. אנא רענן את העמוד.")
