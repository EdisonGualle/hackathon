import networkx as nx
import plotly.graph_objects as go
import pandas as pd


NIVEL_COLOR = {"ROJO": "#FF4444", "AMARILLO": "#FFAA00", "VERDE": "#44BB44"}


def build_graph(sheets: dict, scores_df: pd.DataFrame, filter_nivel: list | None = None):
    siniestros = sheets.get("1_Siniestros", pd.DataFrame())
    asegurados = sheets.get("3_Asegurados", pd.DataFrame())
    proveedores = sheets.get("4_Proveedores", pd.DataFrame())

    score_map = {}
    nivel_map = {}
    alert_map = {}
    if not scores_df.empty:
        for _, r in scores_df.iterrows():
            sid = r["ID Siniestro"]
            score_map[sid] = r.get("Score", 0)
            nivel_map[sid] = r.get("Nivel", "VERDE")
            alert_map[sid] = r.get("Alertas", "")

    # ── Asegurado lookup ──────────────────────────────────────────────
    aseg_name = {}
    for _, r in asegurados.iterrows():
        aseg_name[r["ID Asegurado"]] = r.get("Nombres Asegurado", r["ID Asegurado"])

    # ── Proveedor lookup ──────────────────────────────────────────────
    prov_name = {}
    prov_restrictiva = {}
    for _, r in proveedores.iterrows():
        pid = r.get("ID Proveedor", "")
        prov_name[pid] = r.get("Nombre Proveedor", pid)
        prov_restrictiva[pid] = str(r.get("En Lista Restrictiva", "No")).lower() in ("sí", "si", "yes")

    G = nx.Graph()
    nodes_info = {}

    for _, row in siniestros.iterrows():
        sid = row.get("ID Siniestro", "")
        aseg_id = row.get("ID Asegurado", "")
        prov_id = row.get("ID Proveedor", "")
        nivel = nivel_map.get(sid, "VERDE")

        if filter_nivel and nivel not in filter_nivel:
            continue

        color_sin = NIVEL_COLOR.get(nivel, "#AAAAAA")
        score = score_map.get(sid, 0)

        G.add_node(sid, ntype="siniestro", color=color_sin, size=14, score=score,
                   label=sid, hover=f"{sid}<br>Score: {score}<br>Nivel: {nivel}<br>{alert_map.get(sid, '')[:80]}")
        nodes_info[sid] = {"ntype": "siniestro", "color": color_sin}

        if aseg_id:
            if aseg_id not in G:
                name = aseg_name.get(aseg_id, aseg_id)
                G.add_node(aseg_id, ntype="asegurado", color="#4488FF", size=20,
                           label=name[:18], hover=f"Asegurado<br>{name}<br>{aseg_id}")
                nodes_info[aseg_id] = {"ntype": "asegurado"}
            G.add_edge(aseg_id, sid)

        if prov_id and prov_id.strip():
            if prov_id not in G:
                pname = prov_name.get(prov_id, prov_id)
                pcolor = "#FF6600" if prov_restrictiva.get(prov_id) else "#FF9944"
                G.add_node(prov_id, ntype="proveedor", color=pcolor, size=18,
                           label=pname[:18], hover=f"Proveedor<br>{pname}<br>{prov_id}")
                nodes_info[prov_id] = {"ntype": "proveedor"}
            G.add_edge(sid, prov_id)

    if len(G.nodes) == 0:
        return go.Figure().update_layout(title="Sin datos para mostrar")

    # Limit to top 120 nodes by degree for performance
    if len(G.nodes) > 120:
        top = sorted(G.degree, key=lambda x: x[1], reverse=True)[:120]
        G = G.subgraph([n for n, _ in top]).copy()

    pos = nx.spring_layout(G, k=1.8, iterations=60, seed=42)

    # ── Edges ─────────────────────────────────────────────────────────
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.6, color="#555555"),
        hoverinfo="none",
    )

    # ── Node traces by type ───────────────────────────────────────────
    node_traces = []
    type_cfg = {
        "siniestro": ("circle", 12, "Siniestros"),
        "asegurado": ("diamond", 16, "Asegurados"),
        "proveedor": ("square", 14, "Proveedores"),
    }

    for ntype, (symbol, sz, legend_name) in type_cfg.items():
        nodes = [n for n in G.nodes if G.nodes[n].get("ntype") == ntype]
        if not nodes:
            continue
        trace = go.Scatter(
            x=[pos[n][0] for n in nodes],
            y=[pos[n][1] for n in nodes],
            mode="markers+text",
            name=legend_name,
            text=[G.nodes[n].get("label", n) for n in nodes],
            textposition="top center",
            textfont=dict(size=8, color="white"),
            hovertext=[G.nodes[n].get("hover", n) for n in nodes],
            hoverinfo="text",
            marker=dict(
                symbol=symbol,
                size=[G.nodes[n].get("size", sz) for n in nodes],
                color=[G.nodes[n].get("color", "#AAAAAA") for n in nodes],
                line=dict(width=1.5, color="white"),
            ),
        )
        node_traces.append(trace)

    fig = go.Figure(
        data=[edge_trace] + node_traces,
        layout=go.Layout(
            title=dict(text="Red Relacional — Asegurados · Siniestros · Proveedores", font=dict(color="white", size=15)),
            showlegend=True,
            legend=dict(font=dict(color="white")),
            hovermode="closest",
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            margin=dict(b=10, l=5, r=5, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=650,
            annotations=[
                dict(text="🔴 Siniestro rojo &nbsp;&nbsp; 🟡 Amarillo &nbsp;&nbsp; 🟢 Verde &nbsp;&nbsp; 🔷 Asegurado &nbsp;&nbsp; 🟠 Proveedor",
                     x=0.5, y=-0.02, xref="paper", yref="paper", showarrow=False,
                     font=dict(color="#888", size=11))
            ],
        ),
    )
    return fig
