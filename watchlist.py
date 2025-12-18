import streamlit as st
import yfinance as yf
import pandas as pd
from mftool import Mftool
import requests
import urllib3

# --- 1. ROBUST CONNECTION FIX ---
class CustomMftool(Mftool):
    def __init__(self):
        super().__init__()
        self._session.verify = False 
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    mf = CustomMftool()
except Exception as e:
    st.error(f"Connection Error: {e}")
    mf = None

st.set_page_config(page_title="Wealth Watcher", layout="wide")
st.title("📈 Wealth Watcher: Stocks & Mutual Funds")

# --- 2. SIDEBAR ---
st.sidebar.header("Settings")
stock_input = st.sidebar.text_area("Stocks (e.g. AAPL, RELIANCE.NS)", "AAPL, RELIANCE.NS")
mf_input = st.sidebar.text_area("MF Codes (e.g. 118989, 102885)", "118989, 102885")

# --- 3. DATA FETCHING ---
def fetch_stock_data(symbols):
    data = []
    for sym in [s.strip().upper() for s in symbols.split(",") if s.strip()]:
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="2d")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else curr
                change = ((curr - prev) / prev) * 100
                data.append({"Symbol": sym, "Price": f"{curr:.2f}", "Day %": round(change, 2)})
        except: continue
    return pd.DataFrame(data)

def fetch_mf_data(codes):
    data = []
    if not mf: return pd.DataFrame()
    for code in [c.strip() for c in codes.split(",") if c.strip()]:
        try:
            q = mf.get_scheme_quote(code)
            # Find NAV even if the key name changes (case-insensitive search)
            nav_val = q.get('nav') or q.get('last_updated_nav') or "N/A"
            name = q.get('scheme_name', 'Unknown Scheme')
            date = q.get('date', 'N/A')
            
            data.append({"Code": code, "Scheme": name, "NAV": nav_val, "Updated": date})
        except Exception: continue
    return pd.DataFrame(data)

# --- 4. DISPLAY ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("Stocks")
    s_df = fetch_stock_data(stock_input)
    st.dataframe(s_df, use_container_width=True, hide_index=True) if not s_df.empty else st.info("No stock data.")

with c2:
    st.subheader("Mutual Funds")
    m_df = fetch_mf_data(mf_input)
    if not m_df.empty:
        # Displaying with custom formatting
        st.dataframe(m_df, use_container_width=True, hide_index=True)
    else:
        st.warning("MF values not found. Check if codes are correct or AMFI server is busy.")

# Help for finding codes
if st.sidebar.checkbox("Help: Find MF Codes"):
    search = st.text_input("Search Fund Name:")
    if search:
        st.write(mf.get_available_schemes(search))
