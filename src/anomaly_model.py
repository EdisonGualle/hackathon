"""
Modelo de Anomalías — Isolation Forest
Detecta siniestros atípicos que las reglas de negocio podrían no capturar.
Complementa el score basado en reglas con un score estadístico de rareza.
"""

import os
import json
from functools import lru_cache
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


@lru_cache(maxsize=1)
def _provincia_lines():
    """Coordenadas (lon, lat) de los límites provinciales de Ecuador para dibujarlos
    como líneas de fondo en el mapa. Devuelve ([], []) si no está el GeoJSON."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "ecuador_provincias.geojson")
    lons, lats = [], []
    try:
        with open(path, encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj.get("features", []):
            geom = feat.get("geometry", {}) or {}
            coords = geom.get("coordinates", [])
            polys = [coords] if geom.get("type") == "Polygon" else coords
            for poly in polys:
                for ring in poly:
                    for pt in ring:
                        lons.append(pt[0]); lats.append(pt[1])
                    lons.append(None); lats.append(None)
    except Exception:
        return [], []
    return lons, lats
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ECUADOR_CITIES = {
    "Quito":        (-0.1807, -78.4678),
    "Guayaquil":    (-2.1962, -79.8862),
    "Cuenca":       (-2.9001, -79.0059),
    "Ambato":       (-1.2490, -78.6135),
    "Portoviejo":   (-1.0545, -80.4545),
    "Riobamba":     (-1.6635, -78.6541),
    "Loja":         (-3.9928, -79.2042),
    "Ibarra":       (0.3517,  -78.1221),
    "Manta":        (-0.9677, -80.7089),
    "Esmeraldas":   (0.9592,  -79.6537),
    "Machala":      (-3.2581, -79.9554),
    "Santo Domingo":(-0.2500, -79.1600),
    "Babahoyo":     (-1.8013, -79.5337),
}

FEATURE_LABELS = {
    "dias_inicio":   "Días desde inicio póliza",
    "dias_fin":      "Días hasta fin póliza",
    "monto_rec":     "Monto reclamado ($)",
    "monto_est":     "Monto estimado ($)",
    "suma_aseg":     "Suma asegurada ($)",
    "ratio_monto":   "Ratio monto/suma asegurada",
    "reclamos_prev": "N° reclamos previos asegurado",
    "similitud":     "Similitud narrativa",
    "dias_reporte":  "Días para reportar",
    "docs_ok":       "Documentos completos (0=No)",
}


def _find_col(df: pd.DataFrame, *fragments: str) -> str | None:
    for frag in fragments:
        for c in df.columns:
            if frag.lower() in c.lower():
                return c
    return None


def build_feature_matrix(sheets: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Construye la matriz de features para Isolation Forest.
    Retorna (features_df, meta_df) donde meta_df tiene IDs para reidentificar filas.
    """
    df = sheets.get("1_Siniestros", pd.DataFrame()).copy()
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    meta = df[["ID Siniestro"]].copy()

    c_ini  = _find_col(df, "inicio")
    c_fin  = _find_col(df, "hasta fin", "fin p")
    c_mon  = _find_col(df, "monto reclamado")
    c_est  = _find_col(df, "monto estimado")
    c_suma = _find_col(df, "suma asegurada")
    c_prev = _find_col(df, "reclamos previos")
    c_sim  = _find_col(df, "similitud")
    c_doc  = _find_col(df, "docs")
    c_rep_list = [c for c in df.columns if "ocurr" in c.lower() and "reporte" in c.lower()]
    c_rep = c_rep_list[0] if c_rep_list else None

    def num(col): return pd.to_numeric(df[col], errors="coerce").fillna(0) if col else pd.Series(0, index=df.index)

    dias_inicio = num(c_ini)
    dias_fin    = num(c_fin)
    monto_rec   = num(c_mon)
    monto_est   = num(c_est)
    suma_aseg   = num(c_suma)
    reclamos    = num(c_prev)
    similitud   = num(c_sim)
    dias_rep    = num(c_rep)
    docs_ok     = (df[c_doc].str.lower() == "no").astype(int) if c_doc else pd.Series(0, index=df.index)

    ratio = (monto_rec / suma_aseg.replace(0, np.nan)).fillna(0).clip(0, 3)

    feat = pd.DataFrame({
        "dias_inicio":   dias_inicio,
        "dias_fin":      dias_fin,
        "monto_rec":     monto_rec,
        "monto_est":     monto_est,
        "suma_aseg":     suma_aseg,
        "ratio_monto":   ratio,
        "reclamos_prev": reclamos,
        "similitud":     similitud,
        "dias_reporte":  dias_rep,
        "docs_ok":       docs_ok,
    })

    return feat, meta


