import streamlit as st
import yfinance as yf
import pandas as pd
from mftool import Mftool
import requests
import urllib3

# --- 1. SSL & CONNECTION FIX ---
# This bypasses the HTTPS errors often encountered with AMFI servers.
class CustomMftool(Mftool):
    def __init__(self):
        super().__init__()
        self._session.verify = False 
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize the tool safely
@st.cache_resource
def get_mf_tool():
    try:
        return CustomMftool()
    except Exception as e:
        st.error(f"Mutual Fund API Connection Failed: {e}")
        return None

mf = get_mf_tool()

# --- 2. STREAMLIT UI SETUP ---
st.set_page_config(page_title="Wealth Watcher", layout="wide")
st.title("📈 Wealth Watcher: Stocks & Mutual Funds")

# --- 3. SIDEBAR: SETTINGS & SEARCH ---
st.sidebar.header("Control Panel")

# Refresh Button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# MF Search Tool
st.sidebar.subheader("🔍 Find MF Code")
search_term = st.sidebar.text_input("Type fund name (e.g. 'Axis')")
if search_term and mf:
    res = mf.get_available_schemes(search_term)
    if res:
        st.sidebar.json(res)

st.sidebar.markdown("---")

# Watchlist Inputs
default_stocks = "AAPL, RELIANCE.NS, TSLA"
default_mfs = "118989, 102885"

stock_input = st.sidebar.text_area("Stock Tickers (comma separated)", default_stocks)
mf_input = st.sidebar.text_area("MF Codes (comma separated)", default_mfs)

# --- 4. DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
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
                data.append({
                    "Symbol": sym, 
                    "Price": f"{curr:.2f}", 
                    "Day %": round(change, 2)
                })
        except: continue
    return pd.DataFrame(data)

@st.cache_data(ttl=3600) # Cache MF data for 1 hour (NAV updates daily)
def fetch_mf_data(codes):
    data = []
    if not mf: return pd.DataFrame()
    for code in [c.strip() for c in codes.split(",") if c.strip()]:
        try:
            q = mf.get_scheme_quote(code)
            nav = q.get('nav') or q.get('last_updated_nav') or "N/A"
            data.append({
                "Code": code,
                "Scheme": q.get('scheme_name', 'Unknown'),
                "NAV": nav,
                "Date": q.get('date', 'N/A')
            })
        except: continue
    return pd.DataFrame(data)

# --- 5. MAIN DISPLAY ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Stocks Portfolio")
    df_s = fetch_stock_data(stock_input)
    if not df_s.empty:
        # Standard IF block to avoid DeltaGenerator display issues
        st.dataframe(df_s, use_container_width=True, hide_index=True)
    else:
        st.info("Add stock symbols to begin.")

with col2:
    st.subheader("💰 Mutual Fund NAVs")
    df_m = fetch_mf_data(mf_input)
    if not df_m.empty:
        st.dataframe(df_m, use_container_width=True, hide_index=True)
    else:
        st.info("Add 6-digit MF codes to begin.")

st.markdown("---")
st.caption("Data Sources: Yahoo Finance & AMFI. Symbols ending in .NS are for NSE India.")
