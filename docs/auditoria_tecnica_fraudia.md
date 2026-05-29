# 🔍 INFORME DE AUDITORÍA TÉCNICA Y EVALUACIÓN DE JURADO — FRAUDIA

Este documento presenta una auditoría técnica, funcional y metodológica exhaustiva del prototipo **FRAUDIA**, desarrollado para el **hackIAthon 2026 — Reto Aseguradora del Sur**. La evaluación se realiza bajo el rol de un Auditor Senior, Arquitecto de Software y Jurado Técnico con más de 10 años de experiencia en la evaluación de soluciones empresariales de Inteligencia Artificial.

---

## 1. Resumen Ejecutivo General

**FRAUDIA** es un prototipo funcional bien estructurado que aborda la detección de posibles fraudes en siniestros de seguros mediante un **enfoque híbrido**. Combina reglas de negocio deterministas, Machine Learning no supervisado (anomalías con *Isolation Forest* y agrupamiento de narrativas con *TF-IDF*), y supervisado (*Random Forest*), junto con una interfaz conversacional basada en **RAG local** (vectorización con *Sentence Transformers* y *FAISS*) y el LLM *Llama 3.1 8B* vía *Groq*.

La interfaz de usuario construida en **Streamlit** es visualmente excelente, ofreciendo KPIs claros, simulaciones de ahorro financiero, visualizaciones geográficas y grafos de red relacionales interactivos. Técnicamente, destaca por su modularidad y por implementar validaciones cruzadas avanzadas entre documentos PDF extraídos y registros estructurados del Excel. 

Sin embargo, el sistema presenta un **fallo metodológico crítico de circularidad (data leakage)** en el entrenamiento de su modelo de Machine Learning supervisado y un **incumplimiento total de la estructura de repositorio sugerida** en los requerimientos oficiales del reto. Esto limita su viabilidad de producción inmediata sin una reestructuración profunda.

---

## 2. Nivel de Cumplimiento del Hackathon

A partir de la confrontación del sistema actual contra el PDF oficial *"hackIAthon - reto Aseguradora del Sur.pdf"*, se determina el siguiente estado de cumplimiento:

| Requerimiento Oficial | Estado | Observación Técnica |
| :--- | :---: | :--- |
| **Carga de Dataset Estructurado (6.1)** | **Cumplido** | Lee correctamente el archivo Excel con las 5 hojas y sus columnas. |
| **Análisis de Variables y Señales (7)** | **Cumplido** | Implementa las 14 señales del reto con su respectiva asignación de puntos. |
| **Reglas de Negocio Críticas (8)** | **Cumplido** | RF-01 a RF-04 fuerzan semáforo rojo; RF-05 a RF-07 aseguran amarillo. |
| **Machine Learning Supervisado (9)** | **Parcial** | Implementado, pero con fallos de circularidad (data leakage) en la etiqueta. |
| **Detección de Anomalías (9)** | **Cumplido** | Usa *Isolation Forest* para identificar casos atípicos en variables numéricas. |
| **Procesamiento de Lenguaje Natural (9)** | **Cumplido** | Detecta similitud textual (>85% y 70-84%) y agrupa narrativas clonadas. |
| **Agente de IA Explicativo (9 / 12)** | **Cumplido** | RAG integrado con Groq que responde las 12 preguntas requeridas del PDF. |
| **Dashboard / Interfaz Funcional (10.1)** | **Cumplido** | Interfaz sobresaliente en Streamlit con KPIs y desgloses detallados. |
| **Red de Relaciones (10.2)** | **Cumplido** | Grafo interactivo Asegurados-Siniestros-Proveedores con NetworkX. |
| **Simulación de Ahorro Potencial (10.2)** | **Cumplido** | Calcula el impacto financiero basado en un 20% de recuperación del monto en riesgo. |
| **Exportación de Reporte de Auditoría (10.2)** | **Cumplido** | Generación en memoria de PDF ejecutivo profesional usando `fpdf2`. |
| **API Funcional para Integración Futura (10.2)**| **No Cumplido** | No existe código de API REST (FastAPI o Flask). Es una app puramente monolítica. |
| **Estructura del Repositorio Sugerida (15)** | **No Cumplido** | Estructura real desordenada. Faltan carpetas de `docs/`, `notebooks/`, `tests/` y `presentation/`. |

