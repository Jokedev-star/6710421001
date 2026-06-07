import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="SET50 Dashboard", layout="wide")
st.title("SET50 Thailand Dashboard")
st.markdown("---")

SET50_TICKERS = {
    "PTT": "PTT.BK", "CPALL": "CPALL.BK", "ADVANC": "ADVANC.BK",
    "AOT": "AOT.BK", "BDMS": "BDMS.BK", "BBL": "BBL.BK",
    "KBANK": "KBANK.BK", "SCB": "SCB.BK", "KTB": "KTB.BK",
    "BH": "BH.BK", "BTS": "BTS.BK", "CK": "CK.BK",
    "CPF": "CPF.BK", "CPN": "CPN.BK", "DELTA": "DELTA.BK",
    "EGCO": "EGCO.BK", "GLOBAL": "GLOBAL.BK", "GPSC": "GPSC.BK",
    "GULF": "GULF.BK", "HMPRO": "HMPRO.BK", "INTUCH": "INTUCH.BK",
    "IVL": "IVL.BK", "JMT": "JMT.BK", "LH": "LH.BK",
    "MINT": "MINT.BK", "MTC": "MTC.BK", "OR": "OR.BK",
    "PTTEP": "PTTEP.BK", "PTTGC": "PTTGC.BK", "RATCH": "RATCH.BK",
    "SAWAD": "SAWAD.BK", "SCGP": "SCGP.BK", "SIRI": "SIRI.BK",
    "SCC": "SCC.BK", "STA": "STA.BK", "STEC": "STEC.BK",
    "TISCO": "TISCO.BK", "TLI": "TLI.BK", "TOA": "TOA.BK",
    "TOP": "TOP.BK", "TPS": "TPS.BK", "TRUE": "TRUE.BK",
    "TTB": "TTB.BK", "TU": "TU.BK", "VGI": "VGI.BK",
    "WHA": "WHA.BK", "BAM": "BAM.BK", "CRC": "CRC.BK",
    "DOHOME": "DOHOME.BK", "COM7": "COM7.BK",
}

@st.cache_data(ttl=3600)
def load_index_data(period="6mo"):
    idx = yf.Ticker("^SET50.BK")
    df = idx.history(period=period)
    info = idx.info
    return df, info

@st.cache_data(ttl=3600)
def load_stocks_data(tickers, period="1mo"):
    data = yf.download(
        [t for t in tickers.values()],
        period=period,
        group_by="ticker",
        progress=False,
    )
    return data

@st.cache_data(ttl=3600)
def load_all_stocks_summary(tickers):
    names = list(tickers.keys())
    symbols = list(tickers.values())
    df_info = []
    for name, sym in zip(names, symbols):
        try:
            t = yf.Ticker(sym)
            info = t.info
            df_info.append({
                "Name": name,
                "Symbol": sym,
                "Price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "Change%": info.get("regularMarketChangePercent"),
                "Volume": info.get("regularMarketVolume"),
                "MarketCap": info.get("marketCap"),
                "PE": info.get("trailingPE"),
            })
        except Exception:
            continue
    return pd.DataFrame(df_info)

st.sidebar.header("Settings")
period = st.sidebar.selectbox("Data Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)

with st.spinner("Loading SET50 data..."):
    try:
        index_df, index_info = load_index_data(period)
        stocks_summary = load_all_stocks_summary(SET50_TICKERS)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

if index_df.empty:
    st.warning("No index data returned. The market may be closed.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
current = index_df["Close"].iloc[-1]
if len(index_df) >= 2:
    prev = index_df["Close"].iloc[-2]
    change = current - prev
    change_pct = (change / prev) * 100
    delta_str = f"{change:.2f} ({change_pct:.2f}%)"
else:
    delta_str = None

col1.metric("SET50 Index", f"{current:.2f}", delta_str)
col2.metric("High (Period)", f"{index_df['High'].max():.2f}")
col3.metric("Low (Period)", f"{index_df['Low'].min():.2f}")
col4.metric("Volume (Period)", f"{index_df['Volume'].sum():,.0f}")

st.markdown("### SET50 Index Chart")
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=index_df.index,
    open=index_df["Open"],
    high=index_df["High"],
    low=index_df["Low"],
    close=index_df["Close"],
    name="SET50",
))
fig.update_layout(height=500, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, width='stretch')

st.markdown("### SET50 Constituents Overview")
if not stocks_summary.empty:
    stocks_summary_display = stocks_summary.copy()
    stocks_summary_display["Price"] = stocks_summary_display["Price"].apply(
        lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A"
    )
    stocks_summary_display["Change%"] = stocks_summary_display["Change%"].apply(
        lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"
    )
    stocks_summary_display["Volume"] = stocks_summary_display["Volume"].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
    )
    stocks_summary_display["MarketCap"] = stocks_summary_display["MarketCap"].apply(
        lambda x: f"{x/1e9:,.2f}B" if pd.notna(x) else "N/A"
    )
    st.dataframe(stocks_summary_display, width='stretch', hide_index=True)

    valid = stocks_summary.dropna(subset=["Change%"])
    if not valid.empty:
        top_gainers = valid.nlargest(5, "Change%")
        top_losers = valid.nsmallest(5, "Change%")

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### Top Gainers")
            fig_gain = px.bar(
                top_gainers, x="Change%", y="Name", orientation="h",
                color="Change%", color_continuous_scale="RdYlGn",
                text_auto=".2f",
            )
            fig_gain.update_layout(height=300, showlegend=False, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_gain, width='stretch')

        with col_right:
            st.markdown("#### Top Losers")
            fig_loss = px.bar(
                top_losers, x="Change%", y="Name", orientation="h",
                color="Change%", color_continuous_scale="RdYlGn_r",
                text_auto=".2f",
            )
            fig_loss.update_layout(height=300, showlegend=False, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_loss, width='stretch')

    if not stocks_summary.dropna(subset=["MarketCap"]).empty:
        st.markdown("#### Market Cap Distribution")
        marketcap_data = stocks_summary.dropna(subset=["MarketCap"]).nlargest(15, "MarketCap")
        fig_pie = px.pie(marketcap_data, values="MarketCap", names="Name", hole=0.4)
        st.plotly_chart(fig_pie, width='stretch')
else:
    st.warning("Could not load individual stock data. The Yahoo Finance API may have rate-limited requests. Please try again later.")

if st.sidebar.button("Clear Cache & Retry"):
    st.cache_data.clear()
    st.rerun()
