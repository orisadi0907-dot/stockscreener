import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import random

# הגדרות תצוגה אוטומטיות בעברית (RTL)
st.set_page_config(page_title="סורק המניות האוטומטי הגלובלי", layout="wide")
st.markdown("""
    <style>
    body, div, p, h1, h2, h3, th, td { direction: RTL; text-align: right; }
    </style>
""", unsafe_allow_html=True)

st.title("🌍 סורק המניות האוטומטי הגלובלי - מניות מנצחות בזמן אמת")
st.write("מערכת עצמאית לחלוטין המושכת מניות מכל רחבי הרשת, מנתחת את נתוני העומק הפיננסיים ומדרגת את הווינריות הגדולות ביותר.")

@st.cache_data(ttl=3600)
def fetch_all_market_tickers_from_web():
    """ פונקציה אוטומטית לחלוטין שמושכת את כל המניות הקיימות ברשת ללא מגע יד אדם """
    try:
        # פנייה אוטומטית לוויקיפדיה כדי למשוך את רשימת חברות הענק מהרשת
        url_sp = "https://wikipedia.org"
        df_sp = pd.read_html(url_sp)[0]
        sp_tickers = df_sp['Symbol'].tolist()
        
        # הרחבה מובנית קבועה לכל המניות המובילות והחמות בעולם (טכנולוגיה, ישראל, אירופה)
        global_pool = [
            "AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMZN", "AVGO", "AMD", "QCOM", 
            "NFLX", "INTC", "PLTR", "BABA", "ASML", "NIO", "1105436.TA", "748038.TA", "662577.TA", 
            "AZN.L", "SHEL.L", "OR.PA", "MC.PA", "SAP.DE", "SIE.DE", "TM", "SONY", "DIS"
        ]
        
        # איחוד כל המניות שמצאנו ברשת לרשימה אחת ענקית ומניעת כפילויות
        total_market = list(set(sp_tickers + global_pool))
        return total_market
    except Exception:
        # במקרה שאין אינטרנט או שהאתר חסום - רשימת גיבוי אוטומטית רחבה
        return ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMZN", "NFLX", "AMD", "INTC", "PLTR", "BABA"]

# שלב 1: משיכת המניות מהרשת מאחורי הקלעים ללא מעורבות המשתמש
all_discovered_tickers = fetch_all_market_tickers_from_web()

# שלב 2: בחירה אקראית חכמה של 40 מניות בכל הרצה כדי לעקוף חסימות API ולשמור על מהירות שיא בטלפון/מחשב
sample_size = min(40, len(all_discovered_tickers))
tickers_to_scan = random.sample(all_discovered_tickers, sample_size)

st.info(f"🔄 המערכת סורקת כעת באופן אוטומטי {sample_size} מניות שנבחרו מתוך מאגר הרשת הרחב...")

# שלב 3: הרצת סורק העומק הפונדמנטלי
progress_bar = st.progress(0)
data_list = []

for index, t in enumerate(tickers_to_scan):
    progress_bar.progress((index + 1) / len(tickers_to_scan))
    try:
        t_clean = t.replace('.', '-') # התאמת פורמטי בורסה ליאהו פיננסים
        stock = yf.Ticker(t_clean)
        info = stock.info
        
        market_cap = info.get('marketCap', None)
        ev = info.get('enterpriseValue', None)
        profit_margin = info.get('profitMargins', None)
        debt_to_equity = info.get('debtToEquity', None)
        rev_growth = info.get('revenueGrowth', None)
        fcf = info.get('freeCashflow', None)
        
        if market_cap and ev:
            ev_to_cap = ev / market_cap
            pm_pct = profit_margin * 100 if profit_margin else 0.0
            rg_pct = rev_growth * 100 if rev_growth else 0.0
            de_ratio = debt_to_equity / 100 if debt_to_equity and debt_to_equity > 5 else debt_to_equity if debt_to_equity else 0.0
            fcf_yield_pct = (fcf / market_cap) * 100 if fcf and market_cap else 0.0
            
            # --- משוואת הציון המשולב המנצח (5 מדדים) ---
            score_ev = max(0, min(100, (1.5 - ev_to_cap) * 100))
            score_pm = max(0, min(100, pm_pct * 2))
            score_de = max(0, min(100, (2.0 - de_ratio) * 50))
            score_rg = max(0, min(100, rg_pct * 3))
            score_fcf = max(0, min(100, fcf_yield_pct * 10))
            
            winning_score = (score_ev * 0.25) + (score_pm * 0.20) + (score_de * 0.15) + (score_rg * 0.20) + (score_fcf * 0.20)
            
            data_list.append({
                "טיקר": t,
                "שם חברה": info.get('shortName', t),
                "שווי שוק ($B)": round(market_cap / 1e9, 2),
                "יחס EV/Market Cap": round(ev_to_cap, 3),
                "שיעור רווח נקי": f"{round(pm_pct, 1)}%",
                "צמיחת הכנסות (שנתי)": f"{round(rg_pct, 1)}%",
                "תשואת תזרים (FCF Yield)": f"{round(fcf_yield_pct, 2)}%",
                "🌟 ציון מנצח משוקלל": round(winning_score, 1)
            })
    except Exception:
        continue # אם מניה מסוימת חסרת נתונים, המערכת מדלגת עליה אוטומטית בלי לעצור את הריצה

# שלב 4: הצגת התוצאות הסופיות למשתמש
df = pd.DataFrame(data_list)

if not df.empty:
    # מיון אוטומטי מהציון הגבוה לנמוך
    df = df.sort_values(by="🌟 ציון מנצח משוקלל", ascending=False).reset_index(drop=True)
    
    st.subheader("📋 טבלת הדירוג האוטומטית - המניות המנצחות של הסבב")
    st.dataframe(df.style.highlight_max(subset=["🌟 ציון מנצח משוקלל"], color="#d4edda"), use_container_width=True)
    
    # הצגת גרף עמודות אינטראקטיבי אוטומטי של ה-15 המובילות
    st.subheader("📉 גרף השוואתי חזותי של המובילות בשוק")
    fig = px.bar(
        df.head(15), 
        x="טיקר", 
        y="🌟 ציון מנצח משוקלל", 
        color="🌟 ציון מנצח משוקלל",
        text="🌟 ציון מנצח משוקלל",
        labels={"🌟 ציון מנצח משוקלל": "ציון המודל (0-100)", "טיקר": "סימול החברה"},
        color_continuous_scale=px.colors.sequential.Viridis
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # אפשרות הורדה לקובץ אקסל/CSV בלחיצה אחת
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 הורד את כל תוצאות הסריקה לקובץ CSV", data=csv, file_name="automatic_winning_stocks.csv", mime="text/csv")
else:
    st.error("לא הצלחנו לקבל נתונים תקינים ברשת כרגע. אנא נסה לרענן את העמוד בעוד מספר רגעים.")