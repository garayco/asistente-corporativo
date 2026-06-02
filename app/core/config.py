"""
Configuración centralizada para el proyecto TQ Corporativo.

Este archivo centraliza las rutas, conexiones a LocalAI y Qdrant,
y parámetros del modelo para que sean consistentes en todo el proyecto.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────  Paths  ──────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_CHUNKED_PATH = PROJECT_DIR / "scraping" / "output" / "dataset_chunked.json"
PROMPT_FILE_PATH = PROJECT_DIR / "scraping" / "output" / "tq_system_prompt.md"

# ──────────────────────────  LocalAI (LLM & Embeddings)  ──────────────────────────
LOCALAI_BASE_URL = os.getenv("LOCALAI_BASE_URL", "http://localhost:8080/v1")
LOCALAI_API_KEY  = os.getenv("LOCALAI_API_KEY", "")
GEMINI_API_KEY   = os.getenv("GOOGLE_API_KEY", "")

# LLM Config (usado por el chatbot)
CHAT_MODEL = os.getenv("LOCALAI_MODEL", "gemma-3-12b-it-UD-IQ2_XXS.gguf")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemma-4-26b-a4b-it")

# Embedding Config (usado por el pipeline RAG)
EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL", "bge-m3:567m")
EMBEDDING_DIM    = int(os.getenv("EMBEDDING_DIM", "1024"))

# ──────────────────────────  Qdrant  ──────────────────────────
QDRANT_URL            = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY        = os.getenv("QDRANT_API_KEY", None)
QDRANT_COLLECTION     = os.getenv("QDRANT_COLLECTION", "tq_corporativo")
QDRANT_DISTANCE       = "Cosine"   # Cosine | Euclid | Dot

# ──────────────────────────  Batching / Performance  ──────────────────────────
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))
MAX_HISTORY_MESSAGES = 8
