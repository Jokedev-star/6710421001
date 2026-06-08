import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os, time, re
from datetime import datetime, timedelta
from pyvis.network import Network
import networkx as nx

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

def classify_holder_type(name):
    if not name:
        return "unknown"
    name_upper = name.upper()

    government_patterns = [
        "กระทรวง", "กองทุนรวม วายุภักษ์", "สำนักงาน", "กองทุนบำเหน็จ",
        "MINISTRY", "GOVERNMENT", "TREASURY", "FIDF", "Bank of Thailand",
        "กระทรวงการคลัง", "ธนาคารแห่งประเทศไทย",
    ]
    for pat in government_patterns:
        if pat.upper() in name_upper or pat in name:
            return "government"

    if "ไทยเอ็นวีดีอาร์" in name or "THAI NVDR" in name_upper or name_upper == "THAI NVDR COMPANY LIMITED":
        return "nvdr"

    fund_patterns = [
        "กองทุน", " FUND", "FUND ", "VAYUPAK", "กองทุนรวม",
    ]
    for pat in fund_patterns:
        if pat.upper() in name_upper or pat in name:
            return "fund"

    bank_patterns = [
        "ธนาคาร", "BANK", "KBANK", "SCB", "BBL", "KTB", "TISCO", "TCAP", "KKP",
        "UBS", "BNP PARIBAS", "CITI", "CITIBANK", "HSBC", "STATE STREET BANK",
        "BANK OF NEW YORK", "BANK OF SINGAPORE", "MORGAN STANLEY",
    ]
    for pat in bank_patterns:
        if pat in name_upper:
            return "institution"

    insurance_patterns = [
        "ประกัน", "INSURANCE", "TLI", "ไทยประกัน",
    ]
    for pat in insurance_patterns:
        if pat in name_upper or pat in name:
            return "institution"

    coop_patterns = [
        "สหกรณ์", "COOPERATIVE", "ชุมนุมสหกรณ์",
    ]
    for pat in coop_patterns:
        if pat in name_upper or pat in name:
            return "institution"

    company_patterns = [
        "บริษัท", " จำกัด", "CORPORATION", "INC.", "PLC", "LIMITED", "LTD",
        "HOLDINGS", "HOLDING", "PTE.", "PCL", "PUBLIC COMPANY",
    ]
    for pat in company_patterns:
        if pat in name_upper or pat in name:
            return "company"

    nominee_patterns = [
        "NOMINEE", "NOMINEES",
    ]
    for pat in nominee_patterns:
        if pat in name_upper:
            return "institution"

    if name_upper == name and any(c.isalpha() for c in name):
        return "institution"

    return "individual"

