import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Market Distribution & Probability Tool", layout="wide")

st.title("📊 Market Analysis Dashboard")

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
    today_cpr = st.sidebar.number_input("Input CPR Width %", value=0.50, step=0.05, format="%.4f")

# --- APP LOGIC ---
try:
    full_data = get_historical_data(ticker, history_years)
    tab1, tab2 = st.tabs(["📈 Historical Distribution", "🔮 Today's Probability"])

    # --- TAB 1: HISTORICAL DISTRIBUTION ---
    with tab1:
        st.subheader("Historical Analysis & Formulas")
        
        # Formula Section
        st.markdown("#### Logic & Formulas")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.latex(r"Pivot (P) = \frac{High + Low + Close}{3}")
            st.latex(r"CPR Width (\%) = \frac{|TC - BC|}{P} \times 100")
        with f_col2:
            st.latex(r"Range = \frac{High - Low}{Open}")
            st.latex(r"Move = \frac{Close - Open}{Open}")

        st.divider()

        # Data Filtering
        filtered = full_data[(full_data['CPR_Width_Pct'] > c_threshold_pct) & (full_data['Vix'] <= vix_threshold)]
        st.metric("Matching Days Found", len(filtered))

        # Distributions
        bins = [-np.inf, -0.01, -0.005, 0, 0.005, 0.01, np.inf]
        labels = ['<-1%', '-1% to -0.5%', '-0.5% to 0%', '0% to 0.5%', '0.5% to 1%', '>1%']
        
        def get_dist(series):
            d = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
            d.columns = ['Bin', 'Count']
            d['%'] = (d['Count'] / d['Count'].sum() * 100).round(1)
            return d

        dist_col1, dist_col2 = st.columns(2)
        with dist_col1:
            st.write("**Open to Close Distribution**")
            oc_df = get_dist(filtered['OpentoClose'])
            st.table(oc_df)
            st.plotly_chart(px.bar(oc_df, x='Bin', y='Count', text='%'), use_container_width=True)

        with dist_col2:
            st.write("**High to Low (Range) Distribution**")
            hl_df = get_dist(filtered['High_to_low'])
            st.table(hl_df)
            st.plotly_chart(px.bar(hl_df, x='Bin', y='Count', text='%', color_discrete_sequence=['orange']), use_container_width=True)

        with st.expander("📄 View Matching Data (Filtered Raw Data)"):
            st.dataframe(filtered.sort_index(ascending=False), use_container_width=True)

    # --- TAB 2: TODAY'S PROBABILITY ---
    with tab2:
        st.subheader(f"Predictive Probability (Target CPR: {today_cpr:.4f}%)")
        
        st.markdown("#### Probability Formula")
        st.latex(r"P(\text{Event}) = \frac{\text{Historical Matches}}{\text{Total Samples with Similar CPR}}")
        
        buffer = 0.15 # 15% similarity buffer
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
                st.write("**Outcome Probability (O to C)**")
                st.plotly_chart(px.bar(get_dist(similar_days['OpentoClose']), x='Bin', y='Count', text='%'), use_container_width=True)
            with prob_col2:
                st.write("**Range Probability (H to L)**")
                st.plotly_chart(px.bar(get_dist(similar_days['High_to_low']), x='Bin', y='Count', text='%', color_discrete_sequence=['orange']), use_container_width=True)
            
            with st.expander("📄 View Similar CPR Days"):
                st.dataframe(similar_days.sort_index(ascending=False), use_container_width=True)
        else:
            st.warning("Not enough similar days found in history.")

except Exception as e:
    st.error(f"Error: {e}")
