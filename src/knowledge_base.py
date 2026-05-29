"""
Base de Conocimiento — Reglas de Negocio y Fraude
Documenta las 7 reglas críticas (RF-01..RF-07) y las 14 señales con puntaje
del PDF del reto Aseguradora del Sur. Se inyecta al índice RAG como contexto.
"""

# ══════════════════════════════════════════════════════════════════════
# REGLAS CRÍTICAS — Sección 8 del PDF del reto
# ══════════════════════════════════════════════════════════════════════

REGLAS_CRITICAS = [
    {
        "id": "RF-01",
        "nombre": "Cobertura Pérdida Total por Robo (PTxRB)",
        "nivel": "ROJO",
        "descripcion": (
            "Cualquier siniestro cuya cobertura sea 'Pérdida Total' o 'Robo' se "
            "clasifica automáticamente como ROJO independientemente del score numérico. "
            "Estas coberturas tienen el mayor riesgo de fraude histórico en el sector "
            "asegurador ecuatoriano."
        ),
    },
    {
        "id": "RF-02",
        "nombre": "Evidencia de Falsificación o Adulteración Documental Evidente",
        "nivel": "ROJO",
        "descripcion": (
            "Si el sistema detecta marcas de 'DOCUMENTO ALTERADO' en cualquier PDF del "
            "expediente (parte policial, declaración, factura), el siniestro se marca "
            "automáticamente como ROJO. La adulteración documental es prueba directa de "
            "intento de fraude."
        ),
    },
    {
        "id": "RF-03",
        "nombre": "Asegurado, Beneficiario o Proveedor en Lista Restrictiva",
        "nivel": "ROJO",
        "descripcion": (
            "Si el proveedor (taller, clínica, perito) o el asegurado coinciden "
            "exactamente con la Lista Restrictiva interna, el caso se clasifica como "
            "ROJO. La lista incluye proveedores con historial de fraude confirmado."
        ),
    },
    {
        "id": "RF-04",
        "nombre": "Dinámica del Accidente Físicamente Imposible",
        "nivel": "ROJO",
        "descripcion": (
            "Cuando el relato del accidente contradice la evidencia física o las "
            "facturas: por ejemplo, un robo total declarado pero con factura de "
            "reparación de carrocería del mismo vehículo. Estos casos requieren "
            "investigación de campo inmediata."
        ),
    },
    {
        "id": "RF-05",
        "nombre": "Siniestro Extremo al Borde de Vigencia (<48 hrs)",
        "nivel": "AMARILLO",
        "descripcion": (
            "Siniestros ocurridos en las primeras 48 horas de la póliza o en las "
            "últimas 48 horas antes del fin de vigencia. Indicador clásico de fraude "
            "por contratación dolosa o aprovechamiento de cobertura próxima a vencer."
        ),
    },
    {
        "id": "RF-06",
        "nombre": "Demora Atípica en Denuncia de Robo (>4 días)",
        "nivel": "AMARILLO",
        "descripcion": (
            "En casos de Robo, si la denuncia policial se realiza más de 4 días después "
            "del evento, el caso se eleva a AMARILLO. Las víctimas reales de robo "
            "normalmente denuncian dentro de las primeras 24-48 horas."
        ),
    },
    {
        "id": "RF-07",
        "nombre": "Narrativa Idéntica (Clonada)",
        "nivel": "AMARILLO",
        "descripcion": (
            "Cuando la descripción textual del evento tiene similitud >85% con la "
            "narrativa de otro siniestro distinto. Indica posible uso de plantillas "
            "o fraude coordinado por bandas que copian el mismo relato."
        ),
    },
]


# ══════════════════════════════════════════════════════════════════════
# 14 SEÑALES CON PUNTAJE — Sección 7 del PDF del reto
# ══════════════════════════════════════════════════════════════════════

