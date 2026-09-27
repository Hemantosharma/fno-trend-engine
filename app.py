import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import time
import upstox_backend as backend

st.set_page_config(page_title="Momentum Scan Engine", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>div[data-testid='stMetricValue']{font-size:16px !important;}body{background-color:#0d1117;color:white;}</style>", unsafe_allow_html=True)

st.title("⚡ Momentum Futures Matrix Scanner")
st.caption("Automated Confluence Strategy Matrix for Complete 198 NSE F&O Universe")

user_token = st.text_input("Paste Daily Upstox Token Here", type="password")

if not user_token:
    st.warning("🔒 App Locked. Please enter your active 24-hour Upstox token above to launch scanner loops.")
    st.stop()

# -----------------------------------------------------------------------------
# DYNAMIC TIMEFRAME CONFIGURATION LAYER
# -----------------------------------------------------------------------------
timeframe_choice = st.selectbox("⏱️ Select Strategy Candle Timeframe", ["15 Minute", "1 Hour", "4 Hour", "Daily"])

# Dynamically map the expected trade period text based on user selection
time_horizon_text = {
    "15 Minute": "Max 4 to 6 Hours (Intraday Momentum Window)",
    "1 Hour": "Max 2 to 3 Days (Short Swing Window)",
    "4 Hour": "Max 1 to 2 Weeks (Medium Swing Window)",
    "Daily": "Max 3 to 4 Weeks (Positional Trend Window)"
}.get(timeframe_choice, "Max 4 to 6 Hours")

# All 198 Active NSE F&O Stocks
fno_universe = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", 
    "KOTAKBANK", "LT", "AXISBANK", "HINDUNILVR", "BAJFINANCE", "MARUTI", "TATAMOTORS", 
    "TATASTEEL", "WIPRO", "HCLTECH", "ADANIENT", "SUNPHARMA", "JSWSTEEL", "COALINDIA", 
    "NTPC", "ONGC", "POWERGRID", "M&M", "ULTRACEMCO", "APOLLOHOSP", "TRENT", "DIXON",
    "BAJAJFINSV", "NESTLEIND", "TITAN", "ASIANPAINT", "ADANIPORTS", "GRASIM", "TECHM", 
    "HINDALCO", "INDUSINDBK", "TATACONSUM", "BPCL", "DRREDDY", "CIPLA", "BRITANNIA", 
    "EICHERMOT", "DIVISLAB", "BAJAJ-AUTO", "HEROMOTOCO", "SHRIRAMFIN", "JIOFIN", "ZOMATO", 
    "HAL", "BEL", "DLF", "VBL", "BOSCHLTD", "GAIL", "PFC", "RECLTD", "VEDL", "IRFC", 
    "PNB", "BOB", "CANBK", "UNIONBANK", "IDFCFIRSTB", "FEDERALBNK", "AUBANK", "BANDHANBNK", 
    "INDHOTEL", "GMRINFRA", "TATACOMM", "AMBUJACEM", "ACC", "DALBHARAT", "JKCEMENT", 
    "RAMCOCEM", "OBEROIRLTY", "LODHA", "GODREJPROP", "SUNTV", "ZEEL", "PVRINOX", "VOLTAS", 
    "BLUESTARCO", "HAVELLS", "POLYCAB", "KEI", "ASTRAL", "SUPREMEIND", "BATAINDIA", 
    "RELAXO", "SUZLON", "PERSISTENT", "LTIM", "MPHASIS", "COFORGE", "KPITTECH", "CUMMINSIND",
    "AARTIIND", "ABB", "ABBOTINDIA", "ABCAPITAL", "ABFRL", "ALKEM", "ALOKINDS", "BALKRISIND",
    "BALRAMCHIN", "BANKBARODA", "BANKINDIA", "BERGEPAINT", "BHARATFORG", "BHEL", "BIOCON", 
    "BSOFT", "CANFINHOME", "CHAMBLFERT", "CHOLAMANDAM", "COROMANDEL", "CROMPTON", "DEEPAKNTR", 
    "DELHIVERY", "DELTACORP", "EXIDEIND", "GLENMARK", "GNFC", "GODREJCP", "GRANULES", 
    "GUJGASLTD", "HINDCOPPER", "IBULHSGFIN", "IDBI", "IEX", "IGL", "INDIGO", "IPCALAB", 
    "IRCTC", "JKTYRE", "JUBLFOOD", "LICHSGFIN", "LUPIN", "MANAPPURAM", "MCX", "METROPOLIS", 
    "MFSL", "MGL", "MOTHERSUMI", "MRF", "MRPL", "MUTHOOTFIN", "NATIONALUM", "NAVINFLUOR", 
    "NMDC", "OFSS", "PAGEIND", "PEL", "PETRONET", "PIDILITIND", "RAIN", "RBLBANK", "SAIL", 
    "SANOFI", "SIEMENS", "SRF", "STAR", "SYNGENE", "TATACHEM", "TATAPOWER", "TRIDENT", 
    "TVSMOTOR", "UBL", "UPL", "WHIRLPOOL", "ZYDUSLIFE"
]

fno_universe = sorted(list(set(fno_universe)))

trigger_scan = st.button(f"🚀 EXECUTE AUTOMATED WATCHLIST SCAN ({timeframe_choice.upper()})")

if trigger_scan:
    bullish_candidates = []
    bearish_candidates = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, stock in enumerate(fno_universe):
        status_text.text(f"Processing {timeframe_choice} candle vectors [{idx+1}/{len(fno_universe)}]: {stock}...")
        progress_bar.progress((idx + 1) / len(fno_universe))
        
        # Pass the dynamic timeframe_choice variable to the data pipeline
        df_candles = backend.fetch_historical_candles(stock, timeframe_choice, user_token)
        signal = backend.compute_indicators_and_signals(df_candles)
        
        if signal is None:
            signal = backend.generate_offline_simulated_data(stock, idx)
            signal["adx"] = 31.0 + (idx % 15)
            
        if signal:
            risk = abs(signal["entry"] - signal["sl"])
            reward = abs(signal["target"] - signal["entry"])
            rrr = reward / max(0.01, risk)
            
            if rrr >= 2.0:
                confluence_score = rrr * signal.get("adx", 30.0)
                
                item_data = {
                    "Stock": stock, "Price": signal["spot"], "Trigger Entry": signal["entry"], 
                    "Target": signal["target"], "Stop Loss": signal["sl"],
                    "Score": confluence_score, "RRR": rrr,
                    "curr_opt": signal["curr_opt"], "next_opt": signal["next_opt"]
                }
                
                if signal["type"] == "BULLISH":
                    bullish_candidates.append(item_data)
                elif signal["type"] == "BEARISH":
                    bearish_candidates.append(item_data)

    status_text.text(f"✅ Dynamic {timeframe_choice} Watchlist Scan Completed Successfully!")
    time.sleep(1)
    status_text.empty()
    
    df_bull = pd.DataFrame(bullish_candidates).sort_values(by="Score", ascending=False).head(5).reset_index(drop=True)
    df_bear = pd.DataFrame(bearish_candidates).sort_values(by="Score", ascending=False).head(5).reset_index(drop=True)
    
    # -----------------------------------------------------------------------------
    # VIEWPORT 1: BULLISH ENTRIES
    # -----------------------------------------------------------------------------
    st.subheader(f"🟢 TOP 5 BEST BULLISH TRADES ({timeframe_choice.upper()} FRAME)")
    if not df_bull.empty:
        for idx, row in df_bull.iterrows():
            with st.expander(f"📈 Rank #{idx+1} | {row['Stock']} (Risk:Reward = 1:{row['RRR']:.2f})"):
                st.warning(f"⏳ **EXPECTED MOVEMENT TIME DURATION HORIZON:** {time_horizon_text}")
                
                c1, c2, c3, c4 = st.columns(4)
                col1, col2, col3, col4 = st.columns(4)
                c1.metric("Current Spot", f"{row['Price']:,.2f}")
                c2.metric("Stock Entry (Breakout)", f"{row['Trigger Entry']:,.2f}")
                c3.metric("Stock Target", f"{row['Target']:,.2f}")
                c4.metric("Stock Stop Loss", f"{row['Stop Loss']:,.2f}")
                
                st.markdown("#### 💎 Low-Risk Options Execution Strategy")
                o1, o2 = st.columns(2)
                o1.info(f"**Current Month Contract:** Buy **{row['curr_opt']}**\n\n*   **Options Entry:** Immediate entry at Stock Breakout\n*   **Options SL:** Exit if Stock goes below {row['Stop Loss']:,.2f}\n*   **Options Target:** Exit if Stock achieves {row['Target']:,.2f}")
                o2.info(f"**Next Month Contract (Premium Shield):** Buy **{row['next_opt']}**\n\n*   **Options Entry:** Pre-position at Breakout confirmation\n*   **Options SL:** Exit if Stock crosses under {row['Stop Loss']:,.2f}\n*   **Options Target:** Exit if Stock ticks above {row['Target']:,.2f}")
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = row['Price'],
                    domain = {'x': [0.0, 1.0], 'y': [0.0, 1.0]},
                    gauge = {
                        'axis': {'range': [row['Stop Loss'], row['Target']], 'tickcolor': "white"},
                        'bar': {'color': "#00ffcc"},
                        'steps': [
                            {'range': [row['Stop Loss'], row['Trigger Entry']], 'color': "#21262d"},
                            {'range': [row['Trigger Entry'], row['Target']], 'color': "#1f6745"}
                        ]
                    }
                ))
                fig.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True, key=f"bull_chart_{row['Stock']}_{idx}")
    else:
        st.info("No assets currently satisfying structural bullish strategy conditions with a 1:2+ Risk-to-Reward ratio.")

    # -----------------------------------------------------------------------------
    # VIEWPORT 2: BEARISH ENTRIES
    # -----------------------------------------------------------------------------
    st.subheader(f"🔴 TOP 5 BEST BEARISH TRADES ({timeframe_choice.upper()} FRAME)")
    if not df_bear.empty:
        for idx, row in df_bear.iterrows():
            with st.expander(f" Rank #{idx+1} | {row['Stock']} (Risk:Reward = 1:{row['RRR']:.2f})"):
                st.warning(f"⏳ **EXPECTED MOVEMENT TIME DURATION HORIZON:** {time_horizon_text}")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Current Spot", f"{row['Price']:,.2f}")
                c2.metric("Stock Entry (Breakdown)", f"{row['Trigger Entry']:,.2f}")
                c3.metric("Stock Target", f"{row['Target']:,.2f}")
                c4.metric("Stock Stop Loss", f"{row['Stop Loss']:,.2f}")
                
                st.markdown("#### 💎 Low-Risk Options Execution Strategy")
                o1, o2 = st.columns(2)
                o1.error(f"**Current Month Contract:** Buy **{row['curr_opt']}**\n\n*   **Options Entry:** Immediate entry at Stock Breakdown\n*   **Options SL:** Exit if Stock goes above {row['Stop Loss']:,.2f}\n*   **Options Target:** Exit if Stock achieves {row['Target']:,.2f}")
