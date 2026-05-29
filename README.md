# 🔍 FRAUDIA — Detector de Posibles Fraudes en Siniestros

Prototipo funcional para la **hackIAthon 2026 — Reto Aseguradora del Sur**.
Sistema **híbrido de IA** que combina **Reglas de Negocio (RF-01…07) + Isolation Forest + Random Forest + RAG + NLP**
para asignar a cada siniestro un **score de riesgo explicable** y generar **alertas de revisión**.

> ⚖️ **Importante:** FRAUDIA genera **alertas de revisión**, no acusaciones formales de fraude.
> La decisión final es siempre del analista humano.

---

## 🚀 Instalación

```bash
# 1. Entrar a la carpeta del proyecto
cd hackathon

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
# Si "streamlit" no está en el PATH:
python -m streamlit run app.py
```

Abre el navegador en `http://localhost:8501`.

**Flujo de uso:**
1. En la **pantalla de bienvenida**, elige el *Dataset Principal · 500 siniestros* y pulsa **Cargar y analizar dataset**.
2. Al terminar la carga, se abre un **tour guiado** que te lleva por cada pantalla.
3. Navega con el **menú lateral**. En cada pantalla tienes el botón **"Guía de pantalla"**.
4. (Opcional) Pega tu **Groq API Key** en el panel lateral para respuestas redactadas del Agente IA.
   Sin clave, el agente funciona en **modo retrieval-only**.

> La primera carga genera un caché en disco; los siguientes arranques son casi instantáneos.

---

## 📁 Estructura del proyecto

```
hackathon/
├── app.py                          # Aplicación Streamlit (navegación lateral, 9 pantallas)
├── run_publico.py                  # Lanzador con túnel ngrok (enlace público)
├── requirements.txt
├── .env.example
├── README.md
│
├── data/
│   ├── dataset/                    # Dataset incluido (Excel + PDFs)
│   │   ├── Evento Datasets_Sinteticos_Fraude_500_v2.xlsx
│   │   ├── PARTE POLICIAL/ · DECLARACIÓN DE ACCIDENTE/ · FACTURAS/
│   ├── ecuador_provincias.geojson  # Límites provinciales para el mapa
│   └── cache/                      # Caché de datos y del índice RAG (se autogenera)
│
├── src/
│   ├── data_loader.py              # Carga el Excel (5 hojas) + mapea PDFs
│   ├── pdf_extractor.py            # Extracción y detección de tipo de PDF
│   ├── fraud_rules.py              # Motor de reglas RF-01…07 + señales (score 0-100)
│   ├── cross_validator.py          # Cruce de campos entre PDFs y Excel
│   ├── anomaly_model.py            # Isolation Forest + mapa Ecuador + narrativas clonadas
│   ├── supervised_model.py         # Random Forest + score combinado
│   ├── rag_engine.py               # RAG (sentence-transformers + FAISS + Groq)
│   ├── knowledge_base.py           # Reglas y señales como contexto para el RAG
│   ├── network_graph.py            # Grafo relacional asegurados-siniestros-proveedores
│   ├── report_generator.py         # Reporte ejecutivo PDF (fpdf2)
│   └── api.py                      # API REST (FastAPI): /score y /validate
│
├── docs/                           # Arquitectura, modelo de datos, reglas, ética, pitch
└── tests/test_rules.py
```

---

## 🧭 Pantallas (navegación lateral)

| Pantalla | Funcionalidad |
|---|---|
| 📊 Dashboard | KPIs · panel de ahorro · mapa de Ecuador (con provincias) · bandeja de siniestros (coloreada por nivel) · export CSV/PDF |
| 🔍 Siniestro | Expediente 360° · desglose de señales · validación cruzada PDF ↔ Excel |
| 🏢 Proveedores | Ranking por alertas rojas · lista restrictiva |
| 🤖 Agente IA | RAG con Groq + 12 preguntas del reto |
| 🧠 Modelo ML | Random Forest · Isolation Forest · narrativas clonadas |
| 🕸️ Red Relacional | Grafo interactivo de relaciones |
| 📄 Cargar Documento | Sube un PDF/Excel y valida contra el dataset (reemplazar o **combinar**) |
| ⚖️ Ética | Limitaciones · sesgo · flujo de revisión humana |
| 📘 Manual | Guía de uso del sistema |

---

## 🎯 Score de Riesgo

```
0  – 40   🟢 VERDE     Continuar flujo normal
41 – 75   🟡 AMARILLO  Escalar para revisión documental
76 – 100  🔴 ROJO      Escalar a Unidad Antifraude (revisión de campo)
```

**Reglas críticas que fuerzan ROJO:** RF-01 (Pérdida Total/Robo), RF-02 (Adulteración),
RF-03 (Lista restrictiva), RF-04 (Dinámica imposible).
**Reglas que fuerzan AMARILLO mínimo:** RF-05 (borde vigencia), RF-06 (demora robo), RF-07 (narrativa clonada).

---

## 🔧 Stack técnico

- **Streamlit** — interfaz web (navegación lateral + tour guiado, responsive)
- **pandas + openpyxl** — manejo del Excel
- **pdfplumber** — extracción de PDFs
- **scikit-learn** — Isolation Forest + Random Forest + TF-IDF
- **sentence-transformers + FAISS** — embeddings y búsqueda vectorial (RAG)
- **Groq llama-3.1-8b-instant** — LLM del agente conversacional con streaming
- **plotly + networkx** — visualizaciones y grafos
- **fpdf2** — reporte ejecutivo PDF
- **FastAPI + uvicorn** — API REST

---

## 🌐 Despliegue

> ⚠️ **Streamlit NO funciona en Vercel/Netlify** (son para sitios estáticos/serverless; Streamlit
> necesita un servidor persistente con websockets). Usa una de estas opciones:

### Opción A — Streamlit Community Cloud (recomendada, gratis)
1. Sube el repo a GitHub (público).
2. Entra a [share.streamlit.io](https://share.streamlit.io) con tu cuenta de GitHub.
3. *New app* → elige el repo, rama y `app.py` → **Deploy**.
4. Agrega `GROQ_API_KEY` en *Settings → Secrets* si quieres el Agente IA con LLM.

### Opción B — Enlace público temporal con ngrok (para la demo en vivo)
```bash
pip install pyngrok
python run_publico.py        # arranca la app y muestra un enlace https público
```

### Opción C — Render / Railway / Hugging Face Spaces
Plataformas con servidor persistente. Comando de arranque:
`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

### 🔌 API REST (FastAPI)
```bash
uvicorn src.api:app --reload      # docs interactivas en http://localhost:8000/docs
```

---

## 🛡️ Ética y limitaciones

- Datos **100% sintéticos** — sin credenciales ni datos personales reales.
- El sistema **declara sus limitaciones** (falsos positivos ~15-20%).
- Toda decisión final **requiere revisión humana**.
- Análisis de sesgo por ramo y sucursal disponible en la pantalla **Ética**.
