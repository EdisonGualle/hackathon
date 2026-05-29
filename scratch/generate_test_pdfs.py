import os
import sys

# Asegurar que reportlab esté instalado
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    import subprocess
    print("Instalando reportlab para generación de PDFs...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

# Carpeta de salida de pruebas
output_dir = r"c:\Users\PC\Desktop\fraudia\fraudia\data\dataset\TEST_DOCUMENTS"
os.makedirs(output_dir, exist_ok=True)

styles = getSampleStyleSheet()

# Estilos personalizados
title_style = ParagraphStyle(
    'TitleStyle',
    parent=styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=16,
    leading=20,
    textColor=colors.HexColor('#1B4F8A'),
    alignment=1 # Centrado
)

subtitle_style = ParagraphStyle(
    'SubTitleStyle',
    parent=styles['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=12,
    leading=16,
    textColor=colors.HexColor('#2C3E50'),
    spaceAfter=10
)

body_style = ParagraphStyle(
    'BodyStyle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=10,
    leading=14,
    textColor=colors.HexColor('#1A3A5C')
)

bold_style = ParagraphStyle(
    'BoldStyle',
    parent=body_style,
    fontName='Helvetica-Bold'
)

alert_style = ParagraphStyle(
    'AlertStyle',
    parent=body_style,
    fontName='Helvetica-Bold',
    textColor=colors.HexColor('#E74C3C')
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. FACTURA DE PRUEBA ALTERADA (SIN-0030)
# ─────────────────────────────────────────────────────────────────────────────
def gen_factura():
    pdf_path = os.path.join(output_dir, "TEST_FACTURA_ALTERADA_SIN-0030.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    story = []

    # Cabecera
    story.append(Paragraph("TALLER AUTOPRO REPARACIONES S.A.", title_style))
    story.append(Spacer(1, 15))

    # Info Factura
    data = [
        [Paragraph("Factura No:", bold_style), Paragraph("FACT-TEST-0030", body_style)],
        [Paragraph("RUC Taller:", bold_style), Paragraph("1792345678001", body_style)],
        [Paragraph("Fecha:", bold_style), Paragraph("2024-10-15", body_style)],
        [Paragraph("Cliente:", bold_style), Paragraph("Gloria Susana Pacheco", body_style)],
        [Paragraph("Placa Vehículo:", bold_style), Paragraph("MNT-9999", alert_style)], # <--- ALTERADA (Excel es MNT-7384)
        [Paragraph("Siniestro ID:", bold_style), Paragraph("SIN-0030", bold_style)]
    ]
    t = Table(data, colWidths=[120, 300])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D6EAF8')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EBF5FB')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Detalle de servicios
    story.append(Paragraph("Detalle del Servicio Realizado", subtitle_style))
    items = [
        ["Cantidad", "Descripción del Repuesto / Servicio", "Precio Unit.", "Total"],
        ["1", "Cambio de guardafangos delantero", "$450.00", "$450.00"],
        ["1", "Enderezada y pintura de puerta lateral", "$350.00", "$350.00"],
        ["1", "Faro delantero derecho halógeno", "$180.00", "$180.00"],
        ["-", "Mano de Obra Especializada", "-", "$3,989.00"],
        ["-", "TOTAL A PAGAR", "-", "$4,879.00"] # <--- Monto coincide
    ]
    t_items = Table(items, colWidths=[60, 240, 60, 60])
    t_items.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B4F8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 30))

    # Marca crítica de adulteración
    story.append(Paragraph("ADVERTENCIA DE SEGURIDAD INTERNA: DOCUMENTO ALTERADO", alert_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Nota: Este archivo simula una alteración para validación del detector antifraude.", body_style))

    doc.build(story)
    print(f"Generado: {pdf_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. PARTE POLICIAL SOSPECHOSO (SIN-0030)
# ─────────────────────────────────────────────────────────────────────────────
def gen_parte():
    pdf_path = os.path.join(output_dir, "TEST_PARTE_POLICIAL_SOSPECHOSO_SIN-0030.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    story = []

    # Cabecera
    story.append(Paragraph("POLICÍA NACIONAL DEL ECUADOR", title_style))
    story.append(Paragraph("PARTE POLICIAL DE TRÁNSITO", subtitle_style))
    story.append(Spacer(1, 15))

    # Datos Generales
    data = [
        [Paragraph("Parte No:", bold_style), Paragraph("PP-TEST-0030", body_style)],
        [Paragraph("Siniestro Vinculado:", bold_style), Paragraph("SIN-0030", bold_style)],
        [Paragraph("Placa Vehículo A:", bold_style), Paragraph("AZY-9999", alert_style)], # <--- ALTERADA
        [Paragraph("Fecha del Hecho:", bold_style), Paragraph("2024-10-06", body_style)],
        [Paragraph("Fecha de Elaboracion:", bold_style), Paragraph("2024-10-21", alert_style)], # <--- 15 días después
        [Paragraph("Hora Aproximada:", bold_style), Paragraph("02:30", alert_style)], # <--- Madrugada
        [Paragraph("Apellidos y Nombres:", bold_style), Paragraph("Juan Carlos Choque", body_style)],
        [Paragraph("Cedula:", bold_style), Paragraph("1712345678", body_style)],
    ]
    t = Table(data, colWidths=[140, 280])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D6EAF8')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EBF5FB')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Relato del Hecho
    story.append(Paragraph("Descripción del Evento / Observaciones del Agente", subtitle_style))
    relato = (
        "El presente informe policial de tránsito detalla que el vehículo A colisionó contra un poste de alumbrado público. "
        "Se constata que el conductor se retiró del lugar del siniestro. Se indica además que **EL CIUDADANO SE RETIRÓ SIN DENUNCIA PREVIA AL PARTE POLICIAL**. "
        "El parte policial fue elaborado 15 días después del hecho debido a demoras de trámite administrativo."
    )
    story.append(Paragraph(relato, body_style))
    story.append(Spacer(1, 15))

    doc.build(story)
    print(f"Generado: {pdf_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. DECLARACION CON PLACA DISCREPANTE (SIN-0030)
# ─────────────────────────────────────────────────────────────────────────────
def gen_declaracion():
    pdf_path = os.path.join(output_dir, "TEST_DECLARACION_DISCREPANTE_SIN-0030.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    story = []

    # Cabecera
    story.append(Paragraph("ASEGURADORA DEL SUR S.A.", title_style))
    story.append(Paragraph("FORMULARIO DE DECLARACIÓN JURADA DE ACCIDENTE", subtitle_style))
    story.append(Spacer(1, 15))

    # Datos
    data = [
        [Paragraph("Formulario No:", bold_style), Paragraph("DA-TEST-0030", body_style)],
        [Paragraph("Siniestro ID:", bold_style), Paragraph("SIN-0030", bold_style)],
        [Paragraph("Poliza:", bold_style), Paragraph("POL-7384-ACTIVE", body_style)],
        [Paragraph("Asegurado:", bold_style), Paragraph("Gloria Susana Pacheco", body_style)],
        [Paragraph("Placa:", bold_style), Paragraph("XYZ-8888", alert_style)], # <--- ALTERADA (MNT-7384)
        [Paragraph("Marca:", bold_style), Paragraph("CHEVROLET", body_style)],
        [Paragraph("Modelo:", bold_style), Paragraph("SAIL", body_style)],
        [Paragraph("Fecha:", bold_style), Paragraph("2024-10-06", body_style)],
        [Paragraph("Hora:", bold_style), Paragraph("15:30", body_style)],
    ]
    t = Table(data, colWidths=[140, 280])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D6EAF8')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EBF5FB')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Declaración
    story.append(Paragraph("Relato detalladamente de cómo sucedió el accidente:", subtitle_style))
    declaracion_texto = (
        "Yo, Gloria Susana Pacheco, declaro bajo juramento que me encontraba conduciendo mi vehículo Chevrolet Sail por la Av. Eloy Alfaro, "
        "cuando de forma imprevista otro vehículo frenó a raya delante de mí, causándome daños menores de colisión frontal."
    )
    story.append(Paragraph(declaracion_texto, body_style))

    doc.build(story)
    print(f"Generado: {pdf_path}")

if __name__ == "__main__":
    gen_factura()
    gen_parte()
    gen_declaracion()
