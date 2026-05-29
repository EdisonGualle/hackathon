"""
Motor de scoring de fraude — hackIAthon 2026 / Aseguradora del Sur
Implementa fielmente las reglas del PDF del reto:
  · RF-01 a RF-04 → fuerzan ROJO independientemente del score numérico
  · RF-05 a RF-07 → fuerzan AMARILLO mínimo
  · Señales con puntaje suman al score 0-100
"""

import pandas as pd


def _f(val, default=0):
    try:
        return float(str(val).replace(",", "."))
    except Exception:
        return default


def _col(row: dict, *fragments):
    """Encuentra el valor de la primera columna cuyo nombre contiene todos los fragmentos."""
    for frag_group in fragments:
        parts = frag_group.lower().split()
        for rk, rv in row.items():
            rk_l = str(rk).lower()
            if all(p[:4] in rk_l for p in parts) and str(rv) not in ("", "nan", "None"):
                return rv
    return 0


# ═══════════════════════════════════════════════════════════════════════
# SCORE INDIVIDUAL
# ═══════════════════════════════════════════════════════════════════════

def score_siniestro(row: dict, pdf_fields: dict | None = None) -> dict:
    """
    Calcula score y nivel de riesgo para un siniestro.
    Retorna: {score, nivel, color, alerts, breakdown, critical_rules}
    """
    pts = []          # [(descripción, puntos, código)]
    critical_rojo = []     # Reglas que fuerzan ROJO directamente
    critical_amarillo = [] # Reglas que fuerzan AMARILLO mínimo

    cobertura = str(row.get("Cobertura", "")).lower().strip()
    lista_rest = str(_col(row, "lista restrictiva", "restrictiva")).lower()

    # ── Señal S4: Alta frecuencia siniestros mismo vehículo (placa) ───
    veh_freq = int(_f(pdf_fields.get("vehicle_freq", 0))) if pdf_fields else 0
    if veh_freq >= 3:
        pts.append(("Alta frecuencia siniestros mismo vehículo (≥3 en 18m)", 6, "S4"))
    elif veh_freq == 2:
        pts.append(("Frecuencia media siniestros mismo vehículo (2)", 3, "S4"))

    # ── Señal S5: Alta frecuencia de conductor vehículo ───
    # En la demo, el asegurado actúa como el conductor principal registrado
    cond_prev = _f(_col(row, "reclamos previos asegurado", "reclamos previos"))
    if cond_prev >= 3:
        pts.append(("Alta frecuencia del conductor (≥3)", 8, "S5"))
    elif cond_prev == 2:
        pts.append(("Frecuencia media del conductor (2)", 4, "S5"))

    # ── Señal S6: Alta frecuencia reclamos solo RC ───
    rc_freq = int(_f(pdf_fields.get("rc_sin_tercero", 0))) if pdf_fields else 0
    if "responsabilidad civil" in cobertura or cobertura == "rc":
        if rc_freq >= 3:
            pts.append(("Alta frecuencia de siniestros de Responsabilidad Civil sin tercero (≥3)", 6, "S6"))
        elif rc_freq == 2:
            pts.append(("Frecuencia media de siniestros de Responsabilidad Civil sin tercero (2)", 3, "S6"))

    # ── Señal: Borde de vigencia ──────────────────────────────────────
    d_ini = _f(_col(row, "días inicio póliza", "inicio poliza", "inicio"))
    d_fin = _f(_col(row, "días fin póliza", "fin poliza", "hasta fin"))
    borde = min(d_ini if d_ini > 0 else 999, d_fin if d_fin > 0 else 999)

    if borde < 2:       # < 48 horas → RF-05 extremo → AMARILLO mínimo
        pts.append(("Siniestro al borde extremo de vigencia (<48 h)", 8, "RF-05"))
        critical_amarillo.append("RF-05: Siniestro al borde de vigencia (<48 h)")
    elif borde <= 10:
        pts.append(("Siniestro al borde de vigencia (≤10 días)", 8, "RF-05"))
    elif borde <= 30:
        pts.append(("Siniestro cercano a vigencia (11-30 días)", 4, "RF-05"))

    # ── Señal: Frecuencia reclamos asegurado ─────────────────────────
    prev = _f(_col(row, "reclamos previos asegurado", "reclamos previos"))
    if prev >= 3:
        pts.append(("Alta frecuencia reclamos asegurado (≥3)", 8, "FREQ-A"))
    elif prev == 2:
        pts.append(("Frecuencia media reclamos asegurado (2)", 4, "FREQ-A"))

    # ── Señal: Proveedor en lista restrictiva → RF-03 ROJO ────────────
    if lista_rest in ("sí", "si", "yes", "1", "true"):
        pts.append(("Proveedor en Lista Restrictiva", 10, "RF-03"))
        critical_rojo.append("RF-03: Proveedor en Lista Restrictiva")

    # ── Señal: Documentos incompletos ────────────────────────────────
    docs_ok = str(_col(row, "docs completos", "documentos completos") or "Sí").lower()
    if docs_ok in ("no", "false", "0"):
        pts.append(("Documentos incompletos / falta evidencia", 4, "DOCS"))

    # ── Señal: Reporte tardío ─────────────────────────────────────────
    # Busca la columna que contenga AMBAS palabras: "ocurr" y "reporte"
    dias_rep = 0
    for rk, rv in row.items():
        rk_l = str(rk).lower()
        if "ocurr" in rk_l and "reporte" in rk_l:
            dias_rep = _f(rv)
            break

    if dias_rep > 7:
        pts.append((f"Reporte tardío ({int(dias_rep)} días)", 5, "RF-06"))
    elif dias_rep >= 4:
        pts.append((f"Reporte tardío ({int(dias_rep)} días)", 3, "RF-06"))

    # ── Señal: Demora denuncia en casos de Robo → RF-06 AMARILLO ─────
    if "robo" in cobertura and dias_rep > 4:
        critical_amarillo.append(f"RF-06: Demora atípica denuncia robo ({int(dias_rep)} días)")

    # ── Señal: Narrativa similar / idéntica ───────────────────────────
    sim = _f(_col(row, "similitud narrativa", "similitud"))
    if sim > 0.85:
        pts.append((f"Narrativa clonada — similitud {sim:.0%}", 8, "RF-07"))
        critical_amarillo.append(f"RF-07: Narrativa Idéntica Clonada ({sim:.0%})")
    elif sim >= 0.70:
        pts.append((f"Narrativa similar — similitud {sim:.0%}", 4, "RF-07"))

    # ── Señal: Monto vs suma asegurada ───────────────────────────────
    monto = _f(_col(row, "monto reclamado"))
    suma  = _f(_col(row, "suma asegurada"))
    if suma > 0 and monto > 0:
        ratio = monto / suma
        if ratio > 0.95:
            pts.append((f"Monto reclamado {ratio:.0%} de suma asegurada", 4, "MONTO"))
        elif ratio > 0.50:
            pts.append((f"Monto reclamado {ratio:.0%} de suma asegurada", 2, "MONTO"))

    # ── REGLAS CRÍTICAS (fuerzan nivel) ──────────────────────────────

    # RF-01: Cobertura Pérdida Total por Robo → ROJO
    if "pérdida total" in cobertura or "perdida total" in cobertura or cobertura == "robo":
        pts.append(("Cobertura de Pérdida Total / Robo (PTxRB)", 8, "RF-01"))
        critical_rojo.append("RF-01: Cobertura Pérdida Total por Robo (PTxRB)")

    # RF-02: Adulteración documental → ROJO
    if pdf_fields and pdf_fields.get("documento_alterado"):
        pts.append(("Evidencia de adulteración documental", 15, "RF-02"))
        critical_rojo.append("RF-02: Adulteración / Falsificación Documental Evidente")

    # RF-04: Dinámica físicamente imposible (Robo + Factura de reparación)
    if pdf_fields and pdf_fields.get("logica_imposible"):
        pts.append(("Dinámica del accidente físicamente imposible", 10, "RF-04"))
        critical_rojo.append("RF-04: Dinámica del Accidente Físicamente Imposible")

    # Señales adicionales desde PDFs
    if pdf_fields:
        if pdf_fields.get("ruc_invalido"):
            pts.append(("RUC del proveedor INVÁLIDO en factura", 10, "RUC"))
        if pdf_fields.get("es_madrugada"):
            pts.append(("Accidente/evento en horas de madrugada", 3, "HORA"))
        if pdf_fields.get("sin_denuncia"):
            pts.append(("Sin denuncia policial previa al parte", 4, "DENUNCIA"))
        dias_r = _f(pdf_fields.get("dias_retraso_parte", 0))
        if dias_r >= 13:
            pts.append((f"Parte elaborado {int(dias_r)} días después del hecho", 8, "RF-06"))
        elif dias_r >= 5:
            pts.append((f"Parte elaborado {int(dias_r)} días después del hecho", 4, "RF-06"))

    # ── Score numérico ────────────────────────────────────────────────
    total = min(sum(p[1] for p in pts), 100)

    # ── Clasificación final con reglas críticas ───────────────────────
    if critical_rojo:
        nivel = "ROJO"
        color = "#FF4444"
        total = max(total, 76)   # score mínimo de ROJO
    elif total >= 76:
        nivel = "ROJO"
        color = "#FF4444"
    elif critical_amarillo or total >= 41:
        nivel = "AMARILLO"
        color = "#FFAA00"
        total = max(total, 41)   # score mínimo de AMARILLO
    else:
        nivel = "VERDE"
        color = "#44BB44"

    all_critical = critical_rojo + critical_amarillo
    alerts = all_critical + [p[0] for p in pts if p[1] >= 5 and p[0] not in all_critical]

    return {
        "score": total,
        "nivel": nivel,
        "color": color,
        "alerts": alerts,
        "breakdown": [{"señal": p[0], "puntos": p[1], "codigo": p[2]} for p in pts],
        "critical_rules": all_critical,
        "critical_rojo": critical_rojo,       # reglas que fuerzan ROJO
        "critical_amarillo": critical_amarillo, # reglas que fuerzan mínimo AMARILLO
    }