---

## 3. Puntos Fuertes del Sistema (Fortalezas)

1. **Diseño de Interfaz e Interactividad de Primer Nivel**: La UI en Streamlit implementa una paleta de colores azul corporativo muy pulida, micro-animaciones en tarjetas de KPIs y componentes visuales de alta calidad como mapas geográficos de Ecuador y grafos de red dinámicos.
2. **Arquitectura RAG Local y Cacheado Vectorial**: La implementación de RAG en `src/rag_engine.py` utiliza *sentence-transformers* y *FAISS* persistiendo el índice en disco (`rag_{key}.faiss` y `.pkl`). Esto optimiza los tiempos de carga de la demo de ~30s a instantáneo y cuenta con un fallback inteligente a *retrieval-only* sin necesidad de API Key.
3. **Validación Cruzada Avanzada de PDFs**: La capacidad de extraer texto de PDFs en tiempo real (`pdfplumber`) e identificar inconsistencias complejas (ej. Cobertura de Robo pero Factura de reparación del taller, placas distintas, nombres cruzados) simula de forma robusta la operación real de una aseguradora.
4. **Reporte PDF de Producción**: La descarga del reporte en `src/report_generator.py` genera un archivo PDF formal estructurado con KPIs, desgloses financieros, top 10 de siniestros, distribuciones por ramo y secciones dedicadas a disclaimers éticos y firmas físicas.

---

## 4. Problemas Detectados y Críticas del Jurado

### 🔴 Observación 1: Circularidad Metodológica Grave (Data Leakage) en Random Forest
* **Por qué es un problema**: En `src/supervised_model.py` (Línea 37), el modelo supervisado *Random Forest* se entrena utilizando una etiqueta binaria artificial calculada directamente como `(Score_Reglas >= 76)`. El modelo no está aprendiendo a detectar fraude de forma estadística independiente, sino a aproximar y memorizar las mismas reglas de negocio deterministas preestablecidas.
* **Impacto**: Como jurado técnico, esto representa una **descalificación inmediata en la dimensión de IA**. El modelo supervisado es matemáticamente redundante y carece de capacidad de generalización. Si cambian las reglas de negocio, el modelo deja de tener sentido. Su precisión en validación cruzada es ficticia debido al sobreajuste sobre la lógica de las reglas.
* **Mitigación**: Debe entrenarse el modelo utilizando una etiqueta histórica real de siniestros fraudulentos confirmados en el dataset (columna `etiqueta_fraude_simulada` si se provee en los datos del reto) o, en su defecto, simular una etiqueta aleatoria estructurada que dependa de variables ocultas no utilizadas en las reglas de negocio (ej. historial de mora del asegurado combinada con sumas aseguradas del ramo).

### 🔴 Observación 2: Incumplimiento de la Estructura de Repositorio Sugerida
* **Por qué es un problema**: El PDF oficial del reto (sección 15) define una estructura de directorios estricta con carpetas separadas para `docs/`, `notebooks/`, `tests/` y `presentation/`. La implementación actual tiene `app.py` en la raíz, los módulos directamente en `src/` sin subcarpetas, y carece por completo de la documentación técnica y los cuadernos de Jupyter requeridos.
* **Impacto**: Un jurado técnico senior que clone el repositorio penalizará severamente el proyecto en la dimensión de **Tecnología y Arquitectura** (peso del 10% en el score final), reduciendo la calificación al nivel "Básico" o "Limitado" por falta de reproducibilidad y orden en la entrega.
* **Mitigación**: Reorganizar el repositorio de inmediato moviendo la app a `src/app/main.py` (o ajustar el archivo de arranque) y creando las carpetas y archivos markdown de documentación requeridos en la sección 15 del reto (`arquitectura.md`, `modelo_datos.md`, `reglas_negocio.md`, `uso_ia.md`, `limitaciones.md`).

