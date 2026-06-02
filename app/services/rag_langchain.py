import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(override=True)

BASE_KNOWLEDGE_PATH = Path("data/base_conocimiento.md")

_vector_store = None


def _load_base_knowledge() -> str:
    if not BASE_KNOWLEDGE_PATH.exists():
        return ""

    return BASE_KNOWLEDGE_PATH.read_text(encoding="utf-8")


def _build_documents() -> List[Document]:
    text = _load_base_knowledge()

    if not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    chunks = splitter.split_text(text)

    return [
        Document(
            page_content=chunk,
            metadata={"source": str(BASE_KNOWLEDGE_PATH), "chunk": i},
        )
        for i, chunk in enumerate(chunks)
    ]


def get_vector_store():
    global _vector_store

    if _vector_store is not None:
        return _vector_store

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("Falta GOOGLE_API_KEY en el archivo .env")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=os.getenv("GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001"),
        google_api_key=api_key,
    )

    documents = _build_documents()

    if not documents:
        _vector_store = InMemoryVectorStore(embeddings)
        return _vector_store

    _vector_store = InMemoryVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
    )

    return _vector_store


def search_knowledge_base(query: str, k: int = 4) -> str:
    vector_store = get_vector_store()

    docs = vector_store.similarity_search(query, k=k)

    if not docs:
        return "No se encontró información documental relevante en la base de conocimiento."

    return "\n\n---\n\n".join(
        f"Fuente: {doc.metadata.get('source', 'base_conocimiento')}\n{doc.page_content}"
        for doc in docs
    )