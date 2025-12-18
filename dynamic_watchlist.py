import streamlit as st
import requests
import yfinance as yf
import pandas as pd

# -----------------------------
# FUNCTIONS
# -----------------------------
def get_mutual_fund_data(fund_dict):
    """Fetch NAV data for mutual funds from MFAPI."""
    data = []
    for name, code in fund_dict.items():
        try:
            url = f"https://api.mfapi.in/mf/{code}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                json_data = resp.json()
                nav = json_data['data'][0]['nav']
                date = json_data['data'][0]['date']
                data.append({"Name": name, "NAV": float(nav), "Date": date})
            else:
                data.append({"Name": name, "NAV": None, "Date": None})
        except Exception:
            data.append({"Name": name, "NAV": None, "Date": None})
    return pd.DataFrame(data)

def get_stock_data(stock_list):
    """Fetch latest stock prices using yfinance."""
    data = []
    for ticker in stock_list:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                data.append({"Ticker": ticker, "Price": round(price, 2)})
            else:
                data.append({"Ticker": ticker, "Price": None})
        except Exception:
            data.append({"Ticker": ticker, "Price": None})
    return pd.DataFrame(data)

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Dynamic Mutual Funds & Stocks Watchlist", layout="wide")
st.title("📊 Dynamic Mutual Funds & Stocks Watchlist")

# Initialize session state
if "mutual_funds" not in st.session_state:
    st.session_state.mutual_funds = {
        "SBI Bluechip Fund": "118834",
        "Axis Growth Opportunities": "120503"
    }

if "stocks" not in st.session_state:
    st.session_state.stocks = ["TCS.NS", "INFY.NS", "RELIANCE.NS"]

# -----------------------------
# MUTUAL FUNDS SECTION
# -----------------------------
st.subheader("Mutual Funds")

# Add new mutual fund
with st.expander("➕ Add Mutual Fund"):
    mf_name = st.text_input("Fund Name")
    mf_code = st.text_input("MFAPI Fund Code (e.g., 118834)")
    if st.button("Add Fund"):
        if mf_name and mf_code:
            st.session_state.mutual_funds[mf_name] = mf_code
            st.success(f"Added {mf_name}")
        else:
            st.error("Please enter both name and code.")

# Display mutual funds table
mf_df = get_mutual_fund_data(st.session_state.mutual_funds)
st.dataframe(mf_df, use_container_width=True)

# Remove mutual fund
remove_mf = st.selectbox("Remove Mutual Fund", [""] + list(st.session_state.mutual_funds.keys()))
if st.button("Remove Selected Fund") and remove_mf:
    st.session_state.mutual_funds.pop(remove_mf, None)
    st.success(f"Removed {remove_mf}")

# -----------------------------
# STOCKS SECTION
# -----------------------------
st.subheader("Stocks")

# Add new stock
with st.expander("➕ Add Stock"):
    stock_symbol = st.text_input("Stock Symbol (e.g., TCS.NS)")
    if st.button("Add Stock"):
        if stock_symbol:
            st.session_state.stocks.append(stock_symbol.upper())
            st.success(f"Added {stock_symbol.upper()}")
        else:
            st.error("Please enter a stock symbol.")

# Display stocks table
stock_df = get_stock_data(st.session_state.stocks)
st.dataframe(stock_df, use_container_width=True)

# Remove stock
remove_stock = st.selectbox("Remove Stock", [""] + st.session_state.stocks)
if st.button("Remove Selected Stock") and remove_stock:
    st.session_state.stocks.remove(remove_stock)
    st.success(f"Removed {remove_stock}")

# -----------------------------
# REFRESH BUTTON
# -----------------------------
if st.button("🔄 Refresh Data"):
    st.experimental_rerun()

st.caption("Data from MFAPI & Yahoo Finance | Built with Streamlit")
