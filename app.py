import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

# הגדרת תצורת העמוד
st.set_page_config(page_title="סורק הזדמנויות ומניות בתמחור חסר", layout="wide")

# מנגנון רענון אוטומטי בכל 10 דקות
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=600000, key="datarefresh")
except ImportError:
    pass

st.title("🎯 סורק הזדמנויות: מניות שנסחרות מתחת לשווי האמיתי שלהן")
st.caption("🔄 הסורק מזהה מניות עם פוטנציאל זינוק (פער בין מחיר השוק לשווי המוערך לפי דיווחים) ומעדכן נתונים וחדשות בכל 10 דקות.")

# רשימת מניות מגוונת מורחבת (כוללת חברות סחורות, אנרגיה, תעשייה וחברות קטנות/לא מוכרות)
tickers = [
    # Small & Mid Caps (חברות קטנות/פחות מוכרות עם פוטנציאל תמחור חסר)
    "ARCH", "AMR", "CEIX", "ARLP", "SXC", "INSW", "DAC", "GSL", "SBLK", "GNK",
    "FLNG", "JAKK", "BBW", "HVT", "VIR", "BXC", "PLAB", "WIRE", "PRDO", "MHO",
    "CCS", "TPH", "GRBK", "VHI", "GENC", "ZEUS", "BOOT", "CAL", "FL", "BHE",
    # Large & Mid Caps
    "PBR", "VALE", "STLA", "FCX", "NUE", "CLF", "JXN", "BHF", "GNW", "MET",
    "PRU", "MFC", "LNC", "AEL", "VOYA", "SLF", "AIG", "HIG", "ALL", "TRV",
    "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "JPM", "BAC"
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
            target_price = info.get("targetMeanPrice")  # שווי מוערך לפי דיווחים ואנליסטים
            last_price = hist['Close'].iloc[-1] if not hist.empty else info.get("currentPrice")
            name = info.get("shortName", symbol)
            
            if market_cap and last_price and target_price and not hist.empty:
                # חישוב אחוז הקפיצה המוערך (פוטנציאל רווח)
                upside_pct = ((target_price - last_price) / last_price) * 100
                
                # סינון: מתמקדים במניות שהשווי המוערך שלהן גבוה ממחיר השוק הנוכחי
                if upside_pct > 0:
                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else last_price
                    day_change_pct = ((last_price - prev_close) / prev_close) * 100
                    volume = hist['Volume'].iloc[-1]
                    
                    if market_cap >= 10e9:
                        cap_type = "חברה גדולה (Large Cap)"
                    elif market_cap >= 2e9:
                        cap_type = "חברה בינונית (Mid Cap)"
                    else:
                        cap_type = "חברה קטנה (Small Cap)"
                    
                    mcap_billion = round(market_cap / 1e9, 2)
                    upside_dollar = round(target_price - last_price, 2)
                    
                    results.append({
                        "סימול": symbol,
                        "שם החברה": name,
                        "גודל חברה": cap_type,
                        "מחיר נוכחי": f"${round(last_price, 2):,}",
                        "שווי מוערך (לפי דיווחים)": f"${round(target_price, 2):,}",
                        "פוטנציאל קפיצה (%)": round(upside_pct, 2),
                        "פער דולרי": f"+${upside_dollar:,}",
                        "שינוי יומי (%)": f"{round(day_change_pct, 2)}%",
                        "_upside_raw": upside_pct
                    })
                    
                    # ניתוח חדשות ודיווחים משפיעים
                    news_list = ticker.news
                    news_summary = "לא אותרו דיווחים חריגים ביממה האחרונה."
                    news_time_str = current_date_str
                    impact_tag = "⚪ ניטרלית"
                    
                    if news_list and len(news_list) > 0:
                        first_news = news_list[0]
                        title = first_news.get('title') or first_news.get('content', {}).get('title', '')
                        pub_time = first_news.get('providerPublishTime') or first_news.get('content', {}).get('pubDate')
                        
                        if pub_time:
                            if isinstance(pub_time, (int, float)):
                                event_dt = datetime.fromtimestamp(pub_time, israel_tz)
                            else:
                                event_dt = datetime.now(israel_tz)
                            news_time_str = event_dt.strftime("%d/%m/%Y בשעה %H:%M")
                        
                        if title:
                            if day_change_pct >= 0.5:
                                impact_tag = "🟢 לטובה (תומך בעליית המחיר)"
                            elif day_change_pct <= -0.5:
                                impact_tag = "🔴 לרעה (עיכוב זמני/השפעה שלילית)"
                            else:
                                impact_tag = "🟡 ניטרלית / מעורבת"
                                
                            news_summary = title

                    direction_text = "עלו" if day_change_pct >= 0 else "ירדו"
                    
                    structured_summary = {
                        "price": f"${round(last_price, 2):,}",
                        "target_price": f"${round(target_price, 2):,}",
                        "upside_pct": f"+{round(upside_pct, 2)}%",
                        "upside_dollar": f"+${upside_dollar:,}",
                        "change": f"{direction_text} ב-{abs(round(day_change_pct, 2))}%",
                        "volume": f"{int(volume):,}",
                        "event_title": news_summary,
                        "event_date": news_time_str,
                        "event_impact": impact_tag
                    }
                    daily_summaries[symbol] = structured_summary
        except Exception:
            continue
            
    df = pd.DataFrame(results)
    if not df.empty:
        # מיון מהמנייה עם אחוז הקפיצה הכלכלי הגבוה ביותר להכי נמוך
        df = df.sort_values(by="_upside_raw", ascending=False).head(50).reset_index(drop=True)
        df.insert(0, "דירוג פוטנציאל", range(1, len(df) + 1))
        df = df.drop(columns=["_upside_raw"])
        
    return df, daily_summaries, current_date_str, current_time_str

with st.spinner("סורק את השוק ומחפש מניות בתמחור חסר ופוטנציאל זינוק..."):
    df_top50, summaries, date_str, time_str = scan_market(tickers)

if not df_top50.empty:
    st.subheader(f"🚀 Top מניות בתמחור חסר ופוטנציאל זינוק (עדכון: {date_str} | {time_str})")
    
    st.dataframe(df_top50, use_container_width=True)
    
    # גרף מציג את אחוזי הפוטנציאל (כמה המנייה אמורה לקפוץ)
    st.subheader("📈 גרף השוואתי: אחוזי הקפיצה המוערכים (Upside Potential)")
    fig, ax = plt.subplots(figsize=(14, 5))
    
    df_chart = df_top50.head(15)
    bars = ax.bar(df_chart["סימול"], df_chart["פוטנציאל קפיצה (%)"], color="#2E7D32", width=0.45)
    
    if len(bars) > 0:
        bars[0].set_color("#1B5E20")
        
    avg_upside = df_chart["פוטנציאל קפיצה (%)"].mean()
    ax.axhline(y=avg_upside, color="red", linestyle="--", linewidth=1.5, label=f"פוטנציאל ממוצע ({round(avg_upside, 2)}%)")
    
    ax.set_ylabel("אחוז קפיצה צפוי (%)")
    ax.set_title(f"15 המניות בעלות הפער הגדול ביותר בין מחיר השוק לשווי האמיתי - {date_str}")
    ax.legend()
    plt.xticks(rotation=0, fontweight="bold", fontsize=10)
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    
    st.pyplot(fig)
    
    st.subheader(f"📝 ניתוח עומק, אירועים ודיווחי שוק עבור כל מנייה ({date_str})")
    for idx, row in df_top50.iterrows():
        symbol = row["סימול"]
        if symbol in summaries:
            s = summaries[symbol]
            
            st.markdown(f"### מקום #{row['דירוג פוטנציאל']} - {row['שם החברה']} (`{symbol}`) | {row['גודל חברה']}")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("**🎯 ניתוח פוטנציאל מחיר:**")
                st.markdown(f"* **מחיר נוכחי בשוק:** {s['price']}")
                st.markdown(f"* **שווי ראוי לפי דיווחים:** {s['target_price']}")
                st.markdown(f"* **פער קפיצה מוערך:** **{s['upside_pct']}** ({s['upside_dollar']} למנייה)")
                st.markdown(f"* **שינוי יומי בבורסה:** {s['change']} (נפח: {s['volume']} מניות)")
                
            with col2:
                st.markdown("**📰 אירוע/דיווח משפיע מהזמן האחרון:**")
                st.markdown(f"* **תאריך ושעה מדויקים:** {s['event_date']}")
                st.markdown(f"* **כותרת הדיווח:** {s['event_title']}")
                st.markdown(f"* **הערכת השפעה:** {s['event_impact']}")
                
            st.divider()
else:
    st.error("לא נשלפו נתונים. אנא רענן את העמוד.")