SEÑALES_PUNTAJE = [
    {
        "id": "S01",
        "nombre": "Reclamo cercano al borde de vigencia",
        "puntaje_max": 8,
        "criterio": "≤10 días: 8 pts · 11-30 días: 4 pts · >30 días: 0 pts",
        "ejemplo": "Siniestro ocurrido pocos días después de contratar la póliza o antes del fin de vigencia.",
    },
    {
        "id": "S02",
        "nombre": "Demora denuncia por robo",
        "puntaje_max": 8,
        "criterio": ">48h: 8 pts · 24-48h: 4 pts · <24h: 0 pts",
        "ejemplo": "Tiempos prolongados entre ocurrencia del robo y denuncia formal.",
    },
    {
        "id": "S03",
        "nombre": "Alta frecuencia de reclamos del asegurado",
        "puntaje_max": 8,
        "criterio": "≥3 siniestros en 18m: 8 pts · 2 siniestros: 4 pts · 0-1: 0 pts",
        "ejemplo": "Asegurado con múltiples siniestros en período corto.",
    },
    {
        "id": "S04",
        "nombre": "Alta frecuencia de reclamos del vehículo",
        "puntaje_max": 6,
        "criterio": "≥3 siniestros mismo vehículo en 18m: 6 pts · 2: 3 pts · 0-1: 0 pts",
        "ejemplo": "Misma placa con varios siniestros en período corto.",
    },
    {
        "id": "S05",
        "nombre": "Alta frecuencia del conductor",
        "puntaje_max": 8,
        "criterio": "≥3 siniestros del mismo conductor: 8 pts · 2: 4 pts",
        "ejemplo": "Conductor presente en múltiples siniestros.",
    },
    {
        "id": "S06",
        "nombre": "Alta frecuencia reclamos solo de RC",
        "puntaje_max": 6,
        "criterio": ">2 eventos previos solo RC: 6 pts · 1 evento: 3 pts",
        "ejemplo": "Frecuencia atípica de siniestros donde solo se afecta Responsabilidad Civil.",
    },
    {
        "id": "S07",
        "nombre": "Beneficiario / Proveedor recurrente o restrictivo",
        "puntaje_max": 10,
        "criterio": "En Lista Restrictiva: 10 pts · En >2 casos observados este año: 5 pts",
        "ejemplo": "Proveedor (taller, clínica) asociado a varios casos observados.",
    },
    {
        "id": "S08",
        "nombre": "Documentos incompletos",
        "puntaje_max": 4,
        "criterio": "Falta documento legal obligatorio: 4 pts",
        "ejemplo": "Falta denuncia, factura, informe o evidencia requerida.",
    },
    {
        "id": "S09",
        "nombre": "Dinámica sospechosa del accidente",
        "puntaje_max": 6,
        "criterio": "Relato ilógico vs tipo de impacto: 6 pts · Accidente múltiple en madrugada: 3 pts",
        "ejemplo": "Accidentes que requieren revisión minuciosa: Frontal, Posterior, Volcadura.",
    },
    {
        "id": "S10",
        "nombre": "Eventos sin tercero identificado",
        "puntaje_max": 6,
        "criterio": "Daño severo sin rastro del tercero ni cámaras: 5 pts",
        "ejemplo": "Vehículo asegurado afectado pero el tercero no existe o huye.",
    },
    {
        "id": "S11",
        "nombre": "Documentos inconsistentes",
        "puntaje_max": 10,
        "criterio": "Alteración confirmada o fechas de factura previas al evento: 10 pts",
        "ejemplo": "Fechas no coinciden entre documentos, valores diferentes o ilegibles.",
    },
    {
        "id": "S12",
        "nombre": "Reporte tardío",
        "puntaje_max": 5,
        "criterio": ">7 días: 5 pts · 4-7 días: 3 pts · ≤3 días: 0 pts",
        "ejemplo": "El siniestro se reporta muchos días después del evento.",
    },
    {
        "id": "S13",
        "nombre": "Narrativas similares",
        "puntaje_max": 8,
        "criterio": ">85% similitud textual: 8 pts · 70-85%: 4 pts",
        "ejemplo": "Descripciones parecidas entre varios reclamos.",
    },
    {
        "id": "S14",
        "nombre": "Monto cercano o superior a suma asegurada",
        "puntaje_max": 5,
        "criterio": "Reclamo >95% suma asegurada o +50% del promedio: 4 pts",
        "ejemplo": "Valor reclamado representa proporción muy alta de la cobertura.",
    },
]


# ══════════════════════════════════════════════════════════════════════
# CLASIFICACIÓN POR SCORE — Sección 13 del PDF
# ══════════════════════════════════════════════════════════════════════

CLASIFICACION_SCORE = """
SCORE DE RIESGO Y ACCIONES:
- 0 a 40 puntos: VERDE (Bajo). Acción: Continuar flujo normal de procesamiento.
- 41 a 75 puntos: AMARILLO (Medio). Acción: Escalar a Unidad Antifraude para revisión documental.
- 76 a 100 puntos: ROJO (Alto). Acción: Escalar a Unidad Antifraude para revisión especializada de campo.

REGLAS CRÍTICAS RF-01 a RF-04 fuerzan automáticamente ROJO sin importar el score numérico.
REGLAS RF-05 a RF-07 fuerzan automáticamente AMARILLO como mínimo.

SCORE COMBINADO (cuando se usa el modelo híbrido):
- Score Final = 50% Reglas + 25% Isolation Forest (anomalías) + 25% Random Forest (supervisado)
- Si las reglas críticas marcan ROJO, el score combinado preserva ROJO como mínimo (76).
"""


