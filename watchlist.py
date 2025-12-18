import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import urllib3
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Wealth Watcher Final", layout="wide")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 2. HELPER FUNCTIONS ---
def calculate_perf(df, days):
    """Calculates Point-to-Point return or CAGR, rounded to 2 decimals."""
    if df.empty or len(df) < 2: return None
    
    # Identify price column
    col = 'nav' if 'nav' in df.columns else 'Close'
    
    try:
        curr_val = float(df.iloc[-1][col])
        target_date = df.index[-1] - timedelta(days=days)
        
        # Find closest historical date
        past_data = df[df.index <= target_date]
        if past_data.empty: return None
        
        past_val = float(past_data.iloc[-1][col])
        
        val = 0.0
        if days <= 365:
            val = ((curr_val - past_val) / past_val) * 100
        else:
            years = days / 365.25
            val = (((curr_val / past_val) ** (1 / years)) - 1) * 100
            
        return round(val, 2)
    except:
        return None

def color_returns(val):
    if isinstance(val, (int, float)):
        return f'color: {"green" if val >= 0 else "red"}'
    return None

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=600)
def fetch_mf_perf(codes_str):
    all_rows = []
    code_list = [c.strip() for c in codes_str.split(",") if c.strip()]
    
    for code in code_list:
        try:
            # Direct API call
            url = f"https://api.mfapi.in/mf/{code}"
            response = requests.get(url)
            
            if response.status_code != 200:
                continue
                
            res = response.json()
            if 'data' not in res or not res['data']:
                continue

            # Process Data
            df = pd.DataFrame(res['data'])
            df['date_obj'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
            df.set_index('date_obj', inplace=True)
            df.sort_index(inplace=True) 
            
            days_inc = (df.index[-1] - df.index[0]).days
            
            all_rows.append({
                "Code": code,
                "Scheme": res['meta']['scheme_name'],
                "NAV": round(float(df.iloc[-1]['nav']), 2),
                "1W %": calculate_perf(df, 7),
                "1M %": calculate_perf(df, 30),
                "6M %": calculate_perf(df, 180),
                "1Y %": calculate_perf(df, 365),
                "3Y %": calculate_perf(df, 1095),
                "5Y %": calculate_perf(df, 1825),
                "Inception %": calculate_perf(df, days_inc)
            })
        except Exception:
            continue
            
    return pd.DataFrame(all_rows)

@st.cache_data(ttl=600)
def fetch_stock_perf(symbols_str):
    all_rows = []
    sym_list = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
    
    for sym in sym_list:
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period="max")
            
            if df.empty: continue
                
            days_inc = (df.index[-1] - df.index[0]).days
            
            all_rows.append({
                "Symbol": sym,
                "Price": round(df.iloc[-1]['Close'], 2),
                "1W %": calculate_perf(df, 7),
                "1M %": calculate_perf(df, 30),
                "6M %": calculate_perf(df, 180),
                "1Y %": calculate_perf(df, 365),
                "3Y %": calculate_perf(df, 1095),
                "5Y %": calculate_perf(df, 1825),
                "Inception %": calculate_perf(df, days_inc)
            })
        except Exception:
             continue
             
    return pd.DataFrame(all_rows)

# --- 4. MAIN UI ---
st.title("📈 Wealth Watcher Final")

# SIDEBAR
st.sidebar.title("Controls")
if st.sidebar.button("🔄 REFRESH DATA", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("Your Watchlist")
s_in = st.sidebar.text_area("Stocks (comma separated)", "AAPL, RELIANCE.NS, TSLA")
m_in = st.sidebar.text_area("MF Codes (comma separated)", "118989, 122639")

# --- NEW: STOCK SEARCH TOOL ---
with st.expander("🔍 **Find Stock Symbols (Indian & Global)**", expanded=False):
    col_s_search, col_s_help = st.columns([3, 1])
    with col_s_search:
        stock_query = st.text_input("Enter Company Name (e.g. 'Tata Motors')")
    
    if stock_query:
        try:
            # Yahoo Finance Autocomplete API
            headers = {'User-Agent': 'Mozilla/5.0'}
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={stock_query}&quotesCount=10&newsCount=0"
            r = requests.get(url, headers=headers)
            data = r.json()
            
            if 'quotes' in data and data['quotes']:
                quotes = []
                for q in data['quotes']:
                    # We want to prioritize Indian stocks (.NS or .BO)
                    sym = q.get('symbol', '')
                    name = q.get('shortname', '') or q.get('longname', '')
                    exch = q.get('exchange', '')
                    if sym and name:
                        quotes.append({"Symbol": sym, "Name": name, "Exchange": exch})
                
                if quotes:
                    st.dataframe(pd.DataFrame(quotes), use_container_width=True, hide_index=True)
                    st.success("✅ Copy the 'Symbol' (e.g., TATAMOTORS.NS) into your sidebar.")
                else:
                    st.warning("No matches found.")
            else:
                st.warning("No matches found.")
        except Exception as e:
            st.error(f"Stock search failed: {e}")

# --- MF SEARCH TOOL ---
with st.expander("🔍 **Find Mutual Fund Code (India Only)**", expanded=False):
    mf_query = st.text_input("Enter Fund Name (e.g. 'HDFC Mid Cap')")
    if mf_query:
        try:
            s_url = f"https://api.mfapi.in/mf/search?q={mf_query}"
            s_res = requests.get(s_url).json()
            if s_res:
                s_df = pd.DataFrame(s_res).rename(columns={'schemeCode': 'Code', 'schemeName': 'Name'})
                st.dataframe(s_df, use_container_width=True, hide_index=True)
            else:
                st.warning("No funds found.")
        except Exception as e:
            st.error(f"Search failed: {e}")

st.divider()

# DISPLAY TABLES
perf_cols = ["1W %", "1M %", "6M %", "1Y %", "3Y %", "5Y %", "Inception %"]

st.subheader("📊 Stocks")
df_s = fetch_stock_perf(s_in)
if not df_s.empty:
    st.dataframe(df_s.style.applymap(color_returns, subset=perf_cols).format(precision=2), use_container_width=True, hide_index=True)
else:
    st.info("No stock data found.")

st.subheader("💰 Mutual Funds")
df_m = fetch_mf_perf(m_in)
if not df_m.empty:
    st.dataframe(df_m.style.applymap(color_returns, subset=perf_cols).format(precision=2), use_container_width=True, hide_index=True)
else:
    st.info("No mutual fund data found.")
