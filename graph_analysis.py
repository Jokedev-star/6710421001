"""
graph_analysis.py
-----------------
Social-network graph analysis page for the SET50 dashboard.

Reads an edge list CSV (default: edges_rows.csv) and provides:
  1. Import CSV and Build Graph
  2. Find Bridges
  3. Visualize Centrality values (Betweenness, Bridge, Closeness,
     Degree, Eigenvector, PageRank)
  4. K-means community detection on the imported graph
  5. K-means / Louvain community detection on the Zachary karate club

Entry point: render_graph_analysis(csv_path="edges_rows.csv")

Required: pip install pyvis networkx scikit-learn pandas numpy plotly streamlit
"""

import os

import numpy as np
import pandas as pd
import networkx as nx
import plotly.express as px
import streamlit as st
from pyvis.network import Network
from streamlit.components.v1 import html as components_html

try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False


COMMUNITY_PALETTE = [
    "#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12",
    "#1abc9c", "#e91e63", "#34495e", "#16a085", "#d35400",
    "#7f8c8d", "#27ae60", "#2980b9", "#c0392b", "#8e44ad",
]


# ---------------------------------------------------------------------------
# 1) Import CSV and build graph
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_edges(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df


def build_graph(df: pd.DataFrame, src="person_a", dst="person_b",
                relation="relation") -> nx.Graph:
    """Build an undirected simple graph from an edge list."""
    G = nx.Graph()
    for _, row in df.iterrows():
        a, b = row.get(src), row.get(dst)
        if pd.isna(a) or pd.isna(b) or a == b:
            continue
        rel = row.get(relation, "") if relation in df.columns else ""
        G.add_edge(str(a).strip(), str(b).strip(), relation=rel)
    return G


# ---------------------------------------------------------------------------
# 2) Bridges
# ---------------------------------------------------------------------------
def find_bridges(G: nx.Graph):
    """Return list of bridge edges (edges whose removal disconnects a component)."""
    if G.number_of_edges() == 0:
        return []
    return list(nx.bridges(G))


# ---------------------------------------------------------------------------
# 3) Centrality measures
# ---------------------------------------------------------------------------
def bridging_coefficient(G: nx.Graph) -> dict:
    """Hwang et al. bridging coefficient: (1/d(v)) / sum_{w in N(v)} 1/d(w)."""
    deg = dict(G.degree())
    bc = {}
    for v in G.nodes():
        dv = deg.get(v, 0)
        if dv == 0:
            bc[v] = 0.0
            continue
        denom = sum(1.0 / deg[w] for w in G.neighbors(v) if deg[w] > 0)
        bc[v] = (1.0 / dv) / denom if denom > 0 else 0.0
    return bc


def _eigenvector_centrality_safe(G: nx.Graph) -> dict:
    """Eigenvector centrality, computed per connected component.

    ``eigenvector_centrality_numpy`` raises on disconnected graphs, so we run
    it on each component separately and merge the results.
    """
    result = {n: 0.0 for n in G.nodes()}
    for comp in nx.connected_components(G):
        sub = G.subgraph(comp)
        if sub.number_of_nodes() == 1:
            result[next(iter(comp))] = 0.0
            continue
        try:
            ev = nx.eigenvector_centrality_numpy(sub)
        except Exception:
            try:
                ev = nx.eigenvector_centrality(sub, max_iter=1000)
            except Exception:
                ev = {n: 0.0 for n in sub.nodes()}
        result.update(ev)
    return result


def compute_centralities(G: nx.Graph) -> pd.DataFrame:
    """Return a DataFrame of every centrality measure, one row per node."""
    if G.number_of_nodes() == 0:
        return pd.DataFrame()

    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    eigenvector = _eigenvector_centrality_safe(G)
    pagerank = nx.pagerank(G)

    # Bridging centrality = betweenness * bridging coefficient (Hwang et al.)
    bcoef = bridging_coefficient(G)
    bridge = {n: betweenness[n] * bcoef[n] for n in G.nodes()}

    df = pd.DataFrame({
        "Node": list(G.nodes()),
        "Degree": [degree[n] for n in G.nodes()],
        "Betweenness": [betweenness[n] for n in G.nodes()],
        "Closeness": [closeness[n] for n in G.nodes()],
        "Eigenvector": [eigenvector[n] for n in G.nodes()],
        "PageRank": [pagerank[n] for n in G.nodes()],
        "Bridge": [bridge[n] for n in G.nodes()],
    })
    return df.round(4)


# ---------------------------------------------------------------------------
# Community detection helpers
# ---------------------------------------------------------------------------
def spectral_features(G: nx.Graph, k: int) -> tuple:
    """Laplacian-eigenmap embedding used as features for k-means."""
    nodes = list(G.nodes())
    L = nx.normalized_laplacian_matrix(G, nodelist=nodes).toarray()
    eigvals, eigvecs = np.linalg.eigh(L)
    # skip the first (trivial) eigenvector, take next k
    dim = min(k, eigvecs.shape[1] - 1)
    features = eigvecs[:, 1:1 + max(dim, 1)]
    return nodes, features


def kmeans_communities(G: nx.Graph, k: int) -> dict:
    """K-means over a spectral embedding -> {node: community_id}."""
    if not HAS_SKLEARN or G.number_of_nodes() == 0:
        return {}
    nodes, features = spectral_features(G, k)
    k = min(k, len(nodes))
    if k < 2:
        return {n: 0 for n in nodes}
    labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(features)
    return {n: int(c) for n, c in zip(nodes, labels)}


def louvain_communities(G: nx.Graph) -> dict:
    """Louvain modularity communities -> {node: community_id}."""
    if G.number_of_edges() == 0:
        return {n: 0 for n in G.nodes()}
    try:
        comms = nx.community.louvain_communities(G, seed=42)
    except Exception:
        comms = list(nx.community.greedy_modularity_communities(G))
    cmap = {}
    for cid, group in enumerate(comms):
        for n in group:
            cmap[n] = cid
    return cmap


# ---------------------------------------------------------------------------
# PyVis rendering
# ---------------------------------------------------------------------------
def _value_to_color(value, vmin, vmax):
    """Map a scalar to a blue->red gradient hex color."""
    if vmax <= vmin:
        t = 0.5
    else:
        t = (value - vmin) / (vmax - vmin)
    r = int(40 + t * 215)
    g = int(90 + (1 - abs(t - 0.5) * 2) * 80)
    b = int(220 - t * 180)
    return f"#{r:02x}{g:02x}{b:02x}"


def render_pyvis(G, value_map=None, color_map=None, size_map=None,
                 highlight_edges=None, height_px=600, label_suffix=None):
    """Generic PyVis renderer.

    value_map     : {node: float} used for gradient coloring + tooltip
    color_map     : {node: hex} explicit color (overrides value_map gradient)
    size_map      : {node: float 0..1} drives node size
    highlight_edges : set of frozenset({a,b}) drawn thick/red
    """
    net = Network(
        height=f"{height_px}px", width="100%",
        bgcolor="#0f1923", font_color="#e0e0e0",
        cdn_resources="remote", notebook=False, directed=False,
    )
    highlight_edges = highlight_edges or set()
    deg = dict(G.degree())

    vmin = vmax = 0.0
    if value_map:
        vals = list(value_map.values())
        vmin, vmax = min(vals), max(vals)

    for node in G.nodes():
        if color_map:
            color = color_map.get(node, "#7f8c8d")
        elif value_map:
            color = _value_to_color(value_map.get(node, 0.0), vmin, vmax)
        else:
            color = "#3498db"

        if size_map:
            size = 12 + size_map.get(node, 0.0) * 45
        else:
            size = 12 + deg.get(node, 0) * 3

        title = f"<b>{node}</b><br>Degree: {deg.get(node, 0)}"
        if value_map:
            extra = f"{value_map.get(node, 0.0):.4f}"
            title += f"<br>{label_suffix or 'Value'}: {extra}"
        net.add_node(
            node, label=node, title=title, color=color, size=size,
            borderWidth=2, font={"color": "#ffffff", "size": 14, "face": "Arial"},
        )

    for a, b, data in G.edges(data=True):
        is_bridge = frozenset((a, b)) in highlight_edges
        rel = data.get("relation", "")
        title = f"<b>{a} &harr; {b}</b>"
        if rel:
            title += f"<br>Relation: {rel}"
        if is_bridge:
            net.add_edge(a, b, color="#ff4d4d", width=5, title=title + "<br><b>BRIDGE</b>")
        else:
            net.add_edge(a, b, color="#4a5a6a", width=1.5, title=title)

    net.set_options("""
    {
      "nodes": { "shape": "dot",
        "shadow": { "enabled": true, "size": 6, "x": 0, "y": 2, "color": "rgba(0,0,0,0.4)" } },
      "edges": { "smooth": { "type": "continuous" }, "color": { "opacity": 0.8 } },
      "physics": { "enabled": true, "solver": "forceAtlas2Based",
        "forceAtlas2Based": { "gravitationalConstant": -70, "centralGravity": 0.012,
          "springLength": 120, "springConstant": 0.08, "damping": 0.5 },
        "stabilization": { "iterations": 200, "fit": true } },
      "interaction": { "hover": true, "tooltipDelay": 80, "navigationButtons": true,
        "keyboard": true, "zoomView": true, "dragView": true }
    }
    """)
    return net.generate_html(notebook=False)


def _render_legend(items):
    html = ("<div style='display:flex;flex-wrap:wrap;gap:14px;padding:8px 0;"
            "font-size:13px;color:#cfd8e0;'>")
    for label, color in items:
        html += (f"<span style='display:flex;align-items:center;gap:6px'>"
                 f"<span style='width:12px;height:12px;border-radius:50%;background:{color};"
                 f"border:1px solid #333;display:inline-block'></span>{label}</span>")
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def render_graph_analysis(csv_path="edges_rows.csv"):
    st.title("Graph Analysis")
    st.caption("Social-network analysis of the people relationship edge list")

    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(__file__), csv_path)

    if not os.path.exists(csv_path):
        st.error(f"CSV not found: `{csv_path}`")
        return

    df = load_edges(csv_path)
    G = build_graph(df)

    # ---------------- 1. Import CSV & build graph ----------------
    st.header("1 · Import CSV and Build Graph")
    st.caption(f"Source: `{os.path.basename(csv_path)}`")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Edges (rows)", len(df))
    c2.metric("Nodes", G.number_of_nodes())
    c3.metric("Graph edges", G.number_of_edges())
    n_comp = nx.number_connected_components(G) if G.number_of_nodes() else 0
    c4.metric("Components", n_comp)

    with st.expander("Preview edge list"):
        st.dataframe(df, use_container_width=True, hide_index=True)

    if G.number_of_nodes() == 0:
        st.warning("Graph is empty — nothing to analyze.")
        return

    components_html(render_pyvis(G, height_px=560), height=580, scrolling=False)

    # ---------------- 2. Bridges ----------------
    st.markdown("---")
    st.header("2 · Bridges")
    st.caption("A bridge is an edge whose removal increases the number of connected components.")
    bridges = find_bridges(G)
    bridge_set = {frozenset(e) for e in bridges}

    st.metric("Bridges found", len(bridges))
    if bridges:
        bdf = pd.DataFrame(bridges, columns=["Node A", "Node B"])
        st.dataframe(bdf, use_container_width=True, hide_index=True)
        components_html(
            render_pyvis(G, highlight_edges=bridge_set, height_px=560),
            height=580, scrolling=False,
        )
        _render_legend([("Bridge edge", "#ff4d4d"), ("Normal edge", "#4a5a6a")])
    else:
        st.info("No bridges in this graph (every edge lies on a cycle).")

    # ---------------- 3. Centrality ----------------
    st.markdown("---")
    st.header("3 · Centrality Values")
    cent_df = compute_centralities(G)

    metric = st.selectbox(
        "Centrality measure to visualize",
        ["Betweenness", "Bridge", "Closeness", "Degree", "Eigenvector", "PageRank"],
    )
    value_map = dict(zip(cent_df["Node"], cent_df[metric]))
    vmax = max(value_map.values()) if value_map else 1.0
    size_map = {n: (v / vmax if vmax > 0 else 0.0) for n, v in value_map.items()}

    col_g, col_t = st.columns([0.62, 0.38])
    with col_g:
        components_html(
            render_pyvis(G, value_map=value_map, size_map=size_map,
                         height_px=560, label_suffix=metric),
            height=580, scrolling=False,
        )
        _render_legend([("Low", _value_to_color(0, 0, 1)),
                        ("High", _value_to_color(1, 0, 1))])
    with col_t:
        st.markdown(f"**Top 10 by {metric}**")
        top = cent_df[["Node", metric]].sort_values(metric, ascending=False).head(10)
        st.dataframe(top, use_container_width=True, hide_index=True)

    fig = px.bar(
        cent_df.sort_values(metric, ascending=False).head(15),
        x="Node", y=metric, color=metric, color_continuous_scale="Turbo",
    )
    fig.update_layout(height=340, xaxis_title="", margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Full centrality table"):
        st.dataframe(
            cent_df.sort_values("Betweenness", ascending=False),
            use_container_width=True, hide_index=True,
        )

    # ---------------- 4. K-means on imported graph ----------------
    st.markdown("---")
    st.header("4 · K-means Community Detection")
    st.caption("Spectral (Laplacian-eigenmap) embedding clustered with K-means.")
    if not HAS_SKLEARN:
        st.error("scikit-learn is not installed. Run `pip install scikit-learn`.")
    else:
        max_k = max(2, min(10, G.number_of_nodes() - 1))
        k = st.slider("Number of clusters (k)", 2, max_k, min(4, max_k))
        cmap = kmeans_communities(G, k)
        color_map = {n: COMMUNITY_PALETTE[c % len(COMMUNITY_PALETTE)]
                     for n, c in cmap.items()}
        components_html(
            render_pyvis(G, color_map=color_map, height_px=560),
            height=580, scrolling=False,
        )
        used = sorted(set(cmap.values()))
        _render_legend([(f"Cluster {c + 1}",
                         COMMUNITY_PALETTE[c % len(COMMUNITY_PALETTE)]) for c in used])
        sizes = pd.Series(cmap).value_counts().sort_index()
        sizes.index = [f"Cluster {i + 1}" for i in sizes.index]
        st.bar_chart(sizes)

    # ---------------- 5. Karate club ----------------
    st.markdown("---")
    st.header("5 · Karate Club — K-means / Louvain")
    st.caption("Zachary's karate club, a classic community-detection benchmark.")
    K = nx.karate_club_graph()
    K = nx.relabel_nodes(K, {n: str(n) for n in K.nodes()})

    method = st.radio("Community method", ["Louvain", "K-means"], horizontal=True)
    if method == "Louvain":
        kc_map = louvain_communities(K)
    else:
        if not HAS_SKLEARN:
            st.error("scikit-learn is not installed.")
            kc_map = {n: 0 for n in K.nodes()}
        else:
            kk = st.slider("Number of clusters (k)", 2, 8, 2, key="karate_k")
            kc_map = kmeans_communities(K, kk)

    color_map = {n: COMMUNITY_PALETTE[c % len(COMMUNITY_PALETTE)]
                 for n, c in kc_map.items()}
    n_comm = len(set(kc_map.values()))
    try:
        groups = {}
        for n, c in kc_map.items():
            groups.setdefault(c, set()).add(n)
        modularity = nx.community.modularity(K, list(groups.values()))
    except Exception:
        modularity = float("nan")

    cc1, cc2 = st.columns(2)
    cc1.metric("Communities", n_comm)
    cc2.metric("Modularity", f"{modularity:.3f}")

    components_html(
        render_pyvis(K, color_map=color_map, height_px=560),
        height=580, scrolling=False,
    )
    used = sorted(set(kc_map.values()))
    _render_legend([(f"Community {c + 1}",
                     COMMUNITY_PALETTE[c % len(COMMUNITY_PALETTE)]) for c in used])