def train_model(sheets: dict, contamination: float = 0.30) -> dict:
    """
    Entrena Isolation Forest y retorna un dict con modelo, scaler y scores.
    contamination: fracción esperada de anomalías (ajustado a ~30% del dataset).
    """
    feat, meta = build_feature_matrix(sheets)
    if feat.empty:
        return {}

    scaler = StandardScaler()
    X = scaler.fit_transform(feat)

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)

    raw_scores = model.decision_function(X)   # más negativo = más anómalo
    predictions = model.predict(X)            # -1 = anomalía, 1 = normal

    # Convertir a escala 0-100 (100 = más anómalo)
    s_min, s_max = raw_scores.min(), raw_scores.max()
    anomaly_scores = ((s_max - raw_scores) / (s_max - s_min) * 100).round(1)

    result_df = meta.copy()
    result_df["Anomaly_Score"] = anomaly_scores
    result_df["Es_Anomalia"] = (predictions == -1)
    result_df["Raw_Score"] = raw_scores

    # Importancia aproximada: varianza de cada feature entre anomalías vs normal
    feat_imp = {}
    anomaly_mask = predictions == -1
    for col in feat.columns:
        mean_anom   = feat.loc[anomaly_mask, col].mean()
        mean_normal = feat.loc[~anomaly_mask, col].mean()
        feat_imp[FEATURE_LABELS.get(col, col)] = abs(mean_anom - mean_normal)

    total_imp = sum(feat_imp.values()) or 1
    feat_imp_pct = {k: round(v / total_imp * 100, 1) for k, v in feat_imp.items()}
    feat_imp_pct = dict(sorted(feat_imp_pct.items(), key=lambda x: -x[1]))

    return {
        "model": model,
        "scaler": scaler,
        "scores_df": result_df,
        "feature_importance": feat_imp_pct,
        "n_anomalies": int(anomaly_mask.sum()),
        "contamination": contamination,
        "feature_names": list(feat.columns),
    }


