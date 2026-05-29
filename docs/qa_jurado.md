# 🏆 GUÍA DE QA CRÍTICO Y PREPARACIÓN PARA EL PITCH — JURADO TÉCNICO

Esta guía contiene la recopilación de preguntas críticas y simulaciones de "Pruebas de Fuego" que el jurado técnico del **hackIAthon 2026** realizará durante la presentación y demostración en vivo de **FRAUDIA**. Su objetivo es proporcionar al equipo las respuestas exactas, fundamentadas en la arquitectura y código real del sistema, demostrando un dominio técnico de nivel de producción.

---

## 1. Cuestionario Crítico del Jurado (Pitch de 10 Minutos)

### 💬 Pregunta 1 (Técnica): ¿Cómo detectan específicamente la similitud entre dos narrativas de reclamo?
* **Respuesta del Equipo:**
  "Detectamos la similitud en dos niveles complementarios para evitar falsos negativos:
  1. **Nivel Sintáctico y Estructural (NLP Tradicional):** En `anomaly_model.py`, procesamos las descripciones de los siniestros utilizando un vectorizador **TF-IDF** configurado con n-gramas de 1 a 2 palabras. Normalizamos el texto en minúsculas y eliminamos de forma nativa los acentos de la codificación Unicode. Con la matriz resultante, calculamos la **similitud del coseno** (`cosine_similarity`). Si la similitud supera el **85%**, el sistema activa la regla **RF-07 (Narrativa Clonada)** asignando 8 puntos y forzando una alerta de nivel amarillo.
  2. **Nivel Semántico y Conceptual (IA Vectorial):** En `rag_engine.py`, convertimos el texto a representaciones vectoriales densas utilizando el modelo multilingüe de embeddings `paraphrase-multilingual-MiniLM-L12-v2` de *Sentence-Transformers*. Estos vectores se indexan en un motor de base de datos vectorial local con **FAISS**. Esto permite al Agente de IA identificar siniestros conceptualmente relacionados aunque utilicen sinónimos o palabras diferentes."

### 💬 Pregunta 2 (Negocio): ¿Cómo ayuda su solución a que un analista humano tome una decisión más rápida?
* **Respuesta del Equipo:**
  "FRAUDIA optimiza drásticamente los tiempos operativos a través de dos mecanismos clave:
  1. **Bandeja de Entrada Semaforizada y Priorizada:** En el Dashboard visualizamos de forma instantánea el estado de toda la cartera de siniestros, clasificándolos en verde, amarillo o rojo. Esto permite al analista enfocarse únicamente en los **casos críticos**. Mostramos además una simulación de ahorro potencial estimado del **20%** sobre la cartera en riesgo, facilitando la toma de decisiones presupuestarias y de asignación de personal.
  2. **Módulo Automático de Validación Cruzada:** En `cross_validator.py`, comparamos en milisegundos las placas, nombres de conductores, RUCs de talleres y descripciones extraídas de los PDFs (parte policial, declaración jurada y facturas) contra el registro estructurado de la base de datos Excel. Detectar que un asegurado declara un siniestro por *Robo Total* pero presenta una *Factura de reparación de carrocería* (Lógica Imposible) o que el RUC del proveedor es inválido le tomaría horas de cruce documental manual a un analista. Con FRAUDIA es inmediato."

### 💬 Pregunta 3 (Ética): ¿Qué medidas tomaron para evitar que la IA acuse a un cliente de fraude injustamente?
* **Respuesta del Equipo:**
  "Bajo el principio de **Inteligencia Artificial Responsable y Ética**, implementamos las siguientes salvaguardas:
  1. **Lenguaje No Acusatorio:** En todo el código, interfaz y reportes PDF declaramos formalmente que el sistema genera **'alertas de revisión prioritaria'** y **'posibles anomalías'**, prohibiendo estrictamente los términos de acusación directa.
  2. **Revisión Humana Obligatoria (Human-in-the-Loop):** La decisión final de rechazar o pausar un siniestro reside 100% en el analista y la jefatura. El sistema es una herramienta de apoyo a la decisión, no un decisor autónomo.
  3. **Trazabilidad y Explicabilidad Completa:** No utilizamos algoritmos de 'caja negra'. En la tab de *Siniestro Individual* desglosamos visualmente el origen exacto de los puntos del score por cada señal activada.
  4. **Auditoría de Sesgos:** En la tab de *Ética y Limitaciones* el sistema calcula y grafica de forma dinámica el porcentaje de alertas rojas emitidas por ramo y por sucursal. Esto permite a los auditores detectar si el modelo está sesgado contra una ciudad o segmento específico y calibrar los pesos de las reglas."

---

## 2. Pruebas de Fuego de la Demo en Vivo (Live Demo)

### 🔥 Prueba 1 (Consulta Agéntica): "Pregúntele a su sistema: ¿Qué proveedores concentran el 80% de las alertas rojas?"
* **Lógica del Sistema:**
  Al hacer clic en el botón de chat o ingresar la pregunta en el tab **🤖 Agente IA**, nuestro motor RAG busca semánticamente en el índice FAISS los fragmentos relacionados con *proveedores* y *siniestros en nivel rojo*. 
