"""
Generador de Reporte PDF Ejecutivo — FRAUDIA
Usa fpdf2 para producir un PDF profesional descargable desde la app.
"""

from datetime import datetime
import io
import pandas as pd


def _safe(text) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


def generate_pdf_report(
    scores_df: pd.DataFrame,
    sheets: dict,
    combined_df: pd.DataFrame | None = None,
) -> bytes:
    from fpdf import FPDF

    AZUL    = (27,  79,  138)
    AZUL2   = (41, 128, 185)
    ROJO    = (231, 76,  60)
    AMAR    = (243, 156, 18)
    VERDE   = (39,  174, 96)
    GRIS    = (93,  109, 126)
    GRIS_BG = (235, 245, 251)

    # DataFrame principal
    main_df = combined_df if combined_df is not None else scores_df
    score_col = "Score_Final" if "Score_Final" in main_df.columns else "Score"
    nivel_col = "Nivel_Final" if "Nivel_Final" in main_df.columns else "Nivel"

    top10   = main_df.nlargest(10, score_col)
    rojos   = (main_df[nivel_col] == "ROJO").sum()
    amarillos = (main_df[nivel_col] == "AMARILLO").sum()
    verdes  = (main_df[nivel_col] == "VERDE").sum()
    total   = len(main_df)

    monto_col = "Monto Reclamado" if "Monto Reclamado" in main_df.columns else None
    total_monto  = main_df[monto_col].sum() if monto_col else 0
    riesgo_monto = main_df[main_df[nivel_col].isin(["ROJO","AMARILLO"])][monto_col].sum() if monto_col else 0
    ahorro_est   = riesgo_monto * 0.20

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(*AZUL)
            self.rect(0, 0, 210, 22, "F")
            self.set_font("Helvetica", "B", 15)
            self.set_text_color(255, 255, 255)
            self.set_y(5)
            self.cell(0, 8, "  FRAUDIA - Reporte Ejecutivo de Alertas", ln=False)
            self.set_font("Helvetica", "", 9)
            self.set_y(13)
            self.cell(0, 5, f"  Aseguradora del Sur  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  Uso interno - Confidencial", ln=True)
            self.set_text_color(0, 0, 0)
            self.ln(6)

        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*GRIS)
            self.cell(0, 6,
                "FRAUDIA genera ALERTAS de revision. No constituye acusacion formal de fraude. "
                f"Pagina {self.page_no()}",
                align="C",
            )

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Resumen ejecutivo ─────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 8, "1. Resumen Ejecutivo", ln=True)
    pdf.set_draw_color(*AZUL2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # KPI boxes
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    kpis = [
        (str(total), "Total siniestros analizados", AZUL),
        (str(rojos), "Criticos (ROJO)", ROJO),
        (str(amarillos), "Medios (AMARILLO)", AMAR),
        (str(verdes), "Bajos (VERDE)", VERDE),
    ]
    x0 = pdf.get_x()
    y0 = pdf.get_y()
    box_w = 43
    for i, (val, lbl, color) in enumerate(kpis):
        bx = x0 + i * (box_w + 2)
        pdf.set_fill_color(235, 245, 251)
        pdf.rect(bx, y0, box_w, 18, "F")
        pdf.set_xy(bx, y0 + 1)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*color)
        pdf.cell(box_w, 9, val, align="C", ln=False)
        pdf.set_xy(bx, y0 + 10)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*GRIS)
        pdf.cell(box_w, 5, _safe(lbl), align="C")
    pdf.ln(24)

    # Montos
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(*GRIS_BG)
    pdf.set_draw_color(*AZUL2)
    pdf.rect(10, pdf.get_y(), 190, 22, "FD")
    pdf.set_xy(12, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*AZUL)
    pdf.cell(63, 6, f"Total reclamado:  ${total_monto:,.0f}", ln=False)
    pdf.cell(63, 6, f"Monto en riesgo:  ${riesgo_monto:,.0f}", ln=False)
    pdf.cell(63, 6, f"Ahorro estimado 20%:  ${ahorro_est:,.0f}", ln=True)
    pdf.set_xy(12, pdf.get_y())
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    pct = (riesgo_monto / total_monto * 100) if total_monto > 0 else 0
    pdf.cell(0, 5, f"El {pct:.1f}% del monto total reclamado requiere revision prioritaria.", ln=True)
    pdf.ln(10)

    # ── Top 10 casos criticos ─────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 8, "2. Top 10 Siniestros de Mayor Riesgo", ln=True)
    pdf.set_draw_color(*AZUL2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Cabecera tabla
    headers = ["#", "ID Siniestro", "Cobertura", "Score", "Nivel", "Monto ($)", "Alerta Principal"]
    widths  = [8, 26, 35, 16, 22, 26, 57]
    pdf.set_fill_color(*AZUL)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, _safe(h), border=1, fill=True, align="C")
    pdf.ln()

    # Filas
    pdf.set_font("Helvetica", "", 8)
    for idx, (_, row) in enumerate(top10.iterrows()):
        nivel = str(row.get(nivel_col, ""))
        score = row.get(score_col, 0)
        nc = ROJO if nivel == "ROJO" else AMAR if nivel == "AMARILLO" else VERDE
        pdf.set_text_color(*nc if idx % 2 == 0 else (0,0,0))
        pdf.set_fill_color(245, 248, 252) if idx % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        alerta = str(row.get("Alertas", ""))[:55]
        monto  = f"{row.get('Monto Reclamado', 0):,.0f}" if monto_col else "—"
        vals   = [str(idx+1), str(row.get("ID Siniestro","")),
                  _safe(str(row.get("Cobertura",""))[:18]),
                  str(int(score)), _safe(nivel), monto, _safe(alerta)]
        pdf.set_text_color(0, 0, 0)
        for val, w in zip(vals, widths):
            pdf.cell(w, 6, val, border=1, fill=True)
        pdf.ln()

    pdf.ln(8)

    # ── Distribucion por ramo ─────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 8, "3. Distribucion por Ramo", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    ramo_stats = main_df.groupby("Ramo").agg(
        Total=(nivel_col, "count"),
        Rojos=(nivel_col, lambda x: (x=="ROJO").sum()),
    ).reset_index()
    ramo_stats["Pct_Rojo"] = (ramo_stats["Rojos"]/ramo_stats["Total"]*100).round(1)

    pdf.set_fill_color(*AZUL)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for h, w in zip(["Ramo","Total","Casos ROJO","% Criticos"], [60,35,40,55]):
        pdf.cell(w, 7, h, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for _, r in ramo_stats.iterrows():
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 6, _safe(r["Ramo"]),    border=1)
        pdf.cell(35, 6, str(r["Total"]),      border=1, align="C")
        pdf.cell(40, 6, str(r["Rojos"]),      border=1, align="C")
        pdf.cell(55, 6, f"{r['Pct_Rojo']}%", border=1, align="C")
        pdf.ln()
    pdf.ln(8)

    # ── Seccion etica y limitaciones ─────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 8, "4. Etica, Limitaciones y Declaracion de Uso", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    disclaimers = [
        ("Proposito del sistema",
         "FRAUDIA genera alertas de posible irregularidad para apoyar la revision humana. "
         "NO acusa formalmente de fraude. La decision final es SIEMPRE del analista especializado."),
        ("Falsos positivos",
         "El modelo puede generar falsos positivos. Se estima una tasa del 15-20%. "
         "Ningun siniestro debe ser rechazado unicamente por la alerta del sistema."),
        ("Datos sinteticos",
         "Este prototipo fue entrenado con datos sinteticos. En produccion, los parametros "
         "deben recalibrarse con datos historicos reales de la aseguradora."),
        ("Revision humana obligatoria",
         "Todo caso ROJO debe pasar por revision de la Unidad Antifraude antes de cualquier "
         "accion. FRAUDIA es una herramienta de apoyo, no un decisor automatico."),
        ("Sesgo y equidad",
         "Se recomienda auditar periodicamente el modelo para detectar sesgos por ramo, "
         "ciudad o canal de venta que puedan afectar la equidad del proceso."),
    ]

    pdf.set_font("Helvetica", "", 10)
    for title, body in disclaimers:
        pdf.set_fill_color(*GRIS_BG)
        pdf.set_draw_color(*AZUL2)
        pdf.set_text_color(*AZUL)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, f"  {_safe(title)}", fill=True, border="LRB", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, f"  {_safe(body)}", border="LRB")
        pdf.ln(3)

    # Firma
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 5, f"Reporte generado automaticamente por FRAUDIA v1.0 el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}", ln=True)
    pdf.cell(0, 5, "Para consultas tecnicas contactar al equipo de Tecnologia - Aseguradora del Sur", ln=True)
    pdf.ln(15)
    pdf.set_draw_color(*AZUL)
    pdf.line(10, pdf.get_y(), 80, pdf.get_y())
    pdf.set_xy(10, pdf.get_y() + 2)
    pdf.cell(70, 5, "Firma Analista Antifraude", align="C")
    pdf.set_xy(120, pdf.get_y())
    pdf.line(120, pdf.get_y() - 2, 200, pdf.get_y() - 2)
    pdf.cell(80, 5, "Firma Jefatura de Siniestros", align="C")

    return bytes(pdf.output())
