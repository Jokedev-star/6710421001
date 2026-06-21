"""
network_analysis.py
-------------------
Interactive correlation-network analysis for the SET50 dashboard.

Entry point: render_analysis(corr, sectors=None)
    corr    : pandas DataFrame correlation matrix (tickers x tickers)
    sectors : optional dict {ticker: sector}; falls back to SET50_SECTORS

Required: pip install pyvis networkx pandas numpy streamlit
"""

import pandas as pd
import numpy as np
import networkx as nx
import streamlit as st
from pyvis.network import Network
from streamlit.components.v1 import html as components_html


SET50_SECTORS = {
    "BBL": "Banking", "KBANK": "Banking", "KTB": "Banking", "SCB": "Banking",
    "TTB": "Banking", "TISCO": "Banking", "KKP": "Banking",
    "PTT": "Energy", "PTTEP": "Energy", "GULF": "Energy", "GPSC": "Energy",
    "EGCO": "Energy", "RATCH": "Energy", "BANPU": "Energy", "TOP": "Energy",
    "OR": "Energy",
    "PTTGC": "Petrochemicals", "IVL": "Petrochemicals",
    "CPALL": "Commerce", "CRC": "Commerce", "HMPRO": "Commerce",
    "BJC": "Commerce", "COM7": "Commerce",
    "CPF": "Food", "TU": "Food", "OSP": "Food", "CBG": "Food",
    "MINT": "Tourism", "CENTEL": "Tourism",
    "ADVANC": "ICT", "TRUE": "ICT",
    "AOT": "Transportation", "BEM": "Transportation", "BTS": "Transportation",
    "BDMS": "Healthcare", "BH": "Healthcare",
    "CPN": "Property", "AWC": "Property", "WHA": "Property", "LH": "Property",
    "SCC": "Materials", "SCGP": "Materials",
    "TLI": "Insurance",
    "KTC": "Finance", "MTC": "Finance", "TIDLOR": "Finance",
    "SAWAD": "Finance", "TCAP": "Finance",
    "DELTA": "Electronics", "CCET": "Electronics",
}

SECTOR_COLORS = {
    "Banking": "#1f77b4",
    "Energy": "#e74c3c",
    "Petrochemicals": "#ff7f0e",
    "Commerce": "#2ca02c",
    "Food": "#27ae60",
    "Tourism": "#bcbd22",
    "ICT": "#9467bd",
    "Transportation": "#17becf",
    "Healthcare": "#e377c2",
    "Property": "#8c564b",
    "Materials": "#7f7f7f",
    "Insurance": "#d62728",
    "Finance": "#f39c12",
    "Electronics": "#1abc9c",
    "Unknown": "#95a5a6",
}

COMMUNITY_PALETTE = [
    "#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12",
    "#1abc9c", "#e91e63", "#34495e", "#16a085", "#d35400",
    "#7f8c8d", "#27ae60",
]


# ---------------------------------------------------------------------------
# 1) load_data — normalize inputs
# ---------------------------------------------------------------------------
def load_data(corr: pd.DataFrame, sectors=None):
    if sectors is None:
        sectors = {t: SET50_SECTORS.get(t, "Unknown") for t in corr.columns}
    elif isinstance(sectors, pd.Series):
        sectors = sectors.to_dict()
    return corr, sectors


# ---------------------------------------------------------------------------
# 2) build_correlation_graph
# ---------------------------------------------------------------------------
def build_correlation_graph(corr, threshold=0.65, use_abs=True,
                            sector_filter=None, sectors=None,
                            hide_isolated=True):
    if sectors is None:
        sectors = {}

    tickers = [
        t for t in corr.columns
        if sector_filter is None or sectors.get(t, "Unknown") in sector_filter
    ]
    G = nx.Graph()
    G.add_nodes_from(tickers)

    for i, a in enumerate(tickers):
        for b in tickers[i + 1:]:
            w = float(corr.loc[a, b])
            score = abs(w) if use_abs else w
            if score >= threshold:
                G.add_edge(a, b, weight=w, abs_weight=abs(w))

    if hide_isolated:
        G.remove_nodes_from([n for n, d in G.degree() if d == 0])
    return G


# ---------------------------------------------------------------------------
# 3) calculate_network_metrics
# ---------------------------------------------------------------------------
def calculate_network_metrics(G):
    if G.number_of_nodes() == 0:
        return {}, {}, [], {}, 0.0
    deg_cent = nx.degree_centrality(G)
    btw_cent = nx.betweenness_centrality(G)
    if G.number_of_edges() > 0:
        communities = list(nx.community.greedy_modularity_communities(G))
        modularity = float(nx.community.modularity(G, communities))
    else:
        communities = [{n} for n in G.nodes()]
        modularity = 0.0
    comm_map = {}
    for cid, nodes in enumerate(communities):
        for node in nodes:
            comm_map[node] = cid
    return deg_cent, btw_cent, communities, comm_map, modularity


