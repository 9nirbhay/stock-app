# import streamlit as st
# import yfinance as yf
# import pandas as pd
# import numpy as np
# import plotly.express as px

# # --- PAGE CONFIG ---
# st.set_page_config(page_title="Market Distribution Tool", layout="wide")

# st.title("📊 Market Distribution Analysis (Yahoo Finance)")
# st.markdown("This tool pulls live data to calculate distributions based on CPR Width and VIX levels.")

# # --- SIDEBAR: INPUTS ---
# st.sidebar.header("Parameters")
# ticker = st.sidebar.text_input("Stock Ticker", value="^NSEI", help="e.g., ^NSEI for Nifty, ^GSPC for S&P500")
# vix_ticker = "^VIX"
# history_years = st.sidebar.slider("Years of History", 1, 10, 5)

# c_threshold = st.sidebar.number_input("C > (CPR Width)", value=0.010, step=0.001, format="%.3f")
# vix_threshold = st.sidebar.number_input("Vix <=", value=15.0, step=0.5)

# # --- DATA FETCHING ---
# @st.cache_data(ttl=3600)  # Refresh every hour
# def get_data(symbol, vix_sym, years):
#     period = f"{years}y"
#     # Fetch Stock Data
#     stock = yf.download(symbol, period=period, interval="1d")
#     # Fetch VIX Data
#     vix = yf.download(vix_sym, period=period, interval="1d")['Close']
    
#     # Flatten MultiIndex columns if necessary
#     if isinstance(stock.columns, pd.MultiIndex):
#         stock.columns = stock.columns.get_level_values(0)
    
#     df = stock.copy()
#     df['Vix'] = vix
    
#     # --- CALCULATIONS (Matching your Excel Logic) ---
#     # Pivot = (H+L+C)/3 | BC = (H+L)/2 | TC = (2*P)-BC
#     pivot = (df['High'] + df['Low'] + df['Close']) / 3
#     bc = (df['High'] + df['Low']) / 2
#     tc = (2 * pivot) - bc
    
#     # CPR Width Ratio (C)
#     df['CPR_PP'] = abs(tc - bc) / pivot
    
#     # Performance Metrics
#     df['High_to_low'] = (df['High'] - df['Low']) / df['Open']
#     df['OpentoClose'] = (df['Close'] - df['Open']) / df['Open']
    
#     return df.dropna()

# try:
#     data = get_data(ticker, vix_ticker, history_years)
    
#     # --- FILTERING ---
#     filtered = data[(data['CPR_PP'] > c_threshold) & (data['Vix'] <= vix_threshold)]
    
#     # --- BINNING LOGIC ---
#     bins = [-np.inf, -0.06, -0.05, -0.04, -0.03, -0.02, -0.01, -0.005, 0, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, np.inf]
#     labels = ['-6% or less', '-6% to -5%', '-5% to -4%', '-4% to -3%', '-3% to -2%', '-2% to -1%', 
#               '-1% to -0.5%', '-0.5% to 0%', '0% to 0.5%', '0.5% to 1%', '1% to 2%', '2% to 3%', 
#               '3% to 4%', '4% to 5%', '5% to 6%', 'More than 6%']

#     def get_distribution(series):
#         dist = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
#         dist.columns = ['Bin', 'Frequency']
#         dist['Percentage'] = (dist['Frequency'] / dist['Frequency'].sum() * 100).round(2)
#         return dist

#     # --- UI LAYOUT ---
#     st.metric("Total Trading Days Found", len(filtered))
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.subheader("Open to Close Distribution")
#         oc_dist = get_distribution(filtered['OpentoClose'])
#         st.table(oc_dist)
#         fig_oc = px.bar(oc_dist, x='Bin', y='Frequency', title="Open-to-Close Frequency")
#         st.plotly_chart(fig_oc, use_container_width=True)

#     with col2:
#         st.subheader("High to Low Distribution")
#         hl_dist = get_distribution(filtered['High_to_low'])
#         st.table(hl_dist)
#         fig_hl = px.bar(hl_dist, x='Bin', y='Frequency', title="High-to-Low Frequency", color_discrete_sequence=['orange'])
#         st.plotly_chart(fig_hl, use_container_width=True)

#     with st.expander("Show Filtered Raw Data"):
#         st.dataframe(filtered.sort_index(ascending=False))

# except Exception as e:
#     st.error(f"Error fetching data: {e}")




# import streamlit as st
# import yfinance as yf
# import pandas as pd
# import numpy as np
# import plotly.express as px

# # --- PAGE CONFIG ---
# st.set_page_config(page_title="Market Distribution Tool", layout="wide")

# st.title("📊 Market Distribution Analysis (Yahoo Finance)")

