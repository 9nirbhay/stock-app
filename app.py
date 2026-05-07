import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Custom Market Distribution Tool", layout="wide")

st.title("📊 Market Analysis & Probability Dashboard")

# --- DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_historical_data(symbol, years):
    data = yf.download(symbol, period=f"{years}y", interval="1d")
    vix = yf.download("^VIX", period=f"{years}y", interval="1d")['Close']
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    df = data.copy()
    df['Vix'] = vix
    
    # CALCULATIONS
    pivot = (df['High'] + df['Low'] + df['Close']) / 3
    bc = (df['High'] + df['Low']) / 2
    tc = (2 * pivot) - bc
    
    df['CPR_Width_Pct'] = (abs(tc - bc) / pivot) * 100
    df['High_to_low'] = (df['High'] - df['Low']) / df['Open']
    df['OpentoClose'] = (df['Close'] - df['Open']) / df['Open']
    
    return df.dropna()

def get_latest_market_info(symbol):
    data = yf.download(symbol, period="5d", interval="1d")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    last_row = data.iloc[-1]
    last_date = data.index[-1].strftime('%Y-%m-%d')
    
    h, l, c = last_row['High'], last_row['Low'], last_row['Close']
    p = (h + l + c) / 3
    bc = (h + l) / 2
    tc = (2 * p) - bc
    width = (abs(tc - bc) / p) * 100
    return float(width), last_date

# --- DYNAMIC BINNING LOGIC ---
def get_dynamic_dist(series, b_width, b_lower, b_upper, is_range=False):
    # Convert percentages to decimals for calculation
    w = b_width / 100
    low = b_lower / 100
    high = b_upper / 100
    
    if is_range:
        # Range is always positive, start from 0
        bins = list(np.arange(0, high + w, w))
        if bins[-1] < high: bins.append(high)
        bins.append(np.inf)
        
        labels = []
        for i in range(len(bins)-2):
            labels.append(f"{bins[i]*100:.2f}% to {bins[i+1]*100:.2f}%")
        labels.append(f"> {bins[-2]*100:.2f}%")
    else:
        # Standard Move (Open to Close)
        main_bins = list(np.arange(low, high + w, w))
        bins = [-np.inf] + main_bins + [np.inf]
        
        labels = [f"< {main_bins[0]*100:.2f}%"]
        for i in range(len(main_bins)-1):
            labels.append(f"{main_bins[i]*100:.2f}% to {main_bins[i+1]*100:.2f}%")
        labels.append(f"> {main_bins[-1]*100:.2f}%")

    # Cut and count
    d = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
    d.columns = ['Bin', 'Count']
    d['%'] = (d['Count'] / d['Count'].sum() * 100).round(2)
    return d

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("1. Data & Filters")
ticker = st.sidebar.text_input("Stock Ticker", value="^NSEI")
history_years = st.sidebar.slider("Years of History", 1, 15, 10)
c_threshold_pct = st.sidebar.number_input("Filter: CPR Width > %", value=1.0, step=0.1)
vix_threshold = st.sidebar.number_input("Filter: Vix <=", value=20.0, step=0.5)

st.sidebar.header("2. Today's CPR")
cpr_mode = st.sidebar.radio("Input Method", ["Automatic", "Manual"])
if cpr_mode == "Automatic":
    try:
        auto_width, last_day = get_latest_market_info(ticker)
        today_cpr = st.sidebar.number_input("Auto-calculated CPR %", value=auto_width, format="%.4f", disabled=True)
        st.sidebar.success(f"Last Trading Day: {last_day}")
    except:
        today_cpr = st.sidebar.number_input("Input CPR Width %", value=0.50, step=0.05)
else:
    today_cpr = st.sidebar.number_input("Manual CPR Width %", value=0.50, step=0.05, format="%.4f")

