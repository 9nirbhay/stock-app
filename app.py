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
st.set_page_config(page_title="Market Stats & Probability", layout="wide")

st.title("📊 Market Analysis Dashboard")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("1. Data Settings")
ticker = st.sidebar.text_input("Stock Ticker", value="^NSEI")
history_years = st.sidebar.slider("Years of History", 1, 15, 10)

st.sidebar.header("2. Filtering Parameters")
c_threshold_pct = st.sidebar.number_input("Filter: C > (CPR Width %)", value=1.0, step=0.1)
vix_threshold = st.sidebar.number_input("Filter: Vix <=", value=20.0, step=0.5)

st.sidebar.header("3. Today's Prediction")
today_cpr = st.sidebar.number_input("Today's Current CPR Width %", value=0.50, step=0.05)

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_data(symbol, years):
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

try:
    full_data = get_data(ticker, history_years)
    
    # Create the Tabs
    tab1, tab2 = st.tabs(["📈 Historical Distribution", "🔮 Today's Probability"])

    # --- TAB 1: HISTORICAL ANALYSIS ---
    with tab1:
        st.subheader("General Distribution (Filtered by Sidebar)")
        filtered = full_data[(full_data['CPR_Width_Pct'] > c_threshold_pct) & (full_data['Vix'] <= vix_threshold)]
        st.metric("Total Days Found", len(filtered))
        
        col1, col2 = st.columns(2)
        bins = [-np.inf, -0.01, -0.005, 0, 0.005, 0.01, np.inf]
        labels = ['<-1%', '-1% to -0.5%', '-0.5% to 0%', '0% to 0.5%', '0.5% to 1%', '>1%']

        def get_dist(series):
            d = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index().reset_index()
            d.columns = ['Bin', 'Count']
            d['%'] = (d['Count'] / d['Count'].sum() * 100).round(1)
            return d

        with col1:
            oc_dist = get_dist(filtered['OpentoClose'])
            st.write("**Open to Close**")
            st.table(oc_dist)
            st.plotly_chart(px.bar(oc_dist, x='Bin', y='Count', text='%'), use_container_width=True)

        with col2:
            hl_dist = get_dist(filtered['High_to_low'])
            st.write("**High to Low**")
            st.table(hl_dist)
            st.plotly_chart(px.bar(hl_dist, x='Bin', y='Count', text='%', color_discrete_sequence=['orange']), use_container_width=True)

    # --- TAB 2: TODAY'S PROBABILITY ---
    with tab2:
        st.subheader(f"Probability Analysis for CPR Width: {today_cpr}%")
        
        # Formula Display
        st.info("💡 **Probability Formula:** $P(\text{Event}) = \frac{\text{Historical Days Matching Event}}{\text{Total Days with Similar CPR}}$")
        
        # Filter for similar CPR days (+/- 15% range)
        buffer = 0.15
        similar_days = full_data[
            (full_data['CPR_Width_Pct'] >= today_cpr * (1 - buffer)) & 
            (full_data['CPR_Width_Pct'] <= today_cpr * (1 + buffer))
        ]

        if len(similar_days) > 0:
            # Probability Stats
            p_range_1 = (similar_days['High_to_low'] > 0.01).mean() * 100
            p_green = (similar_days['OpentoClose'] > 0).mean() * 100
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Historical Sample", f"{len(similar_days)} days")
            m2.metric("Prob. Range > 1%", f"{p_range_1:.1f}%")
            m3.metric("Prob. Green Close", f"{p_green:.1f}%")

            st.divider()
            
            # Probability Distributions for the new tab
            p_col1, p_col2 = st.columns(2)
            
            with p_col1:
                st.markdown("#### Move Probability (Open to Close)")
                p_oc = get_dist(similar_days['OpentoClose'])
                fig_p_oc = px.bar(p_oc, x='Bin', y='Count', text='%', title="Likely Move Today")
                st.plotly_chart(fig_p_oc, use_container_width=True)

            with p_col2:
                st.markdown("#### Range Probability (High to Low)")
                p_hl = get_dist(similar_days['High_to_low'])
                fig_p_hl = px.bar(p_hl, x='Bin', y='Count', text='%', title="Likely Range Today", color_discrete_sequence=['orange'])
                st.plotly_chart(fig_p_hl, use_container_width=True)
        else:
            st.error("No historical data found for this CPR width.")

except Exception as e:
    st.error(f"Data Error: {e}")