# # --- FORMULA EXPLANATION ---
# with st.expander("ℹ️ View CPR Width Formula"):
#     st.markdown("The **Central Pivot Range (CPR)** consists of three levels:")
#     st.latex(r"Pivot (P) = \frac{High + Low + Close}{3}")
#     st.latex(r"Bottom Central (BC) = \frac{High + Low}{2}")
#     st.latex(r"Top Central (TC) = (2 \times P) - BC")
#     st.markdown("The **CPR Width (C)** is calculated as a percentage of the Pivot price:")
#     st.latex(r"C (\%) = \frac{|TC - BC|}{P} \times 100")

# # --- SIDEBAR: INPUTS ---
# st.sidebar.header("Parameters")
# ticker = st.sidebar.text_input("Stock Ticker", value="^NSEI", help="e.g., ^NSEI for Nifty, ^GSPC for S&P500")
# vix_ticker = "^VIX"
# history_years = st.sidebar.slider("Years of History", 1, 10, 5)

# # Input as Percentage (e.g., 1.0 = 1%)
# c_threshold_pct = st.sidebar.number_input("C > (CPR Width %)", value=1.0, step=0.1, format="%.2f")
# vix_threshold = st.sidebar.number_input("Vix <=", value=15.0, step=0.5)

# # --- DATA FETCHING ---
# @st.cache_data(ttl=3600)
# def get_data(symbol, vix_sym, years):
#     period = f"{years}y"
#     stock = yf.download(symbol, period=period, interval="1d")
#     vix = yf.download(vix_sym, period=period, interval="1d")['Close']
    
#     if isinstance(stock.columns, pd.MultiIndex):
#         stock.columns = stock.columns.get_level_values(0)
    
#     df = stock.copy()
#     df['Vix'] = vix
    
#     # --- CALCULATIONS ---
#     pivot = (df['High'] + df['Low'] + df['Close']) / 3
#     bc = (df['High'] + df['Low']) / 2
#     tc = (2 * pivot) - bc
    
#     # CPR Width as Percentage
#     df['CPR_Width_Pct'] = (abs(tc - bc) / pivot) * 100
    
#     # Performance Metrics
#     df['High_to_low'] = (df['High'] - df['Low']) / df['Open']
#     df['OpentoClose'] = (df['Close'] - df['Open']) / df['Open']
    
#     return df.dropna()

# try:
#     data = get_data(ticker, vix_ticker, history_years)
    
#     # --- FILTERING ---
#     # Compare against the percentage input directly
#     filtered = data[(data['CPR_Width_Pct'] > c_threshold_pct) & (data['Vix'] <= vix_threshold)]
    
#     # --- BINNING LOGIC ---
#     bins = [-np.inf, -0.06, -0.05, -0.04, -0.03, -0.02, -0.01, -0.005, 0, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, np.inf]
#     labels = ['-6% or less', '-6% to -5%', '-5% to -4%', '-4% to -3%', '-3% to -2%', '-2% to -1%', 
#               '-1% to -0.5%', '-0.5% to 0%', '0% to 0.5%', '0.5% to 1%', '1% to 2%', '2% to 3%', 
#               '3% to 4%', '4% to 5%', '5% to 6%', 'More than 6%']

#     def get_distribution(series):
#         dist = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
#         dist.columns = ['Bin', 'Frequency']
#         dist['Percentage'] = (dist['Frequency'] / dist['Frequency'].sum() * 100).round(2)
#         return dist

#     # --- UI LAYOUT ---
#     st.metric("Total Trading Days Found", len(filtered))
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.subheader("Open to Close Distribution")
#         oc_dist = get_distribution(filtered['OpentoClose'])
#         st.table(oc_dist)
#         fig_oc = px.bar(oc_dist, x='Bin', y='Frequency', title="Open-to-Close Frequency")
#         st.plotly_chart(fig_oc, use_container_width=True)

#     with col2:
#         st.subheader("High to Low Distribution")
#         hl_dist = get_distribution(filtered['High_to_low'])
#         st.table(hl_dist)
#         fig_hl = px.bar(hl_dist, x='Bin', y='Frequency', title="High-to-Low Frequency", color_discrete_sequence=['orange'])
#         st.plotly_chart(fig_hl, use_container_width=True)

#     with st.expander("Show Filtered Raw Data"):
#         # Formatting for display
#         display_df = filtered.copy().sort_index(ascending=False)
#         st.dataframe(display_df)

# except Exception as e:
#     st.error(f"Error fetching data: {e}")



import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Market Probability Dashboard", layout="wide")

st.title("📊 Market Stats & Probability Analysis")

# --- FORMULA EXPLANATION ---
with st.expander("ℹ️ View Formulas & Probability Logic"):
    st.markdown("### 1. CPR Formulas")
    st.latex(r"Pivot (P) = \frac{High + Low + Close}{3}")
    st.latex(r"CPR Width (C \%) = \frac{|TC - BC|}{P} \times 100")
    
    st.markdown("### 2. Probability Distribution Logic")
    st.markdown("""
    The probability is calculated by filtering historical days where the CPR width was within **±10%** of today's value.
    """)
    st.latex(r"P(\text{Event} | C_{today}) = \frac{\text{Historical days matching event}}{\text{Total days with similar CPR width}}")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("1. Historical Context")
