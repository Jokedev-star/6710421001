import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, re, random
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
def load_all_stocks_summary(tickers):
    names = list(tickers.keys())
    symbols = list(tickers.values())
    df_info = []
    for name, sym in zip(names, symbols):
        try:
            t = yf.Ticker(sym)
            info = t.info
            df_info.append({
                "Name": name, "Symbol": sym,
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
    gov = ["กระทรวง", "กองทุนรวม วายุภักษ์", "สำนักงาน", "กองทุนบำเหน็จ",
           "MINISTRY", "GOVERNMENT", "TREASURY", "FIDF", "Bank of Thailand",
           "กระทรวงการคลัง", "ธนาคารแห่งประเทศไทย"]
    for p in gov:
        if p.upper() in name_upper or p in name:
            return "government"
    if "ไทยเอ็นวีดีอาร์" in name or "THAI NVDR" in name_upper:
        return "nvdr"
    fund = ["กองทุน", " FUND", "FUND ", "VAYUPAK", "กองทุนรวม"]
    for p in fund:
        if p.upper() in name_upper or p in name:
            return "fund"
    bank = ["ธนาคาร", "BANK", "UBS", "BNP PARIBAS", "CITI", "CITIBANK",
            "HSBC", "STATE STREET BANK", "BANK OF NEW YORK", "MORGAN STANLEY"]
    for p in bank:
        if p in name_upper:
            return "institution"
    ins = ["ประกัน", "INSURANCE"]
    for p in ins:
        if p in name_upper or p in name:
            return "institution"
    coop = ["สหกรณ์", "COOPERATIVE", "ชุมนุมสหกรณ์"]
    for p in coop:
        if p in name_upper or p in name:
            return "institution"
    comp = ["บริษัท", " จำกัด", "CORPORATION", "INC.", "PLC", "LIMITED",
            "LTD", "HOLDINGS", "HOLDING", "PTE.", "PCL", "PUBLIC COMPANY"]
    for p in comp:
        if p in name_upper or p in name:
            return "company"
    nom = ["NOMINEE", "NOMINEES"]
    for p in nom:
        if p in name_upper:
            return "institution"
    if name_upper == name and any(c.isalpha() for c in name):
        return "institution"
    return "individual"

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
            "Symbol": symbol, "Company": company_name,
            "Rank": holder.get("sequence"),
            "Shareholder Name": holder.get("name"),
            "Shares Held": holder.get("numberOfShare"),
            "Ownership %": holder.get("percentOfShare"),
            "As of Date": as_of,
            "Source": "Stock Exchange of Thailand (SET)",
            "Source URL": source_url,
        })
    return rows

def make_shareholder_graph_html(nodes, edges):
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)
    return f"""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vis-network@10.0.2/dist/dist/vis-network.min.css"/>
<script src="https://cdn.jsdelivr.net/npm/vis-network@10.0.2/standalone/umd/vis-network.min.js"></script>
<style>
#graph-wrap {{ position:relative; width:100%; background:#0f1923; overflow:hidden; }}
#mynetwork {{ width:100%; height:600px; }}
#tooltip {{
  position:absolute; display:none; background:rgba(15,25,35,0.95); color:#e0e0e0;
  padding:10px 14px; border-radius:8px; font-size:13px; line-height:1.5;
  border:1px solid rgba(255,255,255,0.12); box-shadow:0 4px 20px rgba(0,0,0,0.5);
  pointer-events:none; z-index:999; max-width:320px;
}}
#tooltip b {{ color:#fff; }}
</style>
<div id="graph-wrap">
<div id="mynetwork"></div>
<div id="tooltip"></div>
</div>
<script>
try {{
var nodes = new vis.DataSet({nodes_json});
var edges = new vis.DataSet({edges_json});
var container = document.getElementById('mynetwork');
var options = {{
  nodes: {{
    font: {{ color: '#e0e0e0', face: 'Arial', size: 12 }},
    borderWidth: 2,
    shadow: {{ enabled: true, size: 4, x: 0, y: 2, color: 'rgba(0,0,0,0.3)' }}
  }},
  edges: {{
    font: {{ color: '#8899aa', size: 10, strokeWidth: 0, align: 'middle' }},
    arrows: {{ to: {{ enabled: true, type: 'arrow', scaleFactor: 0.8 }} }},
    smooth: {{ type: 'curvedCW', roundness: 0.15 }},
    color: {{ color: '#4a5a6a', highlight: '#66ccff', hover: '#66ccff', opacity: 0.6 }},
    hoverWidth: 2,
    selectionWidth: 2,
  }},
  physics: {{
    solver: 'barnesHut',
    barnesHut: {{ gravitationalConstant: -3000, centralGravity: 0.3, springLength: 180, springConstant: 0.02, damping: 0.08 }},
    stabilization: {{ iterations: 150, updateInterval: 20, fit: true }}
  }},
  interaction: {{
    hover: true, tooltipDelay: 0, navigationButtons: true, keyboard: true,
    zoomView: true, dragView: true, multiselect: false
  }},
  layout: {{ improvedLayout: true }}
}};
var network = new vis.Network(container, {{ nodes, edges }}, options);
network.fit();

network.on('hoverNode', function(p) {{
  var node = nodes.get(p.node);
  var t = document.getElementById('tooltip');
  if (t) {{ t.innerHTML = node.title || node.label; t.style.display = 'block'; }}
}});
network.on('hoverEdge', function(p) {{
  var edge = edges.get(p.edge);
  var t = document.getElementById('tooltip');
  if (t) {{ t.innerHTML = edge.title || ''; t.style.display = 'block'; }}
}});
network.on('blurNode', function() {{ var t = document.getElementById('tooltip'); if (t) t.style.display = 'none'; }});
network.on('blurEdge', function() {{ var t = document.getElementById('tooltip'); if (t) t.style.display = 'none'; }});

network.on('click', function(p) {{
  if (p.nodes.length > 0) {{
    var node = nodes.get(p.nodes[0]);
    var t = document.getElementById('tooltip');
    if (t) {{ t.innerHTML = '<b>Selected:</b> ' + (node.title || node.label) + '<br><small>View details below</small>'; t.style.display = 'block'; }}
  }}
}});

document.addEventListener('mousemove', function(e) {{
  var t = document.getElementById('tooltip');
  if (t && t.style.display === 'block') {{ t.style.left = (e.clientX + 15) + 'px'; t.style.top = (e.clientY + 15) + 'px'; }}
}});
}} catch(e) {{
  document.getElementById('mynetwork').innerHTML = '<div style=\"padding:20px;color:#ff6b6b;background:#0f1923;font-family:sans-serif;\">Graph error: ' + e.message + '</div>';
}}
</script>"""