# ---------------------------------------------------------------------------
# 4) render_pyvis_graph — interactive PyVis network
# ---------------------------------------------------------------------------
def render_pyvis_graph(G, deg_cent, btw_cent, sectors, comm_map,
                       color_mode="sector", height_px=650):
    net = Network(
        height=f"{height_px}px", width="100%",
        bgcolor="#0f1923", font_color="#e0e0e0",
        cdn_resources="remote", notebook=False, directed=False,
    )

    deg_dict = dict(G.degree())

    for node in G.nodes():
        deg = deg_dict.get(node, 0)
        dc = deg_cent.get(node, 0.0)
        bc = btw_cent.get(node, 0.0)
        sector = sectors.get(node, "Unknown")
        community = comm_map.get(node, 0)

        if color_mode == "community":
            color = COMMUNITY_PALETTE[community % len(COMMUNITY_PALETTE)]
            group_label = f"Community {community + 1}"
        else:
            color = SECTOR_COLORS.get(sector, SECTOR_COLORS["Unknown"])
            group_label = sector

        size = 14 + dc * 60
        title = (
            f"<b>{node}</b><br>"
            f"Group: {group_label}<br>"
            f"Degree: {deg}<br>"
            f"Degree centrality: {dc:.3f}<br>"
            f"Betweenness: {bc:.3f}"
        )
        net.add_node(
            node, label=node, title=title, color=color, size=size,
            borderWidth=2,
            font={"color": "#ffffff", "size": 14, "face": "Arial"},
        )

    for a, b, data in G.edges(data=True):
        w = data.get("weight", 0.0)
        aw = abs(w)
        width = 1 + aw * 8
        edge_color = "#66ccff" if w >= 0 else "#ff6b6b"
        title = f"<b>{a} &harr; {b}</b><br>Correlation: {w:.3f}"
        net.add_edge(a, b, value=aw, width=width, color=edge_color, title=title)

    net.set_options("""
    {
      "nodes": {
        "shape": "dot",
        "scaling": { "min": 14, "max": 60 },
        "shadow": { "enabled": true, "size": 6, "x": 0, "y": 2, "color": "rgba(0,0,0,0.4)" }
      },
      "edges": {
        "smooth": { "type": "continuous" },
        "color": { "opacity": 0.7 }
      },
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 130,
          "springConstant": 0.08,
          "damping": 0.5
        },
        "stabilization": { "iterations": 200, "fit": true }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 80,
        "navigationButtons": true,
        "keyboard": true,
        "zoomView": true,
        "dragView": true
      }
    }
    """)
    return net.generate_html(notebook=False)


# ---------------------------------------------------------------------------
# 5) render_summary_cards
# ---------------------------------------------------------------------------
def render_summary_cards(G):
    if G.number_of_nodes() == 0:
        st.warning("No stocks match the current filters.")
        return

    weights = [d["weight"] for _, _, d in G.edges(data=True)]
    deg_dict = dict(G.degree())
    avg_corr = float(np.mean(weights)) if weights else 0.0
    top_deg = max(deg_dict, key=deg_dict.get) if deg_dict else "-"

    if weights:
        a, b, d = max(G.edges(data=True), key=lambda e: abs(e[2]["weight"]))
        strong_pair, strong_val = f"{a} - {b}", d["weight"]
    else:
        strong_pair, strong_val = "-", 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Visible stocks", G.number_of_nodes())
    c2.metric("Edges", G.number_of_edges())
    c3.metric("Avg correlation", f"{avg_corr:.3f}")
    c4.metric("Top degree stock", f"{top_deg}",
              delta=f"deg = {deg_dict.get(top_deg, 0)}" if top_deg != "-" else None)
    c5.metric("Strongest pair", strong_pair, delta=f"r = {strong_val:.3f}")


