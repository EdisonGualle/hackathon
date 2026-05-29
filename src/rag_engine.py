"""
RAG Engine — Groq + sentence-transformers + FAISS
No hardcoded if/else logic. The LLM reasons freely over retrieved context.
"""

import os
# Forzar a Hugging Face a desactivar enlaces simbólicos (symlinks) en Windows para evitar OSError Errno 22
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["TQDM_DISABLE"] = "1"

try:
    import transformers
    transformers.utils.logging.disable_progress_bar()
except Exception:
    pass

import pickle
import hashlib
import numpy as np
import pandas as pd
from groq import Groq


EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
GROQ_MODEL = "llama-3.1-8b-instant"   # < 3s en respuestas típicas
CHUNK_OVERLAP = 50
TOP_K = 6                              # menos contexto = más rápido
MAX_TOKENS = 800                       # respuestas concisas

# Directorio de caché en disco para persistir el índice RAG
_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "cache",
)
os.makedirs(_CACHE_DIR, exist_ok=True)


class RAGEngine:
    def __init__(self, groq_api_key: str | None = None):
        # Si no hay API Key, el agente funciona en modo retrieval-only
        self.api_key = groq_api_key
        self.groq = Groq(api_key=groq_api_key) if groq_api_key else None
        self.retrieval_only = not bool(groq_api_key)
        self._encoder = None
        self._index = None
        self.chunks: list[str] = []
        self.metadata: list[dict] = []

    def _get_encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer(EMBED_MODEL)
        return self._encoder

    # ── Chunk builders ────────────────────────────────────────────────

    def _siniestro_chunk(self, row: dict, scores_row: dict | None = None) -> str:
        score_info = ""
        if scores_row:
            score_info = (
                f"Score de riesgo: {scores_row.get('Score', '?')}/100 "
                f"Nivel: {scores_row.get('Nivel', '?')} "
                f"Alertas: {scores_row.get('Alertas', 'ninguna')}"
            )
        return (
            f"SINIESTRO {row.get('ID Siniestro', '')} | "
            f"Póliza {row.get('ID Póliza', '')} | Asegurado {row.get('ID Asegurado', '')} | "
            f"Ramo {row.get('Ramo', '')} | Cobertura {row.get('Cobertura', '')} | "
            f"Placa {row.get('Placa Vehículo Asegurado', '')} | "
            f"Fecha ocurrencia {row.get('Fecha Ocurrencia', '')} | "
            f"Fecha reporte {row.get('Fecha Reporte', '')} | "
            f"Días reporte {row.get('Días Ocurr→Reporte', '')} | "
            f"Monto reclamado ${row.get('Monto Reclamado ($)', '')} | "
            f"Monto estimado ${row.get('Monto Estimado ($)', '')} | "
            f"Estado {row.get('Estado', '')} | Sucursal {row.get('Sucursal', '')} | "
            f"Proveedor {row.get('ID Proveedor', '')} | "
            f"Docs completos {row.get('Docs Completos', '')} | "
            f"Prov lista restrictiva {row.get('Prov. Lista Restrictiva', '')} | "
            f"Días inicio póliza {row.get('Días desde Inicio Póliza', '')} | "
            f"Días fin póliza {row.get('Días hasta Fin Póliza', '')} | "
            f"Reclamos previos {row.get('N° Reclamos Previos Asegurado', '')} | "
            f"Suma asegurada ${row.get('Suma Asegurada ($)', '')} | "
            f"Similitud narrativa {row.get('Similitud Narrativa Máx.', '')} | "
            f"Descripción: {row.get('Descripción del Evento', '')} | "
            f"{score_info}"
        )

    def _asegurado_chunk(self, row: dict) -> str:
        return (
            f"ASEGURADO {row.get('ID Asegurado', '')} | "
            f"Nombre: {row.get('Nombres Asegurado', '')} | "
            f"Ciudad {row.get('Ciudad', '')} | Segmento {row.get('Segmento', '')} | "
            f"Antigüedad {row.get('Antigüedad (años)', '')} años | "
            f"Pólizas activas {row.get('N° Pólizas Activas', '')} | "
            f"Reclamos 12m {row.get('N° Reclamos Últimos 12 Meses', '')} | "
            f"Reclamos total {row.get('N° Reclamos Histórico Total', '')} | "
            f"Reclamos RC sin tercero {row.get('Reclamos RC sin Tercero', '')} | "
            f"Perfil riesgo {row.get('Perfil Riesgo Histórico', '')}"
        )

    def _proveedor_chunk(self, row: dict) -> str:
        return (
            f"PROVEEDOR {row.get('ID Proveedor', '')} | "
            f"Nombre: {row.get('Nombre Proveedor', '')} | "
            f"Tipo {row.get('Tipo', '')} | Ciudad {row.get('Ciudad', '')} | "
            f"Siniestros asociados {row.get('N° Siniestros Asociados', '')} | "
            f"Lista restrictiva {row.get('En Lista Restrictiva', '')} | "
            f"Motivo restricción: {row.get('Motivo Restricción', '')} | "
            f"Monto promedio ${row.get('Promedio Monto ($)', '')}"
        )

    def _pdf_chunks(self, sin_id: str, text: str, doc_type: str) -> list[str]:
        words = text.split()
        size = 200
        step = size - CHUNK_OVERLAP
        result = []
        for i in range(0, max(len(words) - size + 1, 1), step):
            chunk_words = words[i: i + size]
            result.append(f"DOCUMENTO {doc_type} (siniestro {sin_id}): {' '.join(chunk_words)}")
        return result

    # ── Index building ────────────────────────────────────────────────

    def _cache_key(self, sheets: dict, pdf_texts: dict | None) -> str:
        """Hash de los datos para invalidar caché si cambian."""
        h = hashlib.md5()
        for name in ("1_Siniestros", "3_Asegurados", "4_Proveedores"):
            df = sheets.get(name)
            if df is not None and not df.empty:
                h.update(str(df.shape).encode())
                h.update(str(df.iloc[0].to_dict()).encode())
        if pdf_texts:
            h.update(str(len(pdf_texts)).encode())
        return h.hexdigest()[:12]

    def _try_load_cache(self, key: str) -> bool:
        """Si existe el caché en disco, cargarlo. Retorna True si tuvo éxito."""
        cache_file = os.path.join(_CACHE_DIR, f"rag_{key}.pkl")
        if not os.path.exists(cache_file):
            return False
        try:
            import faiss
            with open(cache_file, "rb") as f:
                data = pickle.load(f)
            self.chunks = data["chunks"]
            self.metadata = data["metadata"]
            # FAISS index se serializa aparte
            faiss_file = os.path.join(_CACHE_DIR, f"rag_{key}.faiss")
            self._index = faiss.read_index(faiss_file)
            return True
        except Exception:
            return False

    def _save_cache(self, key: str):
        """Guarda el índice en disco para reutilizar en próximos arranques."""
        try:
            import faiss
            cache_file = os.path.join(_CACHE_DIR, f"rag_{key}.pkl")
            faiss_file = os.path.join(_CACHE_DIR, f"rag_{key}.faiss")
            with open(cache_file, "wb") as f:
                pickle.dump({"chunks": self.chunks, "metadata": self.metadata}, f)
            faiss.write_index(self._index, faiss_file)
        except Exception:
            pass

    def build_index(self, sheets: dict, pdf_texts: dict | None = None,
                    scores_df: pd.DataFrame | None = None):
        import faiss
        from src.knowledge_base import build_knowledge_chunks

        # ── 1. Intentar cargar caché en disco (instantáneo) ──────────
        cache_key = self._cache_key(sheets, pdf_texts)
        if self._try_load_cache(cache_key):
            return  # Ya estamos listos, no hace falta reconstruir

        scores_map: dict = {}
        if scores_df is not None and not scores_df.empty:
            for _, r in scores_df.iterrows():
                scores_map[r["ID Siniestro"]] = r.to_dict()

        chunks: list[str] = []
        meta: list[dict] = []

        # ── Base de Conocimiento: Reglas RF-01..RF-07 y 14 Señales ──
        for text, metadata in build_knowledge_chunks():
            chunks.append(text)
            meta.append(metadata)

        # Siniestros
        for _, row in sheets.get("1_Siniestros", pd.DataFrame()).iterrows():
            sid = row.get("ID Siniestro", "")
            text = self._siniestro_chunk(row.to_dict(), scores_map.get(sid))
            chunks.append(text)
            meta.append({"type": "siniestro", "id": sid})

        # Asegurados
        for _, row in sheets.get("3_Asegurados", pd.DataFrame()).iterrows():
            chunks.append(self._asegurado_chunk(row.to_dict()))
            meta.append({"type": "asegurado", "id": row.get("ID Asegurado", "")})

        # Proveedores
        for _, row in sheets.get("4_Proveedores", pd.DataFrame()).iterrows():
            chunks.append(self._proveedor_chunk(row.to_dict()))
            meta.append({"type": "proveedor", "id": row.get("ID Proveedor", "")})

        # PDFs
        if pdf_texts:
            for sin_id, docs in pdf_texts.items():
                for doc_type, text in docs.items():
                    if text:
                        for chunk in self._pdf_chunks(sin_id, text, doc_type):
                            chunks.append(chunk)
                            meta.append({"type": doc_type, "id": sin_id})

        enc = self._get_encoder()
        embeddings = enc.encode(chunks, show_progress_bar=False, batch_size=64)
        embeddings = embeddings.astype("float32")

        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        self.chunks = chunks
        self.metadata = meta
        self._index = index

        # ── Guardar en disco para próximos arranques ──────────────
        self._save_cache(cache_key)

    def add_document(self, text: str, sin_id: str, doc_type: str) -> bool:
        """Añade un nuevo documento cargado al índice en tiempo de ejecución si no existe."""
        # Evitar duplicados: verificar si ya existe un documento del mismo tipo para este siniestro
        if any(m.get("id") == sin_id and m.get("type") == doc_type for m in self.metadata):
            return False

        import faiss

        new_chunks = self._pdf_chunks(sin_id, text, doc_type)
        enc = self._get_encoder()
        new_embeddings = enc.encode(new_chunks, show_progress_bar=False).astype("float32")

        if self._index is None:
            dim = new_embeddings.shape[1]
            self._index = faiss.IndexFlatL2(dim)

        self._index.add(new_embeddings)
        for ch in new_chunks:
            self.chunks.append(ch)
            self.metadata.append({"type": doc_type, "id": sin_id})
        return True

    # ── Retrieval ─────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 8) -> list[dict]:
        if self._index is None or not self.chunks:
            return []
        enc = self._get_encoder()
        q_emb = enc.encode([query]).astype("float32")
        distances, indices = self._index.search(q_emb, top_k)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.chunks):
                results.append({
                    "chunk": self.chunks[idx],
                    "metadata": self.metadata[idx],
                    "distance": float(dist),
                })
        return results

    # ── Generation ────────────────────────────────────────────────────

    def _build_messages(self, question: str, chat_history: list[dict] | None):
        retrieved = self.search(question, top_k=TOP_K)
        context = "\n".join(r["chunk"] for r in retrieved)

        system_prompt = (
            "Eres FRAUDIA, un agente experto en detección de posibles fraudes en siniestros "
            "de seguros de la Aseguradora del Sur (Ecuador).\n\n"
            "TIENES ACCESO EN EL CONTEXTO A:\n"
            "1. Las 7 REGLAS CRÍTICAS de negocio (RF-01 a RF-07) con su nivel de clasificación.\n"
            "2. Las 14 SEÑALES DE FRAUDE con sus puntajes específicos (S01 a S14).\n"
            "3. La clasificación de Score: 0-40 VERDE, 41-75 AMARILLO, 76-100 ROJO.\n"
            "4. Los datos reales de 500 siniestros, asegurados, proveedores y PDFs.\n\n"
            "REGLAS ESTRICTAS:\n"
            "- Responde SIEMPRE en español, breve y estructurado.\n"
            "- Cuando expliques POR QUÉ un siniestro tiene cierto nivel, CITA la regla "
            "  (ej: 'por RF-01 Cobertura Pérdida Total por Robo') o la señal (ej: 'S13 Narrativa Similar +8 pts').\n"
            "- Fundamenta tu respuesta SOLO en el contexto recuperado.\n"
            "- NUNCA inventes siniestros, montos ni nombres.\n"
            "- Usa lenguaje de 'posible irregularidad' o 'requiere revisión' — NUNCA acuses formalmente.\n"
            "- Cuando menciones un siniestro, incluye su ID (SIN-XXXX).\n"
            "- Si te preguntan por reglas o señales, explica usando el conocimiento del contexto.\n"
            "- Usa listas con viñetas cuando ayude a la claridad.\n"
        )
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for turn in chat_history[-4:]:
                messages.append(turn)
        messages.append({
            "role": "user",
            "content": f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}",
        })
        return messages

    def answer(self, question: str, chat_history: list[dict] | None = None) -> str:
        """Respuesta no-streaming (fallback). Llama a Groq y devuelve texto completo."""
        messages = self._build_messages(question, chat_history)
        response = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=0.15,
        )
        return response.choices[0].message.content

    def answer_stream(self, question: str, chat_history: list[dict] | None = None):
        """Generador que va emitiendo tokens. El usuario ve la respuesta aparecer en tiempo real."""
        # Modo RETRIEVAL-ONLY: sin API Key, solo recupera y formatea los chunks
        if self.retrieval_only or self.groq is None:
            yield from self._retrieval_only_answer(question)
            return

        # Modo completo: RAG + Groq LLM
        messages = self._build_messages(question, chat_history)
        try:
            stream = self.groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=0.15,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            # Fallback: si Groq falla, usar retrieval-only
            yield f"⚠️ No se pudo conectar con Groq ({e}). Usando modo retrieval-only:\n\n"
            yield from self._retrieval_only_answer(question)

    def _retrieval_only_answer(self, question: str):
        """Sin LLM: recupera chunks relevantes y los formatea como respuesta."""
        retrieved = self.search(question, top_k=TOP_K)
        if not retrieved:
            yield "No se encontró información relevante en el dataset para tu pregunta.\n"
            return

        yield "📚 **Resultados encontrados en el dataset** (modo retrieval-only, sin LLM):\n\n"
        for i, r in enumerate(retrieved, 1):
            meta = r.get("metadata", {})
            mtype = meta.get("type", "desconocido")
            mid   = meta.get("id", "")
            # Etiqueta del tipo
            label = {
                "siniestro": "📋 Siniestro",
                "asegurado": "👤 Asegurado",
                "proveedor": "🏢 Proveedor",
                "knowledge": "📖 Conocimiento",
                "FACTURA": "🧾 Factura",
                "PARTE_POLICIAL": "📋 Parte Policial",
                "DECLARACION": "📝 Declaración",
            }.get(mtype, f"📄 {mtype}")

            yield f"**{i}. {label} — {mid}**\n"
            chunk_text = r["chunk"]
            # Mostrar primeros 350 caracteres
            preview = chunk_text[:350] + ("…" if len(chunk_text) > 350 else "")
            yield f"> {preview}\n\n"

        yield (
            "\n💡 *Para respuestas naturales (con redacción), pega tu Groq API Key "
            "en el panel lateral. Es gratis en console.groq.com.*"
        )
