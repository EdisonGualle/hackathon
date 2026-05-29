# ⚖️ ÉTICA, SESGOS Y LIMITACIONES DEL MODELO — FRAUDIA

Este documento define la política de uso ético, las limitaciones técnicas conocidas y los mecanismos de mitigación del sesgo implementados en **FRAUDIA** para la **Aseguradora del Sur**.

---

## 1. Declaración de Uso Ético y Responsable

FRAUDIA ha sido diseñado estrictamente como un **sistema de recomendación y apoyo a la decisión humana**. 

> [!CAUTION]
> **Ningún siniestro puede ser rechazado o pausado automáticamente por las alertas de este sistema.**
> Toda penalización o investigación de campo formal requiere la revisión directa y la firma aprobatoria de la Jefatura de Siniestros y el analista antifraude. El sistema alerta, no sentencia.

---

## 2. Limitaciones Técnicas Conocidas

1. **Tasa de Falsos Positivos Estimada (15% - 20%):** Al ser un modelo entrenado con datos sintéticos equilibrados, existe la posibilidad de que siniestros legítimos con dinámicas atípicas (ej. accidentes en días festivos con facturas altas) se clasifiquen como alerta roja. Se requiere supervisión humana para evitar perjuicios injustificados a los asegurados.
2. **Dependencia Temporal de Calibración:** Los pesos de las 14 señales del reto son referenciales. En un entorno real, estos deben calibrarse dinámicamente según la siniestralidad real histórica de la aseguradora.
3. **Fragilidad ante Documentación Incompleta:** La validación cruzada y extracción de PDFs depende de la legibilidad de la extracción OCR (`pdfplumber`). Documentos arrugados o de baja calidad digital pueden reportar campos vacíos.

---

## 3. Mitigación del Sesgo Algorítmico

Los modelos de machine learning pueden replicar sesgos geográficos o comerciales históricos de las sucursales. Para mitigar esto, FRAUDIA integra:

* **Monitoreo de Equidad en Ramo y Sucursales:** Analizamos y mostramos dinámicamente en el Dashboard la tasa de casos en semáforo rojo emitidos por ciudad y por tipo de cobertura.
* **Acción sugerida ante desviaciones:** Si se detecta un porcentaje de alertas rojas atípicamente superior en una sucursal (ej: Manta o Guayaquil) respecto a la siniestralidad base, el administrador del sistema debe auditar si las reglas geográficas (como la asignación de sucursales en proveedores) están induciendo falsos positivos y reajustar los pesos de las señales.
