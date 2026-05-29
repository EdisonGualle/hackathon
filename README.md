# 🔍 FRAUDIA — Detector de Posibles Fraudes en Siniestros

Prototipo funcional para la **hackIAthon 2026 — Reto Aseguradora del Sur**.
Sistema híbrido de IA que combina **Reglas de Negocio + Isolation Forest + Random Forest + RAG + NLP**
para detectar señales de posible fraude en siniestros de seguros.

> ⚖️ **Importante:** FRAUDIA genera **alertas de revisión**, no acusaciones formales de fraude.
> La decisión final es siempre del analista humano.

---

## 🚀 Instalación

```bash
# 1. Clonar / descargar el proyecto
cd fraudia

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. (Opcional) configurar API Key de Groq para el Agente IA
cp .env.example .env
# Editar .env y poner tu GROQ_API_KEY (gratis en console.groq.com)
```

---

## ▶️ Ejecución

```bash
streamlit run app.py
```

Abre el navegador en `http://localhost:8501`.

En el panel lateral:
1. Pega tu **Groq API Key** (gratis en https://console.groq.com)
2. Clic en **🚀 Cargar Dataset**
3. (Opcional) Clic en **🧠 Activar Agente IA** para habilitar el chat RAG

---

## 📁 Estructura del proyecto

```
fraudia/
├── app.py                          # Aplicación Streamlit (8 tabs)
├── requirements.txt
├── .env.example
├── README.md
│
├── data/dataset/                   # Dataset incluido
│   ├── Evento Datasets_Sinteticos_Fraude_500_v2.xlsx
│   ├── PARTE POLICIAL/             # 6 PDFs
│   ├── DECLARACIÓN DE ACCIDENTE/   # 5 PDFs
│   └── FACTURAS/                   # 13 PDFs
│
└── src/
    ├── data_loader.py              # Carga Excel + mapea PDFs
    ├── pdf_extractor.py            # Extracción y detección de tipo de PDF
    ├── fraud_rules.py              # Motor de reglas RF-01..RF-07 + 14 señales
    ├── cross_validator.py          # Cruce de campos entre PDFs y Excel
    ├── anomaly_model.py            # Isolation Forest + mapa + clusters narrativos
    ├── supervised_model.py         # Random Forest + score combinado
    ├── rag_engine.py               # RAG con sentence-transformers + Groq
    ├── network_graph.py            # Grafo relacional asegurados-siniestros-proveedores
    └── report_generator.py         # PDF ejecutivo con fpdf2
```

---

## 🧠 Pantallas

| Tab | Funcionalidad |
|---|---|
| 📊 Dashboard | KPIs · Tabla filtrable · Mapa Ecuador · Top ciudades · Exportar CSV/PDF |
| 🔍 Siniestro | Detalle · Score breakdown · Cross-validación de PDFs |
| 📄 Cargar Documento | Subir PDF/Excel y validar contra el dataset en tiempo real |
| 🤖 Agente IA | RAG con Groq + 12 preguntas del reto |
| 🧠 Modelo ML | Isolation Forest + Random Forest + Narrativas clonadas |
| 🕸️ Red Relacional | Grafo interactivo de relaciones |
| ⚖️ Ética | Limitaciones · Sesgo · Flujo revisión humana |
| 🏢 Proveedores | Ranking + lista restrictiva |

---

## 🎯 Score de Riesgo

```
0  – 40   🟢 VERDE     Continuar flujo normal
41 – 75   🟡 AMARILLO  Escalar para revisión documental
76 – 100  🔴 ROJO      Escalar a Unidad Antifraude (revisión de campo)
```

**Reglas críticas que fuerzan ROJO:** RF-01 (Pérdida Total Robo), RF-02 (Adulteración),
RF-03 (Lista restrictiva), RF-04 (Dinámica imposible).

**Reglas que fuerzan AMARILLO mínimo:** RF-05 (borde vigencia), RF-06 (demora robo), RF-07 (narrativa clonada).

---

## 🔧 Stack técnico

- **Streamlit** — interfaz web
- **pandas + openpyxl** — manejo del Excel
- **pdfplumber** — extracción de PDFs
- **scikit-learn** — Isolation Forest + Random Forest + TF-IDF
- **sentence-transformers + FAISS** — embeddings y búsqueda vectorial (RAG)
- **Groq llama-3.1-8b-instant** — LLM del agente conversacional con RAG + streaming (<3s)
- **plotly + networkx** — visualizaciones y grafos
- **fpdf2** — generación de reporte ejecutivo PDF

---

## 📦 Despliegue

El proyecto es completamente portable. Solo necesitas:
- Python 3.10+
- Acceso a internet (para descargar el modelo de embeddings la primera vez)
- (Opcional) Groq API Key para el agente IA

Los archivos del dataset están dentro de `data/dataset/` por lo que no se requiere configurar rutas externas.

### 🌐 Ejecución de la API REST (FastAPI)

Para desplegar y consultar el motor de scoring y validación mediante servicios web externos:

```bash
# Iniciar servidor Uvicorn en el puerto 8000
uvicorn src.api:app --reload
```

Una vez levantado, accede a la documentación Swagger interactiva en `http://localhost:8000/docs` para realizar peticiones POST automáticas a los endpoints `/score` y `/validate`.

---

## 🛡️ Ética y limitaciones

- Datos 100% sintéticos
- No se exponen credenciales ni datos personales reales
- El sistema declara explícitamente sus limitaciones (falsos positivos 15-20%)
- Toda decisión final requiere revisión humana
- Análisis de sesgo por ramo y sucursal disponible en la tab Ética