* **Respuesta Esperada del Agente:**
  El LLM *Llama 3.1 8B* vía *Groq* razonará sobre los datos vectorizados del Excel e identificará de inmediato los talleres mecánicos y clínicas asociadas a siniestros rojos. Responderá de la siguiente forma estructurada:
  * *"Basado en el análisis de datos indexados, los proveedores que concentran la mayor cantidad de siniestros con alerta roja de posible fraude son:*
    1. **TALLER XYZ (ID: PROV-0004)** *con N siniestros en nivel crítico.*
    2. **CLÍNICA ABC (ID: PROV-0009)** *con M siniestros en nivel crítico.*
    *Recomendamos priorizar la auditoría técnica sobre estos proveedores debido a la alta coincidencia en facturaciones atípicas."*

### 🔥 Prueba 2 (Prueba de Score): "Cargue este siniestro ocurrido 24 horas después de la póliza y explíquenos el riesgo asignado."
* **Lógica del Sistema:**
  Cuando el jurado nos pida simular este caso en el tab **📄 Cargar Documento**, el sistema procesará la fecha de contratación de la póliza y la fecha de ocurrencia del siniestro.
* **Respuesta Esperada del Equipo:**
  "Al ingresar el siniestro, el motor de reglas en `src/fraud_rules.py` calcula la diferencia de tiempo. Al ser menor a 48 horas:
  1. Se activa automáticamente la regla de negocio crítica **RF-05 (Siniestro Extremo al Borde de Vigencia)**.
  2. Esta regla asigna **8 puntos** al score y fuerza un semáforo de riesgo mínimo de **AMARILLO** ( score mínimo de 41), de acuerdo con la Sección 8 del PDF oficial.
  3. El sistema emitirá la alerta visual correspondiente e indicará en la sección de acción recomendada: **'REVISAR → Unidad Antifraude (revisión documental obligatoria)'**."

### 🔥 Prueba 3 (Verificación de Repositorio): "Muestre la estructura de su GitHub para verificar la modularidad del código."
* **Lógica del Sistema:**
  Aunque tuvimos discrepancias iniciales en la fase de desarrollo, el repositorio se encuentra estructurado en módulos de alta cohesión y bajo acoplamiento dentro del directorio `src/`, separando el frontend del motor de cálculo.
* **Respuesta Esperada del Equipo:**
  "Nuestra arquitectura de código está diseñada para la escalabilidad empresarial:
  * `src/data_loader.py`: Encargado del consumo estructurado del dataset Excel.
  * `src/pdf_extractor.py`: Encargado de la extracción de texto y campos clave de los PDFs.
  * `src/fraud_rules.py`: El core del motor que computa las 14 señales del reto y las 7 reglas críticas.
  * `src/cross_validator.py`: Realiza el cruce y validación documental automatizada.
  * `src/anomaly_model.py`: Implementa el modelo de agrupamiento de narrativas NLP y el *Isolation Forest*.
  * `src/supervised_model.py`: Contiene el entrenamiento y métricas del clasificador *Random Forest*.
  * `src/rag_engine.py`: El cerebro agéntico que gestiona la base vectorial FAISS local y el streaming de Groq."

---

## 3. Respuestas de Seguridad y Escalabilidad (Preguntas Avanzadas)

### 🔒 Pregunta: ¿Cómo garantizan la privacidad de los datos al enviar información de siniestros a una API externa de LLM como Groq?
* **Respuesta del Equipo:**
  "Para este prototipo de hackathon, utilizamos datos 100% sintéticos libres de información personal identificable (PII), cumpliendo estrictamente con la Ley Orgánica de Protección de Datos Personales (LOPD) de Ecuador.
  En un despliegue productivo para la Aseguradora del Sur:
  1. **RAG Local Autónomo:** La base de datos vectorial FAISS y el modelo de embeddings *MiniLM* corren de forma 100% local en los servidores de la compañía.
  2. **Privacidad en Generación:** La API de Groq puede ser desconectada del backend instantáneamente. El código de `rag_engine.py` permite sustituir a Groq por un **LLM local de código abierto** (como *Llama 3 8B* o *Mistral 7B*) desplegado dentro de la red corporativa privada mediante herramientas como Ollama o vLLM, garantizando que **ningún dato sensible salga del perímetro de seguridad** de la aseguradora."

### 🔒 Pregunta: Su modelo Random Forest tiene una precisión sospechosamente alta del 100% en el notebook. ¿Por qué ocurre esto?
* **Respuesta del Equipo (Honestidad y Madurez Metodológica):**
  "Detectamos que en el dataset sintético proporcionado no existía una columna confirmada de fraude real. Para demostrar la capacidad predictiva del pipeline supervisado (Sección 9 del PDF del reto), generamos una etiqueta simulada basada en el umbral de reglas `(Score >= 76)`.
  Como científicos de datos, reconocemos plenamente que esto introduce una **circularidad de datos (data leakage)**, por lo que el Random Forest está simplemente imitando la lógica determinista de las reglas de negocio.
  En producción, **esta etiqueta se reemplazará por la resolución histórica de fraudes reales confirmados** por el departamento de auditoría o sentencias legales. Esto permitirá al modelo supervisado aprender correlaciones multivariables y patrones latentes complejos que las reglas de negocio estáticas nunca podrían predecir por sí solas, completando el verdadero valor del enfoque híbrido."