# ══════════════════════════════════════════════════════════════════════
# PROPÓSITO DEL SISTEMA Y PRINCIPIOS ÉTICOS
# ══════════════════════════════════════════════════════════════════════

PROPOSITO_SISTEMA = """
PROPÓSITO DE FRAUDIA:
FRAUDIA es un detector de POSIBLES fraudes en siniestros de seguros para la Aseguradora del Sur.
Genera alertas de revisión, NUNCA acusa formalmente de fraude. La decisión final es siempre del
analista humano especializado.

PRINCIPIOS ÉTICOS:
1. Los resultados son ALERTAS, no acusaciones.
2. Ningún siniestro se rechaza automáticamente por el sistema.
3. Todo caso ROJO requiere revisión humana antes de cualquier acción.
4. Se estima una tasa de falsos positivos del 15-20%.
5. Datos 100% sintéticos, sin información personal real.

LO QUE NO ESTÁ PERMITIDO:
- Rechazar automáticamente un siniestro.
- Acusar formalmente a un asegurado de fraude.
- Sustituir el análisis humano especializado.
- Tomar decisiones legales o contractuales.
"""


# ══════════════════════════════════════════════════════════════════════
# GENERADOR DE CHUNKS PARA EL RAG
# ══════════════════════════════════════════════════════════════════════

def build_knowledge_chunks() -> list[tuple[str, dict]]:
    """
    Retorna lista de (chunk_text, metadata) para indexar en el RAG.
    Cada regla y señal es un chunk separado para mejor recuperación.
    """
    chunks: list[tuple[str, dict]] = []

    # Propósito
    chunks.append((
        f"CONOCIMIENTO DEL SISTEMA — PROPÓSITO DE FRAUDIA:\n{PROPOSITO_SISTEMA}",
        {"type": "knowledge", "category": "proposito", "id": "PROP-01"},
    ))

    # Clasificación por score
    chunks.append((
        f"CONOCIMIENTO DEL SISTEMA — CLASIFICACIÓN DE RIESGO:\n{CLASIFICACION_SCORE}",
        {"type": "knowledge", "category": "score", "id": "SCORE-01"},
    ))

    # Reglas críticas (una por chunk)
    for r in REGLAS_CRITICAS:
        text = (
            f"REGLA DE NEGOCIO {r['id']} — {r['nombre']} (Clasificación: {r['nivel']}):\n"
            f"{r['descripcion']}\n"
            f"Cuando esta regla se activa, el siniestro debe ser clasificado como {r['nivel']} "
            f"y escalado para revisión correspondiente."
        )
        chunks.append((text, {"type": "knowledge", "category": "regla_critica", "id": r["id"]}))

    # Señales con puntaje (una por chunk)
    for s in SEÑALES_PUNTAJE:
        text = (
            f"SEÑAL DE FRAUDE {s['id']} — {s['nombre']} (Puntaje máximo: {s['puntaje_max']} pts):\n"
            f"Criterio de puntuación: {s['criterio']}\n"
            f"Ejemplo: {s['ejemplo']}"
        )
        chunks.append((text, {"type": "knowledge", "category": "señal", "id": s["id"]}))

    # Resumen de todas las reglas críticas (un chunk consolidado)
    reglas_resumen = "RESUMEN DE REGLAS CRÍTICAS RF-01 a RF-07:\n"
    for r in REGLAS_CRITICAS:
        reglas_resumen += f"- {r['id']} ({r['nivel']}): {r['nombre']}\n"
    chunks.append((reglas_resumen, {"type": "knowledge", "category": "resumen_reglas", "id": "RESUMEN-RF"}))

    # Resumen de todas las señales (un chunk consolidado)
    señales_resumen = "RESUMEN DE LAS 14 SEÑALES DE FRAUDE CON PUNTAJE:\n"
    for s in SEÑALES_PUNTAJE:
        señales_resumen += f"- {s['id']} ({s['puntaje_max']} pts): {s['nombre']}\n"
    chunks.append((señales_resumen, {"type": "knowledge", "category": "resumen_señales", "id": "RESUMEN-S"}))

    return chunks