# ---------------------------------------------------------------------------
# 6) render_tables
# ---------------------------------------------------------------------------
def render_tables(G, deg_cent, btw_cent, sectors, comm_map, color_mode):
    if G.number_of_nodes() == 0:
        return

    deg_dict = dict(G.degree())

    df_nodes = pd.DataFrame([
        {
            "Ticker": n,
            "Sector": sectors.get(n, "Unknown"),
            "Community": comm_map.get(n, 0) + 1,
            "Degree": deg_dict.get(n, 0),
            "Degree centrality": round(deg_cent.get(n, 0.0), 3),
            "Betweenness": round(btw_cent.get(n, 0.0), 3),
        }
        for n in G.nodes()
    ]).sort_values("Degree", ascending=False).reset_index(drop=True)

    df_edges = pd.DataFrame([
        {
            "Stock A": a, "Stock B": b,
            "Correlation": round(d["weight"], 3),
            "|Correlation|": round(abs(d["weight"]), 3),
        }
        for a, b, d in G.edges(data=True)
    ])
    if not df_edges.empty:
        df_edges = df_edges.sort_values("|Correlation|", ascending=False).reset_index(drop=True)

    group_key = "Community" if color_mode == "community" else "Sector"
    df_groups = (
        df_nodes.groupby(group_key)
        .agg(Stocks=("Ticker", "count"),
             AvgDegree=("Degree", "mean"),
             AvgCentrality=("Degree centrality", "mean"))
        .round(3).reset_index()
        .sort_values("Stocks", ascending=False)
        .reset_index(drop=True)
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Top 10 most connected stocks")
        st.dataframe(df_nodes.head(10), use_container_width=True, hide_index=True)
    with col2:
        st.markdown("#### Top 10 strongest correlation pairs")
        if df_edges.empty:
            st.info("No edges to rank.")
        else:
            st.dataframe(df_edges.head(10), use_container_width=True, hide_index=True)

    st.markdown(f"#### {group_key} summary")
    st.dataframe(df_groups, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Helper: color legend
# ---------------------------------------------------------------------------
def _render_legend(color_mode, sectors_used, communities_used):
    if color_mode == "community":
        items = [
            (f"Community {g + 1}", COMMUNITY_PALETTE[g % len(COMMUNITY_PALETTE)])
            for g in sorted(communities_used)
        ]
    else:
        items = [
            (s, SECTOR_COLORS.get(s, SECTOR_COLORS["Unknown"]))
            for s in sorted(sectors_used)
        ]

    html = (
        "<div style='display:flex;flex-wrap:wrap;gap:14px;padding:8px 0;"
        "font-size:13px;color:#cfd8e0;'>"
    )
    for label, color in items:
        html += (
            f"<span style='display:flex;align-items:center;gap:6px'>"
            f"<span style='width:12px;height:12px;border-radius:50%;background:{color};"
            f"border:1px solid #333;display:inline-block'></span>{label}</span>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def render_analysis(corr: pd.DataFrame, sectors=None):
    st.title("Network Analysis")
    st.caption("Interactive correlation network of SET50 daily returns")

    corr, sectors = load_data(corr, sectors)
    available_sectors = sorted({sectors.get(t, "Unknown") for t in corr.columns})

    # --- Sidebar filters ---
    st.sidebar.markdown("### Network filters")
    threshold = st.sidebar.slider("Correlation threshold", 0.0, 1.0, 0.65, 0.05)
    use_abs = st.sidebar.checkbox("Use absolute correlation", value=True)
    hide_isolated = st.sidebar.checkbox("Hide isolated nodes", value=True)
    color_mode = st.sidebar.radio(
        "Node color mode", ["sector", "community"], horizontal=True
    )
    if available_sectors:
        sector_filter = st.sidebar.multiselect(
            "Sector filter", available_sectors, default=available_sectors
        )
    else:
        sector_filter = None

    # --- Build & analyze ---
    G = build_correlation_graph(
        corr, threshold=threshold, use_abs=use_abs,
        sector_filter=sector_filter, sectors=sectors,
        hide_isolated=hide_isolated,
    )
    deg_cent, btw_cent, communities, comm_map, modularity = calculate_network_metrics(G)

    # --- Dashboard ---
    st.subheader("Network summary")
    render_summary_cards(G)

    st.subheader("Interactive network graph")
    if G.number_of_edges() == 0:
        st.warning("No edges match the current filters. Try lowering the threshold.")
    else:
        html = render_pyvis_graph(
            G, deg_cent, btw_cent, sectors, comm_map,
            color_mode=color_mode, height_px=650,
        )
        components_html(html, height=680, scrolling=False)

        sectors_used = {sectors.get(n, "Unknown") for n in G.nodes()}
        communities_used = set(comm_map.values())
        _render_legend(color_mode, sectors_used, communities_used)

    st.subheader("Network tables")
    render_tables(G, deg_cent, btw_cent, sectors, comm_map, color_mode)

    if communities and G.number_of_edges() > 0:
        st.caption(
            f"Detected {len(communities)} communities · "
            f"modularity = {modularity:.3f}"
        )
