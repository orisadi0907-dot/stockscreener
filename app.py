import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import streamlit as st  # במידה ואתה משתמש ב-Streamlit להצגה

# התקנה אוטומטית של הספריות הדרושות כדי שיעבוד מכל מקום בלחיצת כפתור אחת
def install_packages():
    required_packages = ["pandas", "yfinance", "matplotlib"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_packages()

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# 1. רשימה מגוונת של מניות (גדולות, בינוניות וקטנות/מיקרו)
tickers = [
    # Mega & Large Caps
    "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "JPM", "BAC", "WFC", "C",
    # Mid Caps
    "JXN", "BHF", "GNW", "NWLI", "MET", "PRU", "MFC", "LNC", "AEL", "VOYA", "SLF", "GL", "PRI",
    "PBR", "VALE", "AIG", "HIG", "ALL", "CB", "TRV", "STLA", "FCX", "NUE", "CLF",
    # Small & Micro Caps (אמינות ופחות מוכרות)
    "INSW", "DAC", "GSL", "SBLK", "GNK", "ARCH", "AMR", "CEIX", "ARLP", "FLNG",
    "JAKK", "BBW", "HVT", "VIR", "SXC", "BXC", "PLAB", "WIRE", "PRDO", "MHO",
    "CCS", "TPH", "GRBK", "VHI", "GENC", "ZEUS", "BOOT", "CAL", "FL", "BHE"
]

def scan_and_analyze_market(symbol_list):
    results = []
    daily_summaries = {}
    
    # בדיקת התאריך הנוכחי של סריקת השוק
    current_date_str = datetime.now().strftime("%d/%m/%Y")
    print(f"--- סורק את השוק בזמן אמת עבור תאריך: {current_date_str} ---")
    
    for symbol in symbol_list:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="5d") # מושך היסטוריה קצרה כדי לחשב את השינוי ביום האחרון
            
            market_cap = info.get("marketCap")
            book_value = info.get("bookValue")
            shares = info.get("sharesOutstanding")
            name = info.get("shortName", symbol)
            
            if market_cap and book_value and shares and not hist.empty:
                total_book_value = book_value * shares
                
                # סינון: רק מניות שבהן שווי השוק עולה על הערך המאזני המקורי
                if market_cap > total_book_value and total_book_value > 0:
                    pb_ratio = market_cap / total_book_value
                    
                    # חישוב ביצועי היום האחרון (היום שבו הקוד מורץ)
                    last_close = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else last_close
                    day_change_pct = ((last_close - prev_close) / prev_close) * 100
                    volume = hist['Volume'].iloc[-1]
                    
                    # סיווג סוג המנייה
                    if market_cap >= 10e9:
                        cap_type = "Large Cap"
                    elif market_cap >= 2e9:
                        cap_type = "Mid Cap"
                    else:
                        cap_type = "Small/Micro Cap"
                    
                    results.append({
                        "Ticker": symbol,
                        "Company": name,
                        "Cap Size": cap_type,
                        "Market Cap ($B)": round(market_cap / 1e9, 2),
                        "Book Value ($B)": round(total_book_value / 1e9, 2),
                        "P/B Ratio": round(pb_ratio, 2),
                        "Daily Change (%)": round(day_change_pct, 2)
                    })
                    
                    # ניסוח הפסקה היומית עבור המנייה
                    direction = "עלה" if day_change_pct >= 0 else "ירד"
                    summary_text = (
                        f"בתאריך {current_date_str}, מניית {name} ({symbol}) נסגרה במחיר של ${round(last_close, 2)}. "
                        f"המחיר {direction} ב-{abs(round(day_change_pct, 2))}% לעומת יום המסחר הקודם, עם נפח מסחר של {int(volume):,} מניות. "
                        f"נכון להיום, שווי השוק שלה עומד על ${round(market_cap / 1e9, 2)}B לעומת ערך בספרים של ${round(total_book_value / 1e9, 2)}B (יחס P/B של {round(pb_ratio, 2)})."
                    )
                    daily_summaries[symbol] = summary_text
        except Exception:
            continue
            
    df = pd.DataFrame(results)
    
    # מיון מחדש בזמן אמת לפי שווי השוק העדכני להיום
    df_top50 = df.sort_values(by="Market Cap ($B)", ascending=False).head(50).reset_index(drop=True)
    
    return df_top50, daily_summaries, current_date_str

# הרצת הסריקה
df_top50, summaries, date_str = scan_and_analyze_market(tickers)

# 2. הצגת הטבלה הדינמית
print(f"\n================ 50 המניות המובילות נכון ל-{date_str} ================")
print(df_top50.to_string(index=False))

# 3. יצירת הגרף (בסגנון התמונה)
plt.figure(figsize=(16, 7))

# מיון 15 המניות המובילות בגרף לפי יחס P/B כדי לזהות את האטרקטיביות ביותר
df_chart = df_top50.sort_values(by="P/B Ratio", ascending=True).head(15)

bars = plt.bar(df_chart["Ticker"], df_chart["P/B Ratio"], color="#4A7BB0", width=0.45)

# הדגשת המניה הראשונה בירוק (כמו בתמונה)
if len(bars) > 0:
    bars[0].set_color("#72B063")

# קו תמחור ממוצע באדום
avg_pb = df_chart["P/B Ratio"].mean()
plt.axhline(y=avg_pb, color="red", linestyle="--", linewidth=1.5, label=f"תמחור ממוצע ({round(avg_pb, 2)})")

plt.xticks(rotation=45, ha="right", fontsize=10)
plt.ylabel("שווי החברה ביחס לערך המאזני (P/B Ratio)", fontsize=12)
plt.title(f"סריקת מניות מנצחות נכון ל-{date_str}", fontsize=14, fontweight="bold")
plt.grid(axis="y", linestyle=":", alpha=0.6)
plt.legend()
plt.tight_layout()
plt.show()

# 4. פירוט יומי מורחב לכל מנייה שנכנסה לטבלה
print("\n" + "="*80)
print(f"סיכום אירועי יום המסחר האחרון ({date_str}) עבור כל מנייה בטבלה:")
print("="*80)

for idx, row in df_top50.iterrows():
    symbol = row["Ticker"]
    if symbol in summaries:
        print(f"\n[{idx + 1}] {row['Company']} ({symbol}):")
        print(summaries[symbol])