def build_graph_data(symbol, all_shareholder_rows, top_n=10, min_pct=0.0, holder_types=None, layout="force"):
    is_all = symbol == "ALL"

    type_colors = {
        "government": "#e74c3c", "nvdr": "#9b59b6", "fund": "#27ae60",
        "institution": "#f39c12", "company": "#1abc9c", "individual": "#e91e63",
        "unknown": "#7f8c8d",
    }

    nodes = []
    edges = []
    seen_holders = {}
    seen_edges = set()
    added_companies = set()

    if is_all:
        filtered = []
        for r in all_shareholder_rows:
            pct = float(r.get("Ownership %", 0) or 0)
            if pct >= min_pct:
                htype = classify_holder_type(r["Shareholder Name"])
                if holder_types and holder_types != "All" and htype != holder_types:
                    continue
                filtered.append(r)

        companies_used = set(r["Symbol"] for r in filtered)
        for sym in sorted(companies_used)[:50]:
            company_rows = [r for r in filtered if r["Symbol"] == sym]
            company_rows = sorted(company_rows, key=lambda x: float(x.get("Ownership %", 0) or 0), reverse=True)[:max(3, top_n // 4)]
            name = SET50_NAMES.get(sym, sym)

            nodes.append({
                "id": f"COMPANY_{sym}",
                "label": sym,
                "title": f"<b>{sym}</b><br>{name}<br>Shareholders: {len(company_rows)}",
                "group": "company",
                "color": {"background": "#1a73e8", "border": "#4fc3f7"},
                "size": 35, "shape": "box", "font": {"size": 14, "color": "#ffffff", "face": "Arial"},
                "borderWidth": 2,
            })
            added_companies.add(sym)

            for row in company_rows:
                hname = row["Shareholder Name"]
                pct = float(row.get("Ownership %", 0) or 0)
                shares = row.get("Shares Held", 0)
                htype = classify_holder_type(hname)
                color = type_colors.get(htype, "#7f8c8d")

                hid = f"HOLDER_{hash(hname) % 10**9}"
                if hid not in seen_holders:
                    seen_holders[hid] = hname
                    nodes.append({
                        "id": hid,
                        "label": hname[:20],
                        "title": f"<b>{hname}</b><br>Type: {htype}",
                        "group": htype,
                        "color": {"background": color, "border": "#ffffff"},
                        "size": 15, "shape": "dot",
                        "font": {"size": 9, "color": "#aabbcc"},
                        "borderWidth": 1,
                    })

                edge_id = f"E_{sym}_{hid}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    ew = min(6, max(0.5, pct / 5))
                    edges.append({
                        "id": edge_id,
                        "from": hid, "to": f"COMPANY_{sym}",
                        "value": pct,
                        "width": ew,
                        "label": f"{pct:.1f}%",
                        "title": f"<b>{hname}</b> owns {pct:.2f}% of {sym}<br>Shares: {{:,}}".format(shares) if isinstance(shares, int) else f"<b>{hname}</b> owns {pct:.2f}% of {sym}<br>Shares: {shares}",
                        "color": {"color": "#4a5a6a", "opacity": max(0.2, min(0.8, pct / 25))},
                    })

    else:
        company_rows = [r for r in all_shareholder_rows if r["Symbol"] == symbol]
        company_rows = [r for r in company_rows if float(r.get("Ownership %", 0) or 0) >= min_pct]
        company_rows = sorted(company_rows, key=lambda x: float(x.get("Ownership %", 0) or 0), reverse=True)[:top_n]

        if holder_types and holder_types != "All":
            company_rows = [r for r in company_rows if classify_holder_type(r["Shareholder Name"]) == holder_types]

        name = SET50_NAMES.get(symbol, symbol)
        nodes.append({
            "id": f"COMPANY_{symbol}",
            "label": f"{symbol}\n{name[:25]}",
            "title": f"<b>{symbol}</b><br>{name}<br>Major shareholders: {len(company_rows)}",
            "group": "company",
            "color": {"background": "#1a73e8", "border": "#4fc3f7"},
            "size": 50, "shape": "box",
            "font": {"size": 16, "color": "#ffffff", "face": "Arial", "multi": True},
            "borderWidth": 3,
        })
        added_companies.add(symbol)

        for row in company_rows:
            hname = row["Shareholder Name"]
            pct = float(row.get("Ownership %", 0) or 0)
            shares = row.get("Shares Held", 0)
            htype = classify_holder_type(hname)
            color = type_colors.get(htype, "#7f8c8d")
            hsize = max(12, min(30, pct * 2))

            hid = f"HOLDER_{hash(hname) % 10**9}"
            if hid not in seen_holders:
                seen_holders[hid] = hname
                nodes.append({
                    "id": hid,
                    "label": hname[:25],
                    "title": f"<b>{hname}</b><br>Type: {htype}<br>Shares: {{:,}}".format(shares) if isinstance(shares, int) else f"<b>{hname}</b><br>Type: {htype}<br>Shares: {shares}<br>Ownership: {pct:.2f}%",
                    "group": htype,
                    "color": {"background": color, "border": "#ffffff"},
                    "size": hsize, "shape": "dot",
                    "font": {"size": 11, "color": "#c0d0e0"},
                    "borderWidth": 1,
                })

            edge_id = f"E_{symbol}_{hid}"
            if edge_id not in seen_edges:
                seen_edges.add(edge_id)
                ew = min(8, max(0.5, pct / 3))
                edges.append({
                    "id": edge_id,
                    "from": hid, "to": f"COMPANY_{symbol}",
                    "value": pct,
                    "width": ew,
                    "label": f"{pct:.2f}%",
                    "title": f"<b>Ownership</b><br>Shareholder: {hname}<br>Company: {symbol}<br>Shares: {{:,}}".format(shares) if isinstance(shares, int) else f"<b>Ownership</b><br>Shareholder: {hname}<br>Company: {symbol}<br>Shares: {shares}<br>Percent: {pct:.2f}%<br>As of: {row.get('As of Date', 'N/A')}<br>Source: {row.get('Source URL', 'N/A')}",
                    "color": {"color": "#4fc3f7", "opacity": max(0.3, min(1.0, pct / 20))},
                })

    return nodes, edges

stocks_summary = load_all_stocks_summary(SET50_TICKERS)

tab1, tab2 = st.tabs(["Shareholder Data", "Top Gainers / Losers"])

with tab1:
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
                "Symbol": sym, "Company": company_name,
                "Rank": holder.get("sequence"),
                "Shareholder Name": holder.get("name"),
                "Shares Held": holder.get("numberOfShare"),
                "Ownership %": holder.get("percentOfShare"),
                "As of Date": as_of, "Source": "Stock Exchange of Thailand (SET)",
                "Source URL": source_url, "Note": note,
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
                color="Top 5 Ownership %", color_continuous_scale="Blues", text_auto=".1f",
            )
            fig_own.update_layout(xaxis_title="Company", yaxis_title="Top 5 Shareholders Total %", height=400)
            st.plotly_chart(fig_own, width='stretch')

    st.markdown("---")
    st.markdown("#### Shareholder Relationship Graph")

    gcol1, gcol2, gcol3, gcol4 = st.columns(4)
    with gcol1:
        graph_company = st.selectbox("Company", ["ALL"] + sorted(SET50_CONSTITUENTS), key="graph_company")
    with gcol2:
        graph_top_n = st.slider("Top N shareholders", 3, 10, 5, key="graph_top_n")
    with gcol3:
        graph_min_pct = st.slider("Min ownership %", 0.0, 20.0, 0.0, 0.5, key="graph_min_pct")
    with gcol4:
        graph_holder_type = st.selectbox("Holder type", ["All", "government", "nvdr", "fund", "institution", "company", "individual"], key="graph_holder_type")

    rows_for_graph = []
    for sym in SET50_CONSTITUENTS:
        rows_for_graph.extend(get_shareholders_for_symbol(sym, sh_data))

    nodes_data, edges_data = build_graph_data(
        graph_company, rows_for_graph,
        top_n=graph_top_n, min_pct=graph_min_pct,
        holder_types=graph_holder_type if graph_holder_type != "All" else None,
    )

    col_graph, col_detail = st.columns([0.7, 0.3])

    with col_graph:
        if nodes_data:
            html = make_shareholder_graph_html(nodes_data, edges_data)
            st.iframe(html, height=650)

            legend_html = "<div style='display:flex;flex-wrap:wrap;gap:12px;padding:8px 0;font-size:13px;color:#ccc;'>"
            legend_items = {
                "company": "#1a73e8", "government": "#e74c3c", "nvdr": "#9b59b6",
                "fund": "#27ae60", "institution": "#f39c12", "company (holder)": "#1abc9c",
                "individual": "#e91e63", "unknown": "#7f8c8d",
            }
            for lname, lcolor in legend_items.items():
                legend_html += f"<span style='display:flex;align-items:center;gap:4px'><span style='width:10px;height:10px;border-radius:50%;background:{lcolor}'></span>{lname}</span>"
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)
        else:
            st.info("No nodes match the current filters.")

    with col_detail:
        st.markdown("#### Node Details")
        all_node_ids = [n["id"] for n in nodes_data]
        node_labels = {}
        node_map = {}
        for n in nodes_data:
            node_labels[n["id"]] = n.get("label", n["id"])
            node_map[n["id"]] = n

        if "graph_selected_node" not in st.session_state:
            st.session_state.graph_selected_node = ""

        selected_id = st.selectbox(
            "Select a node:",
            [""] + all_node_ids,
            format_func=lambda x: node_labels.get(x, "None") if x else "None",
            key="graph_node_selector",
        )

        if selected_id and selected_id in node_map:
            nd = node_map[selected_id]
            is_company = nd.get("group") == "company"

            if is_company:
                sym = nd["label"].split("\n")[0]
                cname = SET50_NAMES.get(sym, sym)
                st.markdown(f"**Company:** {sym}")
                st.markdown(f"**Name:** {cname}")
                company_holders = [r for r in rows_for_graph if r["Symbol"] == sym]
                st.markdown(f"**Shareholders:** {len(company_holders)}")
                st.markdown("**Top 5:**")
                for r in company_holders[:5]:
                    pct = r.get("Ownership %", 0)
                    st.markdown(f"- {r['Shareholder Name'][:30]}: {pct:.2f}%" if isinstance(pct, (int, float)) else f"- {r['Shareholder Name'][:30]}: {pct}%")
            else:
                hname_clean = node_labels.get(selected_id, "Unknown")
                htype = nd.get("group", "unknown")
                owned = []
                for e in edges_data:
                    if e["from"] == selected_id:
                        target_sym = e["to"].replace("COMPANY_", "")
                        owned.append((target_sym, e.get("value", 0)))
                st.markdown(f"**Holder:** {hname_clean}")
                st.markdown(f"**Type:** {htype}")
                st.markdown(f"**Companies owned:** {len(owned)}")
                if owned:
                    st.markdown("**Ownership:**")
                    for osym, opct in sorted(owned, key=lambda x: x[1], reverse=True):
                        st.markdown(f"- {osym}: {opct:.2f}%")
        else:
            st.info("Select a node to view details.\n\nHover over graph nodes for tooltips or click to track.")

    st.markdown("---")
    st.caption("Note: Shareholder names are displayed as registered in the SET system (mostly in Thai). "
               "NVDR (Thai NVDR) indicates shares held through Thai NVDR Company Limited, "
               "which represents foreign investors holding through the non-voting depository receipt program.")

with tab2:
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
                    color="Change%", color_continuous_scale="RdYlGn", text_auto=".2f",
                )
                fig_gain.update_layout(height=300, showlegend=False, yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_gain, width='stretch')
            with col_right:
                st.markdown("#### Top Losers")
                fig_loss = px.bar(
                    top_losers, x="Change%", y="Name", orientation="h",
                    color="Change%", color_continuous_scale="RdYlGn_r", text_auto=".2f",
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