st.sidebar.header("3. Custom Binning Settings")
user_width = st.sidebar.number_input("Bin Width %", value=0.25, step=0.05, format="%.2f")
user_lower = st.sidebar.number_input("Lower Bin Limit %", value=-2.0, step=0.25, format="%.2f")
user_upper = st.sidebar.number_input("Upper Bin Limit %", value=2.0, step=0.25, format="%.2f")

# --- APP LOGIC ---
try:
    full_data = get_historical_data(ticker, history_years)
    tab1, tab2 = st.tabs(["📈 Historical Distribution", "🔮 Today's Probability"])

    # --- TAB 1: HISTORICAL ---
    with tab1:
        st.subheader("Historical Distribution Analysis")
        
        # Formulas
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.latex(r"Pivot (P) = \frac{High + Low + Close}{3}")
            st.latex(r"CPR Width (\%) = \frac{|TC - BC|}{P} \times 100")
        with f_col2:
            st.latex(r"Range = \frac{High - Low}{Open}")
            st.latex(r"Move = \frac{Close - Open}{Open}")

        st.divider()

        filtered = full_data[(full_data['CPR_Width_Pct'] > c_threshold_pct) & (full_data['Vix'] <= vix_threshold)]
        st.metric("Matching Days Found", len(filtered))

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Open to Close ({user_width}% steps)**")
            oc_df = get_dynamic_dist(filtered['OpentoClose'], user_width, user_lower, user_upper)
            st.table(oc_df)
            st.plotly_chart(px.bar(oc_df, x='Bin', y='Count', text='%'), use_container_width=True)

        with c2:
            st.write(f"**High to Low Range ({user_width}% steps)**")
            # Range always starts from 0 for readability
            hl_df = get_dynamic_dist(filtered['High_to_low'], user_width, 0, user_upper, is_range=True)
            st.table(hl_df)
            st.plotly_chart(px.bar(hl_df, x='Bin', y='Count', text='%', color_discrete_sequence=['orange']), use_container_width=True)

        with st.expander("📄 View Matching Data Rows"):
            st.dataframe(filtered.sort_index(ascending=False), use_container_width=True)

    # --- TAB 2: PROBABILITY ---
    with tab2:
        st.subheader(f"Predictive Probability (Target CPR: {today_cpr:.4f}%)")
        st.latex(r"P(\text{Event}) = \frac{\text{Historical Matches}}{\text{Total Samples with Similar CPR}}")
        
        buffer = 0.15 
        similar_days = full_data[
            (full_data['CPR_Width_Pct'] >= today_cpr * (1 - buffer)) & 
            (full_data['CPR_Width_Pct'] <= today_cpr * (1 + buffer))
        ]

        if len(similar_days) > 3:
            p_range_1 = (similar_days['High_to_low'] > 0.01).mean() * 100
            p_green = (similar_days['OpentoClose'] > 0).mean() * 100
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Sample Size", f"{len(similar_days)} days")
            m2.metric("Prob. Range > 1%", f"{p_range_1:.1f}%")
            m3.metric("Prob. Green Close", f"{p_green:.1f}%")

            st.divider()
            prob_col1, prob_col2 = st.columns(2)
            with prob_col1:
                st.write("**Move Probability (O to C)**")
                p_oc = get_dynamic_dist(similar_days['OpentoClose'], user_width, user_lower, user_upper)
                st.plotly_chart(px.bar(p_oc, x='Bin', y='Count', text='%'), use_container_width=True)
            with prob_col2:
                st.write("**Range Probability (H to L)**")
                p_hl = get_dynamic_dist(similar_days['High_to_low'], user_width, 0, user_upper, is_range=True)
                st.plotly_chart(px.bar(p_hl, x='Bin', y='Count', text='%', color_discrete_sequence=['orange']), use_container_width=True)
            
            with st.expander("📄 View Similar CPR Days"):
                st.dataframe(similar_days.sort_index(ascending=False), use_container_width=True)
        else:
            st.warning("Insufficient historical data for this CPR value.")

except Exception as e:
    st.error(f"Error: {e}")