# ═══════════════════════════════════════════════════════════════════════
# BATCH SCORING
# ═══════════════════════════════════════════════════════════════════════

def calculate_scores_batch(sheets: dict, pdf_map: dict | None = None) -> pd.DataFrame:
    """
    pdf_map: {sin_id: {doc_type: pdf_path}}
    Procesa los PDFs disponibles para enriquecer el scoring.
    Lee los PDFs en paralelo y cachea los resultados por path.
    """
    from src.pdf_extractor import extract_text, extract_fields
    from src.cross_validator import cross_validate
    from concurrent.futures import ThreadPoolExecutor

    siniestros = sheets.get("1_Siniestros", pd.DataFrame())
    rows = []

    # Pre-extraer todos los campos de PDFs en paralelo una sola vez
    pdf_fields_cache: dict = {}   # {sin_id: {doc_type: fields}}
    if pdf_map:
        def _extract_one(args):
            sin_id, doc_type, path = args
            try:
                text = extract_text(path)
                return (sin_id, doc_type, extract_fields(text, doc_type))
            except Exception:
                return (sin_id, doc_type, {})

        tasks = [
            (sid, dtype, path)
            for sid, docs in pdf_map.items()
            for dtype, path in docs.items()
        ]
        with ThreadPoolExecutor(max_workers=8) as ex:
            for sid, dtype, fields in ex.map(_extract_one, tasks):
                pdf_fields_cache.setdefault(sid, {})[dtype] = fields

    # Pre-computar frecuencia por vehículo (placa) — Señal S4
    placa_col = next((c for c in siniestros.columns if "placa" in c.lower()), None)
    placa_freq: dict = {}
    if placa_col:
        for p in siniestros[placa_col].dropna():
            p = str(p).strip()
            if p and p.upper() not in ("N/A", ""):
                placa_freq[p] = placa_freq.get(p, 0) + 1

    # Pre-computar datos de la hoja 3_Asegurados para el cruce de RC (S6)
    asegurados_df = sheets.get("3_Asegurados", pd.DataFrame())
    aseg_rc_map = {}
    if not asegurados_df.empty:
        for _, r in asegurados_df.iterrows():
            aseg_rc_map[str(r.get("ID Asegurado", ""))] = _f(r.get("Reclamos RC sin Tercero", 0))

    for _, row in siniestros.iterrows():
        sin_id = str(row.get("ID Siniestro", ""))
        row_dict = row.to_dict()

        pdf_signals: dict = {}
        cv_boost: int = 0

        # Inyectar cruce de reclamos de Responsabilidad Civil sin tercero (S6)
        aseg_id = str(row_dict.get("ID Asegurado", ""))
        pdf_signals["rc_sin_tercero"] = aseg_rc_map.get(aseg_id, 0)

        # Inyectar frecuencia de vehículo en pdf_signals
        placa_val = str(row_dict.get(placa_col or "", "")).strip()
        if placa_val and placa_val.upper() not in ("N/A", ""):
            pdf_signals["vehicle_freq"] = placa_freq.get(placa_val, 0)

        if sin_id in pdf_fields_cache:
            all_pdf_fields = pdf_fields_cache[sin_id]
            for fields in all_pdf_fields.values():
                pdf_signals.update({k: v for k, v in fields.items() if k != "_raw"})

            if all_pdf_fields:
                issues, _, cv_boost = cross_validate(sin_id, row_dict, all_pdf_fields)
                for iss in issues:
                    if "imposible" in iss.get("descripcion", "").lower():
                        pdf_signals["logica_imposible"] = True
                        break

        result = score_siniestro(row_dict, pdf_signals if pdf_signals else None)
        total = min(result["score"] + cv_boost, 100)

        # Re-clasificar post-boost respetando las reglas críticas por nivel
        if result["critical_rojo"]:
            # RF-01, RF-02, RF-03, RF-04 → fuerzan ROJO sin importar el score
            total = max(total, 76)
            nivel = "ROJO"
        elif total >= 76:
            nivel = "ROJO"
        elif result["critical_amarillo"] or total >= 41:
            # RF-05, RF-06, RF-07 → fuerzan AMARILLO mínimo
            total = max(total, 41)
            nivel = "AMARILLO"
        else:
            nivel = "VERDE"

        color = {"ROJO": "#FF4444", "AMARILLO": "#FFAA00", "VERDE": "#44BB44"}[nivel]

        rows.append({
            "ID Siniestro": sin_id,
            "ID Asegurado": row_dict.get("ID Asegurado", ""),
            "ID Proveedor": row_dict.get("ID Proveedor", ""),
            "Ramo": row_dict.get("Ramo", ""),
            "Cobertura": row_dict.get("Cobertura", ""),
            "Sucursal": row_dict.get("Sucursal", ""),
            "Monto Reclamado": _f(row_dict.get("Monto Reclamado ($)", 0)),
            "Score": total,
            "Nivel": nivel,
            "Color": color,
            "Alertas": " | ".join(result["alerts"][:3]) if result["alerts"] else "Sin alertas críticas",
            "N_Alertas": len(result["alerts"]),
            "Reglas Críticas": " | ".join(result["critical_rules"]) if result["critical_rules"] else "",
        })

    return pd.DataFrame(rows)
