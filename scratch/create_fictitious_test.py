import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. GENERAR EL EXCEL FICTICIO MINIMALISTA (1 Siniestro)
excel_dir = r"c:\Users\PC\Desktop\fraudia\fraudia\data\dataset"
excel_path = os.path.join(excel_dir, "dataset_ficticio_prueba.xlsx")
os.makedirs(excel_dir, exist_ok=True)

# Hoja 1: Siniestros
df_siniestros = pd.DataFrame([{
    "ID Siniestro": "SIN-9999",
    "ID Póliza": "POL-9999",
    "ID Asegurado": "ASEG-9999",
    "Ramo": "Vehículos",
    "Cobertura": "Choque",
    "Placa Vehículo Asegurado": "ABC-1234",
    "Fecha Ocurrencia": "2026-05-20",
    "Fecha Reporte": "2026-05-22",
    "Días Ocurr→Reporte": 2,
    "Monto Reclamado ($)": 1500.0,
    "Monto Estimado ($)": 1500.0,
    "Estado": "Pendiente",
    "Sucursal": "Quito",
    "ID Proveedor": "PROV-9999",
    "Docs Completos": "Sí",
    "Prov. Lista Restrictiva": "No",
    "Días desde Inicio Póliza": 50,
    "Días hasta Fin Póliza": 300,
    "N° Reclamos Previos Asegurado": 0,
    "Suma Asegurada ($)": 20000.0,
    "Similitud Narrativa Máx.": 0.1,
    "Descripción del Evento": "El asegurado colisionó contra un muro de contención en la Av. Occidental debido a calzada mojada."
}])

# Hoja 3: Asegurados
df_asegurados = pd.DataFrame([{
    "ID Asegurado": "ASEG-9999",
    "Nombres Asegurado": "Juan Carlos Ficticio",
    "Ciudad": "Quito",
    "Antigüedad (años)": 3,
    "Reclamos RC sin Tercero": 0
}])

# Hoja 4: Proveedores
df_proveedores = pd.DataFrame([{
    "ID Proveedor": "PROV-9999",
    "Nombre Proveedor": "Taller Ficticio Excelente",
    "En Lista Restrictiva": "No"
}])

with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    df_siniestros.to_excel(writer, sheet_name="1_Siniestros", index=False)
    # Crear hojas vacías para las hojas 2 y 5 que espera la app de forma segura
    pd.DataFrame(columns=["ID Vehículo"]).to_excel(writer, sheet_name="2_Vehiculos", index=False)
    df_asegurados.to_excel(writer, sheet_name="3_Asegurados", index=False)
    df_proveedores.to_excel(writer, sheet_name="4_Proveedores", index=False)
    pd.DataFrame(columns=["ID Siniestro"]).to_excel(writer, sheet_name="5_Coberturas", index=False)

print(f"Excel Ficticio Generado en: {excel_path}")


# 2. GENERAR EL PDF (FACTURA) QUE COINCIDE PERFECTAMENTE CON SIN-9999
pdf_dir = os.path.join(excel_dir, "TEST_DOCUMENTS")
os.makedirs(pdf_dir, exist_ok=True)
pdf_path = os.path.join(pdf_dir, "TEST_FACTURA_FICTICIA_SIN-9999.pdf")

doc = SimpleDocTemplate(pdf_path, pagesize=letter)
story = []
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'TitleStyle', parent=styles['Heading1'],
    fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#1B4F8A'), alignment=1
)
body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14)
bold_style = ParagraphStyle('BoldStyle', parent=body_style, fontName='Helvetica-Bold')

story.append(Paragraph("FACTURA COMERCIAL — TALLER FICTICIO EXCELENTE", title_style))
story.append(Spacer(1, 15))

data = [
    [Paragraph("Factura No:", bold_style), Paragraph("FAC-9999", body_style)],
    [Paragraph("Cliente:", bold_style), Paragraph("Juan Carlos Ficticio", body_style)],
    [Paragraph("Siniestro ID:", bold_style), Paragraph("SIN-9999", bold_style)],
    [Paragraph("Placa Vehículo:", bold_style), Paragraph("ABC-1234", body_style)], # <--- COINCIDE PERFECTAMENTE
    [Paragraph("Total a Pagar:", bold_style), Paragraph("$1,500.00", body_style)], # <--- COINCIDE PERFECTAMENTE
]
t = Table(data, colWidths=[130, 290])
t.setStyle(TableStyle([
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
    ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EBF5FB')),
    ('PADDING', (0,0), (-1,-1), 6),
]))
story.append(t)
story.append(Spacer(1, 20))

doc.build(story)
print(f"PDF Ficticio Generado en: {pdf_path}")
