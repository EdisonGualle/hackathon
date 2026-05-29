import pandas as pd
import os
import re


# Ruta del proyecto (..\fraudia\)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATASET_DIR  = os.path.join(_PROJECT_ROOT, "data", "dataset")

DEFAULT_EXCEL = os.path.join(_DATASET_DIR, "Evento Datasets_Sinteticos_Fraude_500_v2.xlsx")
DEFAULT_DOCS  = _DATASET_DIR

EXPECTED_SHEETS = {
    "1_Siniestros": [
        "ID Siniestro", "ID Póliza", "ID Asegurado", "Ramo",
        "Placa Vehículo Asegurado", "Cobertura", "Fecha Ocurrencia",
        "Fecha Reporte", "Monto Reclamado ($)", "Monto Estimado ($)",
        "Estado", "Sucursal", "ID Proveedor", "Descripción del Evento",
        "Docs Completos", "Prov. Lista Restrictiva",
        "Días desde Inicio Póliza", "Días hasta Fin Póliza",
        "N° Reclamos Previos Asegurado", "Suma Asegurada ($)",
        "Similitud Narrativa Máx.",
    ],
    "2_Polizas": [
        "ID Póliza", "ID Asegurado", "Ramo", "Fecha Inicio",
        "Fecha Fin", "Suma Asegurada ($)", "Prima Anual ($)",
        "Canal Venta", "Estado Póliza",
    ],
    "3_Asegurados": [
        "ID Asegurado", "Nombres Asegurado", "Segmento", "Ciudad",
        "Antigüedad (años)", "N° Pólizas Activas",
        "N° Reclamos Últimos 12 Meses", "N° Reclamos Histórico Total",
        "Reclamos RC sin Tercero", "Perfil Riesgo Histórico",
    ],
    "4_Proveedores": [
        "ID Proveedor", "Nombre Proveedor", "Tipo", "Ciudad",
        "N° Siniestros Asociados", "En Lista Restrictiva",
        "Motivo Restricción", "Promedio Monto ($)",
    ],
    "5_Documentos": [
        "ID Documento", "ID Siniestro", "Tipo Documento", "Nombre Archivo PDF",
    ],
}


def load_excel(path=None):
    path = path or DEFAULT_EXCEL
    sheets = {}
    # Usar context manager para CERRAR el handle del archivo (si no, en Windows
    # queda bloqueado y os.unlink del temporal lanza WinError 32).
    with pd.ExcelFile(path) as xl:
        for name in xl.sheet_names:
            if name == "README":
                continue
            sheets[name] = pd.read_excel(xl, sheet_name=name, dtype=str).fillna("")
    return sheets


def validate_excel_structure(sheets):
    results = {}
    for sheet_name, expected_cols in EXPECTED_SHEETS.items():
        if sheet_name not in sheets:
            results[sheet_name] = {"found": False, "rows": 0, "missing_cols": expected_cols, "present_cols": []}
            continue
        df = sheets[sheet_name]
        present = [c for c in expected_cols if c in df.columns]
        missing = [c for c in expected_cols if c not in df.columns]
        results[sheet_name] = {
            "found": True,
            "rows": len(df),
            "cols": len(df.columns),
            "missing_cols": missing,
            "present_cols": present,
        }
    return results


def map_pdfs(folder=None):
    folder = folder or DEFAULT_DOCS
    pdf_map = {}
    for root, _, files in os.walk(folder):
        for fname in files:
            if not fname.lower().endswith(".pdf"):
                continue
            m = re.search(r"SIN-?(\d+)", fname, re.IGNORECASE)
            if not m:
                continue
            sin_id = f"SIN-{m.group(1).zfill(4)}"
            folder_upper = os.path.basename(root).upper()
            full_path = os.path.join(root, fname)
            if sin_id not in pdf_map:
                pdf_map[sin_id] = {}
            if "POLICIAL" in folder_upper or "PARTE" in folder_upper:
                pdf_map[sin_id]["PARTE_POLICIAL"] = full_path
            elif "DECLARACI" in folder_upper or "ACCIDENTE" in folder_upper:
                pdf_map[sin_id]["DECLARACION"] = full_path
            elif "FACTURA" in folder_upper:
                pdf_map[sin_id]["FACTURA"] = full_path
    return pdf_map
