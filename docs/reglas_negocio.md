# ⚖️ REGLAS DE NEGOCIO Y RÚBRICA DE ALERTAS — FRAUDIA

Este documento consolida la lógica formal del motor de scoring determinista de **FRAUDIA**, detallando los pesos de las 14 señales del reto y el comportamiento de las 7 reglas críticas de negocio (RF-01 a RF-07).

---

## 1. Rúbrica de Puntuación de las 14 Señales

El score numérico final se calcula de forma acumulativa (acotado a un rango de 0 a 100 puntos) basándose en las siguientes señales:

| Código | Señal de Posible Fraude | Criterio de Activación (Código Real) | Puntos |
| :--- | :--- | :--- | :---: |
| **S01** | Borde de Vigencia | Siniestro ocurrido ≤ 10 días: **8 pts** \| De 11 a 30 días: **4 pts**. | **Up to 8** |
| **S02** | Demora denuncia Robo | Reporte de siniestros de robo tardíos (> 4 días). | **Up to 8** |
| **S03** | Frecuencia Asegurado | Asegurado con ≥ 3 siniestros en 18 meses: **8 pts** \| Con 2: **4 pts**. | **Up to 8** |
| **S04** | Frecuencia Vehículo | Vehículo (placa) con ≥ 3 siniestros: **6 pts** \| Con 2: **3 pts**. | **Up to 6** |
| **S05** | Frecuencia Conductor | Conductor asociado a múltiples siniestros (no procesado por datos). | **Up to 8** |
| **S06** | Frecuencia de solo RC | Cobertura única de Responsabilidad Civil con casos anteriores. | **Up to 6** |
| **S07** | Proveedor Recurrente | Proveedor en lista restrictiva: **10 pts** \| >2 casos este año: **5 pts**. | **Up to 10** |
| **S08** | Documentos Incompletos | Docs completos marcados como "No": **4 pts**. | **4** |
| **S09** | Dinámica Sospechosa | Relato inconsistente: **6 pts** \| Accidente de madrugada: **3 pts**. | **Up to 6** |
| **S10** | Evento sin Tercero | Daños graves sin tercero ni cámaras identificadas: **5 pts**. | **Up to 6** |
| **S11** | Documentos Inconsistentes | Alteraciones de firmas o fechas confirmadas en PDF: **10 pts**. | **10** |
| **S12** | Reporte Tardío | Ocurrencia a reporte > 7 días: **5 pts** \| De 4 a 7 días: **3 pts**. | **Up to 5** |
| **S13** | Narrativas Similares | Similitud textual > 85%: **8 pts** \| De 70% a 84%: **4 pts**. | **Up to 8** |
| **S14** | Monto vs Suma Asegurada | Reclamado >95% de suma: **4 pts** \| Reclamado >50% de suma: **2 pts**. | **Up to 5** |

---

## 2. Reglas de Negocio Críticas (RF-01 a RF-07)

Estas reglas representan directrices empresariales estrictas de la Aseguradora del Sur que alteran el semáforo de riesgo independientemente de los puntos sumados por las señales:

### 🔴 Nivel de Alerta: ROJO (Fuerzan Score ≥ 76)
* **RF-01 (Cobertura Pérdida Total por Robo - PTxRB):** Si la cobertura del siniestro es "Robo Total" o "Pérdida Total", el caso es crítico y escala directo a la Unidad Antifraude para investigación especializada en campo.
* **RF-02 (Falsificación Documental Evidente):** Si la validación de integridad detecta firmas modificadas, fechas previas alteradas o la marca de documento alterado en PDFs.
* **RF-03 (Lista Restrictiva):** Si el asegurado o proveedor coincide exactamente con bases de datos de sancionados.
* **RF-04 (Dinámica Físicamente Imposible):** Incoherencias lógicas severas entre documentos (ej: se declara *Robo Total* de vehículo pero el taller emite una *factura de reparación* de carrocería).

### 🟡 Nivel de Alerta: AMARILLO (Fuerzan Score ≥ 41)
* **RF-05 (Extremo al Borde de Vigencia):** Siniestros ocurridos en las primeras 48 horas de vigencia de la póliza contratada. Requiere revisión documental exhaustiva.
* **RF-06 (Demora Atípica en Denuncia de Robo):** Reportes de siniestros de robo notificados más de 4 días después de la fecha de ocurrencia del hecho.
* **RF-07 (Narrativa Clonada):** Coeficiente NLP de similitud de descripción superior al 85% contra otros reclamos (anillos de colusión).