def get_city_ranking(scores_df: pd.DataFrame, siniestros_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el ranking completo de ciudades con métricas por nivel.
    Retorna DataFrame con: Ciudad, Total, Rojos, Amarillos, Verdes, % de cada uno, Score promedio, Nivel predominante.
    """
    merged = siniestros_df.merge(
        scores_df[["ID Siniestro", "Nivel", "Score"]],
        on="ID Siniestro", how="left",
    )
    merged["Nivel"] = merged["Nivel"].fillna("VERDE")
    suc_col = next((c for c in siniestros_df.columns if "sucursal" in c.lower()), None)
    if not suc_col:
        return pd.DataFrame()

    grp = merged.groupby(suc_col).agg(
        Total=("ID Siniestro", "count"),
        Rojos=("Nivel", lambda x: (x == "ROJO").sum()),
        Amarillos=("Nivel", lambda x: (x == "AMARILLO").sum()),
        Score_Prom=("Score", "mean"),
    ).reset_index().rename(columns={suc_col: "Ciudad"})

    grp["Verdes"] = grp["Total"] - grp["Rojos"] - grp["Amarillos"]
    grp["Pct_Rojo"]      = (grp["Rojos"]     / grp["Total"] * 100).round(1)
    grp["Pct_Amarillo"]  = (grp["Amarillos"] / grp["Total"] * 100).round(1)
    grp["Pct_Verde"]     = (grp["Verdes"]    / grp["Total"] * 100).round(1)
    grp["Score_Prom"]    = grp["Score_Prom"].round(1)

    def _nivel_pred(r):
        counts = {"ROJO": r["Rojos"], "AMARILLO": r["Amarillos"], "VERDE": r["Verdes"]}
        return max(counts, key=counts.get)
    grp["Nivel_Predominante"] = grp.apply(_nivel_pred, axis=1)

    return grp


def build_ecuador_map(
    scores_df: pd.DataFrame,
    siniestros_df: pd.DataFrame,
    filter_nivel: str | None = None,
) -> "go.Figure":
    """Mapa de Ecuador — burbujas pequeñas por ciudad, coloreadas por nivel predominante."""
    import plotly.graph_objects as go

    merged = siniestros_df.merge(
        scores_df[["ID Siniestro", "Nivel", "Score"]],
        on="ID Siniestro", how="left"
    )
    merged["Nivel"] = merged["Nivel"].fillna("VERDE")

    suc_col = next((c for c in siniestros_df.columns if "sucursal" in c.lower()), None)
    if not suc_col:
        return go.Figure()

    grp = merged.groupby(suc_col).agg(
        Total=("ID Siniestro", "count"),
        Rojos=("Nivel", lambda x: (x == "ROJO").sum()),
        Amarillos=("Nivel", lambda x: (x == "AMARILLO").sum()),
        Score_Prom=("Score", "mean"),
    ).reset_index()

    nivel_color = {"ROJO": "#E74C3C", "AMARILLO": "#F39C12", "VERDE": "#27AE60"}

    # Color de cada ciudad por CONCENTRACIÓN DE RIESGO (% de rojos), no por
    # nivel predominante — así las ciudades con más alertas resaltan en rojo
    # en vez de verse casi todas verdes.
    grp["Verdes"] = grp["Total"] - grp["Rojos"] - grp["Amarillos"]

    def _nivel_riesgo(r):
        total = max(int(r["Total"]), 1)
        pct_rojo = r["Rojos"] / total * 100
        pct_riesgo = (r["Rojos"] + r["Amarillos"]) / total * 100
        if pct_rojo >= 25:
            return "ROJO"
        if pct_rojo >= 8 or pct_riesgo >= 30:
            return "AMARILLO"
        return "VERDE"
    grp["Nivel_Ciudad"] = grp.apply(_nivel_riesgo, axis=1)

    nivel_to_col = {"ROJO": "Rojos", "AMARILLO": "Amarillos", "VERDE": "Verdes"}
    traces = []

    # ── Modo TODOS: cada ciudad coloreada por nivel predominante ─────
    if not filter_nivel or filter_nivel == "Todos":
        for nivel, color in nivel_color.items():
            lats, lons, names, sizes, hovers = [], [], [], [], []
            for _, row in grp.iterrows():
                city   = row[suc_col]
                coords = next(
                    (v for k, v in ECUADOR_CITIES.items()
                     if k.lower() in city.lower() or city.lower() in k.lower()),
                    None,
                )
                if not coords or row["Nivel_Ciudad"] != nivel:
                    continue
                sz = max(int(np.log1p(row["Total"]) * 5 + 6), 8)
                sz = min(sz, 22)
                lats.append(coords[0]); lons.append(coords[1])
                names.append(city); sizes.append(sz)
                hovers.append(
                    f"<b>{city}</b><br>"
                    f"Total: {row['Total']} siniestros<br>"
                    f"🔴 Rojos: {row['Rojos']} ({row['Rojos']/row['Total']*100:.0f}%)<br>"
                    f"🟡 Amarillos: {row['Amarillos']} ({row['Amarillos']/row['Total']*100:.0f}%)<br>"
                    f"🟢 Verdes: {row['Verdes']} ({row['Verdes']/row['Total']*100:.0f}%)<br>"
                    f"Score promedio: {row['Score_Prom']:.0f}"
                )
            if not lats:
                continue
            _lbl = {"ROJO":"Alta concentración","AMARILLO":"Riesgo medio","VERDE":"Bajo riesgo"}[nivel]
            traces.append(go.Scattergeo(
                lat=lats, lon=lons,
                name=_lbl,
                hovertext=hovers, hoverinfo="text",
                mode="markers+text", text=names,
                textposition="top center",
                textfont=dict(size=10, color="#1B4F8A"),
                marker=dict(size=sizes, color=color, opacity=0.80,
                            line=dict(width=1, color="white")),
            ))

    # ── Modo FILTRO POR NIVEL: todas las ciudades en ese color, tamaño = casos de ese nivel ─
    else:
        color = nivel_color[filter_nivel]
        count_col = nivel_to_col[filter_nivel]
        emoji = {"ROJO":"🔴","AMARILLO":"🟡","VERDE":"🟢"}[filter_nivel]

        lats, lons, names, sizes, hovers = [], [], [], [], []
        for _, row in grp.iterrows():
            city   = row[suc_col]
            coords = next(
                (v for k, v in ECUADOR_CITIES.items()
                 if k.lower() in city.lower() or city.lower() in k.lower()),
                None,
            )
            if not coords:
                continue
            casos_nivel = int(row[count_col])
            if casos_nivel == 0:
                # Esa ciudad no tiene casos de ese nivel — saltar
                continue
            # Tamaño proporcional al número de casos del nivel
            sz = max(int(np.log1p(casos_nivel) * 6 + 8), 10)
            sz = min(sz, 28)
            lats.append(coords[0]); lons.append(coords[1])
            names.append(city); sizes.append(sz)
            pct = casos_nivel / row["Total"] * 100
            hovers.append(
                f"<b>{city}</b><br>"
                f"{emoji} {filter_nivel}: <b>{casos_nivel}</b> casos ({pct:.0f}%)<br>"
                f"Total siniestros: {row['Total']}<br>"
                f"Score promedio: {row['Score_Prom']:.0f}"
            )

        if lats:
            traces.append(go.Scattergeo(
                lat=lats, lon=lons,
                name=filter_nivel.capitalize(),
                hovertext=hovers, hoverinfo="text",
                mode="markers+text", text=names,
                textposition="top center",
                textfont=dict(size=10, color="#1B4F8A"),
                marker=dict(size=sizes, color=color, opacity=0.80,
                            line=dict(width=1.2, color="white")),
            ))

    # Líneas de provincias de Ecuador como fondo (debajo de las ciudades)
    _plons, _plats = _provincia_lines()
    if _plons:
        traces.insert(0, go.Scattergeo(
            lon=_plons, lat=_plats, mode="lines",
            line=dict(width=0.6, color="#B7C2D0"),
            hoverinfo="skip", showlegend=False,
        ))

    fig = go.Figure(data=traces)
    title_text = "Distribución de Alertas por Ciudad — Ecuador"
    if filter_nivel and filter_nivel != "Todos":
        em = {"ROJO":"🔴","AMARILLO":"🟡","VERDE":"🟢"}.get(filter_nivel, "")
        title_text = f"Ciudades con nivel predominante {em} {filter_nivel}"
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(color="#1B4F8A", size=13),
        ),
        showlegend=True,
        legend=dict(
            orientation="h", y=-0.05, x=0.5, xanchor="center",
            font=dict(color="#1B4F8A"),
            bgcolor="rgba(235,245,251,0.8)",
            bordercolor="#D6EAF8", borderwidth=1,
        ),
        geo=dict(
            scope="south america",
            center=dict(lat=-1.8, lon=-78.5),
            projection_scale=6,            # zoom más alejado → puntos no se solapan
            showland=True,  landcolor="#F0F6FF",
            showocean=True, oceancolor="#EBF5FB",
            showcoastlines=True, coastlinecolor="#AED6F1",
            showcountries=True, countrycolor="#D6EAF8",
            showframe=False,
        ),
        paper_bgcolor="white",
        margin=dict(l=0, r=0, t=45, b=30),
        height=420,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════
# CLUSTERS DE NARRATIVA CLONADA
# ══════════════════════════════════════════════════════════════════════

def compute_narrative_clusters(
    siniestros_df: pd.DataFrame,
    scores_df: pd.DataFrame,
    threshold: float = 0.85,
    only_risky: bool = True,
    max_group_size: int = 25,
) -> dict:
    """
    Detecta grupos de siniestros con narrativas similares usando TF-IDF + cosine.
    Agrupa por descripción casi idéntica (clonada) y señala grupos con al menos
    un siniestro ROJO o AMARILLO como 'posible anillo de fraude coordinado'.
    """
    desc_col = next((c for c in siniestros_df.columns if "descrip" in c.lower()), None)
    if not desc_col:
        return {"groups": [], "pairs": [], "n_groups": 0, "n_nodes": 0, "n_pairs": 0}

    ids   = siniestros_df["ID Siniestro"].tolist()
    texts = siniestros_df[desc_col].fillna("sin descripcion").tolist()

    vec = TfidfVectorizer(
        min_df=1, max_df=0.85, ngram_range=(1, 2),
        analyzer="word", lowercase=True,
        strip_accents="unicode", sublinear_tf=True,
    )
    X   = vec.fit_transform(texts)
    sim = cosine_similarity(X)

    score_map = scores_df.set_index("ID Siniestro")["Score"].to_dict() if not scores_df.empty else {}
    nivel_map = scores_df.set_index("ID Siniestro")["Nivel"].to_dict() if not scores_df.empty else {}
    cob_map   = siniestros_df.set_index("ID Siniestro")["Cobertura"].to_dict() if "Cobertura" in siniestros_df.columns else {}

    # ── Agrupar siniestros con narrativa similar (Union-Find) ─────────
    parent = list(range(len(ids)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if sim[i, j] >= threshold:
                union(i, j)

    groups_by_root: dict = {}
    for i, sid in enumerate(ids):
        r = find(i)
        groups_by_root.setdefault(r, []).append(i)

    groups = []
    pairs = []
    for root, members in groups_by_root.items():
        if len(members) < 2:
            continue
        # Submuestreo si es muy grande
        if len(members) > max_group_size:
            members = members[:max_group_size]

        member_ids = [ids[m] for m in members]
        niveles    = [nivel_map.get(mid, "VERDE") for mid in member_ids]
        has_risk   = any(n in ("ROJO","AMARILLO") for n in niveles)

        if only_risky and not has_risk:
            continue

        n_rojo = sum(1 for n in niveles if n == "ROJO")
        n_amar = sum(1 for n in niveles if n == "AMARILLO")

        groups.append({
            "narrativa":  texts[members[0]][:120],
            "tamaño":     len(member_ids),
            "siniestros": member_ids,
            "n_rojo":     n_rojo,
            "n_amarillo": n_amar,
            "n_verde":    len(member_ids) - n_rojo - n_amar,
            "score_max":  max((score_map.get(mid, 0) for mid in member_ids), default=0),
        })

        # Para el grafo: conectar consecutivamente dentro del grupo (estrella)
        center = members[0]
        for m in members[1:]:
            pairs.append({
                "sin_a":   ids[center],
                "sin_b":   ids[m],
                "sim":     round(float(sim[center, m]), 3),
                "score_a": score_map.get(ids[center], 0),
                "score_b": score_map.get(ids[m], 0),
                "nivel_a": nivel_map.get(ids[center], "VERDE"),
                "nivel_b": nivel_map.get(ids[m], "VERDE"),
            })

    groups = sorted(groups, key=lambda g: (-g["n_rojo"], -g["tamaño"]))

    nodes = set()
    for p in pairs:
        nodes.add(p["sin_a"]); nodes.add(p["sin_b"])

    return {
        "groups":    groups,
        "pairs":     pairs,
        "n_groups":  len(groups),
        "n_pairs":   len(pairs),
        "n_nodes":   len(nodes),
        "score_map": score_map,
        "nivel_map": nivel_map,
    }


def build_narrative_graph(clusters: dict) -> "go.Figure":
    """Renderiza el grafo de narrativas clonadas con Plotly."""
    import plotly.graph_objects as go
    import networkx as nx

    pairs     = clusters.get("pairs", [])
    score_map = clusters.get("score_map", {})
    nivel_map = clusters.get("nivel_map", {})

    if not pairs:
        fig = go.Figure()
        fig.update_layout(
            title="Sin pares de narrativas similares detectados",
            paper_bgcolor="white",
        )
        return fig

    G = nx.Graph()
    for p in pairs:
        G.add_node(p["sin_a"], nivel=p["nivel_a"], score=p["score_a"])
        G.add_node(p["sin_b"], nivel=p["nivel_b"], score=p["score_b"])
        G.add_edge(p["sin_a"], p["sin_b"], weight=p["sim"])

    pos = nx.spring_layout(G, k=2.5, iterations=80, seed=42)

    nivel_color = {"ROJO": "#E74C3C", "AMARILLO": "#F39C12", "VERDE": "#27AE60"}

    # Aristas: grosor proporcional a similitud
    edge_traces = []
    for u, v, d in G.edges(data=True):
        x0, y0 = pos[u]; x1, y1 = pos[v]
        sim_val = d.get("weight", 0.7)
        width   = max(1, (sim_val - 0.6) * 20)
        color   = "#E74C3C" if sim_val >= 0.90 else "#F39C12" if sim_val >= 0.75 else "#AED6F1"
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=width, color=color),
            hoverinfo="none", showlegend=False,
        ))

    # Nodos por nivel
    node_traces = []
    for nivel, color in nivel_color.items():
        nodes = [n for n, d in G.nodes(data=True) if d.get("nivel") == nivel]
        if not nodes:
            continue
        node_traces.append(go.Scatter(
            x=[pos[n][0] for n in nodes],
            y=[pos[n][1] for n in nodes],
            mode="markers+text",
            name=f"{'🔴' if nivel=='ROJO' else '🟡' if nivel=='AMARILLO' else '🟢'} {nivel}",
            text=nodes,
            textposition="top center",
            textfont=dict(size=9, color="#1B4F8A"),
            hovertext=[
                f"{n}<br>Score: {G.nodes[n].get('score',0)}<br>Nivel: {G.nodes[n].get('nivel','')}"
                for n in nodes
            ],
            hoverinfo="text",
            marker=dict(
                size=14, color=color, opacity=0.85,
                line=dict(width=2, color="white"),
            ),
        ))

    fig = go.Figure(data=edge_traces + node_traces)
    fig.update_layout(
        title=dict(
            text=f"Red de Narrativas Clonadas — {len(pairs)} pares similares | {G.number_of_nodes()} siniestros involucrados",
            font=dict(color="#1B4F8A", size=13),
        ),
        showlegend=True,
        legend=dict(font=dict(color="#1B4F8A"), bgcolor="rgba(235,245,251,0.9)",
                    bordercolor="#D6EAF8", borderwidth=1),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=5, r=5, t=50, b=5),
        height=500,
    )
    return fig
