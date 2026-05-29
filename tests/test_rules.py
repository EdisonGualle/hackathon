import pytest
from src.fraud_rules import score_siniestro


def test_borde_vigencia_extremo():
    """Prueba que un siniestro con vigencia < 2 días (48 horas) active la regla crítica RF-05 y fuerce Amarillo mínimo."""
    row = {
        "ID Siniestro": "SIN-9999",
        "Cobertura": "Choque",
        "días inicio póliza": 1,  # < 48 horas (1 día)
        "días fin póliza": 150,
        "monto reclamado": 500,
        "suma asegurada": 5000,
        "reclamos previos": 0,
        "docs completos": "Sí",
        "lista restrictiva": "No",
    }
    res = score_siniestro(row)
    assert res["nivel"] == "AMARILLO"
    assert res["score"] >= 41
    assert any("RF-05" in r for r in res["critical_rules"])


def test_proveedor_lista_restrictiva():
    """Prueba que un proveedor en lista restrictiva active la regla crítica RF-03 y fuerce el nivel Rojo."""
    row = {
        "ID Siniestro": "SIN-9998",
        "Cobertura": "Choque",
        "días inicio póliza": 100,
        "días fin póliza": 100,
        "monto reclamado": 800,
        "suma asegurada": 6000,
        "reclamos previos": 1,
        "docs completos": "Sí",
        "lista restrictiva": "Sí",  # Lista restrictiva
    }
    res = score_siniestro(row)
    assert res["nivel"] == "ROJO"
    assert res["score"] >= 76
    assert any("RF-03" in r for r in res["critical_rules"])


def test_lógica_imposible_robo_reparacion():
    """Prueba que la validación cruzada con lógica imposible (Robo + Factura de reparación) fuerce nivel Rojo."""
    row = {
        "ID Siniestro": "SIN-9997",
        "Cobertura": "Robo Total",
        "días inicio póliza": 80,
        "días fin póliza": 80,
        "monto reclamado": 2000,
        "suma asegurada": 10000,
        "reclamos previos": 0,
        "docs completos": "Sí",
        "lista restrictiva": "No",
    }
    # Simulamos señales provenientes de los PDFs extraídos
    pdf_signals = {
        "logica_imposible": True,
        "vehicle_freq": 1
    }
    res = score_siniestro(row, pdf_signals)
    assert res["nivel"] == "ROJO"
    assert res["score"] >= 76
    assert any("RF-04" in r for r in res["critical_rules"])


def test_reporte_tardio_basico():
    """Prueba que un reporte tardío asigne los puntos acumulativos correctos."""
    row = {
        "ID Siniestro": "SIN-9996",
        "Cobertura": "Choque",
        "días inicio póliza": 120,
        "días fin póliza": 120,
        "monto reclamado": 200,
        "suma asegurada": 4000,
        "reclamos previos": 0,
        "docs completos": "Sí",
        "lista restrictiva": "No",
        "dias_ocurrencia_reporte": 10  # > 7 días de retraso
    }
    res = score_siniestro(row)
    # Buscamos si sumó el score correcto por reporte tardío (5 pts)
    # En el motor, busca la columna con ocur y reporte. Simulamos inyectando el valor directo
    row_tardio = row.copy()
    row_tardio["ocurrencia_reporte"] = 10
    res_tardio = score_siniestro(row_tardio)
    
    tardio_breakdown = [b for b in res_tardio["breakdown"] if "RF-06" in b["codigo"]]
    assert len(tardio_breakdown) > 0
    assert tardio_breakdown[0]["puntos"] == 5
