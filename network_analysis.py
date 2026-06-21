"""
network_analysis.py
-------------------
วางโมดูลนี้ลงในโปรเจกต์ Streamlit ของคุณ แล้วเรียก render_analysis(corr)
โดยส่ง correlation matrix (pandas DataFrame ของผลตอบแทนหุ้น SET50)
ที่คุณใช้วาดกราฟ/heatmap อยู่แล้วเข้าไป

ต้องมี: pip install networkx matplotlib pandas numpy
(networkx เวอร์ชัน >= 2.8 รองรับ nx.community)
"""

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st


# ---------------------------------------------------------------------------
# 1) สร้างกราฟจาก correlation matrix
# ---------------------------------------------------------------------------
def build_graph_from_corr(corr: pd.DataFrame, threshold: float = 0.5) -> nx.Graph:
    """ลากเส้นเชื่อม (edge) ระหว่างหุ้นคู่ที่ |correlation| >= threshold"""
    G = nx.Graph()
    G.add_nodes_from(corr.columns)
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            w = corr.loc[a, b]
            if abs(w) >= threshold:
                G.add_edge(a, b, weight=float(w))
    return G


# ---------------------------------------------------------------------------
# 2) วิเคราะห์เครือข่าย — นี่คือส่วน "analyze" ที่โจทย์ต้องการ
# ---------------------------------------------------------------------------
def analyze_network(G: nx.Graph):
    # --- โครงสร้างพื้นฐาน (ง่ายสุด) ---
    n = G.number_of_nodes()
    stats = {
        "Nodes (หุ้น)": n,
        "Edges (เส้นเชื่อม)": G.number_of_edges(),
        "Density": round(nx.density(G), 4),
        "Avg degree": round(sum(d for _, d in G.degree()) / n, 2) if n else 0,
    }

    # --- Centrality: ใครคือศูนย์กลาง ---
    deg = nx.degree_centrality(G)
    btw = nx.betweenness_centrality(G)
    cent = (
        pd.DataFrame({
            "Stock": list(deg.keys()),
            "Degree centrality": [round(deg[k], 3) for k in deg],
            "Betweenness": [round(btw[k], 3) for k in deg],
        })
        .sort_values("Degree centrality", ascending=False)
        .reset_index(drop=True)
    )

    # --- Community detection: กราฟจับกลุ่มหุ้นยังไง ---
    communities = list(nx.community.greedy_modularity_communities(G))
    comm_map = {}
    for cid, nodes in enumerate(communities):
        for node in nodes:
            comm_map[node] = cid
    modularity = round(nx.community.modularity(G, communities), 4)

    return stats, cent, communities, comm_map, modularity


# ---------------------------------------------------------------------------
# 3) วาดกราฟ ระบายสีตามกลุ่ม community
# ---------------------------------------------------------------------------
def draw_colored_graph(G: nx.Graph, comm_map: dict):
    fig, ax = plt.subplots(figsize=(9, 7))
    pos = nx.spring_layout(G, seed=42, k=0.5)
    colors = [comm_map.get(node, 0) for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=colors, cmap=plt.cm.tab10,
                           node_size=450, ax=ax)
    nx.draw_networkx_edges(G, pos, alpha=0.25, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=7, ax=ax)
    ax.set_title("SET50 correlation network (สีตามกลุ่มที่ตรวจพบ)")
    ax.axis("off")
    return fig


# ---------------------------------------------------------------------------
# 4) Render ลง Streamlit + สร้างประโยคตีความให้ลอกไปใส่รายงานได้เลย
# ---------------------------------------------------------------------------
def render_analysis(corr: pd.DataFrame, threshold: float = 0.5):
    st.header("Network Analysis")

    thr = st.slider("Correlation threshold", 0.1, 0.9, threshold, 0.05)
    G = build_graph_from_corr(corr, thr)

    if G.number_of_edges() == 0:
        st.warning("ไม่มีเส้นเชื่อมเลย ลองลด threshold ลง")
        return

    stats, cent, communities, comm_map, modularity = analyze_network(G)

    # โครงสร้างพื้นฐาน
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nodes", stats["Nodes (หุ้น)"])
    c2.metric("Edges", stats["Edges (เส้นเชื่อม)"])
    c3.metric("Density", stats["Density"])
    c4.metric("Communities", len(communities))

    # Centrality
    st.subheader("หุ้นที่เป็นศูนย์กลาง (Top by centrality)")
    st.dataframe(cent.head(10), use_container_width=True)

    # กราฟระบายสีตามกลุ่ม
    st.subheader("กราฟเครือข่าย จับกลุ่มอัตโนมัติ")
    st.pyplot(draw_colored_graph(G, comm_map))

    # สรุปสมาชิกแต่ละกลุ่ม
    st.subheader("สมาชิกแต่ละกลุ่ม")
    for cid, nodes in enumerate(communities):
        st.write(f"**กลุ่ม {cid + 1}** ({len(nodes)} ตัว): {', '.join(sorted(nodes))}")

    # ---- ประโยคตีความ พร้อมลอกลงรายงาน ----
    top_stock = cent.iloc[0]["Stock"]
    top_bridge = cent.sort_values("Betweenness", ascending=False).iloc[0]["Stock"]
    st.subheader("ตีความ (ลอกลงรายงานได้)")
    st.info(
        f"ที่ threshold = {thr}, เครือข่ายมี {stats['Edges (เส้นเชื่อม)']} เส้นเชื่อม "
        f"(density = {stats['Density']}). หุ้น **{top_stock}** มี degree centrality สูงสุด "
        f"จึงเป็นศูนย์กลางของตลาดที่เคลื่อนไหวสอดคล้องกับหุ้นอื่นมากที่สุด ส่วนหุ้น "
        f"**{top_bridge}** มี betweenness สูงสุด ทำหน้าที่เป็นสะพานเชื่อมระหว่างกลุ่ม "
        f"อัลกอริทึมจับได้ {len(communities)} กลุ่ม (modularity = {modularity}) "
        f"ซึ่งสามารถนำไปเทียบกับการแบ่ง sector จริงของตลาดหลักทรัพย์ได้"
    )


# ---------------------------------------------------------------------------
# ถ้ายังไม่มี correlation matrix ในมือ ให้คำนวณจากราคา/ผลตอบแทนแบบนี้:
#   returns = prices.pct_change().dropna()
#   corr = returns.corr()
#   render_analysis(corr)
# ---------------------------------------------------------------------------
