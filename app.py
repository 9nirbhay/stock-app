import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Market Distribution & Probability Tool", layout="wide")

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
    
    # Calculate CPR basis (Raw)
    temp_p = (df['High'] + df['Low'] + df['Close']) / 3
    temp_bc = (df['High'] + df['Low']) / 2
    temp_tc = (2 * temp_p) - temp_bc
    temp_width = (abs(temp_tc - temp_bc) / temp_p) * 100
    
    # SHIFT: Today's CPR is from Yesterday's HLC
    df['CPR_Width_Pct'] = temp_width.shift(1)
    
    # Price Action for the current day
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
    
    return {
        "pivot": float(p),
        "bc": float(bc),
        "tc": float(tc),
        "width": float(width),
        "date": last_date
    }

# --- DYNAMIC BINNING LOGIC ---
def get_dynamic_dist(series, b_width, b_lower, b_upper, is_range=False):
    w, low, high = b_width/100, b_lower/100, b_upper/100
    if is_range:
        bins = list(np.arange(0, high + w, w))
        if bins[-1] < high: bins.append(high)
        bins.append(np.inf)
        labels = [f"{bins[i]*100:.2f}%-{bins[i+1]*100:.2f}%" for i in range(len(bins)-2)] + [f"> {bins[-2]*100:.2f}%"]
    else:
        main_bins = list(np.arange(low, high + w, w))
        bins = [-np.inf] + main_bins + [np.inf]
        labels = [f"< {main_bins[0]*100:.2f}%"] + [f"{main_bins[i]*100:.2f}%-{main_bins[i+1]*100:.2f}%" for i in range(len(main_bins)-1)] + [f"> {main_bins[-1]*100:.2f}%"]

    d = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
    d.columns = ['Bin', 'Count']
    d['%'] = (d['Count'] / d['Count'].sum() * 100).round(2)
    return d

# --- SIDEBAR ---
st.sidebar.header("1. Data & Filters")
ticker = st.sidebar.text_input("Stock Ticker", value="^NSEI")
history_years = st.sidebar.slider("Years of History", 1, 15, 10)
c_threshold_pct = st.sidebar.number_input("Filter: CPR Width > %", value=1.0, step=0.1)
vix_threshold = st.sidebar.number_input("Filter: Vix <=", value=20.0, step=0.5)

st.sidebar.header("2. Today's CPR")
cpr_mode = st.sidebar.radio("Input Method", ["Automatic", "Manual"])

today_levels = None
if cpr_mode == "Automatic":
    try:
        today_levels = get_latest_market_info(ticker)
        today_cpr = st.sidebar.number_input("Auto CPR Width %", value=today_levels['width'], format="%.4f", disabled=True)
        st.sidebar.success(f"Last Close: {today_levels['date']}")
    except:
        today_cpr = st.sidebar.number_input("Manual CPR Width %", value=0.50, step=0.05)
else:
    today_cpr = st.sidebar.number_input("Manual CPR Width %", value=0.50, step=0.05, format="%.4f")

st.sidebar.header("3. Custom Binning")
user_width = st.sidebar.number_input("Bin Width %", value=0.25, step=0.05)
user_lower = st.sidebar.number_input("Lower Limit %", value=-2.0, step=0.25)
user_upper = st.sidebar.number_input("Upper Limit %", value=2.0, step=0.25)

# --- MAIN APP ---
try:
    full_data = get_historical_data(ticker, history_years)
    tab1, tab2 = st.tabs(["📈 Historical Distribution", "🔮 Today's Probability"])

    with tab1:
        st.subheader("Historical Analysis & Formulas")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.latex(r"Pivot (P) = \frac{High + Low + Close}{3}")
            st.latex(r"CPR Width (\%) = \frac{|TC - BC|}{P} \times 100")
        with f_col2:
            st.latex(r"Range = \frac{High - Low}{Open}")
            st.latex(r"Move = \frac{Close - Open}{Open}")
        
        filtered = full_data[(full_data['CPR_Width_Pct'] > c_threshold_pct) & (full_data['Vix'] <= vix_threshold)]
        st.metric("Matching Days Found", len(filtered))

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Open to Close ({user_width}% steps)**")
            st.plotly_chart(px.bar(get_dynamic_dist(filtered['OpentoClose'], user_width, user_lower, user_upper), x='Bin', y='Count', text='%'), use_container_width=True)
        with c2:
            st.write(f"**High to Low Range ({user_width}% steps)**")
            st.plotly_chart(px.bar(get_dynamic_dist(filtered['High_to_low'], user_width, 0, user_upper, is_range=True), x='Bin', y='Count', text='%', color_discrete_sequence=['orange']), use_container_width=True)

    with tab2:
        st.subheader("Today's CPR Levels & Probabilities")
        
        # Display Today's Actual Levels
        if today_levels:
            l1, l2, l3, l4 = st.columns(4)
            l1.metric("TC (Top)", f"{today_levels['tc']:.2f}")
            l2.metric("Pivot (P)", f"{today_levels['pivot']:.2f}")
            l3.metric("BC (Bottom)", f"{today_levels['bc']:.2f}")
            l4.metric("Width %", f"{today_levels['width']:.4f}%")
            st.info(f"Levels based on price action from **{today_levels['date']}**")
        else:
            st.metric("Target CPR Width", f"{today_cpr:.4f}%")
            st.warning("Manual mode: Price levels (TC/BC) are not displayed.")

        st.divider()
        st.markdown("#### Probability Formula")
        st.latex(r"P(\text{Event}) = \frac{\text{Historical Matches}}{\text{Total Samples with Similar CPR}}")
        
        buffer = 0.15 
        similar_days = full_data[(full_data['CPR_Width_Pct'] >= today_cpr * (1 - buffer)) & (full_data['CPR_Width_Pct'] <= today_cpr * (1 + buffer))]

        if len(similar_days) > 3:
            p_range_1 = (similar_days['High_to_low'] > 0.01).mean() * 100
            p_green = (similar_days['OpentoClose'] > 0).mean() * 100
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Sample Size", f"{len(similar_days)} days")
            m2.metric("Prob. Range > 1%", f"{p_range_1:.1f}%")
            m3.metric("Prob. Green Close", f"{p_green:.1f}%")

            prob_col1, prob_col2 = st.columns(2)
            with prob_col1:
                st.write("**Move Probability (O to C)**")
                st.plotly_chart(px.bar(get_dynamic_dist(similar_days['OpentoClose'], user_width, user_lower, user_upper), x='Bin', y='Count', text='%'), use_container_width=True)
            with prob_col2:
                st.write("**Range Probability (H to L)**")
                st.plotly_chart(px.bar(get_dynamic_dist(similar_days['High_to_low'], user_width, 0, user_upper, is_range=True), x='Bin', y='Count', text='%', color_discrete_sequence=['orange']), use_container_width=True)
        else:
            st.warning("Insufficient data for this CPR width.")

except Exception as e:
    st.error(f"Error: {e}")
