"""
FRAUDIA — Detector de Posibles Fraudes en Siniestros
Aseguradora del Sur · hackIAthon 2026
UI: Blanco y Azul Corporativo
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuración de variables de entorno Hugging Face para estabilidad en Windows
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["TQDM_DISABLE"] = "1"

try:
    import transformers
    transformers.utils.logging.disable_progress_bar()
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv(override=True)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

from src.data_loader import (
    load_excel, map_pdfs, validate_excel_structure,
    EXPECTED_SHEETS, DEFAULT_EXCEL, DEFAULT_DOCS,
)
from src.pdf_extractor import extract_text, detect_doc_type, extract_sin_id, extract_fields
from src.fraud_rules import score_siniestro, calculate_scores_batch
from src.cross_validator import cross_validate
from src.network_graph import build_graph

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FRAUDIA · Antifraude IA",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: Tema Blanco y Azul Corporativo ──────────────────────────────────────
st.markdown("""
<style>
/* ══ BASE: todo blanco/azul ══ */
.stApp { background-color: #FFFFFF !important; }
.stApp p, .stApp span, .stApp label, .stApp div { color: #1A3A5C; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #EBF5FB !important; border-right:2px solid #AED6F1; }
[data-testid="stSidebarContent"] * { color: #1A3A5C !important; }

/* ── Bloque principal ── */
.main .block-container { padding-top: 1rem; background: white; }
section[data-testid="stMain"] { background: white !important; }

/* ── Encabezados ── */
h1, h2, h3, h4 { color: #1B4F8A !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #1B4F8A !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #EBF5FB; border-radius:10px; padding:4px; gap:4px;
    border: 1px solid #D6EAF8;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #2471A3 !important;
    border-radius:8px; font-weight:600; font-size:.85rem;
}
.stTabs [aria-selected="true"] {
    background: #1B4F8A !important; color: white !important;
}
.stTabs [data-baseweb="tab-panel"] { background: white; }

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background: white !important; color: #1A3A5C !important;
    border: 1px solid #AED6F1 !important; border-radius:6px !important;
}
.stTextInput input:focus { border-color: #1B4F8A !important; }
.stTextInput label, .stTextArea label { color: #1B4F8A !important; font-weight:600; }

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: white !important; color: #1A3A5C !important;
    border: 1px solid #AED6F1 !important;
}
.stSelectbox label { color: #1B4F8A !important; font-weight:600; }
[data-baseweb="select"] { background: white !important; }
[data-baseweb="select"] * { color: #1A3A5C !important; background: white !important; }
[data-baseweb="popover"] { background: white !important; border:1px solid #D6EAF8 !important; }
[data-baseweb="menu"] { background: white !important; }
[data-baseweb="option"] { background: white !important; color: #1A3A5C !important; }
[data-baseweb="option"]:hover { background: #EBF5FB !important; }

/* ── Multiselect ── */
[data-baseweb="tag"] { background: #1B4F8A !important; color: white !important; }
.stMultiSelect label { color: #1B4F8A !important; font-weight:600; }

/* ── Radio ── */
.stRadio label { color: #1A3A5C !important; }
.stRadio [role="radiogroup"] label { color: #1A3A5C !important; }

/* ── Dataframe / Table ── */
.stDataFrame, .stDataFrame * { color: #1A3A5C !important; }
[data-testid="stDataFrame"] { background: white !important; }
.dataframe th { background: #1B4F8A !important; color: white !important; }
.dataframe td { background: white !important; color: #1A3A5C !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #EBF5FB !important; color: #1B4F8A !important;
    border-radius:8px; border:1px solid #D6EAF8 !important;
    font-weight:600;
}
.streamlit-expanderContent {
    background: white !important; border:1px solid #D6EAF8 !important;
}

/* ── Divider ── */
hr { border-color: #D6EAF8 !important; }

/* ── Metrics ── */
[data-testid="metric-container"] { background: white !important; }
[data-testid="metric-container"] label { color: #5D6D7E !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #1B4F8A !important; }

/* ── Alerts (info, warning, error, success) ── */
.stAlert { border-radius: 8px !important; }
[data-baseweb="notification"] { background: white !important; }

/* ── Form ── */
[data-testid="stForm"] { background: white !important; border:1px solid #D6EAF8; border-radius:10px; padding:10px; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #1B4F8A !important; }

/* ── Captions ── */
.stCaption, small, caption { color: #5D6D7E !important; }

/* ── Botones ── */
.stButton>button {
    background: #1B4F8A !important; color: white !important;
    border: none !important; border-radius:8px !important;
    font-weight:600 !important;
}
.stButton>button:hover { background: #2471A3 !important; }
.stDownloadButton>button {
    background: #27AE60 !important; color: white !important;
    border: none !important; border-radius:8px !important; font-weight:600 !important;
}
.stDownloadButton>button:hover { background: #1E8449 !important; }

/* ── KPI Cards ── */
.kpi-box {
    background: #F8FBFF; border-radius:14px; padding:20px 12px;
    text-align:center; border:2px solid #D6EAF8;
    box-shadow: 0 2px 10px rgba(27,79,138,0.08);
}
.kpi-val { font-size:2.1rem; font-weight:900; }
.kpi-lbl { font-size:.78rem; color:#5D6D7E; margin-top:4px; }

/* ── Cards de alerta ── */
.card-rojo  { background:#FEF5F5; border-left:4px solid #E74C3C; padding:10px 14px; border-radius:6px; margin:4px 0; color:#1A3A5C; }
.card-amar  { background:#FEFAF0; border-left:4px solid #F39C12; padding:10px 14px; border-radius:6px; margin:4px 0; color:#1A3A5C; }
.card-verde { background:#F0FDF4; border-left:4px solid #27AE60; padding:10px 14px; border-radius:6px; margin:4px 0; color:#1A3A5C; }
.card-azul  { background:#EBF5FB; border-left:4px solid #2980B9; padding:10px 14px; border-radius:6px; margin:4px 0; color:#1A3A5C; }
.match-ok   { background:#F0FDF4; border-left:4px solid #27AE60; padding:7px 12px;  border-radius:4px; margin:3px 0; color:#1A3A5C; }
.issue-CRÍTICO { background:#FEF5F5; border-left:4px solid #E74C3C; padding:8px 12px; border-radius:4px; margin:3px 0; color:#1A3A5C; }
.issue-ALTO    { background:#FFF8F0; border-left:4px solid #E67E22; padding:8px 12px; border-radius:4px; margin:3px 0; color:#1A3A5C; }
.issue-MEDIO   { background:#FEFAF0; border-left:4px solid #F39C12; padding:8px 12px; border-radius:4px; margin:3px 0; color:#1A3A5C; }

/* ── Score bar ── */
.score-track      { background:#E8EAF0; border-radius:8px; height:14px; overflow:hidden; }
.score-fill-rojo  { background:linear-gradient(90deg,#E74C3C,#C0392B); height:14px; border-radius:8px; }
.score-fill-amar  { background:linear-gradient(90deg,#F39C12,#E67E22); height:14px; border-radius:8px; }
.score-fill-verde { background:linear-gradient(90deg,#27AE60,#1E8449); height:14px; border-radius:8px; }

/* ── Chat ── */
.chat-user { background:#EBF5FB; border-radius:12px; padding:10px 14px; margin:6px 0; border:1px solid #D6EAF8; color:#1A3A5C; }
.chat-bot  { background:#F8FBFF; border-radius:12px; padding:10px 14px; margin:6px 0; border:1px solid #AED6F1; color:#1A3A5C; }

/* ── Sidebar labels ── */
[data-testid="stSidebar"] label { color: #1B4F8A !important; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "sheets": None, "pdf_map": None, "scores_df": None,
    "rag": None, "rag_ready": False, "chat_history": [],
    "data_loaded": False, "ml_result": None,
    "rf_result": None, "combined_df": None, "clusters": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Modal de Coincidencias (Diálogo Streamlit) ───────────────────────────────
@st.dialog("🔍 Detalles de la Validación Cruzada", width="large")
def mostrar_modal_coincidencia(match_data: dict, row: dict, all_pdf_fields: dict):
    campo_origen = match_data.get("campo", "N/D")
    sin_id = row.get("ID Siniestro", "N/D")
    
    st.markdown(f"### 📋 Expediente del Siniestro: **{sin_id}**")
    st.markdown("Comparativa detallada de campos extraídos vs Base de Datos (Excel):")
    st.markdown("---")

    # Extraer valores de PDFs
    parte = all_pdf_fields.get("PARTE_POLICIAL", {}) if all_pdf_fields else {}
    factura = all_pdf_fields.get("FACTURA", {}) if all_pdf_fields else {}
    declaracion = all_pdf_fields.get("DECLARACION", {}) if all_pdf_fields else {}

    pdf_placa = parte.get("placa") or factura.get("placa") or declaracion.get("placa") or "N/D"
    pdf_monto = factura.get("total") or "N/D"
    pdf_fecha = parte.get("fecha_hecho") or factura.get("fecha") or declaracion.get("fecha") or "N/D"
    pdf_persona = parte.get("nombre_conductor") or factura.get("cliente") or declaracion.get("asegurado") or "N/D"

    # Excel
    ex_placa = row.get("Placa Vehículo Asegurado") or row.get("Placa") or "N/D"
    ex_monto = row.get("Monto Reclamado ($)") or row.get("Monto Reclamado") or "N/D"
    ex_fecha = row.get("Fecha Ocurrencia") or "N/D"
    ex_persona = row.get("ID Asegurado") or "N/D"

    # Formatear montos con $ si son numéricos
    try:
        if ex_monto != "N/D": ex_monto = f"${float(str(ex_monto).replace(',','.')):,.2f}"
    except: pass
    try:
        if pdf_monto != "N/D": pdf_monto = f"${float(str(pdf_monto).replace(',','.')):,.2f}"
    except: pass

    # Crear una hermosa tabla comparativa
    comparison_data = [
        {
            "Campo": "🚗 Placa Vehículo",
            "Excel (Base de Datos)": str(ex_placa),
            "Documentos (PDF)": str(pdf_placa),
            "Estado": "🟩 Coincide" if str(ex_placa).strip().upper() == str(pdf_placa).strip().upper() and ex_placa != "N/D" else "⬜ No Cruzado" if pdf_placa == "N/D" else "🟥 Discrepancia"
        },
        {
            "Campo": "💰 Monto Reclamado",
            "Excel (Base de Datos)": str(ex_monto),
            "Documentos (PDF)": str(pdf_monto),
            "Estado": "🟩 Coincide" if str(ex_monto) in str(pdf_monto) and ex_monto != "N/D" else "⬜ No Cruzado" if pdf_monto == "N/D" else "🟥 Discrepancia"
        },
        {
            "Campo": "📅 Fecha del Evento",
            "Excel (Base de Datos)": str(ex_fecha),
            "Documentos (PDF)": str(pdf_fecha),
            "Estado": "🟩 Coincide" if str(ex_fecha) in str(pdf_fecha) and ex_fecha != "N/D" else "⬜ No Cruzado" if pdf_fecha == "N/D" else "🟥 Discrepancia"
        },
        {
            "Campo": "👤 Titular / Conductor",
            "Excel (Base de Datos)": str(ex_persona),
            "Documentos (PDF)": str(pdf_persona),
            "Estado": "🟩 Coincide" if (str(ex_persona).lower() in str(pdf_persona).lower() or str(pdf_persona).lower() in str(ex_persona).lower()) and ex_persona != "N/D" else "⬜ No Cruzado" if pdf_persona == "N/D" else "🟨 Requiere Revisión"
        }
    ]

    df_comp = pd.DataFrame(comparison_data)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"💡 **Origen de la alerta:** Hiciste clic en la validación de: **{campo_origen}** (Valor verificado: `{match_data.get('valor')}`)")
    
    if st.button("Cerrar", use_container_width=True):
        st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:10px 0">'
        '<span style="font-size:1.8rem;font-weight:900;color:#1B4F8A">🔍 FRAUDIA</span><br>'
        '<span style="font-size:.75rem;color:#5D6D7E">Detector Antifraude IA · hackIAthon 2026</span>'
        '</div>', unsafe_allow_html=True
    )
    st.divider()

    groq_key = st.text_input("🔑 Groq API Key", type="password",
                              value=os.getenv("GROQ_API_KEY", ""),
                              help="Gratis en console.groq.com")
    st.divider()
    import os
    dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dataset")
    os.makedirs(dataset_dir, exist_ok=True)
    excel_files = []
    if os.path.exists(dataset_dir):
        excel_files = [f for f in os.listdir(dataset_dir) if f.endswith((".xlsx", ".xls"))]
        
    # Mapeo de nombres descriptivos
    display_names = {
        "Evento Datasets_Sinteticos_Fraude_500_v2.xlsx": "📊 Dataset Principal (500 Siniestros)",
        "dataset_ficticio_prueba.xlsx": "🧪 Dataset Ficticio de Prueba (SIN-9999)"
    }
    
    if not excel_files:
        excel_files = [os.path.basename(DEFAULT_EXCEL)]
        
    options = [display_names.get(f, f"📁 {f}") for f in excel_files]
    
    st.markdown("**📂 Seleccionar Dataset Excel**")
    selected_display = st.selectbox(
        "Excel del Siniestro",
        options,
        index=0 if len(options) > 0 else 0,
        label_visibility="collapsed"
    )
    
    # Permitir agregar nueva fuente (Excel)
    with st.expander("📤 Subir nueva fuente (Excel)", expanded=False):
        uploaded_file = st.file_uploader(
            "Selecciona un archivo Excel",
            type=["xlsx", "xls"],
            key="sidebar_dataset_uploader",
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            new_file_path = os.path.join(dataset_dir, uploaded_file.name)
            try:
                # Guardar el archivo en el directorio de datasets
                with open(new_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"¡Dataset '{uploaded_file.name}' subido con éxito!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
    
    # Resolver ruta del archivo seleccionado
    reverse_map = {display_names.get(f, f"📁 {f}"): f for f in excel_files}
    selected_file = reverse_map.get(selected_display, selected_display)
    excel_path = os.path.join(dataset_dir, selected_file)
    
    docs_folder = DEFAULT_DOCS

    if st.button("🚀 Cargar Dataset", use_container_width=True, type="primary"):
        try:
            with st.status("Procesando dataset…", expanded=True) as status:
                st.write("📂 Leyendo Excel (5 hojas, 500 siniestros)…")
                sheets = load_excel(excel_path)

                st.write(f"📄 Escaneando carpetas de PDFs…")
                pdf_map = map_pdfs(docs_folder)
                st.write(f"   → {len(pdf_map)} siniestros con documentos vinculados")

                st.write("🎯 Calculando scores de riesgo + validación cruzada de PDFs…")
                scores = calculate_scores_batch(sheets, pdf_map)

                st.session_state.update(
                    sheets=sheets, pdf_map=pdf_map,
                    scores_df=scores, data_loaded=True,
                )
                rj = (scores.Nivel=="ROJO").sum()
                am = (scores.Nivel=="AMARILLO").sum()
                vr = (scores.Nivel=="VERDE").sum()
                st.write(f"✅ Listo: 🔴 {rj} · 🟡 {am} · 🟢 {vr}")
                status.update(label=f"✅ Dataset cargado — {len(sheets.get('1_Siniestros', []))} siniestros",
                              state="complete", expanded=False)
        except Exception as e:
            st.error(f"Error: {e}")

    # Auto-activación del Agente IA: si hay dataset, construir el RAG automáticamente
    # (funciona en modo retrieval-only sin API Key, o completo con Groq si hay key)
    if st.session_state.data_loaded and not st.session_state.rag_ready:
        try:
            # Verificar si existe caché en disco
            import os
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cache")
            has_cache = os.path.exists(cache_dir) and any(f.endswith(".faiss") for f in os.listdir(cache_dir)) if os.path.exists(cache_dir) else False

            label_inicial = "⚡ Cargando caché del RAG…" if has_cache else "🧠 Construyendo índice RAG (primera vez, ~30s)…"

            with st.status(label_inicial, expanded=True) as rag_status:
                from src.rag_engine import RAGEngine

                if has_cache:
                    st.write("⚡ Caché en disco detectado — carga instantánea")
                else:
                    st.write("📥 Descargando modelo de embeddings (1ra vez, ~470MB)…")
                    st.write("⏳ Esto solo pasa la primera vez. Después es instantáneo.")
                    st.write("📚 Indexando 500 siniestros + 25 reglas RF + 14 señales…")
                    st.write("🔢 Vectorizando con FAISS…")

                pdf_texts: dict = {}
                for sid, docs in st.session_state.pdf_map.items():
                    pdf_texts[sid] = {}
                    for dt, path in docs.items():
                        try: pdf_texts[sid][dt] = extract_text(path)
                        except: pass

                rag = RAGEngine(groq_key if groq_key else None)
                rag.build_index(st.session_state.sheets, pdf_texts, st.session_state.scores_df)
                st.session_state.rag = rag
                st.session_state.rag_ready = True
                mode_label = "modo completo (LLM)" if groq_key else "modo retrieval-only"
                st.write(f"✅ Listo — {mode_label}")
                rag_status.update(
                    label=f"✅ Agente IA activo ({mode_label})",
                    state="complete", expanded=False,
                )
                st.rerun()
        except Exception as e:
            st.error(f"Error activando RAG: {e}")

    # Si la clave API de Groq en la interfaz cambió con respecto al RAG cargado, actualizarlo
    if st.session_state.rag_ready and st.session_state.rag is not None:
        current_rag = st.session_state.rag
        if getattr(current_rag, "api_key", None) != (groq_key if groq_key else None):
            try:
                from src.rag_engine import RAGEngine
                new_rag = RAGEngine(groq_key if groq_key else None)
                # Reusar el índice ya construido para evitar demoras
                new_rag._encoder  = current_rag._encoder
                new_rag._index    = current_rag._index
                new_rag.chunks    = current_rag.chunks
                new_rag.metadata  = current_rag.metadata
                st.session_state.rag = new_rag
                st.success("🚀 Agente RAG actualizado dinámicamente con la nueva clave de Groq.")
            except Exception as e:
                st.error(f"Error actualizando el Agente RAG: {e}")

    st.divider()
    if st.session_state.data_loaded:
        df_s = st.session_state.scores_df
        st.markdown(
            f'<div class="kpi-box" style="margin-bottom:6px">'
            f'<span style="color:#E74C3C;font-size:1.3rem;font-weight:900">🔴 {(df_s.Nivel=="ROJO").sum()}</span>'
            f'&nbsp;&nbsp;<span style="color:#F39C12;font-size:1.3rem;font-weight:900">🟡 {(df_s.Nivel=="AMARILLO").sum()}</span>'
            f'&nbsp;&nbsp;<span style="color:#27AE60;font-size:1.3rem;font-weight:900">🟢 {(df_s.Nivel=="VERDE").sum()}</span>'
            f'</div>', unsafe_allow_html=True
        )
    if st.session_state.rag_ready:
        st.markdown('<div class="card-azul">🤖 Agente IA activo</div>', unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(
        '<h1 style="margin-bottom:0">🔍 FRAUDIA</h1>'
        '<p style="color:#5D6D7E;margin-top:0">Detector de Posibles Fraudes en Siniestros · '
        'Aseguradora del Sur · hackIAthon 2026</p>',
        unsafe_allow_html=True,
    )
with col_h2:
    st.markdown('<div style="padding-top:20px;text-align:right;color:#5D6D7E;font-size:.8rem">'
                'Los resultados son alertas de revisión.<br>No sustituyen el análisis humano.</div>',
                unsafe_allow_html=True)
st.divider()

TABS = st.tabs([
    "📘 Manual",
    "📊 Dashboard",
    "🔍 Siniestro",
    "📄 Cargar Documento",
    "🤖 Agente IA",
    "🧠 Modelo ML",
    "🕸️ Red Relacional",
    "⚖️ Ética y Limitaciones",
    "🏢 Proveedores",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0 — MANUAL DE USUARIO INTERACTIVO
# ═══════════════════════════════════════════════════════════════════════════════
with TABS[0]:
    # Banner de bienvenida
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1B4F8A,#2980B9);color:white;
                border-radius:14px;padding:24px 30px;margin-bottom:18px;
                box-shadow:0 4px 18px rgba(27,79,138,0.25)">
      <h2 style="color:white !important;margin:0;font-size:1.6rem">
        👋 Bienvenido a FRAUDIA — Detector de Posibles Fraudes
      </h2>
      <p style="margin:8px 0 0 0;font-size:1rem;opacity:.95">
        Este manual te enseñará cómo usar el sistema en menos de 5 minutos.
        Estás listo, así que vamos a empezar.
      </p>
    </div>
    """, unsafe_allow_html=True)

    man_tab1, man_tab2, man_tab3, man_tab4, man_tab5 = st.tabs([
        "🚀 Empezar en 3 pasos",
        "🗂️ Qué hace cada pantalla",
        "📤 Cómo subir archivos",
        "📖 Glosario",
        "❓ Preguntas frecuentes",
    ])

    # ── 1. EMPEZAR EN 3 PASOS ────────────────────────────────────────
    with man_tab1:
        st.markdown("### 🚀 Empezar en 3 pasos")
        st.markdown("Sigue estos 3 pasos en orden para tener el sistema listo:")
        st.markdown("")

        # Paso 1
        st.markdown("""
        <div style="background:#F8FBFF;border-left:5px solid #1B4F8A;border-radius:10px;
                    padding:18px 22px;margin:10px 0">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
            <div style="background:#1B4F8A;color:white;width:40px;height:40px;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.3rem">1</div>
            <h3 style="color:#1B4F8A !important;margin:0">Carga el dataset</h3>
          </div>
          <p style="margin:0;color:#1A3A5C">
            En el panel <b>lateral izquierdo</b> haz clic en el botón azul <b>🚀 Cargar Dataset</b>.<br>
            El sistema leerá automáticamente:
          </p>
          <ul style="margin:6px 0 0 0;color:#1A3A5C">
            <li>📊 El Excel con <b>500 siniestros</b> (5 hojas)</li>
            <li>📄 Los <b>24 PDFs</b> de Partes Policiales, Declaraciones y Facturas</li>
            <li>🎯 Calcula <b>scores de riesgo</b> con validación cruzada</li>
          </ul>
          <p style="margin:8px 0 0 0;color:#5D6D7E;font-size:.85rem">
            ⏱️ Tarda unos <b>10–12 segundos</b> la primera vez.
          </p>
        </div>
        """, unsafe_allow_html=True)

        # Paso 2
        st.markdown("""
        <div style="background:#F8FBFF;border-left:5px solid #1B4F8A;border-radius:10px;
                    padding:18px 22px;margin:10px 0">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
            <div style="background:#1B4F8A;color:white;width:40px;height:40px;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.3rem">2</div>
            <h3 style="color:#1B4F8A !important;margin:0">Activa el Agente IA <span style="font-size:.7rem;color:#5D6D7E">(opcional)</span></h3>
          </div>
          <p style="margin:0;color:#1A3A5C">
            Si quieres hacer <b>preguntas en lenguaje natural</b> al sistema:
          </p>
          <ol style="margin:6px 0 0 0;color:#1A3A5C">
            <li>Ve a <a href="https://console.groq.com" target="_blank">console.groq.com</a> y crea una cuenta gratis</li>
            <li>Copia tu API Key</li>
            <li>Pégala en el campo <b>🔑 Groq API Key</b> del panel lateral</li>
            <li>Haz clic en <b>🧠 Activar Agente IA</b></li>
          </ol>
          <p style="margin:8px 0 0 0;color:#5D6D7E;font-size:.85rem">
            ⏱️ Tarda unos <b>30–60 segundos</b> mientras construye el índice vectorial.
          </p>
        </div>
        """, unsafe_allow_html=True)

        # Paso 3
        st.markdown("""
        <div style="background:#F8FBFF;border-left:5px solid #1B4F8A;border-radius:10px;
                    padding:18px 22px;margin:10px 0">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
            <div style="background:#1B4F8A;color:white;width:40px;height:40px;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.3rem">3</div>
            <h3 style="color:#1B4F8A !important;margin:0">Explora las pantallas</h3>
          </div>
          <p style="margin:0;color:#1A3A5C">
            Navega por las pestañas de arriba. Te recomendamos este orden:
          </p>
          <ol style="margin:6px 0 0 0;color:#1A3A5C">
            <li><b>📊 Dashboard</b> — vista general de los 500 siniestros</li>
            <li><b>🔍 Siniestro</b> — analiza un caso específico (prueba con <code>SIN-0005</code>)</li>
            <li><b>🤖 Agente IA</b> — haz preguntas</li>
            <li><b>📄 Cargar Documento</b> — sube un PDF nuevo para validar</li>
          </ol>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🎯 ¿Listo? Recomendación")
        st.info("**Empieza por la pestaña 📊 Dashboard.** Es el panel general y desde ahí entiendes el contexto antes de meterte en los detalles.")

    # ── 2. QUÉ HACE CADA PANTALLA ────────────────────────────────────
    with man_tab2:
        st.markdown("### 🗂️ Qué hace cada pantalla")
        st.markdown("Cada pestaña tiene un propósito específico. Esta es la guía completa:")
        st.markdown("")

        pantallas = [
            ("📊", "Dashboard",
             "Vista general del riesgo de toda la cartera de siniestros.",
             [
                "**KPIs** — total de siniestros, conteo por nivel (🔴🟡🟢)",
                "**Simulación de Ahorro** — cuánto dinero se ahorraría revisando los casos críticos",
                "**Tabla filtrable** — busca por ramo, sucursal, ID o nivel de riesgo",
                "**Mapa de Ecuador** — geolocalización de alertas por ciudad",
                "**Ranking de ciudades** — top de ciudades por nivel de riesgo",
                "**Exportar CSV/PDF** — descarga reportes para auditoría",
             ],
             "💡 Tip: usa los filtros para enfocarte en un ramo específico (ej: solo Vehículos)."),

            ("🔍", "Siniestro",
             "Análisis profundo de un siniestro individual.",
             [
                "**Score detallado** con barra de progreso y desglose por señal",
                "**Datos completos** del siniestro, asegurado y póliza",
                "**Documentos PDF asociados** — texto extraído visible",
                "**Validación cruzada** — coincidencias y discrepancias entre PDFs y Excel",
                "**Reglas críticas activadas** (RF-01 a RF-07)",
                "**Acción recomendada** según el nivel de riesgo",
             ],
             "💡 Tip: prueba con SIN-0005 — verás las 5 inconsistencias detectadas (nombre diferente, RUC inválido, etc.)."),

            ("📄", "Cargar Documento",
             "Sube un PDF o Excel nuevo para validarlo contra el dataset.",
             [
                "**PDF**: el sistema detecta el tipo (Parte Policial, Declaración o Factura)",
                "Extrae automáticamente los campos: placas, fechas, nombres, montos",
                "Cruza contra el dataset y muestra coincidencias e inconsistencias",
                "Recalcula el score en tiempo real con la nueva información",
                "**Excel**: valida la estructura de las 5 hojas requeridas",
             ],
             "💡 Tip: esta es la pantalla para la demo en vivo — el jurado puede subir un PDF y ver la magia."),

            ("🤖", "Agente IA",
             "Chat conversacional con RAG (Retrieval Augmented Generation).",
             [
                "Responde preguntas en lenguaje natural usando los datos reales",
                "**12 preguntas pre-cargadas** del reto como botones rápidos",
                "Usa **RAG** con sentence-transformers + FAISS para recuperar contexto",
                "Genera la respuesta con Groq llama-3.1-8b-instant en **streaming (<3s)**",
                "Cita IDs de siniestros específicos en sus respuestas",
                "Mantiene el historial del chat",
             ],
             "💡 Tip: empieza con la pregunta '¿Cuáles son los 10 siniestros con mayor riesgo?'"),

            ("🧠", "Modelo ML",
             "Tres modelos de Machine Learning con vistas comparativas.",
             [
                "**🌲 Random Forest Supervisado** — predicción con validación cruzada 5-fold",
                "Métricas: AUC, F1, Precisión, Recall, Matriz de Confusión",
                "**🔮 Isolation Forest** — detección de anomalías no supervisada",
                "**🕸️ Narrativas Clonadas** — agrupa siniestros con descripciones idénticas (posibles anillos de fraude)",
                "**Score Combinado** = 50% Reglas + 25% IF + 25% RF",
             ],
             "💡 Tip: en Narrativas Clonadas, ajusta el umbral de similitud para ver más o menos grupos."),

            ("🕸️", "Red Relacional",
             "Grafo interactivo de relaciones entre Asegurados ↔ Siniestros ↔ Proveedores.",
             [
                "Cada nodo es un asegurado, siniestro o proveedor",
                "Las aristas conectan entidades relacionadas",
                "Los nodos se colorean por nivel de riesgo",
                "Filtra por nivel para enfocarte solo en casos críticos",
             ],
             "💡 Tip: busca clusters densos — pueden indicar redes de fraude coordinado."),

            ("⚖️", "Ética y Limitaciones",
             "Declaración de uso responsable y análisis de sesgo.",
             [
                "Qué está permitido y qué NO está permitido hacer con el sistema",
                "**Limitaciones del modelo**: falsos positivos, datos sintéticos, etc.",
                "**Análisis de sesgo** por ramo y por sucursal",
                "**Flujo de revisión humana** obligatorio",
             ],
             "💡 Tip: muestra esta pantalla al jurado — es lo que diferencia un sistema ético de uno no ético."),

            ("🏢", "Proveedores",
             "Ranking de proveedores por concentración de alertas.",
             [
                "Identifica talleres y clínicas con más siniestros sospechosos",
                "Marca proveedores en lista restrictiva",
                "Filtra por tipo: Taller, Clínica, Perito",
                "Exporta el ranking a CSV",
             ],
             "💡 Tip: un proveedor con muchas alertas rojas es un foco de investigación prioritario."),
        ]

        for icon, title, subtitle, features, tip in pantallas:
            with st.expander(f"{icon}  **{title}** — {subtitle}", expanded=False):
                for f in features:
                    st.markdown(f"• {f}")
                st.markdown("")
                st.info(tip)

    # ── 3. CÓMO SUBIR ARCHIVOS ──────────────────────────────────────
    with man_tab3:
        st.markdown("### 📤 Cómo subir archivos al sistema")
        st.markdown("Hay **dos lugares** donde puedes cargar información:")
        st.markdown("")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("""
            <div style="background:#EBF5FB;border:2px solid #2980B9;border-radius:12px;
                        padding:18px 22px;height:100%">
              <h4 style="color:#1B4F8A !important;margin:0 0 10px 0">🏠 1. Sidebar — Cargar Dataset</h4>
              <p style="color:#1A3A5C;margin:0">Para cambiar el <b>dataset completo</b> que usa toda la app.</p>
              <p style="color:#1A3A5C;margin:8px 0 0 0"><b>Cuándo usar:</b></p>
              <ul style="color:#1A3A5C;margin:4px 0 0 0">
                <li>Quieres usar un Excel diferente</li>
                <li>Tienes una carpeta nueva de PDFs</li>
              </ul>
              <p style="color:#1A3A5C;margin:12px 0 4px 0"><b>Cómo:</b></p>
              <ol style="color:#1A3A5C;margin:0">
                <li>En el sidebar edita las rutas</li>
                <li>Clic en <b>🚀 Cargar Dataset</b></li>
              </ol>
            </div>
            """, unsafe_allow_html=True)

        with col_b:
            st.markdown("""
            <div style="background:#F0FDF4;border:2px solid #27AE60;border-radius:12px;
                        padding:18px 22px;height:100%">
              <h4 style="color:#1B4F8A !important;margin:0 0 10px 0">📄 2. Tab Cargar Documento</h4>
              <p style="color:#1A3A5C;margin:0">Para subir <b>un solo archivo</b> y validarlo contra el dataset.</p>
              <p style="color:#1A3A5C;margin:8px 0 0 0"><b>Cuándo usar:</b></p>
              <ul style="color:#1A3A5C;margin:4px 0 0 0">
                <li>Llega un PDF nuevo de un siniestro</li>
                <li>El jurado quiere probar la validación</li>
                <li>Quieres ver inconsistencias en tiempo real</li>
              </ul>
              <p style="color:#1A3A5C;margin:12px 0 4px 0"><b>Cómo:</b></p>
              <ol style="color:#1A3A5C;margin:0">
                <li>Ve al tab <b>📄 Cargar Documento</b></li>
                <li>Elige tipo: PDF o Excel</li>
                <li>Arrastra el archivo o haz clic para buscar</li>
              </ol>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📑 Tipos de archivos soportados")

        st.markdown("""
        <table style="width:100%;border-collapse:collapse">
          <tr style="background:#1B4F8A;color:white">
            <th style="padding:10px;text-align:left">Tipo</th>
            <th style="padding:10px;text-align:left">Formato</th>
            <th style="padding:10px;text-align:left">Qué detecta el sistema</th>
          </tr>
          <tr style="background:#F8FBFF;color:#1A3A5C">
            <td style="padding:10px"><b>📋 Parte Policial</b></td>
            <td style="padding:10px"><code>PP_SIN-XXXX_DOC-YYYY.pdf</code></td>
            <td style="padding:10px">Placa, marca, modelo, fecha hecho, fecha elaboración, hora, conductor, observaciones</td>
          </tr>
          <tr style="background:white;color:#1A3A5C">
            <td style="padding:10px"><b>📝 Declaración Accidente</b></td>
            <td style="padding:10px"><code>DA_SIN-XXXX_DOC-YYYY.pdf</code></td>
            <td style="padding:10px">Asegurado, póliza, descripción, datos del tercero, intervención policial</td>
          </tr>
          <tr style="background:#F8FBFF;color:#1A3A5C">
            <td style="padding:10px"><b>🧾 Factura</b></td>
            <td style="padding:10px"><code>Muestras_Facturas_Siniestros-SIN-XXXX.pdf</code></td>
            <td style="padding:10px">Cliente, placa, RUC del taller, fecha factura, descripción servicio, monto total</td>
          </tr>
          <tr style="background:white;color:#1A3A5C">
            <td style="padding:10px"><b>📊 Excel del Dataset</b></td>
            <td style="padding:10px"><code>.xlsx</code> con 5 hojas</td>
            <td style="padding:10px">1_Siniestros, 2_Pólizas, 3_Asegurados, 4_Proveedores, 5_Documentos</td>
          </tr>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.success("✨ **El sistema detecta automáticamente el tipo de PDF** leyendo su contenido — no necesitas decirle qué es.")

    # ── 4. GLOSARIO ──────────────────────────────────────────────────
    with man_tab4:
        st.markdown("### 📖 Glosario de términos")
        st.markdown("Si nunca has trabajado en seguros, este glosario te ayudará a entender el sistema:")
        st.markdown("")

        terminos = [
            ("🚦 Score / Semáforo",
             "Calificación de 0 a 100 del riesgo de fraude. Se traduce en colores:",
             [("🟢 VERDE", "0–40 puntos", "Bajo riesgo — continuar flujo normal"),
              ("🟡 AMARILLO", "41–75 puntos", "Riesgo medio — revisión documental"),
              ("🔴 ROJO", "76–100 puntos", "Riesgo alto — escalar a Unidad Antifraude")]),

            ("⚡ Reglas RF-01 a RF-07",
             "Las 7 reglas críticas del reto de la Aseguradora del Sur:",
             [("RF-01", "Cobertura Pérdida Total por Robo", "→ Rojo"),
              ("RF-02", "Evidencia de Adulteración Documental", "→ Rojo"),
              ("RF-03", "Proveedor en Lista Restrictiva", "→ Rojo"),
              ("RF-04", "Dinámica del Accidente Físicamente Imposible", "→ Rojo"),
              ("RF-05", "Siniestro Extremo al Borde de Vigencia (<48h)", "→ Amarillo"),
              ("RF-06", "Demora Atípica en Denuncia de Robo (>4 días)", "→ Amarillo"),
              ("RF-07", "Narrativa Idéntica (Clonada)", "→ Amarillo")]),

            ("🤖 RAG (Retrieval Augmented Generation)",
             "Es la técnica que usa el Agente IA. Funciona así:",
             [("1️⃣", "Chunking", "El sistema divide el dataset en fragmentos pequeños"),
              ("2️⃣", "Embeddings", "Convierte cada fragmento en un vector numérico"),
              ("3️⃣", "Retrieval", "Cuando preguntas algo, busca los fragmentos más relevantes"),
              ("4️⃣", "Generation", "Le pasa esos fragmentos a Groq + Llama 3.1 para que responda")]),

            ("🧠 Modelos de IA usados",
             "FRAUDIA combina 3 enfoques de Machine Learning:",
             [("📐 Reglas", "Lógica de negocio", "Implementa las 7 reglas críticas del reto"),
              ("🌲 Random Forest", "Aprendizaje supervisado", "Aprende a predecir fraude usando etiquetas"),
              ("🔮 Isolation Forest", "Detección de anomalías", "Encuentra casos estadísticamente raros sin etiquetas"),
              ("💬 NLP (TF-IDF)", "Análisis de texto", "Detecta descripciones similares entre siniestros")]),

            ("📊 Términos del Excel",
             "Las columnas más importantes del dataset:",
             [("ID Siniestro", "SIN-XXXX", "Identificador único del caso"),
              ("Cobertura", "Robo, Choque, …", "Tipo de evento reportado"),
              ("Monto Reclamado", "$ USD", "Lo que pide el asegurado"),
              ("Suma Asegurada", "$ USD", "El máximo que cubre la póliza"),
              ("Días Ocurr→Reporte", "número", "Cuántos días pasaron entre el evento y el aviso"),
              ("Prov. Lista Restrictiva", "Sí/No", "Si el proveedor está vetado"),
              ("Similitud Narrativa Máx.", "0.00–1.00", "Qué tan parecida es la descripción a otra")]),
        ]

        for header, desc, items in terminos:
            with st.expander(header, expanded=False):
                st.markdown(desc)
                st.markdown("")
                for left, mid, right in items:
                    st.markdown(
                        f'<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr;'
                        f'gap:10px;padding:6px 10px;margin:3px 0;background:#F8FBFF;'
                        f'border-left:3px solid #2980B9;border-radius:4px">'
                        f'<div style="font-weight:700;color:#1B4F8A">{left}</div>'
                        f'<div style="color:#1A3A5C"><i>{mid}</i></div>'
                        f'<div style="color:#5D6D7E">{right}</div></div>',
                        unsafe_allow_html=True,
                    )

    # ── 5. FAQ ───────────────────────────────────────────────────────
    with man_tab5:
        st.markdown("### ❓ Preguntas frecuentes")
        st.markdown("")

        faqs = [
            ("¿FRAUDIA acusa a un asegurado de fraude?",
             "**No.** FRAUDIA solo genera *alertas de revisión*. La decisión final de aprobar, rechazar o investigar un siniestro es siempre del **analista humano**. El sistema es una herramienta de apoyo, no un decisor."),

            ("¿Por qué hay 168 casos rojos? Me parecen muchos.",
             "Es correcto. El dataset tiene **77 siniestros de Robo** y **52 de Pérdida Total** que automáticamente clasifican como ROJO por la regla **RF-01** del reto. Esto NO significa que los 168 sean fraude, sino que requieren revisión prioritaria de la Unidad Antifraude."),

            ("¿Cuánto tarda la primera carga del dataset?",
             "Entre **10 y 12 segundos**. El sistema:\n- Lee el Excel con 500 siniestros (3 s)\n- Escanea las carpetas de PDFs (instante)\n- Lee y procesa los 24 PDFs (7 s)\n- Calcula scores con validación cruzada\n\nLas cargas posteriores son casi instantáneas gracias al caché."),

            ("¿Necesito la API Key de Groq para todo?",
             "**No.** Solo el tab **🤖 Agente IA** requiere la API Key. Todas las demás pantallas (Dashboard, Siniestro, Cargar Documento, Modelo ML, etc.) funcionan sin ella."),

            ("¿Qué tan confiable es el score de fraude?",
             "El score combina 3 fuentes:\n- **Reglas de negocio**: 50% — alta confiabilidad (basadas en el PDF del reto)\n- **Random Forest**: 25% — AUC ~0.62 con datos sintéticos (mejorable con datos reales)\n- **Isolation Forest**: 25% — detecta casos raros sin etiquetas\n\nLa tasa estimada de falsos positivos es **15–20%**, por eso siempre se requiere revisión humana."),

            ("¿Puedo subir mi propio Excel?",
             "**Sí.** Ve al tab **📄 Cargar Documento → 📊 Excel**. El sistema validará que tenga las 5 hojas requeridas con las columnas correctas y te mostrará si falta algo."),

            ("¿Cómo funciona la validación cruzada de PDFs?",
             "Cuando un siniestro tiene PDFs asociados (parte policial + declaración + factura), FRAUDIA:\n1. Extrae los campos clave de cada PDF\n2. Los compara entre sí y contra el Excel\n3. Detecta inconsistencias como: nombres diferentes, fechas incoherentes, RUC inválido, lógica imposible (ej: robo + factura de reparación)\n\nCada inconsistencia suma puntos al score de riesgo."),

            ("¿Por qué algunas ciudades no aparecen en el mapa?",
             "El mapa solo muestra las ciudades de Ecuador que tienen siniestros en el dataset cargado. Si filtras por nivel ROJO/AMARILLO/VERDE, solo se ven las ciudades que tienen casos de ese nivel."),

            ("¿Puedo exportar reportes?",
             "**Sí.** En el Dashboard tienes 2 botones:\n- **📥 Exportar CSV** — los casos filtrados\n- **📄 Generar Reporte PDF Ejecutivo** — documento profesional con membrete, top 10 críticos, distribución por ramo y sección de ética para firmas"),

            ("¿Los datos son reales?",
             "**No.** Son 100% sintéticos. El reto exige no usar datos personales reales por seguridad y privacidad. En un despliegue real, el sistema se entrenaría con datos históricos anonimizados de la aseguradora."),
        ]

        for q, a in faqs:
            with st.expander(f"❓ **{q}**", expanded=False):
                st.markdown(a)

        st.markdown("---")
        st.markdown("""
        <div style="background:#1B4F8A;color:white;border-radius:12px;padding:18px 24px;margin-top:14px">
          <h4 style="color:white !important;margin:0 0 6px 0">💬 ¿Tienes otra pregunta?</h4>
          <p style="margin:0;opacity:.95">Ve al tab <b>🤖 Agente IA</b> y pregúntale directamente al sistema.
          Por ejemplo: <i>"¿Qué siniestros tienen documentos alterados?"</i> o <i>"¿Por qué SIN-0005 es alto riesgo?"</i></p>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
with TABS[1]:
    if not st.session_state.data_loaded:
        st.info("👈 Carga el dataset desde el panel lateral para comenzar.")
        st.stop()

    df   = st.session_state.scores_df
    shet = st.session_state.sheets
    sin_df = shet.get("1_Siniestros", pd.DataFrame())

    # ── KPIs principales ──────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    monto_col = [c for c in sin_df.columns if "monto reclamado" in c.lower()]
    total_monto = pd.to_numeric(sin_df[monto_col[0]], errors="coerce").sum() if monto_col else 0
    rojo_monto  = df[df.Nivel=="ROJO"]["Monto Reclamado"].sum() if "Monto Reclamado" in df.columns else 0

    for col, val, lbl, color in [
        (k1, len(df), "Total Siniestros", "#1B4F8A"),
        (k2, (df.Nivel=="ROJO").sum(),    "🔴 Críticos",    "#E74C3C"),
        (k3, (df.Nivel=="AMARILLO").sum(),"🟡 Medios",      "#F39C12"),
        (k4, (df.Nivel=="VERDE").sum(),   "🟢 Bajos",       "#27AE60"),
        (k5, int(df.Score.mean()),        "Score Promedio", "#2980B9"),
    ]:
        col.markdown(
            f'<div class="kpi-box"><div class="kpi-val" style="color:{color}">{val}</div>'
            f'<div class="kpi-lbl">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Ahorro Potencial ──────────────────────────────────────────────
    st.markdown("")
    st.markdown("### 💰 Simulación de Ahorro Potencial")
    a1, a2, a3, a4 = st.columns(4)
    monto_riesgo = df[df.Nivel.isin(["ROJO","AMARILLO"])]["Monto Reclamado"].sum() if "Monto Reclamado" in df.columns else 0
    ahorro_20 = monto_riesgo * 0.20
    pct_riesgo = (monto_riesgo / total_monto * 100) if total_monto > 0 else 0

    for col, val, lbl, color in [
        (a1, f"${total_monto:,.0f}",  "Total reclamado",          "#1B4F8A"),
        (a2, f"${monto_riesgo:,.0f}", "Monto en riesgo (🔴+🟡)",  "#E74C3C"),
        (a3, f"{pct_riesgo:.1f}%",    "% cartera en riesgo",      "#F39C12"),
        (a4, f"${ahorro_20:,.0f}",    "Ahorro est. 20% recuperado","#27AE60"),
    ]:
        col.markdown(
            f'<div class="kpi-box"><div class="kpi-val" style="color:{color};font-size:1.5rem">{val}</div>'
            f'<div class="kpi-lbl">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Filtros + tabla ───────────────────────────────────────────────
    fa, fb, fc, fd = st.columns(4)
    ramo_opts  = ["Todos"] + sorted(df.Ramo.dropna().unique().tolist())
    nivel_opts = ["Todos", "ROJO", "AMARILLO", "VERDE"]
    suc_opts   = ["Todas"] + sorted(df.Sucursal.dropna().unique().tolist())

    r_sel = fa.selectbox("Ramo", ramo_opts, key="d_ramo")
    n_sel = fb.selectbox("Nivel riesgo", nivel_opts, key="d_nivel")
    s_sel = fc.selectbox("Sucursal", suc_opts, key="d_suc")
    q_sel = fd.text_input("Buscar SIN-XXXX", key="d_q")

    filt = df.copy()
    if r_sel != "Todos":   filt = filt[filt.Ramo == r_sel]
    if n_sel != "Todos":   filt = filt[filt.Nivel == n_sel]
    if s_sel != "Todas":   filt = filt[filt.Sucursal == s_sel]
    if q_sel:              filt = filt[filt["ID Siniestro"].str.contains(q_sel, case=False)]

    filt = filt.sort_values("Score", ascending=False)
    disp = filt[["ID Siniestro","Ramo","Cobertura","Score","Nivel","Monto Reclamado","Sucursal","Alertas"]].copy()
    disp["Nivel"] = disp["Nivel"].map({"ROJO":"🔴 ROJO","AMARILLO":"🟡 AMARILLO","VERDE":"🟢 VERDE"})
    disp["Monto Reclamado"] = disp["Monto Reclamado"].apply(lambda x: f"${x:,.0f}")

    st.markdown(f"**{len(filt)} siniestros** encontrados")
    st.dataframe(disp.reset_index(drop=True), use_container_width=True, height=320)

    # ── Botones exportar ──────────────────────────────────────────────
    exp_c1, exp_c2 = st.columns([2, 3])
    csv_buf = filt.to_csv(index=False).encode("utf-8")
    exp_c1.download_button(
        "📥 Exportar CSV", data=csv_buf,
        file_name="fraudia_alertas.csv", mime="text/csv",
    )
    if exp_c2.button("📄 Generar Reporte PDF Ejecutivo"):
        with st.spinner("Generando PDF…"):
            try:
                from src.report_generator import generate_pdf_report
                pdf_bytes = generate_pdf_report(
                    st.session_state.scores_df,
                    st.session_state.sheets,
                    st.session_state.combined_df,
                )
                st.download_button(
                    "⬇️ Descargar Reporte PDF",
                    data=pdf_bytes,
                    file_name=f"FRAUDIA_Reporte_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"Error generando PDF: {e}")

    st.divider()

    # ── Gráficos ──────────────────────────────────────────────────────
    g1, g2 = st.columns(2)
    with g1:
        nivel_c = df.Nivel.value_counts().reset_index()
        nivel_c.columns = ["Nivel","Cantidad"]
        fig_pie = px.pie(
            nivel_c, names="Nivel", values="Cantidad",
            color="Nivel",
            color_discrete_map={"ROJO":"#E74C3C","AMARILLO":"#F39C12","VERDE":"#27AE60"},
            title="Distribución de Riesgo",
            hole=0.4,
        )
        fig_pie.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                              font=dict(color="#1B4F8A"), title_font_color="#1B4F8A")
        st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        ramo_risk = df.groupby("Ramo")["Score"].mean().sort_values(ascending=False).reset_index()
        fig_bar = px.bar(
            ramo_risk, x="Ramo", y="Score",
            title="Score Promedio por Ramo",
            color="Score",
            color_continuous_scale=["#27AE60","#F39C12","#E74C3C"],
        )
        fig_bar.update_layout(paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                              font=dict(color="#1B4F8A"), title_font_color="#1B4F8A",
                              coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Mapa Ecuador ─────────────────────────────────────────────────
    st.markdown("### 🗺️ Mapa de Alertas por Ciudad — Ecuador")
    try:
        from src.anomaly_model import build_ecuador_map, get_city_ranking

        # Filtro del mapa
        mf1, mf2 = st.columns([1, 4])
        map_filter = mf1.selectbox(
            "Filtrar mapa por nivel",
            ["Todos", "🔴 ROJO", "🟡 AMARILLO", "🟢 VERDE"],
            key="map_filter",
        )
        # Extraer el nivel limpio
        filter_clean = {
            "Todos":        "Todos",
            "🔴 ROJO":      "ROJO",
            "🟡 AMARILLO":  "AMARILLO",
            "🟢 VERDE":     "VERDE",
        }[map_filter]
        mf2.markdown(
            '<div style="padding-top:30px;color:#5D6D7E;font-size:.85rem">'
            'Las ciudades se clasifican por su <b>nivel predominante</b> '
            '(el nivel con mayor cantidad de siniestros en esa ciudad).'
            '</div>', unsafe_allow_html=True,
        )

        fig_map = build_ecuador_map(df, sin_df, filter_nivel=filter_clean)
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        st.info(f"Mapa no disponible: {e}")

    # ── Ranking ciudades por nivel (con filtros) ─────────────────────
    st.markdown("### 🏙️ Ranking de Ciudades por Nivel de Riesgo")
    try:
        ranking = get_city_ranking(df, sin_df)
        if not ranking.empty:
            # Filtros
            fc1, fc2, fc3 = st.columns([1, 1, 2])
            nivel_pick = fc1.selectbox(
                "Nivel de riesgo",
                ["🔴 ROJO", "🟡 AMARILLO", "🟢 VERDE"],
                key="city_nivel",
            )
            top_n = fc2.selectbox(
                "Cantidad",
                ["Top 5", "Top 10", "Top 15", "Todas"],
                index=1,
                key="city_topn",
            )
            ciudades_all = ["Todas"] + sorted(ranking["Ciudad"].tolist())
            ciudad_pick = fc3.selectbox("Filtrar por ciudad", ciudades_all, key="city_pick")

            # Determinar columnas y orden según el nivel
            nivel_map_cfg = {
                "🔴 ROJO":     ("Rojos",      "Pct_Rojo",      "#E74C3C", "#FEF5F5", "#FADBD8"),
                "🟡 AMARILLO": ("Amarillos",  "Pct_Amarillo",  "#F39C12", "#FEFAF0", "#FDEBD0"),
                "🟢 VERDE":    ("Verdes",     "Pct_Verde",     "#27AE60", "#F0FDF4", "#D4EFDF"),
            }
            col_count, col_pct, color, bg_color, border_color = nivel_map_cfg[nivel_pick]

            n_map = {"Top 5": 5, "Top 10": 10, "Top 15": 15, "Todas": len(ranking)}
            n = n_map[top_n]

            # Filtrar y ordenar
            ranking_f = ranking.copy()
            if ciudad_pick != "Todas":
                ranking_f = ranking_f[ranking_f["Ciudad"] == ciudad_pick]
            ranking_f = ranking_f.sort_values(
                [col_pct, col_count], ascending=[False, False]
            ).head(n)

            # Banner del nivel
            st.markdown(
                f'<div style="background:{bg_color};border-left:5px solid {color};'
                f'padding:14px 18px;border-radius:8px;margin:10px 0">'
                f'<b style="color:{color};font-size:1.15rem">'
                f'{nivel_pick} — {top_n if ciudad_pick=="Todas" else ciudad_pick}'
                f'</b>'
                f'<span style="color:#5D6D7E;margin-left:14px">'
                f'{len(ranking_f)} ciudades mostradas</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if ranking_f.empty:
                st.info("No hay datos para esa combinación.")
            else:
                # Dos columnas: lista visual + gráfico
                lst_col, chart_col = st.columns([1, 1])

                with lst_col:
                    for _, row in ranking_f.iterrows():
                        casos = int(row[col_count])
                        pct   = row[col_pct]
                        total = int(row["Total"])
                        bar_w = min(int(pct), 100)
                        st.markdown(
                            f'<div style="background:white;border:1px solid {border_color};'
                            f'border-radius:8px;padding:10px 14px;margin:6px 0">'
                            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">'
                            f'<span style="color:#1A3A5C;font-weight:700;font-size:1rem">{row["Ciudad"]}</span>'
                            f'<span style="color:{color};font-weight:800">{casos} casos ({pct}%)</span>'
                            f'</div>'
                            f'<div style="background:#EAEDED;height:7px;border-radius:4px;overflow:hidden">'
                            f'<div style="background:{color};width:{bar_w}%;height:7px;border-radius:4px"></div>'
                            f'</div>'
                            f'<small style="color:#5D6D7E">Total siniestros: {total} · Score promedio: {row["Score_Prom"]}</small>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                with chart_col:
                    fig_rank = px.bar(
                        ranking_f.sort_values(col_count, ascending=True),
                        x=col_count, y="Ciudad", orientation="h",
                        title=f"Casos {nivel_pick.split()[1]} por Ciudad",
                        color=col_count,
                        color_continuous_scale=["#AED6F1", color],
                        text=col_count,
                    )
                    fig_rank.update_traces(textposition="outside")
                    fig_rank.update_layout(
                        paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                        font=dict(color="#1B4F8A"), title_font_color="#1B4F8A",
                        coloraxis_showscale=False,
                        xaxis_title=f"Cantidad de casos {nivel_pick.split()[1]}",
                        yaxis_title="",
                        height=max(300, 38 * len(ranking_f)),
                    )
                    st.plotly_chart(fig_rank, use_container_width=True)

            with st.expander("📋 Ver ranking completo de ciudades"):
                rank_full = ranking.sort_values("Total", ascending=False)[
                    ["Ciudad","Total","Rojos","Amarillos","Verdes",
                     "Pct_Rojo","Pct_Amarillo","Pct_Verde","Score_Prom","Nivel_Predominante"]
                ].reset_index(drop=True)
                rank_full.columns = ["Ciudad","Total","🔴","🟡","🟢",
                                     "% Rojo","% Amarillo","% Verde","Score Prom","Nivel Predominante"]
                st.dataframe(rank_full, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Ranking no disponible: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SINIESTRO INDIVIDUAL
# ═══════════════════════════════════════════════════════════════════════════════
with TABS[2]:
    if not st.session_state.data_loaded:
        st.info("Carga el dataset primero.")
        st.stop()

    shet      = st.session_state.sheets
    scores_df = st.session_state.scores_df
    pdf_map   = st.session_state.pdf_map

    sin_list = sorted(scores_df["ID Siniestro"].tolist())
    sin_sel  = st.selectbox("Seleccionar Siniestro", sin_list, key="sin_sel")

    sin_df2  = shet["1_Siniestros"]
    sin_row  = sin_df2[sin_df2["ID Siniestro"] == sin_sel].iloc[0].to_dict()
    sc_row   = scores_df[scores_df["ID Siniestro"] == sin_sel].iloc[0].to_dict()
    result   = score_siniestro(sin_row)

    nivel = result["nivel"]
    score = sc_row.get("Score", result["score"])
    em    = {"ROJO":"🔴","AMARILLO":"🟡","VERDE":"🟢"}[nivel]
    color_nivel = {"ROJO":"#E74C3C","AMARILLO":"#F39C12","VERDE":"#27AE60"}[nivel]
    fill_cls    = {"ROJO":"score-fill-rojo","AMARILLO":"score-fill-amar","VERDE":"score-fill-verde"}[nivel]

    st.markdown(
        f'<div style="background:{color_nivel}18;border:2px solid {color_nivel};'
        f'border-radius:12px;padding:14px 20px;margin-bottom:12px">'
        f'<span style="font-size:1.5rem;font-weight:900;color:{color_nivel}">'
        f'{em} {sin_sel} — Score {score}/100 — {nivel}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="score-track"><div class="{fill_cls}" style="width:{score}%"></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 📋 Datos del Siniestro")
        fields_s = {
            "Ramo": sin_row.get("Ramo"), "Cobertura": sin_row.get("Cobertura"),
            "Placa": sin_row.get("Placa Vehículo Asegurado"),
            "Fecha Ocurrencia": sin_row.get("Fecha Ocurrencia"),
            "Fecha Reporte": sin_row.get("Fecha Reporte"),
            "Monto Reclamado": f"${sin_row.get('Monto Reclamado ($)','')}",
            "Monto Estimado":  f"${sin_row.get('Monto Estimado ($)','')}",
            "Estado": sin_row.get("Estado"), "Sucursal": sin_row.get("Sucursal"),
            "Días inicio póliza": sin_row.get("Días desde Inicio Póliza"),
            "Días fin póliza": sin_row.get("Días hasta Fin Póliza"),
            "Reclamos previos": sin_row.get("N° Reclamos Previos Asegurado"),
            "Docs Completos": sin_row.get("Docs Completos"),
        }
        for k, v in fields_s.items():
            st.markdown(f"**{k}:** {v}")
        st.info(f"📝 {sin_row.get('Descripción del Evento','—')}")

        aseg_id = sin_row.get("ID Asegurado","")
        aseg_df = shet.get("3_Asegurados", pd.DataFrame())
        if not aseg_df.empty and aseg_id:
            ar = aseg_df[aseg_df["ID Asegurado"]==aseg_id]
            if not ar.empty:
                ar = ar.iloc[0]
                st.markdown("#### 👤 Asegurado")
                st.markdown(f"**{ar.get('Nombres Asegurado','')}** · {ar.get('Ciudad','')} · {ar.get('Antigüedad (años)','')} años")
                st.markdown(f"Reclamos 12m: **{ar.get('N° Reclamos Últimos 12 Meses','')}** | Histórico: **{ar.get('N° Reclamos Histórico Total','')}** | Perfil: **{ar.get('Perfil Riesgo Histórico','')}**")

    with col_b:
        st.markdown("#### 🎯 Desglose del Score")
        breakdown = result.get("breakdown", [])
        if breakdown:
            for item in sorted(breakdown, key=lambda x: -x["puntos"]):
                pct = int(item["puntos"]/10*100)
                c = "#E74C3C" if item["puntos"]>=8 else "#F39C12" if item["puntos"]>=4 else "#27AE60"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin:5px 0">'
                    f'<div style="width:32px;text-align:right;font-weight:800;color:{c}">{item["puntos"]}</div>'
                    f'<div style="flex:1;background:#E8EAF0;border-radius:4px;height:9px">'
                    f'<div style="background:{c};width:{pct}%;height:9px;border-radius:4px"></div></div>'
                    f'<div style="flex:3;font-size:.83rem;color:#2C3E50">{item["señal"]}'
                    f'<span style="color:#AEB6BF;font-size:.72rem"> [{item["codigo"]}]</span></div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<div class="card-verde">Sin señales de riesgo en datos estructurados.</div>', unsafe_allow_html=True)

        if result.get("critical_rules"):
            st.markdown("**Reglas críticas activadas:**")
            for cr in result["critical_rules"]:
                lvl = "card-rojo" if cr in result.get("critical_rojo",[]) else "card-amar"
                st.markdown(f'<div class="{lvl}">⚡ {cr}</div>', unsafe_allow_html=True)

        # PDFs
        st.markdown("#### 📄 Documentos PDF")
        pdf_docs = (pdf_map or {}).get(sin_sel, {})
        if pdf_docs:
            for dtype, path in pdf_docs.items():
                st.markdown(f'<div class="card-azul">✅ <b>{dtype}</b>: <code>{os.path.basename(path)}</code></div>', unsafe_allow_html=True)
                
                # Extraer y mostrar campos estructurados
                txt = ""
                try:
                    txt = extract_text(path)
                    fields_extracted = extract_fields(txt, dtype)
                    field_rows = [{"Campo": k.replace("_", " ").title(), "Valor": str(v)} 
                                  for k, v in fields_extracted.items()
                                  if v and str(v) not in ("", "False", "0") and not k.startswith("_")]
                    if field_rows:
                        st.dataframe(pd.DataFrame(field_rows), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Error extrayendo datos: {e}")
                
                with st.expander(f"Ver texto sin formato — {dtype}"):
                    if txt:
                        st.text(txt[:2000]+("…" if len(txt)>2000 else ""))
                    else:
                        st.info("Texto no disponible")

            # Cross-validation
            st.markdown("#### ⚡ Validación Cruzada")
            all_f: dict = {}
            for dtype, path in pdf_docs.items():
                try:
                    txt = extract_text(path)
                    all_f[dtype] = extract_fields(txt, dtype)
                except: pass

            issues, matches, boost = cross_validate(sin_sel, sin_row, all_f)
            for idx, m in enumerate(matches):
                col_m1, col_m2 = st.columns([5, 1])
                with col_m1:
                    st.markdown(f'<div class="match-ok">✓ <b>{m["campo"]}</b>: {m["valor"]}</div>', unsafe_allow_html=True)
                with col_m2:
                    st.markdown('<div style="padding-top:4px;"></div>', unsafe_allow_html=True)
                    if st.button("🔍 Ver", key=f"btn_match_t2_{idx}"):
                        mostrar_modal_coincidencia(m, sin_row, all_f)
            for iss in issues:
                css = f'issue-{iss["nivel"]}'
                st.markdown(
                    f'<div class="{css}"><b>✗ [{iss["nivel"]}] {iss["campo"]}</b><br>'
                    f'<i>{iss["descripcion"]}</i></div>', unsafe_allow_html=True,
                )
        else:
            st.markdown('<div class="card-azul">No hay PDFs para este siniestro.</div>', unsafe_allow_html=True)

        # Acción
        st.markdown("#### 🚦 Acción Recomendada")
        if nivel == "ROJO":
            st.error("**ESCALAR** → Unidad Antifraude — revisión especializada de campo.")
        elif nivel == "AMARILLO":
            st.warning("**REVISAR** → Unidad Antifraude — revisión documental.")
        else:
            st.success("**CONTINUAR** → Flujo normal de procesamiento.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CARGAR DOCUMENTO
# ═══════════════════════════════════════════════════════════════════════════════
with TABS[3]:
    st.markdown("## 📄 Ingestión y Validación de Documentos")
    st.caption("Selecciona **PDF** para extraer datos de siniestros y realizar validación cruzada en tiempo real, o **Excel** para comprobar la estructura de una nueva base de datos corporativa.")

    utype = st.radio("Tipo de archivo", ["📄 PDF", "📊 Excel"], horizontal=True, key="utype")

    if utype == "📊 Excel":
        st.markdown("### Estructura esperada")
        for sname, cols in EXPECTED_SHEETS.items():
            with st.expander(f"📋 {sname}"):
                st.markdown(", ".join(f"`{c}`" for c in cols))

        uxl = st.file_uploader("Cargar Excel", type=["xlsx","xls"], key="uxl")
        if uxl:
            import tempfile, shutil
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                shutil.copyfileobj(uxl, tmp); tmp_path = tmp.name
            try:
                new_sh = load_excel(tmp_path)
                val    = validate_excel_structure(new_sh)
                st.markdown("### Resultado de validación")
                for sname, res in val.items():
                    if res["found"] and not res["missing_cols"]:
                        st.success(f"✅ **{sname}** — {res['rows']} filas — Estructura completa")
                    elif res["found"]:
                        st.warning(f"⚠️ **{sname}** — Columnas faltantes: {', '.join(res['missing_cols'])}")
                    else:
                        st.error(f"❌ **{sname}** — No encontrada")
                if all(r["found"] and not r["missing_cols"] for r in val.values()):
                    if st.button("✅ Usar como dataset activo"):
                        sc2 = calculate_scores_batch(new_sh, None)
                        st.session_state.update(sheets=new_sh, scores_df=sc2, data_loaded=True, rag_ready=False)
                        st.success("Dataset cargado."); st.rerun()
            except Exception as e:
                st.error(str(e))
            finally:
                os.unlink(tmp_path)

    else:
        updf = st.file_uploader("Cargar PDF", type=["pdf"], key="updf")
        if updf:
            import tempfile, shutil
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                shutil.copyfileobj(updf, tmp); tmp_path = tmp.name
            try:
                text     = extract_text(tmp_path)
                doc_type = detect_doc_type(text)
                sin_id   = extract_sin_id(text)
                fields   = extract_fields(text, doc_type)
            finally:
                os.unlink(tmp_path)

            tipo_lbl = {"PARTE_POLICIAL":"📋 Parte Policial","DECLARACION":"📝 Declaración Accidente",
                        "FACTURA":"🧾 Factura","UNKNOWN":"❓ Desconocido"}.get(doc_type, doc_type)
            st.markdown(f"### {tipo_lbl}")
            if sin_id:
                st.markdown(f"**Siniestro vinculado:** `{sin_id}`")

            field_rows = [{"Campo": k, "Valor": str(v)} for k, v in fields.items()
                          if v and str(v) not in ("","False","0") and not k.startswith("_")]
            if field_rows:
                st.dataframe(pd.DataFrame(field_rows), use_container_width=True, hide_index=True)

            for msg, lvl in [
                ("🚨 DOCUMENTO MARCADO COMO ALTERADO", "error" if fields.get("documento_alterado") else ""),
                ("⚠️ RUC del proveedor INVÁLIDO", "warning" if fields.get("ruc_invalido") else ""),
                ("⚠️ Evento en horario de madrugada", "warning" if fields.get("es_madrugada") else ""),
                ("⚠️ Sin denuncia policial previa", "warning" if fields.get("sin_denuncia") else ""),
            ]:
                if lvl: getattr(st, lvl)(msg)

            if st.session_state.data_loaded and sin_id:
                st.markdown("### ⚡ Validación Cruzada contra Dataset")
                sin_df3 = st.session_state.sheets.get("1_Siniestros", pd.DataFrame())
                match_r = sin_df3[sin_df3["ID Siniestro"]==sin_id]
                if not match_r.empty:
                    ex_row = match_r.iloc[0].to_dict()
                    ep     = st.session_state.pdf_map.get(sin_id, {})
                    af     = {doc_type: fields}
                    for ed, ep2 in ep.items():
                        if ed != doc_type:
                            try: af[ed] = extract_fields(extract_text(ep2), ed)
                            except: pass
                    issues, matches, boost = cross_validate(sin_id, ex_row, af)
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**✅ Coincidencias ({len(matches)})**")
                        for idx, m in enumerate(matches):
                            col_m1, col_m2 = st.columns([5, 1])
                            with col_m1:
                                st.markdown(f'<div class="match-ok">✓ <b>{m["campo"]}</b>: {m["valor"]}</div>', unsafe_allow_html=True)
                            with col_m2:
                                st.markdown('<div style="padding-top:4px;"></div>', unsafe_allow_html=True)
                                if st.button("🔍 Ver", key=f"btn_match_t3_{idx}"):
                                    mostrar_modal_coincidencia(m, ex_row, af)
                    with c2:
                        st.markdown(f"**⚠️ Inconsistencias ({len(issues)})**")
                        for iss in issues:
                            st.markdown(f'<div class="issue-{iss["nivel"]}"><b>[{iss["nivel"]}] {iss["campo"]}</b><br><i>{iss["descripcion"]}</i></div>', unsafe_allow_html=True)

                    base_r = score_siniestro(ex_row, fields)
                    total  = min(base_r["score"] + boost, 100)
                    nivel2 = "ROJO" if total>=76 else "AMARILLO" if total>=41 else "VERDE"
                    em2    = {"ROJO":"🔴","AMARILLO":"🟡","VERDE":"🟢"}[nivel2]
                    c_n2   = {"ROJO":"#E74C3C","AMARILLO":"#F39C12","VERDE":"#27AE60"}[nivel2]
                    st.markdown(
                        f'<div style="background:{c_n2}18;border:2px solid {c_n2};border-radius:10px;'
                        f'padding:12px 18px;margin-top:10px">'
                        f'<span style="font-size:1.3rem;font-weight:800;color:{c_n2}">'
                        f'{em2} Score actualizado: {total}/100 — {nivel2}</span></div>',
                        unsafe_allow_html=True,
                    )
                    if st.session_state.rag_ready:
                        added = st.session_state.rag.add_document(text, sin_id, doc_type)
                        if added:
                            st.success("Documento añadido al índice del Agente IA.")
                        else:
                            st.info("El documento ya existe en el índice del Agente IA.")
                else:
                    st.warning(f"Siniestro {sin_id} no encontrado en la base de datos oficial (Excel).")
                    st.markdown(
                        '<div class="card-amar" style="padding:15px;border-radius:10px;margin-bottom:12px">'
                        f'💡 <b>Auto-Ingesta Inteligente Activa</b><br>'
                        f'El documento subido pertenece a un siniestro nuevo <b>({sin_id})</b>. '
                        f'¿Deseas dar de alta este siniestro automáticamente en caliente '
                        f'usando los datos extraídos por IA de este PDF?'
                        '</div>', unsafe_allow_html=True
                    )
                    
                    if st.button("📥 Registrar Siniestro en Base de Datos", use_container_width=True, type="primary", key="btn_auto_ingest"):
                        with st.spinner("Procesando auto-ingesta y registrando en caliente…"):
                            try:
                                # 1. Extraer los datos para el nuevo siniestro
                                ex_placa = fields.get("placa") or "N/D"
                                ex_fecha = fields.get("fecha_hecho") or fields.get("fecha") or "2026-05-28"
                                ex_monto = fields.get("total") or 0.0
                                try: 
                                    ex_monto = float(str(ex_monto).replace("$","").replace(",","").strip())
                                except Exception: 
                                    ex_monto = 0.0
                                
                                aseg_nombre = fields.get("nombre_conductor") or fields.get("asegurado") or fields.get("cliente") or "Cliente Auto-Ingestado"
                                aseg_id = f"ASEG-{sin_id.split('-')[-1]}"
                                prov_id = f"PROV-{sin_id.split('-')[-1]}"
                                prov_nombre = fields.get("taller") or "Proveedor Auto-Ingestado"
                                
                                # 2. Agregar fila a Siniestros
                                new_sin_row = {
                                    "ID Siniestro": sin_id,
                                    "ID Póliza": f"POL-{sin_id.split('-')[-1]}",
                                    "ID Asegurado": aseg_id,
                                    "Ramo": "Vehículos",
                                    "Cobertura": "Auto-Ingesta (PDF)",
                                    "Placa Vehículo Asegurado": ex_placa,
                                    "Fecha Ocurrencia": ex_fecha,
                                    "Fecha Reporte": ex_fecha,
                                    "Días Ocurr→Reporte": 0,
                                    "Monto Reclamado ($)": ex_monto,
                                    "Monto Estimado ($)": ex_monto,
                                    "Estado": "Auto-Ingestado",
                                    "Sucursal": "Matriz Quito",
                                    "ID Proveedor": prov_id,
                                    "Docs Completos": "Sí",
                                    "Prov. Lista Restrictiva": "No",
                                    "Días desde Inicio Póliza": 90,
                                    "Días hasta Fin Póliza": 270,
                                    "N° Reclamos Previos Asegurado": 0,
                                    "Suma Asegurada ($)": ex_monto * 1.5 if ex_monto > 0 else 10000.0,
                                    "Similitud Narrativa Máx.": 0.0,
                                    "Descripción del Evento": fields.get("descripcion") or "Siniestro auto-ingestado de forma inteligente a partir de soporte documental."
                                }
                                st.session_state.sheets["1_Siniestros"] = pd.concat([st.session_state.sheets["1_Siniestros"], pd.DataFrame([new_sin_row])], ignore_index=True)
                                
                                # 3. Agregar fila a Asegurados si no existe
                                new_aseg_row = {
                                    "ID Asegurado": aseg_id,
                                    "Nombres Asegurado": aseg_nombre,
                                    "Ciudad": "Quito",
                                    "Antigüedad (años)": 2,
                                    "Reclamos RC sin Tercero": 0
                                }
                                st.session_state.sheets["3_Asegurados"] = pd.concat([st.session_state.sheets["3_Asegurados"], pd.DataFrame([new_aseg_row])], ignore_index=True)
                                
                                # 4. Agregar fila a Proveedores si no existe
                                new_prov_row = {
                                    "ID Proveedor": prov_id,
                                    "Nombre Proveedor": prov_nombre,
                                    "En Lista Restrictiva": "No",
                                    "Tipo": "General"
                                }
                                st.session_state.sheets["4_Proveedores"] = pd.concat([st.session_state.sheets["4_Proveedores"], pd.DataFrame([new_prov_row])], ignore_index=True)
                                
                                # 5. Recalcular score y actualizar st.session_state.scores_df
                                new_scores = calculate_scores_batch(st.session_state.sheets, st.session_state.pdf_map)
                                st.session_state.scores_df = new_scores
                                
                                # 6. Registrar también en el RAG
                                if st.session_state.rag_ready:
                                    st.session_state.rag.add_document(text, sin_id, doc_type)
                                
                                st.success(f"🎉 Siniestro {sin_id} registrado y auto-ingestado con éxito. ¡Base de datos de la sesión actualizada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error en auto-ingesta: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AGENTE IA
# ═══════════════════════════════════════════════════════════════════════════════
with TABS[4]:
    st.markdown("## 🤖 Agente Antifraude IA")
    st.markdown(
        '<div class="card-azul" style="display:flex;align-items:center;gap:10px">'
        '<span style="font-size:1.5rem">🧠</span>'
        '<div>'
        '<b>Sistema RAG local + Groq llama-3.1-8b-instant</b><br>'
        '<small style="color:#5D6D7E">'
        'Indexa tus 500 siniestros + 24 PDFs en vectores (sentence-transformers + FAISS) '
        'y recupera contexto relevante para que el LLM responda en &lt;3 segundos. '
        'Sin reglas if/else — generación aumentada por recuperación.'
        '</small></div></div>',
        unsafe_allow_html=True,
    )

    # Banner: indica el modo actual del agente
    if st.session_state.rag_ready and st.session_state.rag is not None:
        is_retrieval_only = st.session_state.rag.retrieval_only
        if is_retrieval_only:
            st.markdown(
                '<div class="card-amar" style="padding:12px 18px;margin-bottom:12px">'
                '<b>🟡 Agente activo — Modo Retrieval-Only</b><br>'
                '<small>El agente recupera datos reales con FAISS y los muestra. '
                'Para respuestas naturales con redacción, pega tu Groq API Key en el sidebar.</small>'
                '</div>', unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="card-verde" style="padding:12px 18px;margin-bottom:12px">'
                '<b>🟢 Agente activo — Modo Completo</b><br>'
                '<small>RAG + Groq llama-3.1-8b-instant. Respuestas naturales en &lt;3s con streaming.</small>'
                '</div>', unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="card-azul" style="padding:14px 20px;margin-bottom:14px">'
            '<h4 style="color:#1B4F8A !important;margin:0 0 6px 0">🧠 ¿Cómo funciona este agente?</h4>'
            '<p style="margin:0;color:#1A3A5C;font-size:.95rem">'
            'Sistema <b>RAG (Retrieval-Augmented Generation)</b> con dos modos:'
            '</p>'
            '<ul style="margin:6px 0 0 0;color:#1A3A5C;font-size:.95rem">'
            '<li><b>🟡 Retrieval-only:</b> recupera datos del dataset con FAISS. <b>No requiere API Key.</b></li>'
            '<li><b>🟢 Completo:</b> retrieval + LLM Groq llama-3.1-8b-instant. Requiere API Key.</li>'
            '</ul>'
            '<p style="margin:10px 0 0 0;color:#1A3A5C;font-size:.85rem">'
            '⏳ <b>Carga el dataset</b> para activar el agente automáticamente.'
            '</p></div>',
            unsafe_allow_html=True,
        )

    # ── 12 preguntas SIEMPRE visibles ────────────────────────────────
    st.markdown("### 📋 Las 12 preguntas del reto — Sección 12 del PDF")
    if not st.session_state.rag_ready:
        if not st.session_state.data_loaded:
            st.caption("⚠️ Carga el dataset desde el panel lateral primero.")
        else:
            st.caption("⏳ Activando agente automáticamente…")
    else:
        st.caption("Haz clic en cualquier pregunta para obtener la respuesta al instante.")

    PREGUNTAS_PDF = [
        "¿Cuáles son los 10 siniestros con mayor riesgo de posible fraude?",
        "¿Por qué el siniestro SIN-0005 fue marcado como alto riesgo?",
        "¿Qué proveedores concentran más alertas de posible fraude?",
        "¿Qué ramos tienen mayor porcentaje de casos sospechosos?",
        "¿Qué ciudades presentan mayor concentración de alertas?",
        "¿Qué asegurados tienen mayor frecuencia de reclamos?",
        "¿Qué documentos faltan en los casos críticos?",
        "¿Qué casos tienen montos atípicos respecto a su suma asegurada?",
        "¿Qué siniestros ocurrieron cerca del inicio o fin de la póliza?",
        "¿Qué patrones se repiten en los reclamos sospechosos?",
        "Genera un resumen ejecutivo de los casos críticos para gerencia.",
        "Recomienda qué casos debería revisar primero el analista antifraude.",
    ]
    # Encolar pregunta pendiente (no se procesa hasta el bloque del chat)
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    sc1, sc2, sc3 = st.columns(3)
    for i, s in enumerate(PREGUNTAS_PDF):
        emoji = "🔴" if i < 3 else "🟡" if i < 6 else "🔵"
        label = f"{emoji} {s[:42]}…" if len(s) > 42 else f"{emoji} {s}"
        clicked = [sc1, sc2, sc3][i % 3].button(
            label, key=f"pdf_q{i}", use_container_width=True, help=s,
            disabled=(not st.session_state.rag_ready or st.session_state.pending_question is not None),
        )
        if clicked and st.session_state.rag_ready and st.session_state.pending_question is None:
            st.session_state.pending_question = s
            st.rerun()

    if not st.session_state.rag_ready:
        st.stop()

    st.divider()

    # ── Chat ─────────────────────────────────────────────────────────
    # Mostrar TODO el historial primero
    for msg in st.session_state.chat_history:
        css = "chat-user" if msg["role"] == "user" else "chat-bot"
        who = "👤 Analista" if msg["role"] == "user" else "🤖 Agente FRAUDIA"
        st.markdown(
            f'<div class="{css}"><b>{who}:</b> {msg["content"]}</div>',
            unsafe_allow_html=True,
        )

    # Procesar pregunta pendiente (si existe)
    if st.session_state.pending_question:
        q = st.session_state.pending_question
        # Mostrar la pregunta del usuario
        st.markdown(
            f'<div class="chat-user"><b>👤 Analista:</b> {q}</div>',
            unsafe_allow_html=True,
        )
        hist = [m for m in st.session_state.chat_history if m["role"] in ("user","assistant")]

        # Streaming con st.write_stream — mucho más estable que st.empty()
        try:
            import time as _t
            t0 = _t.time()
            st.markdown('<div class="chat-bot"><b>🤖 Agente FRAUDIA:</b></div>', unsafe_allow_html=True)
            response_text = st.write_stream(st.session_state.rag.answer_stream(q, hist))
            elapsed = _t.time() - t0
            st.caption(f"⚡ Respondido en {elapsed:.1f}s")

            # Guardar en historial
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            st.session_state.pending_question = None
            st.rerun()
        except Exception as e:
            st.error(f"Error en la respuesta: {e}")
            st.session_state.pending_question = None

    # Input para pregunta libre
    with st.form("chat_f", clear_on_submit=True):
        ui = st.text_input(
            "Tu pregunta…",
            placeholder="Ej: ¿Por qué SIN-0005 es riesgo alto?",
            disabled=(st.session_state.pending_question is not None),
        )
        submitted = st.form_submit_button(
            "Enviar", use_container_width=True,
            disabled=(st.session_state.pending_question is not None),
        )
        if submitted and ui.strip() and st.session_state.pending_question is None:
            st.session_state.pending_question = ui.strip()
            st.rerun()

    if st.button("🗑️ Limpiar chat"):
        st.session_state.chat_history = []
        st.session_state.pending_question = None
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — MODELO ML (Isolation Forest + Random Forest + Score Combinado)
# ═══════════════════════════════════════════════════════════════════════════════
with TABS[5]:
    st.markdown("## 🧠 Modelo de Inteligencia Artificial — Enfoque Híbrido")
    st.caption(
        "Combina Reglas de Negocio + Isolation Forest (anomalías) + Random Forest (supervisado). "
        "Implementa la sección 9 del reto: enfoque híbrido ML + NLP + Agente IA."
    )

    if not st.session_state.data_loaded:
        st.info("Carga el dataset primero.")
        st.stop()

    ml_subtab1, ml_subtab2, ml_subtab3 = st.tabs([
        "🌲 Random Forest Supervisado",
        "🔮 Isolation Forest (Anomalías)",
        "🕸️ Narrativas Clonadas",
    ])

    # ── SUB-TAB A: RANDOM FOREST ──────────────────────────────────────
    with ml_subtab1:
        st.markdown("### Random Forest Supervisado con Etiqueta Simulada")
        st.markdown(
            '<div class="card-azul">La etiqueta de fraude se genera a partir del score de reglas '
            '(≥76 pts → posible fraude). Esto implementa la sección 9: '
            '<b>Machine Learning supervisado</b>.</div>', unsafe_allow_html=True
        )
        st.markdown("")

        if st.session_state.rf_result is None:
            if st.button("🌲 Entrenar Random Forest (300 árboles)", type="primary"):
                with st.spinner("Entrenando… validación cruzada 5-fold…"):
                    try:
                        from src.supervised_model import train_random_forest, build_combined_df
                        rf = train_random_forest(
                            st.session_state.sheets,
                            st.session_state.scores_df,
                        )
                        if st.session_state.ml_result is None:
                            from src.anomaly_model import train_model
                            ml = train_model(st.session_state.sheets, 0.30)
                            st.session_state.ml_result = ml
                        comb = build_combined_df(
                            st.session_state.scores_df,
                            st.session_state.ml_result or {},
                            rf,
                        )
                        st.session_state.rf_result    = rf
                        st.session_state.combined_df  = comb
                        st.success("✅ Random Forest entrenado")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            rf  = st.session_state.rf_result
            m   = rf["metrics"]
            comb = st.session_state.combined_df

            # KPIs métricas
            ka, kb, kc, kd, ke = st.columns(5)
            for col, val, lbl, color in [
                (ka, f"{m['cv_auc_mean']:.3f}",  "AUC-ROC (CV 5-fold)",  "#1B4F8A"),
                (kb, f"{m['cv_f1_mean']:.3f}",   "F1-Score (CV)",        "#27AE60"),
                (kc, f"{m['cv_pre_mean']:.3f}",  "Precisión (CV)",       "#2980B9"),
                (kd, f"{m['cv_rec_mean']:.3f}",  "Recall (CV)",          "#F39C12"),
                (ke, f"{m['n_positivos']}/{m['n_total']}", "Fraudes/Total", "#E74C3C"),
            ]:
                col.markdown(
                    f'<div class="kpi-box"><div class="kpi-val" style="color:{color};font-size:1.6rem">{val}</div>'
                    f'<div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True,
                )

            st.divider()
            col_rf1, col_rf2 = st.columns(2)

            with col_rf1:
                # Curva ROC
                roc_fig = go.Figure()
                roc_fig.add_trace(go.Scatter(
                    x=rf["roc_fpr"], y=rf["roc_tpr"], mode="lines",
                    name=f"ROC (AUC={m['auc']:.3f})",
                    line=dict(color="#1B4F8A", width=2.5),
                ))
                roc_fig.add_trace(go.Scatter(
                    x=[0,1], y=[0,1], mode="lines",
                    line=dict(dash="dot", color="#AED6F1"),
                    name="Aleatorio (AUC=0.5)", showlegend=True,
                ))
                roc_fig.update_layout(
                    title="Curva ROC — Random Forest",
                    xaxis_title="Tasa Falsos Positivos",
                    yaxis_title="Tasa Verdaderos Positivos",
                    paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                    font=dict(color="#1B4F8A"), title_font_color="#1B4F8A",
                    legend=dict(font=dict(color="#1B4F8A")), height=380,
                )
                st.plotly_chart(roc_fig, use_container_width=True)

            with col_rf2:
                # Feature Importance
                fi = rf["feature_importance"]
                fi_df = pd.DataFrame(list(fi.items()), columns=["Variable", "Importancia"])
                fig_fi = px.bar(
                    fi_df.head(10).sort_values("Importancia", ascending=True),
                    x="Importancia", y="Variable", orientation="h",
                    title="Top 10 Variables — Importancia RF",
                    color="Importancia",
                    color_continuous_scale=["#AED6F1", "#1B4F8A"],
                )
                fig_fi.update_layout(
                    paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                    font=dict(color="#1B4F8A"), title_font_color="#1B4F8A",
                    coloraxis_showscale=False, height=380,
                )
                st.plotly_chart(fig_fi, use_container_width=True)

            # Confusion Matrix
            st.markdown("#### Matriz de Confusión")
            cm = m["confusion_matrix"]
            cm_df = pd.DataFrame(cm,
                index=["Real: No Fraude", "Real: Fraude"],
                columns=["Pred: No Fraude", "Pred: Fraude"])
            fig_cm = px.imshow(
                cm_df, text_auto=True,
                color_continuous_scale=["#EBF5FB", "#1B4F8A"],
                title="Confusion Matrix — Random Forest",
                aspect="auto",
            )
            fig_cm.update_layout(paper_bgcolor="white", font=dict(color="#1B4F8A"),
                                 title_font_color="#1B4F8A", height=300)
            st.plotly_chart(fig_cm, use_container_width=True)

            # Score Combinado
            if comb is not None:
                st.divider()
                st.markdown("### 🎯 Score Final Combinado = 50% Reglas + 25% IF + 25% RF")
                dist_c = comb["Nivel_Final"].value_counts().reset_index()
                dist_c.columns = ["Nivel", "Casos"]
                tc1, tc2 = st.columns(2)
                with tc1:
                    fig_dc = px.pie(
                        dist_c, names="Nivel", values="Casos", hole=0.4,
                        color="Nivel",
                        color_discrete_map={"ROJO":"#E74C3C","AMARILLO":"#F39C12","VERDE":"#27AE60"},
                        title="Distribución Score Final Combinado",
                    )
                    fig_dc.update_layout(paper_bgcolor="white", font=dict(color="#1B4F8A"),
                                         title_font_color="#1B4F8A")
                    st.plotly_chart(fig_dc, use_container_width=True)
                with tc2:
                    fig_sc2 = px.scatter(
                        comb, x="Score_Reglas", y="RF_Score",
                        color="Nivel_Final",
                        color_discrete_map={"ROJO":"#E74C3C","AMARILLO":"#F39C12","VERDE":"#27AE60"},
                        hover_name="ID Siniestro",
                        size="Score_Final",
                        size_max=18,
                        title="Reglas vs Random Forest",
                        labels={"Score_Reglas":"Score Reglas","RF_Score":"Score RF"},
                        opacity=0.75,
                    )
                    fig_sc2.update_layout(paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                                          font=dict(color="#1B4F8A"), title_font_color="#1B4F8A",
                                          legend=dict(font=dict(color="#1B4F8A")), height=360)
                    st.plotly_chart(fig_sc2, use_container_width=True)

                top_comb = comb.head(10)[["ID Siniestro","Score_Reglas","Anomaly_Score","RF_Score","Score_Final","Nivel_Final","Cobertura"]]
                top_comb.columns = ["Siniestro","Score Reglas","Score IF","Score RF","Score Final","Nivel","Cobertura"]
                st.dataframe(top_comb.reset_index(drop=True), use_container_width=True)

            if st.button("🔄 Reentrenar RF"):
                st.session_state.rf_result = None
                st.session_state.combined_df = None
                st.rerun()

    # ── SUB-TAB B: ISOLATION FOREST ───────────────────────────────────
    with ml_subtab2:
        st.markdown("### Isolation Forest — Detección de Anomalías No Supervisada")

        if st.session_state.ml_result is None:
            if st.button("⚙️ Entrenar Isolation Forest", type="primary"):
                with st.spinner("Entrenando Isolation Forest (200 árboles)…"):
                    try:
                        from src.anomaly_model import train_model
                        ml = train_model(st.session_state.sheets, 0.30)
                        st.session_state.ml_result = ml
                        st.success(f"✅ {ml['n_anomalies']} anomalías detectadas")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            ml = st.session_state.ml_result
            sc = st.session_state.scores_df

            ml_df    = ml["scores_df"]
            combined_if = sc.merge(ml_df, on="ID Siniestro", how="left")
            combined_if["Anomaly_Score"] = combined_if["Anomaly_Score"].fillna(50)
            only_ml  = combined_if[combined_if["Es_Anomalia"] == True][combined_if["Nivel"]=="VERDE"]

            m1, m2, m3, m4 = st.columns(4)
            for col, val, lbl, color in [
                (m1, ml["n_anomalies"],          "Anomalías detectadas", "#1B4F8A"),
                (m2, len(only_ml),               "Casos ciegos (solo IF)", "#E74C3C"),
                (m3, f"{ml['contamination']*100:.0f}%", "Contaminación", "#27AE60"),
                (m4, "200", "N° Estimadores", "#2980B9"),
            ]:
                col.markdown(
                    f'<div class="kpi-box"><div class="kpi-val" style="color:{color}">{val}</div>'
                    f'<div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True,
                )

            st.divider()
            cif1, cif2 = st.columns([3,2])
            with cif1:
                fig_if = px.scatter(
                    combined_if, x="Score", y="Anomaly_Score",
                    color="Nivel",
                    color_discrete_map={"ROJO":"#E74C3C","AMARILLO":"#F39C12","VERDE":"#27AE60"},
                    hover_name="ID Siniestro",
                    title="Reglas vs Isolation Forest",
                    labels={"Score":"Score Reglas","Anomaly_Score":"Score Anomalía IF"},
                    opacity=0.70,
                )
                fig_if.add_hline(y=60, line_dash="dot", line_color="#AED6F1",
                                 annotation_text="Umbral IF")
                fig_if.update_layout(paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                                     font=dict(color="#1B4F8A"), height=380)
                st.plotly_chart(fig_if, use_container_width=True)
            with cif2:
                fi_if = ml["feature_importance"]
                fi_if_df = pd.DataFrame(list(fi_if.items()), columns=["Variable","Importancia (%)"])
                fig_fi_if = px.bar(
                    fi_if_df.sort_values("Importancia (%)", ascending=True),
                    x="Importancia (%)", y="Variable", orientation="h",
                    title="Variables — Isolation Forest",
                    color="Importancia (%)",
                    color_continuous_scale=["#AED6F1","#1B4F8A"],
                )
                fig_fi_if.update_layout(paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                                        font=dict(color="#1B4F8A"), coloraxis_showscale=False, height=380)
                st.plotly_chart(fig_fi_if, use_container_width=True)

    # ── SUB-TAB C: NARRATIVAS CLONADAS ───────────────────────────────
    with ml_subtab3:
        st.markdown("### 🕵️ Red de Narrativas Clonadas — Posibles Anillos de Fraude Coordinado")
        st.markdown(
            '<div class="card-rojo">Los nodos representan siniestros con descripciones similares entre sí. '
            'Las aristas indican similitud de texto ≥65%. Grupos conectados pueden indicar '
            'fraude coordinado donde múltiples reclamantes usaron el mismo relato.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        th = st.slider("Umbral de similitud", 0.70, 0.98, 0.85, 0.01,
                       help="Mayor umbral = solo casos casi idénticos. 0.85 = clonación probable.")

        if st.button("🔍 Detectar Narrativas Clonadas", type="primary") or st.session_state.clusters is not None:
            if st.session_state.clusters is None or st.button("🔄 Recalcular", key="reclust"):
                with st.spinner("Analizando similitud textual (TF-IDF)…"):
                    try:
                        from src.anomaly_model import compute_narrative_clusters
                        clusters = compute_narrative_clusters(
                            st.session_state.sheets.get("1_Siniestros", pd.DataFrame()),
                            st.session_state.scores_df,
                            threshold=th,
                        )
                        st.session_state.clusters = clusters
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

            if st.session_state.clusters:
                cl = st.session_state.clusters
                clk1, clk2, clk3 = st.columns(3)
                clk1.markdown(
                    f'<div class="kpi-box"><div class="kpi-val" style="color:#E74C3C">{cl["n_groups"]}</div>'
                    f'<div class="kpi-lbl">Grupos de narrativas clonadas</div></div>', unsafe_allow_html=True,
                )
                clk2.markdown(
                    f'<div class="kpi-box"><div class="kpi-val" style="color:#F39C12">{cl["n_nodes"]}</div>'
                    f'<div class="kpi-lbl">Siniestros involucrados</div></div>', unsafe_allow_html=True,
                )
                clk3.markdown(
                    f'<div class="kpi-box"><div class="kpi-val" style="color:#1B4F8A">{cl["n_pairs"]}</div>'
                    f'<div class="kpi-lbl">Conexiones</div></div>', unsafe_allow_html=True,
                )
                st.markdown("")

                from src.anomaly_model import build_narrative_graph
                fig_narr = build_narrative_graph(cl)
                st.plotly_chart(fig_narr, use_container_width=True)

                # Tabla de grupos clonados
                if cl.get("groups"):
                    st.markdown("#### 🚨 Grupos con narrativas idénticas que incluyen casos de riesgo")
                    grp_rows = []
                    for g in cl["groups"][:30]:
                        grp_rows.append({
                            "Narrativa repetida": g["narrativa"],
                            "Tamaño grupo": g["tamaño"],
                            "🔴 Rojos": g["n_rojo"],
                            "🟡 Amarillos": g["n_amarillo"],
                            "🟢 Verdes": g["n_verde"],
                            "Score máx": g["score_max"],
                            "Primeros siniestros": ", ".join(g["siniestros"][:5]),
                        })
                    st.dataframe(pd.DataFrame(grp_rows), use_container_width=True, height=350)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — RED RELACIONAL
# ═══════════════════════════════════════════════════════════════════════════════
with TABS[6]:
    st.markdown("## 🕸️ Red Relacional")
    st.caption("Grafo interactivo: Asegurados ↔ Siniestros ↔ Proveedores. Coloreado por nivel de riesgo.")

    if not st.session_state.data_loaded:
        st.info("Carga el dataset primero.")
    else:
        fa2, fb2 = st.columns([3,1])
        filtro_niveles = fa2.multiselect(
            "Filtrar por nivel",
            ["ROJO","AMARILLO","VERDE"],
            default=["ROJO","AMARILLO"],
            key="net_fil",
        )
        with st.spinner("Construyendo grafo…"):
            fig_net = build_graph(
                st.session_state.sheets,
                st.session_state.scores_df,
                filter_nivel=filtro_niveles or None,
            )
        fig_net.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                              font=dict(color="#1B4F8A"))
        st.plotly_chart(fig_net, use_container_width=True)

        lc = st.columns(5)
        for col, (ic, lb) in zip(lc, [
            ("🔴","Siniestro crítico"),("🟡","Siniestro medio"),
            ("🟢","Siniestro bajo"),("🔷","Asegurado"),("🟠","Proveedor"),
        ]):
            col.markdown(f"<small>{ic} {lb}</small>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — ÉTICA Y LIMITACIONES
# ═══════════════════════════════════════════════════════════════════════════════
with TABS[7]:
    st.markdown("## ⚖️ Ética, Limitaciones y Declaración de Uso Responsable")
    st.caption("FRAUDIA está diseñado para apoyar — nunca para reemplazar — el juicio del analista humano.")

    st.markdown("""
    <div style="background:#1B4F8A;color:white;border-radius:12px;padding:16px 20px;margin-bottom:20px">
    <b style="font-size:1.1rem">⚖️ Principio fundamental</b><br>
    FRAUDIA genera <b>alertas de revisión</b>, no acusaciones de fraude. Ningún siniestro puede ser
    rechazado automáticamente por este sistema. La decisión final es SIEMPRE del analista especializado.
    </div>
    """, unsafe_allow_html=True)

    e1, e2 = st.columns(2)

    with e1:
        st.markdown("### 🎯 Propósito y alcance")
        items = [
            ("✅ Está permitido", [
                "Generar alertas para priorizar revisión humana",
                "Calcular scores de riesgo como apoyo al analista",
                "Identificar patrones estadísticos sospechosos",
                "Reducir tiempo de búsqueda de casos irregulares",
            ]),
            ("❌ No está permitido", [
                "Rechazar automáticamente un siniestro",
                "Acusar formalmente a un asegurado de fraude",
                "Sustituir el análisis humano especializado",
                "Tomar decisiones legales o contractuales",
            ]),
        ]
        for title, pts in items:
            color = "#27AE60" if "✅" in title else "#E74C3C"
            st.markdown(f'<div style="border-left:4px solid {color};padding:8px 12px;'
                        f'background:{"#F0FDF4" if "✅" in title else "#FEF5F5"};'
                        f'border-radius:6px;margin:8px 0"><b>{title}:</b></div>', unsafe_allow_html=True)
            for pt in pts:
                st.markdown(f"• {pt}")

        st.divider()
        st.markdown("### ⚠️ Limitaciones del modelo")
        limits = [
            ("Tasa de falsos positivos estimada", "15–20%",
             "Casos legítimos que el modelo marca como sospechosos. Requieren revisión para no afectar al asegurado."),
            ("Datos de entrenamiento sintéticos", "500 registros",
             "En producción, el modelo debe recalibrarse con datos históricos reales de la aseguradora."),
            ("Señales documentales limitadas", "24 PDFs disponibles",
             "Solo un subconjunto de siniestros tiene PDFs. El score de cross-validación aplica parcialmente."),
            ("Sin datos en tiempo real", "Dataset estático",
             "El sistema no se actualiza en tiempo real. Requiere recarga periódica del dataset."),
        ]
        for name, val, desc in limits:
            st.markdown(
                f'<div class="card-azul"><b>{name}:</b> <span style="color:#E74C3C;font-weight:700">{val}</span>'
                f'<br><small>{desc}</small></div>', unsafe_allow_html=True,
            )

    with e2:
        st.markdown("### 📊 Análisis de Sesgo por Categoría")

        if st.session_state.data_loaded:
            df_bias = st.session_state.scores_df.copy()

            # Sesgo por ramo
            bias_ramo = df_bias.groupby("Ramo").agg(
                Total=("Score","count"),
                Score_prom=("Score","mean"),
                Pct_Rojo=("Nivel", lambda x: (x=="ROJO").sum()/len(x)*100),
            ).reset_index().round(1)

            fig_bias_r = px.bar(
                bias_ramo, x="Ramo", y="Pct_Rojo",
                title="% Casos ROJO por Ramo",
                color="Pct_Rojo",
                color_continuous_scale=["#AED6F1","#E74C3C"],
                text="Pct_Rojo",
            )
            fig_bias_r.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_bias_r.update_layout(paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                                     font=dict(color="#1B4F8A"), title_font_color="#1B4F8A",
                                     coloraxis_showscale=False, yaxis_title="% Críticos",
                                     showlegend=False, height=280)
            st.plotly_chart(fig_bias_r, use_container_width=True)

            # Sesgo por sucursal
            bias_suc = df_bias.groupby("Sucursal").agg(
                Pct_Rojo=("Nivel", lambda x: (x=="ROJO").sum()/len(x)*100),
            ).reset_index().sort_values("Pct_Rojo", ascending=False).round(1)

            fig_bias_s = px.bar(
                bias_suc, x="Sucursal", y="Pct_Rojo",
                title="% Casos ROJO por Sucursal",
                color="Pct_Rojo",
                color_continuous_scale=["#AED6F1","#E74C3C"],
            )
            fig_bias_s.update_layout(paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                                     font=dict(color="#1B4F8A"), title_font_color="#1B4F8A",
                                     coloraxis_showscale=False, height=280)
            st.plotly_chart(fig_bias_s, use_container_width=True)

            st.markdown(
                '<div class="card-azul"><b>Recomendación:</b> Si algún ramo o sucursal muestra '
                'un porcentaje de alertas ROJO significativamente superior a los demás, '
                'se recomienda revisar si las reglas tienen sesgo hacia ese segmento y '
                'ajustar los pesos de las señales correspondientes.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Carga el dataset para ver el análisis de sesgo.")

        st.divider()
        st.markdown("### 🔄 Flujo de Revisión Humana Recomendado")
        st.markdown("""
        ```
        FRAUDIA genera alerta ROJA
              ↓
        Analista Antifraude revisa el caso
              ↓
        ¿Confirmado como irregular?
         SÍ → Escalar a Jefatura + Auditoría
         NO → Registrar falso positivo → Mejora del modelo
              ↓
        Decisión final: Jefatura de Siniestros
        ```
        """)

# ── Mover Tab Proveedores al índice correcto ──────────────────────────────────
with TABS[8]:
    st.markdown("## 🏢 Análisis de Proveedores")

    if not st.session_state.data_loaded:
        st.info("Carga el dataset primero.")
    else:
        prov_df = st.session_state.sheets.get("4_Proveedores", pd.DataFrame()).copy()
        sin_sc  = st.session_state.scores_df

        if prov_df.empty:
            st.warning("No hay datos de proveedores.")
        else:
            if "Tipo" not in prov_df.columns:
                prov_df["Tipo"] = "General"
            red = sin_sc[sin_sc.Nivel=="ROJO"].groupby("ID Proveedor").size().reset_index(name="Alertas_Rojas")
            prov_df = prov_df.merge(red, on="ID Proveedor", how="left")
            prov_df["Alertas_Rojas"] = prov_df["Alertas_Rojas"].fillna(0).astype(int)

            p1, p2, p3 = st.columns(3)
            rest = prov_df[prov_df["En Lista Restrictiva"].str.lower().isin(["sí","si","yes"])]
            p1.metric("Total Proveedores", len(prov_df))
            p2.metric("🔴 Lista Restrictiva", len(rest))
            p3.metric("Con Alertas Rojas", (prov_df.Alertas_Rojas>0).sum())

            st.divider()
            tipo_f = ["Todos"] + sorted(prov_df["Tipo"].dropna().unique().tolist())
            tp_sel = st.selectbox("Tipo", tipo_f, key="prov_tipo")
            pshow = prov_df if tp_sel=="Todos" else prov_df[prov_df["Tipo"]==tp_sel]
            pshow = pshow.sort_values("Alertas_Rojas", ascending=False)

            def _color_prov(row):
                if str(row.get("En Lista Restrictiva","")).lower() in ("sí","si","yes"):
                    return ["background-color:#FEF5F5"]*len(row)
                if row.get("Alertas_Rojas",0) > 0:
                    return ["background-color:#FEFAF0"]*len(row)
                return [""]*len(row)

            cols_p = [c for c in ["ID Proveedor","Nombre Proveedor","Tipo","Ciudad",
                      "N° Siniestros Asociados","En Lista Restrictiva",
                      "Motivo Restricción","Promedio Monto ($)","Alertas_Rojas"]
                      if c in pshow.columns]
            st.dataframe(
                pshow[cols_p].reset_index(drop=True).style.apply(_color_prov, axis=1),
                use_container_width=True, height=380,
            )

            # Exportar proveedores
            csv_p = pshow[cols_p].to_csv(index=False).encode("utf-8")
            st.download_button("📥 Exportar proveedores", csv_p, "proveedores.csv", "text/csv")

            top10p = pshow.nlargest(10,"Alertas_Rojas")
            if not top10p.empty and top10p["Alertas_Rojas"].sum() > 0:
                fig_pv = px.bar(
                    top10p, x="Nombre Proveedor", y="Alertas_Rojas",
                    title="Top 10 Proveedores por Alertas Rojas",
                    color="Alertas_Rojas",
                    color_continuous_scale=["#AED6F1","#E74C3C"],
                )
                fig_pv.update_layout(paper_bgcolor="white", plot_bgcolor="#F8FBFF",
                                     font=dict(color="#1B4F8A"), title_font_color="#1B4F8A",
                                     coloraxis_showscale=False)
                st.plotly_chart(fig_pv, use_container_width=True)