def build_shareholder_graph(symbol, sh_data_rows, top_n=10, min_pct=0.0):
    net = Network(height="550px", width="100%", directed=True, bgcolor="#ffffff", font_color="#333333")

    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200, spring_strength=0.01, damping=0.09)

    company_name = SET50_NAMES.get(symbol, symbol)
    net.add_node(
        f"COMPANY_{symbol}",
        label=f"{symbol}\n{company_name[:30]}",
        title=f"<b>{symbol}</b><br>{company_name}",
        size=40,
        color="#1a73e8",
        font={"size": 16, "face": "Arial", "color": "#ffffff"},
        shape="box",
        borderWidth=2,
        borderColor="#0d47a1",
    )

    filtered = [r for r in sh_data_rows if r["Symbol"] == symbol]
    filtered = [r for r in filtered if float(r.get("Ownership %", 0) or 0) >= min_pct]
    filtered = sorted(filtered, key=lambda r: float(r.get("Ownership %", 0) or 0), reverse=True)[:top_n]

    type_colors = {
        "government": "#e74c3c",
        "nvdr": "#9b59b6",
        "fund": "#2ecc71",
        "institution": "#f39c12",
        "company": "#1abc9c",
        "individual": "#95a5a6",
        "unknown": "#7f8c8d",
    }

    for row in filtered:
        holder_name = row.get("Shareholder Name", "Unknown")
        pct = float(row.get("Ownership %", 0) or 0)
        shares = row.get("Shares Held", 0)
        htype = classify_holder_type(holder_name)
        color = type_colors.get(htype, "#7f8c8d")
        hsize = max(10, min(25, pct * 1.5))

        safe_name = re.sub(r'[^\w\s]', '', holder_name)[:40]
        node_id = f"HOLDER_{hash(holder_name) % 10**8}"

        title_text = (
            f"<b>{holder_name}</b><br>"
            f"Type: {htype}<br>"
            f"Shares: {shares:,.0f}<br>"
            f"Ownership: {pct:.2f}%<br>"
            f"As of: {row.get('As of Date', 'N/A')}"
        )

        net.add_node(
            node_id,
            label=safe_name[:25],
            title=title_text,
            size=hsize,
            color=color,
            font={"size": 11, "face": "Arial"},
            shape="ellipse",
            borderWidth=1,
        )

        edge_width = max(1, min(8, pct / 2))
        net.add_edge(
            node_id,
            f"COMPANY_{symbol}",
            value=pct,
            title=f"Ownership: {pct:.2f}%<br>Shares: {shares:,.0f}<br>As of: {row.get('As of Date', 'N/A')}<br>Source: {row.get('Source URL', 'N/A')}",
            width=edge_width,
            color={"color": "#2c3e50", "opacity": 0.7},
            arrowStrikethrough=False,
            smooth={"type": "curvedCW", "roundness": 0.1},
        )

    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true,
        "zoomView": true,
        "dragView": true
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -3000,
          "centralGravity": 0.3,
          "springLength": 200,
          "springConstant": 0.01,
          "damping": 0.09
        },
        "stabilization": {
          "enabled": true,
          "iterations": 100,
          "updateInterval": 25
        }
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "type": "arrow",
            "scaleFactor": 1.2
          }
        }
      }
    }
    """)

    return net

def get_shareholders_for_symbol(symbol, sh_data):
    entry = sh_data.get("data", {}).get(symbol, {})
    if "error" in entry:
        return []
    company_name = SET50_NAMES.get(symbol, symbol)
    book_close = entry.get("bookCloseDate", "")
    as_of = book_close[:10] if len(book_close) >= 10 else "N/A"
    source_url = f"https://www.set.or.th/en/market/product/stock/quote/{symbol}/major-shareholders"
    rows = []
    for holder in entry.get("majorShareholders", [])[:10]:
        rows.append({
            "Symbol": symbol,
            "Company": company_name,
            "Rank": holder.get("sequence"),
            "Shareholder Name": holder.get("name"),
            "Shares Held": holder.get("numberOfShare"),
            "Ownership %": holder.get("percentOfShare"),
            "As of Date": as_of,
            "Source": "Stock Exchange of Thailand (SET)",
            "Source URL": source_url,
        })
    return rows

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
    if not df_shares.empty and "Ownership %" in df_shares.columns:
        avg_ownership = df_shares.groupby("Symbol").apply(
            lambda x: x.nlargest(5, "Ownership %")["Ownership %"].sum()
        ).reset_index(name="Top 5 Ownership %")
        if not avg_ownership.empty:
            avg_ownership = avg_ownership.sort_values("Top 5 Ownership %", ascending=False)
            fig_own = px.bar(
                avg_ownership.head(20), x="Symbol", y="Top 5 Ownership %",
                color="Top 5 Ownership %", color_continuous_scale="Blues",
                text_auto=".1f",
            )
            fig_own.update_layout(xaxis_title="Company", yaxis_title="Top 5 Shareholders Total %", height=400)
            st.plotly_chart(fig_own, width='stretch')

    st.markdown("---")
    st.markdown("#### Shareholder Relationship Graph")
    st.markdown("Visualize the ownership relationship between a selected company and its top shareholders.")

    graph_sym = st.selectbox(
        "Select a company to visualize:",
        sorted(SET50_CONSTITUENTS),
        key="graph_symbol",
    )

    col_controls, col_legend = st.columns([2, 1])

    with col_controls:
        top_n = st.radio("Show:", [5, 10], horizontal=True, index=1, key="graph_topn")
        min_pct = st.slider("Minimum ownership %:", 0.0, 5.0, 0.0, 0.1, key="graph_minpct")

    with col_legend:
        st.markdown("**Node Types:**")
        legend_items = {
            "government": "#e74c3c",
            "nvdr": "#9b59b6",
            "fund": "#2ecc71",
            "institution": "#f39c12",
            "company": "#1abc9c",
            "individual": "#95a5a6",
            "unknown": "#7f8c8d",
        }
        for ltype, lcolor in legend_items.items():
            st.markdown(
                f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{lcolor};margin-right:6px;"></span>'
                f'{ltype}',
                unsafe_allow_html=True,
            )

    rows_for_graph = []
    for sym in SET50_CONSTITUENTS:
        rows_for_graph.extend(get_shareholders_for_symbol(sym, sh_data))

    rows_for_graph_df = pd.DataFrame(rows_for_graph)
    net = build_shareholder_graph(graph_sym, rows_for_graph, top_n=top_n, min_pct=min_pct)

    graph_html = net.generate_html()
    graph_html = graph_html.replace('width="100%"', 'width="100%"').replace('height="550px"', 'height="550px"')
    graph_html = graph_html.replace("</body>", """
    <script>
    document.addEventListener('click', function(e) {
        var target = e.target;
        while (target && target.tagName !== 'DIV') target = target.parentNode;
        if (target && target._nodeId) {
            var input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'selected_node';
            input.value = target._nodeId;
            document.body.appendChild(input);
        }
    });
    </script>
    </body>""")

    st.components.v1.html(graph_html, height=600, scrolling=False)

    st.markdown("**Shareholder Details**")
    detail_rows = rows_for_graph_df[rows_for_graph_df["Symbol"] == graph_sym].copy()
    if not detail_rows.empty:
        detail_display = detail_rows.copy()
        detail_display["Type"] = detail_display["Shareholder Name"].apply(classify_holder_type)
        detail_display["Shares Held"] = detail_display["Shares Held"].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
        )
        detail_display["Ownership %"] = detail_display["Ownership %"].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        )
        st.dataframe(
            detail_display[["Rank", "Shareholder Name", "Type", "Shares Held", "Ownership %", "As of Date"]],
            width='stretch', hide_index=True,
        )

    if sel_symbol != "All":
        st.markdown("#### Node Detail")
        st.info("Click on a node in the graph to see its details (hover tooltip also available).")

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
