import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os, time
from datetime import datetime, timedelta

st.set_page_config(page_title="SET50 Dashboard", layout="wide")
st.title("SET50 Thailand Dashboard")
st.markdown("---")

SET50_TICKERS = {
    "DELTA": "DELTA.BK", "ADVANC": "ADVANC.BK", "PTT": "PTT.BK",
    "GULF": "GULF.BK", "AOT": "AOT.BK", "PTTEP": "PTTEP.BK",
    "SCB": "SCB.BK", "CPALL": "CPALL.BK", "KBANK": "KBANK.BK",
    "TRUE": "TRUE.BK", "KTB": "KTB.BK", "BDMS": "BDMS.BK",
    "BBL": "BBL.BK", "CPN": "CPN.BK", "SCC": "SCC.BK",
    "TTB": "TTB.BK", "CPF": "CPF.BK", "OR": "OR.BK",
    "BH": "BH.BK", "MINT": "MINT.BK", "TLI": "TLI.BK",
    "CRC": "CRC.BK", "IVL": "IVL.BK", "GPSC": "GPSC.BK",
    "PTTGC": "PTTGC.BK", "TOP": "TOP.BK", "HMPRO": "HMPRO.BK",
    "BEM": "BEM.BK", "SCGP": "SCGP.BK", "TISCO": "TISCO.BK",
    "AWC": "AWC.BK", "KTC": "KTC.BK", "MTC": "MTC.BK",
    "RATCH": "RATCH.BK", "BJC": "BJC.BK", "EGCO": "EGCO.BK",
    "WHA": "WHA.BK", "TCAP": "TCAP.BK", "KKP": "KKP.BK",
    "BANPU": "BANPU.BK", "COM7": "COM7.BK", "TIDLOR": "TIDLOR.BK",
    "OSP": "OSP.BK", "CCET": "CCET.BK", "TU": "TU.BK",
    "LH": "LH.BK", "CENTEL": "CENTEL.BK", "SAWAD": "SAWAD.BK",
    "CBG": "CBG.BK", "BTS": "BTS.BK",
}

SET50_CONSTITUENTS = [
    "DELTA","ADVANC","PTT","GULF","AOT","PTTEP","SCB","CPALL","KBANK","TRUE",
    "KTB","BDMS","BBL","CPN","SCC","TTB","CPF","OR","BH","MINT",
    "TLI","CRC","IVL","GPSC","PTTGC","TOP","HMPRO","BEM","SCGP","TISCO",
    "AWC","KTC","MTC","RATCH","BJC","EGCO","WHA","TCAP","KKP","BANPU",
    "COM7","TIDLOR","OSP","CCET","TU","LH","CENTEL","SAWAD","CBG","BTS",
]

SET50_NAMES = {
    "DELTA":"Delta Electronics (Thailand)","ADVANC":"Advanced Info Service",
    "PTT":"PTT Public Company Limited","GULF":"Gulf Energy Development",
    "AOT":"Airports of Thailand","PTTEP":"PTT Exploration and Production",
    "SCB":"SCB X Public Company Limited","CPALL":"CP All Public Company Limited",
    "KBANK":"Kasikornbank Public Company Limited","TRUE":"True Corporation",
    "KTB":"Krung Thai Bank","BDMS":"Bangkok Dusit Medical Services",
    "BBL":"Bangkok Bank","CPN":"Central Pattana","SCC":"The Siam Cement",
    "TTB":"TMBThanachart Bank","CPF":"Charoen Pokphand Foods","OR":"PTT Oil and Retail Business",
    "BH":"Bumrungrad International Hospital","MINT":"Minor International",
    "TLI":"Thai Life Insurance","CRC":"Central Retail Corporation","IVL":"Indorama Ventures",
    "GPSC":"Global Power Synergy","PTTGC":"PTT Global Chemical",
    "TOP":"Thai Oil Public Company Limited","HMPRO":"Home Product Center",
    "BEM":"Bangkok Expressway and Metro","SCGP":"SCG Packaging",
    "TISCO":"Tisco Financial Group","AWC":"Asset World Corp",
    "KTC":"Krungthai Card Public Company Limited","MTC":"Muangthai Capital",
    "RATCH":"Ratch Group","BJC":"Berli Jucker","EGCO":"Electricity Generating",
    "WHA":"WHA Corporation","TCAP":"Thanachart Capital","KKP":"Kiatnakin Phatra Bank",
    "BANPU":"Banpu","COM7":"Com Seven","TIDLOR":"Tidlor Holdings",
    "OSP":"Osotspa","CCET":"Cal-Comp Electronics (Thailand)","TU":"Thai Union Group",
    "LH":"Land and Houses","CENTEL":"Central Plaza Hotel","SAWAD":"Srisawad Corporation",
    "CBG":"Carabao Group","BTS":"BTS Group Holdings",
}

@st.cache_data(ttl=3600)
def load_index_data(period="6mo"):
    idx = yf.Ticker("^SET50.BK")
    df = idx.history(period=period)
    info = idx.info
    return df, info

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

