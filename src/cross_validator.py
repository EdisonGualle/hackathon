import re


def _sim(a, b):
    """Simple word-overlap similarity between two strings."""
    if not a or not b:
        return 0.0
    wa = set(a.upper().split())
    wb = set(b.upper().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))


def cross_validate(sin_id, excel_row, pdf_fields_by_type):
    """
    Compare extracted PDF fields against each other and against the Excel row.
    Returns (inconsistencies, matches, score_boost).
    """
    issues = []
    matches = []
    score_boost = 0

    parte = pdf_fields_by_type.get("PARTE_POLICIAL", {})
    factura = pdf_fields_by_type.get("FACTURA", {})
    declaracion = pdf_fields_by_type.get("DECLARACION", {})

    excel_placa = str(excel_row.get("Placa Vehículo Asegurado", "")).strip().upper()
    excel_cobertura = str(excel_row.get("Cobertura", "")).lower()

    def add_issue(nivel, campo, val1, val2, desc):
        nonlocal score_boost
        issues.append({"nivel": nivel, "campo": campo, "doc1": val1, "doc2": val2, "descripcion": desc})
        # Inconsistencias entre documentos son señales muy fuertes de fraude
        score_boost += 15 if nivel == "CRÍTICO" else 8 if nivel == "ALTO" else 5

    def add_match(campo, valor, valor_excel=None, valor_pdf=None, documento=None):
        matches.append({
            "campo": campo,
            "valor": valor,
            "valor_excel": valor_excel if valor_excel is not None else valor,
            "valor_pdf": valor_pdf if valor_pdf is not None else valor,
            "documento": documento if documento is not None else "General"
        })

    # ── Placa vs Excel ────────────────────────────────────────────────
    for doc_type, fields in [("Parte Policial", parte), ("Factura", factura), ("Declaración", declaracion)]:
        placa = fields.get("placa", "").strip().upper()
        if placa:
            if placa == excel_placa:
                add_match(f"Placa ({doc_type})", placa, excel_placa, placa, doc_type)
            else:
                add_issue("CRÍTICO", "Placa", f"Excel: {excel_placa}", f"{doc_type}: {placa}",
                          f"Placa del vehículo no coincide entre Excel y {doc_type}")

    # ── Nombre conductor Parte vs Factura ─────────────────────────────
    nombre_pp = parte.get("nombre_conductor", "")
    nombre_fac = factura.get("cliente", "")
    if nombre_pp and nombre_fac:
        sim = _sim(nombre_pp, nombre_fac)
        if sim < 0.3:
            add_issue("CRÍTICO", "Nombre titular",
                      f"Parte Policial: {nombre_pp}",
                      f"Factura: {nombre_fac}",
                      "El titular en la factura no coincide con el conductor en el parte policial")
        else:
            add_match("Nombre conductor", nombre_pp, "N/D (Cruce entre PDFs)", f"Parte: {nombre_pp} | Factura: {nombre_fac}", "Parte Policial vs Factura")

    # ── Robo total + factura de reparación = lógica imposible ─────────
    tiene_factura = bool(factura)
    desc_fac = factura.get("_raw", str(factura).lower())
    if "robo" in excel_cobertura and tiene_factura and ("reparaci" in desc_fac or "carrocer" in desc_fac):
        add_issue("CRÍTICO", "Tipo evento vs servicio",
                  f"Cobertura: {excel_row.get('Cobertura', '')}",
                  "Factura: Servicio de reparación/carrocería",
                  "LÓGICA IMPOSIBLE: Robo total declarado pero existe factura de reparación")

    # ── Documento alterado ────────────────────────────────────────────
    for doc_type, fields in [("Parte Policial", parte), ("Factura", factura)]:
        if fields.get("documento_alterado"):
            add_issue("CRÍTICO", "Integridad documental",
                      doc_type, "Marcado como DOCUMENTO ALTERADO",
                      f"El documento {doc_type} contiene marca explícita de alteración")

    # ── RUC inválido (removido) ───────────────────────────────────────
    # if factura.get("ruc_invalido"):
    #     add_issue("ALTO", "RUC Proveedor",
    #               f"RUC: {factura.get('ruc', 'N/A')}",
    #               "Estado: INVÁLIDO",
    #               "El RUC del taller en la factura no es válido")

    # ── Sin denuncia policial ─────────────────────────────────────────
    if parte.get("sin_denuncia"):
        add_issue("ALTO", "Denuncia policial",
                  "Parte Policial", "Sin denuncia policial previa al parte",
                  "El ciudadano no presentó denuncia policial antes del parte")

    # ── Parte elaborado días después del hecho ────────────────────────
    dias_retraso = parte.get("dias_retraso_parte", 0)
    if isinstance(dias_retraso, (int, float)) and dias_retraso >= 5:
        add_issue("ALTO", "Retraso elaboración parte",
                  f"Fecha hecho: {parte.get('fecha_hecho', 'N/A')}",
                  f"Fecha elaboración: {parte.get('fecha_elaboracion', 'N/A')} ({dias_retraso} días después)",
                  f"El parte policial fue elaborado {dias_retraso} días después del hecho declarado")

    # ── Hora madrugada ────────────────────────────────────────────────
    if parte.get("es_madrugada"):
        add_issue("MEDIO", "Horario sospechoso",
                  f"Hora: {parte.get('hora', 'N/A')}",
                  "Madrugada (00:00–04:59)",
                  "El accidente ocurrió en horario de madrugada")

    # ── Placa Parte vs Declaración ────────────────────────────────────
    placa_pp = parte.get("placa", "").upper()
    placa_da = declaracion.get("placa", "").upper()
    if placa_pp and placa_da and placa_pp != placa_da:
        add_issue("ALTO", "Placa entre documentos",
                  f"Parte Policial: {placa_pp}",
                  f"Declaración Accidente: {placa_da}",
                  "La placa no coincide entre el parte policial y la declaración de accidente")

    return issues, matches, min(score_boost, 70)
