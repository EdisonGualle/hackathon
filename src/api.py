from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import tempfile
import shutil
import os
import re

from src.pdf_extractor import extract_text, detect_doc_type, extract_fields
from src.fraud_rules import score_siniestro
from src.cross_validator import cross_validate

app = FastAPI(
    title="🔍 FRAUDIA REST API",
    description="API empresarial de microservicios para la detección y scoring de posibles fraudes en siniestros de seguros.",
    version="1.0.0",
)


# ── MODELOS DE PETICIÓN PYDANTIC ──────────────────────────────────────────────

class SiniestroRequest(BaseModel):
    id_siniestro: str = Field(..., example="SIN-0005", description="ID único del siniestro")
    cobertura: str = Field(..., example="Choque", description="Tipo de cobertura (Choque, Robo, Daño, etc.)")
    monto_reclamado: float = Field(..., example=3500.0, description="Monto en USD reclamado")
    suma_asegurada: float = Field(..., example=12000.0, description="Monto en USD máximo cubierto por la póliza")
    dias_inicio_poliza: int = Field(..., example=15, description="Días transcurridos desde inicio de vigencia de póliza")
    dias_fin_poliza: int = Field(..., example=120, description="Días restantes para finalización de vigencia de póliza")
    reclamos_previos: int = Field(..., example=2, description="Número de reclamos históricos del asegurado")
    docs_completos: str = Field("Sí", example="Sí", description="Indicador de documentos completos (Sí/No)")
    prov_lista_restrictiva: str = Field("No", example="No", description="Indicador de proveedor en lista restrictiva (Sí/No)")
    similitud_narrativa: float = Field(0.0, example=0.25, description="Coeficiente de similitud de texto anterior (0.0 a 1.0)")
    dias_ocurrencia_reporte: int = Field(2, example=2, description="Días transcurridos entre accidente y reporte")


# ── ENDPOINTS DE LA API ───────────────────────────────────────────────────────

@app.get("/", tags=["General"])
def read_root():
    return {
        "sistema": "FRAUDIA API",
        "estado": "Activo",
        "descripcion": "Microservicio empresarial de scoring antifraude - Aseguradora del Sur",
        "documentacion": "/docs"
    }


@app.post("/score", tags=["Scoring"], response_model=Dict[str, Any])
def post_score(request: SiniestroRequest):
    """
    Calcula el score de riesgo de fraude de forma determinista para un siniestro estructurado.
    Aplica las 14 señales del reto y evalúa las 7 reglas críticas (RF-01 a RF-07).
    """
    # Mapeo de Pydantic a diccionario compatible con el motor de reglas
    row_dict = {
        "ID Siniestro": request.id_siniestro,
        "Cobertura": request.cobertura,
        "Monto Reclamado ($)": request.monto_reclamado,
        "Suma Asegurada ($)": request.suma_asegurada,
        "Días desde Inicio Póliza": request.dias_inicio_poliza,
        "Días hasta Fin Póliza": request.dias_fin_poliza,
        "N° Reclamos Previos Asegurado": request.reclamos_previos,
        "Docs Completos": request.docs_completos,
        "Prov. Lista Restrictiva": request.prov_lista_restrictiva,
        "Similitud Narrativa Máx.": request.similitud_narrativa,
    }
    
    # Inyectar reporte tardío en los campos dinámicos
    row_dict[f"dias_ocurrencia_reporte"] = request.dias_ocurrencia_reporte
    
    try:
        # Calcular score básico
        result = score_siniestro(row_dict)
        return {
            "id_siniestro": request.id_siniestro,
            "score_final": result["score"],
            "nivel_riesgo": result["nivel"],
            "color_representativo": result["color"],
            "alertas_disparadas": result["alerts"],
            "reglas_criticas_activadas": result["critical_rules"],
            "desglose_puntajes": result["breakdown"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al calcular score: {e}")


@app.post("/validate", tags=["Validación Documental"])
async def post_validate(
    file: UploadFile = File(..., description="Documento PDF (Factura, Parte Policial o Declaración Jurada)")
):
    """
    Sube un archivo PDF del siniestro, extrae su texto, clasifica su tipo de documento
    y extrae de forma estructurada los campos de datos e inconsistencias físicas del negocio.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo subido debe ser un archivo PDF válido.")

    # Guardar en archivo temporal para procesar con pdfplumber
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Extraer texto y estructurar
        text = extract_text(tmp_path)
        doc_type = detect_doc_type(text)
        
        if doc_type == "UNKNOWN":
            raise HTTPException(
                status_code=422, 
                detail="No se pudo identificar el tipo de documento del PDF. Suba una factura, parte policial o declaración."
            )
            
        fields = extract_fields(text, doc_type)
        
        # Eliminar llaves privadas o grandes del output json
        if "_raw" in fields:
            del fields["_raw"]

        tipo_lbl = {
            "PARTE_POLICIAL": "Parte Policial",
            "DECLARACION": "Declaración Jurada de Accidente",
            "FACTURA": "Factura de Taller/Servicio"
        }.get(doc_type, doc_type)

        return {
            "nombre_archivo": file.filename,
            "tipo_documento_detectado": tipo_lbl,
            "id_siniestro_vinculado": extract_fields(text, doc_type).get("placa") or "No identificado",
            "campos_extraidos": fields,
            "alertas_documentales": {
                "documento_alterado": fields.get("documento_alterado", False),
                "ruc_invalido": fields.get("ruc_invalido", False),
                "accidente_madrugada": fields.get("es_madrugada", False),
                "sin_denuncia_previa": fields.get("sin_denuncia", False)
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo PDF: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
