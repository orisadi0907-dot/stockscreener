import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

# הגדרת תצורת העמוד
st.set_page_config(page_title="סורק מניות גלובלי בזמן אמת", layout="wide")

# מנגנון רענון אוטומטי של העמוד בכל 10 דקות
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=600000, key="datarefresh")
except ImportError:
    pass

st.title("📊 סורק מניות מנצחות: יחס שווי שוק מול ערך מקורי")
st.caption("🔄 המערכת מתעדכנת אוטומטית בכל 10 דקות ומחשבת מחדש את דירוג המניות, המחירים ואירועי החדשות בזמן אמת.")

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

@st.cache_data(ttl=600)
def scan_market(symbol_list):
    results = []
    daily_summaries = {}
    
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
                    
                    mcap_billion = round(market_cap / 1e9, 2)
                    bval_billion = round(total_book_value / 1e9, 2)
                    
                    results.append({
                        "סימול": symbol,
                        "שם החברה": name,
                        "סוג חברה": cap_type,
                        "מחיר עדכני": f"${round(last_close, 2):,}",
                        "שווי שוק": f"${mcap_billion:,}B",
                        "ערך בספרים": f"${bval_billion:,}B",
                        "יחס P/B": round(pb_ratio, 2),
                        "שינוי יומי (%)": f"{round(day_change_pct, 2)}%",
                        "_mcap_raw": mcap_billion
                    })
                    
                    # ניתוח חדשות ואירוע משפיע
                    news_list = ticker.news
                    news_summary = "לא אותרו אירועים חריגים ביממה האחרונה."
                    news_time_str = current_date_str
                    impact_tag = "⚪ ניטרלית"
                    
                    if news_list and len(news_list) > 0:
                        first_news = news_list[0]
                        # טיפול במבנה הנתונים המשתנה של yfinance
                        title = first_news.get('title') or first_news.get('content', {}).get('title', '')
                        pub_time = first_news.get('providerPublishTime') or first_news.get('content', {}).get('pubDate')
                        
                        if pub_time:
                            if isinstance(pub_time, (int, float)):
                                event_dt = datetime.fromtimestamp(pub_time, israel_tz)
                            else:
                                event_dt = datetime.now(israel_tz)
                            news_time_str = event_dt.strftime("%d/%m/%Y בשעה %H:%M")
                        
                        if title:
                            # קביעת הערכת השפעה לפי כיוון השינוי היומי או מילות מפתח
                            if day_change_pct >= 0.5:
                                impact_tag = "🟢 לטובה (השפעה חיובית)"
                            elif day_change_pct <= -0.5:
                                impact_tag = "🔴 לרעה (השפעה שלילית)"
                            else:
                                impact_tag = "🟡 ניטרלית / מעורבת"
                                
                            news_summary = f"{title}"

                    direction_text = "עלו" if day_change_pct >= 0 else "ירדו"
                    
                    # בניית ניתוח מובנה ומסודר בנקודות
                    structured_summary = {
                        "date_time": f"{current_date_str} (שעון ישראל: {current_time_str})",
                        "price": f"${round(last_close, 2):,}",
                        "change": f"{direction_text} ב-{abs(round(day_change_pct, 2))}%",
                        "volume": f"{int(volume):,}",
                        "mcap": f"${mcap_billion:,}B",
                        "book": f"${bval_billion:,}B",
                        "pb": round(pb_ratio, 2),
                        "event_title": news_summary,
                        "event_date": news_time_str,
                        "event_impact": impact_tag
                    }
                    daily_summaries[symbol] = structured_summary
        except Exception:
            continue
            
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="_mcap_raw", ascending=False).head(50).reset_index(drop=True)
        df.insert(0, "מיקום בטבלה", range(1, len(df) + 1))
        df = df.drop(columns=["_mcap_raw"])
        
    return df, daily_summaries, current_date_str, current_time_str

with st.spinner("סורק את השוק ומעדכן מחירים, מיקומים וחדשות בזמן אמת..."):
    df_top50, summaries, date_str, time_str = scan_market(tickers)

if not df_top50.empty:
    st.subheader(f"🏆 Top 50 מניות מנצחות (עדכון שעון ישראל: {date_str} | שעה: {time_str})")
    
    # הצגת הטבלה הדינמית
    st.dataframe(df_top50, use_container_width=True)
    
    # הצגת הגרף
    st.subheader("📈 גרף השוואתי: יחס P/B עבור המניות המובילות בטבלה")
    fig, ax = plt.subplots(figsize=(14, 5))
    
    df_chart = df_top50.head(15)
    bars = ax.bar(df_chart["סימול"], df_chart["יחס P/B"], color="#4A7BB0", width=0.45)
    
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
    
    # ניתוח יומי מסודר בנקודות לכל מנייה
    st.subheader(f"📝 ניתוח אירועים ועדכוני מסחר מפורטים ({date_str})")
    for idx, row in df_top50.iterrows():
        symbol = row["סימול"]
        if symbol in summaries:
            s = summaries[symbol]
            
            st.markdown(f"### מיקום #{row['מיקום בטבלה']} - {row['שם החברה']} (`{symbol}`)")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("**📊 נתוני מסחר מעודכנים:**")
                st.markdown(f"* **מחיר עדכני:** {s['price']}")
                st.markdown(f"* **שינוי יומי:** הביצועים {s['change']}")
                st.markdown(f"* **נפח מסחר:** {s['volume']} מניות")
                st.markdown(f"* **שווי שוק מול ערך בספרים:** {s['mcap']} מול {s['book']} (יחס P/B: `{s['pb']}`)")
                
            with col2:
                st.markdown("**📰 אירוע מפתח משפיע (מהימים האחרונים):**")
                st.markdown(f"* **תאריך ושעה מדויקים:** {s['event_date']}")
                st.markdown(f"* **אירוע/דיווח:** {s['event_title']}")
                st.markdown(f"* **הערכת השפעה על המחיר:** {s['event_impact']}")
                
            st.divider()
else:
    st.error("לא נשלפו נתונים. אנא רענן את העמוד.")