ticker = st.sidebar.text_input("Stock Ticker", value="^NSEI")
history_years = st.sidebar.slider("Years of History", 1, 15, 10)

st.sidebar.header("2. Today's CPR Context")
# User inputs today's calculated CPR width to see probabilities
today_cpr = st.sidebar.number_input("Today's CPR Width %", value=0.50, step=0.05, format="%.2f")
c_range_buffer = 0.10 # Look at days within 10% of today's CPR

st.sidebar.header("3. Global Filters")
vix_threshold = st.sidebar.number_input("Vix Max Limit", value=20.0, step=0.5)

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_data(symbol, years):
    data = yf.download(symbol, period=f"{years}y", interval="1d")
    vix = yf.download("^VIX", period=f"{years}y", interval="1d")['Close']
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    df = data.copy()
    df['Vix'] = vix
    
    # Calculations
    pivot = (df['High'] + df['Low'] + df['Close']) / 3
    bc = (df['High'] + df['Low']) / 2
    tc = (2 * pivot) - bc
    
    df['CPR_Width_Pct'] = (abs(tc - bc) / pivot) * 100
    df['High_to_low'] = (df['High'] - df['Low']) / df['Open']
    df['OpentoClose'] = (df['Close'] - df['Open']) / df['Open']
    
    return df.dropna()

try:
    full_data = get_data(ticker, history_years)
    
    # --- PROBABILITY ANALYSIS FOR TODAY ---
    # Filter days with similar CPR width (+/- buffer)
    lower_bound = today_cpr * (1 - c_range_buffer)
    upper_bound = today_cpr * (1 + c_range_buffer)
    
    similar_days = full_data[
        (full_data['CPR_Width_Pct'] >= lower_bound) & 
        (full_data['CPR_Width_Pct'] <= upper_bound) &
        (full_data['Vix'] <= vix_threshold)
    ]

    st.subheader(f"🔮 Probability Analysis for Today (CPR: {today_cpr}%)")
    
    if len(similar_days) > 5:
        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        
        # Calculate Probabilities
        prob_range_1 = (similar_days['High_to_low'] > 0.01).mean() * 100
        prob_green = (similar_days['OpentoClose'] > 0).mean() * 100
        avg_range = similar_days['High_to_low'].mean() * 100
        prob_big_move = (abs(similar_days['OpentoClose']) > 0.01).mean() * 100

        p_col1.metric("Sample Size", f"{len(similar_days)} days", help="Historical days with similar CPR")
        p_col2.metric("Prob. Range > 1%", f"{prob_range_1:.1f}%")
        p_col3.metric("Prob. Green Close", f"{prob_green:.1f}%")
        p_col4.metric("Avg. Range expected", f"{avg_range:.2f}%")
        
        st.write(f"**Insight:** Out of {len(similar_days)} days where CPR was around {today_cpr}%, {prob_range_1:.1f}% of them resulted in a range larger than 1%.")
    else:
        st.warning("Not enough historical data for this specific CPR width. Try increasing the 'Years of History'.")

    # --- HISTORICAL DISTRIBUTIONS (CHARTS) ---
    st.divider()
    
    # Standard Binning for Charts
    bins = [-np.inf, -0.02, -0.01, -0.005, 0, 0.005, 0.01, 0.02, np.inf]
    labels = ['<-2%', '-2% to -1%', '-1% to -0.5%', '-0.5% to 0%', '0% to 0.5%', '0.5% to 1%', '1% to 2%', '>2%']

    def get_dist(series):
        d = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
        d.columns = ['Bin', 'Frequency']
        d['%'] = (d['Frequency'] / d['Frequency'].sum() * 100).round(1)
        return d

    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### Open to Close Distribution")
        oc_data = get_dist(similar_days['OpentoClose'])
        fig_oc = px.bar(oc_data, x='Bin', y='Frequency', text='%', title="Move Probability")
        st.plotly_chart(fig_oc, use_container_width=True)

    with chart_col2:
        st.markdown("### Range (High to Low) Distribution")
        # Custom bins for Range since range is always positive
        r_bins = [0, 0.005, 0.01, 0.015, 0.02, 0.03, np.inf]
        r_labels = ['0-0.5%', '0.5-1%', '1-1.5%', '1.5-2%', '2-3%', '>3%']
        hl_data = pd.cut(similar_days['High_to_low'], bins=r_bins, labels=r_labels).value_counts().sort_index().reset_index()
        hl_data.columns = ['Bin', 'Frequency']
        hl_data['%'] = (hl_data['Frequency'] / hl_data['Frequency'].sum() * 100).round(1)
        
        fig_hl = px.bar(hl_data, x='Bin', y='Frequency', text='%', title="Range Probability", color_discrete_sequence=['orange'])
        st.plotly_chart(fig_hl, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