### 🟡 Observación 3: Extracción de PDFs por Expresiones Regulares "Hardcoded"
* **Por qué es un problema**: La detección de alteraciones documentales y RUCs inválidos en `src/pdf_extractor.py` se basa en la presencia de cadenas de texto literales como `"DOCUMENTO ALTERADO"` o `"INVÁLIDO"` dentro del contenido de los PDFs sintéticos.
* **Impacto**: Es una solución frágil de juguete (*toy solution*). Si se sube un PDF de siniestro real que no contenga exactamente estas etiquetas de depuración, el sistema fallará en identificar la falsificación. El jurado cuestionará la viabilidad de escalabilidad a producción real de la aseguradora.
* **Mitigación**: Integrar validaciones heurísticas reales, tales como el algoritmo de Luhn para el RUC ecuatoriano (13 dígitos, validando el dígito verificador) y el cruce automatizado del RUC con bases de datos simuladas o públicas del SRI para verificar el estado activo.

### 🟡 Observación 4: Ausencia de API Funcional REST
* **Por qué es un problema**: La sección 10.2 del reto lista una "API funcional para integración futura" como una funcionalidad deseable. Sin embargo, no se implementa ningún microservicio o endpoint para consumo externo.
* **Impacto**: Reduce la competitividad en la dimensión de **Negocio e Impacto**. FRAUDIA queda limitado a una herramienta web visual aislada en Streamlit, en lugar de un servicio empresarial integrable con los sistemas *Core* de siniestros de la Aseguradora del Sur.
* **Mitigación**: Crear un script `src/api/main.py` básico usando **FastAPI** que exponga endpoints como `/score` para procesar JSONs de siniestros y `/validate` para subir y verificar PDFs remotamente.

---

## 5. Riesgos Técnicos y Funcionales

1. **Riesgo de Memoria en RAG local (Streamlit)**: Mantener el pipeline de *sentence-transformers* y el índice *FAISS* directamente en la memoria del hilo de Streamlit es propenso a caídas por falta de recursos (*out-of-memory*) si múltiples analistas consultan el sistema concurrentemente en producción.
2. **Omisión de Variables Clave en Reglas**: En `src/fraud_rules.py`, la regla sobre "Frecuencia de conductor de vehículo" no se evalúa adecuadamente sobre una columna de conductor histórico, limitándose únicamente a contar la frecuencia de la placa. Esto genera inconsistencias con el análisis del caso real solicitado en el PDF.

---

## 6. Evaluación de Arquitectura y Código

* **Modularidad**: Excelente. La separación de responsabilidades en `src/` (`fraud_rules.py`, `cross_validator.py`, `rag_engine.py`, `report_generator.py`) facilita el mantenimiento y la escalabilidad del backend.
* **Manejo de Excepciones**: Básico. Muchos bloques se capturan con `try/except: pass` silenciosos (ej. en la carga del RAG y extracción de PDFs), lo cual oculta errores de parsing que dificultan la depuración en producción.
* **Rendimiento**: Muy bueno. El uso de `ThreadPoolExecutor` para la pre-extracción de PDFs en paralelo durante el inicio y el cacheado `lru_cache` de `extract_text` reducen sustancialmente la latencia percibida por el usuario.

---

## 7. Evaluación del Uso de Inteligencia Artificial

* **IA Generativa (RAG)**: **Excelente y de Valor Real**. El motor RAG vectorial es robusto, estructurando de manera impecable el conocimiento del negocio (las reglas críticas y señales) y los datos operativos para guiar libremente las respuestas conversacionales de Llama 3.1 sin depender de flujos rígidos de *If/Else*.
* **Machine Learning Supervisado**: **Insuficiente y Superficial**. Como se analizó, el entrenamiento del *Random Forest* sobre una etiqueta derivada directamente de las reglas es un error clásico de modelado que invalida la justificación científica de la IA supervisada ante un jurado experto.
* **Machine Learning No Supervisado**: **Muy Bueno**. La integración de *Isolation Forest* y el agrupamiento de narrativas clonadas por similitud del vector de embeddings representan técnicas avanzadas que aportan valor real de negocio al descubrir patrones atípicos y sospechas de colusión.

---

## 8. Rúbrica de Evaluación del Jurado

Alineando el sistema con la **Matriz de Evaluación del PDF (Sección 22)**:

| Criterio | Peso | Nivel Asignado | Calificación | Justificación Técnica |
| :--- | :---: | :---: | :---: | :--- |
| **Tecnología y Arquitectura** | 10% | 4: Avanzado | **4.2 / 5.0** | Excelente modularidad y código limpio, pero penalizado severamente por no cumplir con la estructura de archivos e incluir credenciales ficticias configurables vía `.env`. |
| **Análisis del Caso y Lógica** | 15% | 5: Excepcional | **4.8 / 5.0** | Cruza múltiples variables complejas, implementa el motor de reglas determinista de forma impecable y detecta redes de colusión mediante clústeres. |
| **Uso de IA y Prototipo** | 40% | 4: Avanzado | **4.0 / 5.0** | UI en Streamlit premium y RAG local de alta velocidad. Penalizado fuertemente por la circularidad metodológica en el entrenamiento de Random Forest y falta de API. |
| **Explicabilidad y Ética** | 25% | 5: Excepcional | **5.0 / 5.0** | Excelente sección ética integrada. Ofrece explicabilidad por desglose de score, análisis de sesgos, y disclaimers claros sobre el rol humano. |
| **Pitch, Impacto y Negocio** | 10% | 2: Básico | **2.5 / 5.0** | Al carecer de la carpeta `presentation/` con el PDF del Pitch y los diagramas de arquitectura en el repositorio, la calificación del jurado disminuye fuertemente en esta entrega fría. |
| **CALIFICACIÓN PONDERADA FINAL** | **100%** | **Avanzado** | **4.25 / 5.0** | **8.5 / 10** | **Prototipo de alto nivel competitivo**, fuerte candidato al podio, pero lastrado por la circularidad del modelo supervisado y desatención a entregables de estructura. |

---

## 9. Recomendaciones Prioritarias Antes de Entregar

Para asegurar el **primer lugar (10/10)** y mitigar los cuestionamientos del jurado técnico, se deben realizar las siguientes acciones inmediatas:

1. **Reestructurar el Repositorio de GitHub**:
   - Crear las carpetas: `docs/`, `notebooks/`, `tests/` y `presentation/`.
   - Mover la documentación técnica a `docs/` en los nombres de archivos requeridos.
   - Crear un archivo básico `tests/test_rules.py` con `pytest` para verificar la estabilidad de las reglas ante datos de prueba.
2. **Corregir la Circularidad del Modelo de Machine Learning**:
   - Modificar `supervised_model.py` para usar una etiqueta no correlacionada directamente con el score global. Por ejemplo, entrenar el *Random Forest* únicamente para predecir si un siniestro requiere auditoría basándose en anomalías numéricas del *Isolation Forest* y similitudes del NLP, o usar un dataset simulado donde existan casos etiquetados de forma semi-aleatoria.
3. **Implementar una API REST Mínima con FastAPI**:
   - Escribir `src/api.py` exponiendo los métodos principales en endpoints `/score` y `/validate`. Esto deslumbrará al jurado técnico al demostrar escalabilidad e integración empresarial inmediata.
4. **Validación Numérica del RUC**:
   - Reemplazar la búsqueda por regex de `"INVÁLIDO"` en `src/pdf_extractor.py` por una función de validación del módulo 10 para RUCs ecuatorianos reales.
5. **Cargar el Pitch en el Repositorio**:
   - Asegurarse de colocar el archivo `presentation/pitch.pdf` con la presentación ejecutiva del equipo.

---

## 10. Calificación Final General

# 🏆 Nota: 8.5 / 10 (Nivel Avanzado)

**Justificación**: FRAUDIA representa una solución técnica robusta, con una de las interfaces de usuario más limpias y completas evaluadas en competencias de hackathon. Su motor híbrido de reglas, validación cruzada y RAG vectorial conversacional local demuestran un dominio tecnológico excepcional. Sin embargo, los fallos metodológicos de Machine Learning (la circularidad en Random Forest) y el desorden estructural en los entregables del repositorio le restan la puntuación máxima. La implementación de las recomendaciones prioritarias elevará con total seguridad el sistema a un nivel **Excepcional (10/10)**.
