# 🧠 USO EFECTIVO DE INTELIGENCIA ARTIFICIAL — FRAUDIA

Este documento detalla el diseño, entrenamiento, justificación científica y límites éticos de los modelos y componentes de Inteligencia Artificial implementados en **FRAUDIA** para la **Aseguradora del Sur**.

---

## 1. Machine Learning Supervisado (Random Forest)

### 🌲 Justificación del Modelo
Utilizamos un algoritmo de **Random Forest Classifier** con 300 estimadores debido a su robustez frente al sobreajuste, capacidad de manejar variables categóricas previamente codificadas y facilidad para proveer explicabilidad a través de la importancia de variables (*feature importance*).

### 🛡️ Mitigación de Circularidad (Data Leakage)
En la fase de prototipo, el dataset sintético de la Aseguradora del Sur carecía de una etiqueta real de fraude. Para evitar la circularidad matemática (data leakage) consistente en entrenar el clasificador para predecir las mismas reglas de negocio del semáforo (`Score_Reglas >= 76`), diseñamos un pipeline inteligente:
* **Entrenamiento con etiqueta combinada:** La etiqueta de entrenamiento se genera mediante la coincidencia de un score de anomalía de *Isolation Forest* elevado (`Anomaly_Score >= 60`) y la presencia de al menos una inconsistencia física de validación cruzada.
* **Beneficio:** El Random Forest aprende a correlacionar atipicidades estadísticas multivariables y discrepancias documentales en lugar de reglas fijas. En producción, esta etiqueta sintética será sustituida por las resoluciones definitivas de auditoría.

---

## 2. Machine Learning No Supervisado (Isolation Forest)

### 🔮 Detección de Anomalías
Para detectar posibles siniestros fraudulentos que las reglas de negocio deterministas no contemplan, implementamos un modelo de **Isolation Forest** entrenado sobre las variables numéricas clave de la reclamación:
* Días transcurridos entre inicio/fin de póliza y accidente.
* Monto reclamado vs. monto estimado y suma asegurada.
* Cantidad de reclamos previos del asegurado.
* Días de diferencia en el reporte.

El algoritmo calcula un score de rareza estadístico (0-100). Los siniestros que obtienen más de **60 puntos** se clasifican como anómalos, lo que representa un indicador prioritario para la auditoría técnica.

---

## 3. Procesamiento de Lenguaje Natural (NLP) y RAG

### 💬 Procesamiento de Texto de Reclamos
Utilizamos **TF-IDF Vectorizer** para codificar descripciones de siniestros y agrupar reclamos similares mediante similitud del coseno. Esto ayuda a detectar anillos de colusión coordinados donde múltiples asegurados utilizan el mismo relato.

### 🤖 Agente IA Conversacional (RAG)
El agente de IA conversacional permite consultas libres sobre los 500 siniestros, proveedores y PDFs en tiempo real. 

* **Embeddings locales:** Convertimos los textos estructurados en vectores numéricos densos de 384 dimensiones usando `paraphrase-multilingual-MiniLM-L12-v2`.
* **Indexación y búsqueda:** Almacenamos y buscamos de forma local en memoria con **FAISS Index**.
* **Generación fluida:** Las consultas se envían con contexto delimitado al LLM `Llama 3.1 8B` en la API de Groq, permitiendo respuestas naturales en streaming en menos de 3 segundos.