@st.cache_data(ttl=86400)
def load_shareholder_data():
    path = os.path.join(os.path.dirname(__file__), 'shareholder_data.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

period = st.sidebar.selectbox("Data Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)

with st.spinner("Loading SET50 index data..."):
    try:
        index_df, index_info = load_index_data(period)
        stocks_summary = load_all_stocks_summary(SET50_TICKERS)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

tab1, tab2, tab3 = st.tabs(["Index Overview", "Shareholder Data", "Top Gainers / Losers"])

with tab1:
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

with tab2:
    st.header("Major Shareholder Data")
    st.markdown("Source: Stock Exchange of Thailand (SET) — Official Major Shareholders Report")

    sh_data = load_shareholder_data()
    if sh_data is None:
        st.error("Shareholder data file not found. Run `python fetch_all_data.py` first.")
        st.stop()

    fetched_at = sh_data.get("fetched_at", "N/A")
    st.caption(f"Data fetched at: {fetched_at} | Source: SET.or.th API")

    all_rows = []
    for sym in SET50_CONSTITUENTS:
        entry = sh_data.get("data", {}).get(sym, {})
        if "error" in entry:
            continue
        company_name = SET50_NAMES.get(sym, sym)
        book_close = entry.get("bookCloseDate", "")
        as_of = book_close[:10] if len(book_close) >= 10 else "N/A"
        source_url = f"https://www.set.or.th/en/market/product/stock/quote/{sym}/major-shareholders"

        note = ""
        if as_of != "N/A":
            try:
                dt = datetime.strptime(as_of, "%Y-%m-%d")
                if (datetime.now() - dt).days > 365:
                    note = f"Data older than 1 year (as of {as_of})"
            except:
                pass

        for holder in entry.get("majorShareholders", [])[:10]:
            all_rows.append({
                "Symbol": sym,
                "Company": company_name,
                "Rank": holder.get("sequence"),
                "Shareholder Name": holder.get("name"),
                "Shares Held": holder.get("numberOfShare"),
                "Ownership %": holder.get("percentOfShare"),
                "As of Date": as_of,
                "Source": "Stock Exchange of Thailand (SET)",
                "Source URL": source_url,
                "Note": note,
                "NVDR": holder.get("isThaiNVDR", False),
            })

    if not all_rows:
        st.warning("No shareholder data available.")
        st.stop()

    df_shares = pd.DataFrame(all_rows)

    col_search, col_sort = st.columns([2, 1])
    with col_search:
        search = st.text_input("Search by symbol or company name", "").upper()
    with col_sort:
        sort_by = st.selectbox("Sort by", ["Symbol", "Rank", "Ownership %", "Company"], index=0)

    if search:
        df_shares = df_shares[
            df_shares["Symbol"].str.contains(search) |
            df_shares["Company"].str.upper().str.contains(search)
        ]

    if sort_by == "Ownership %":
        df_shares = df_shares.sort_values("Ownership %", ascending=False)
    elif sort_by == "Rank":
        df_shares = df_shares.sort_values(["Symbol", "Rank"])
    elif sort_by == "Company":
        df_shares = df_shares.sort_values("Company")
    else:
        df_shares = df_shares.sort_values("Symbol")

    sel_symbol = st.selectbox("Or select a specific company:", ["All"] + sorted(SET50_CONSTITUENTS))
    if sel_symbol != "All":
        df_shares = df_shares[df_shares["Symbol"] == sel_symbol]

    display_df = df_shares.copy()
    display_df["Shares Held"] = display_df["Shares Held"].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
    )
    display_df["Ownership %"] = display_df["Ownership %"].apply(
        lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
    )

    st.dataframe(
        display_df[["Symbol","Company","Rank","Shareholder Name","Shares Held","Ownership %","As of Date","Source","Note"]],
        width='stretch', hide_index=True,
    )

    st.markdown(f"**Showing {len(df_shares)} shareholder records**")

    st.markdown("---")
    st.markdown("#### Ownership Distribution by Company")
    avg_ownership = df_shares.groupby("Symbol").apply(
        lambda x: x.nlargest(5, "Ownership %")["Ownership %"].sum()
    ).reset_index(name="Top 5 Ownership %")
    avg_ownership = avg_ownership.sort_values("Top 5 Ownership %", ascending=False)

    fig_own = px.bar(
        avg_ownership.head(20), x="Symbol", y="Top 5 Ownership %",
        color="Top 5 Ownership %", color_continuous_scale="Blues",
        text_auto=".1f",
    )
    fig_own.update_layout(
        xaxis_title="Company", yaxis_title="Top 5 Shareholders Total %",
        height=400,
    )
    st.plotly_chart(fig_own, width='stretch')

    st.caption("Note: Shareholder names are displayed as registered in the SET system (mostly in Thai). "
               "NVDR (Thai NVDR) indicates shares held through Thai NVDR Company Limited, "
               "which represents foreign investors holding through the non-voting depository receipt program.")

with tab3:
    st.header("Top Gainers & Losers")

    if not stocks_summary.empty:
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
        st.warning("Stock data unavailable.")

if st.sidebar.button("Clear Cache & Retry"):
    st.cache_data.clear()
    st.rerun()
