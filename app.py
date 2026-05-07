import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Market Distribution Tool", layout="wide")

st.title("📊 Market Distribution Analysis (Yahoo Finance)")
st.markdown("This tool pulls live data to calculate distributions based on CPR Width and VIX levels.")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("Parameters")
ticker = st.sidebar.text_input("Stock Ticker", value="^NSEI", help="e.g., ^NSEI for Nifty, ^GSPC for S&P500")
vix_ticker = "^VIX"
history_years = st.sidebar.slider("Years of History", 1, 10, 5)

c_threshold = st.sidebar.number_input("C > (CPR Width)", value=0.010, step=0.001, format="%.3f")
vix_threshold = st.sidebar.number_input("Vix <=", value=15.0, step=0.5)

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)  # Refresh every hour
def get_data(symbol, vix_sym, years):
    period = f"{years}y"
    # Fetch Stock Data
    stock = yf.download(symbol, period=period, interval="1d")
    # Fetch VIX Data
    vix = yf.download(vix_sym, period=period, interval="1d")['Close']
    
    # Flatten MultiIndex columns if necessary
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = stock.columns.get_level_values(0)
    
    df = stock.copy()
    df['Vix'] = vix
    
    # --- CALCULATIONS (Matching your Excel Logic) ---
    # Pivot = (H+L+C)/3 | BC = (H+L)/2 | TC = (2*P)-BC
    pivot = (df['High'] + df['Low'] + df['Close']) / 3
    bc = (df['High'] + df['Low']) / 2
    tc = (2 * pivot) - bc
    
    # CPR Width Ratio (C)
    df['CPR_PP'] = abs(tc - bc) / pivot
    
    # Performance Metrics
    df['High_to_low'] = (df['High'] - df['Low']) / df['Open']
    df['OpentoClose'] = (df['Close'] - df['Open']) / df['Open']
    
    return df.dropna()

try:
    data = get_data(ticker, vix_ticker, history_years)
    
    # --- FILTERING ---
    filtered = data[(data['CPR_PP'] > c_threshold) & (data['Vix'] <= vix_threshold)]
    
    # --- BINNING LOGIC ---
    bins = [-np.inf, -0.06, -0.05, -0.04, -0.03, -0.02, -0.01, -0.005, 0, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, np.inf]
    labels = ['-6% or less', '-6% to -5%', '-5% to -4%', '-4% to -3%', '-3% to -2%', '-2% to -1%', 
              '-1% to -0.5%', '-0.5% to 0%', '0% to 0.5%', '0.5% to 1%', '1% to 2%', '2% to 3%', 
              '3% to 4%', '4% to 5%', '5% to 6%', 'More than 6%']

    def get_distribution(series):
        dist = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
        dist.columns = ['Bin', 'Frequency']
        dist['Percentage'] = (dist['Frequency'] / dist['Frequency'].sum() * 100).round(2)
        return dist

    # --- UI LAYOUT ---
    st.metric("Total Trading Days Found", len(filtered))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Open to Close Distribution")
        oc_dist = get_distribution(filtered['OpentoClose'])
        st.table(oc_dist)
        fig_oc = px.bar(oc_dist, x='Bin', y='Frequency', title="Open-to-Close Frequency")
        st.plotly_chart(fig_oc, use_container_width=True)

    with col2:
        st.subheader("High to Low Distribution")
        hl_dist = get_distribution(filtered['High_to_low'])
        st.table(hl_dist)
        fig_hl = px.bar(hl_dist, x='Bin', y='Frequency', title="High-to-Low Frequency", color_discrete_sequence=['orange'])
        st.plotly_chart(fig_hl, use_container_width=True)

    with st.expander("Show Filtered Raw Data"):
        st.dataframe(filtered.sort_index(ascending=False))

except Exception as e:
    st.error(f"Error fetching data: {e}")
