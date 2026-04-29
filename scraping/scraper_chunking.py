import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "output" / "dataset.json"
OUTPUT_FILE = BASE_DIR / "output" / "dataset_chunked.json"

NOISE_PATTERNS = [
    "usted esta siendo redirigido",
    "portal de pagos exclusivo",
    "sitio web externo y ajeno",
    "haga clic en aceptar",
]

CHUNK_SIZE = 1200


def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def is_relevant(text):
    text_lower = text.lower()
    for pattern in NOISE_PATTERNS:
        if pattern in text_lower:
            return False
    return True


def split_text(text, chunk_size=CHUNK_SIZE):
    """Fast text splitter using paragraph boundaries and recursive fallback for long blocks."""
    if len(text) <= chunk_size:
        return [text] if len(text) > 100 else []
    
    # Split by paragraphs first
    paragraphs = re.split(r'\n\n+', text)
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If single paragraph exceeds chunk_size, split it further using multi-level fallback
        if len(para) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Level 1: Split by sentences
            parts = re.split(r'(?<=[.!?])\s+', para)
            
            # Level 2 & 3: Semicolons and Commas for parts that are still too long
            refined_parts = []
            for p in parts:
                if len(p) > chunk_size:
                    # Try semicolons
                    sub_p = re.split(r'(?<=;)\s+', p)
                    for item in sub_p:
                        if len(item) > chunk_size:
                            # Last resort: Try commas
                            refined_parts.extend(re.split(r'(?<=,)\s+', item))
                        else:
                            refined_parts.append(item)
                else:
                    refined_parts.append(p)
            
            # Recombine refined parts into manageable chunks
            temp_chunk = ""
            for part in refined_parts:
                if len(temp_chunk) + len(part) + 1 > chunk_size:
                    if temp_chunk:
                        chunks.append(temp_chunk)
                    temp_chunk = part
                else:
                    temp_chunk = (temp_chunk + " " + part).strip() if temp_chunk else part
            
            if temp_chunk:
                chunks.append(temp_chunk)
        
        # Normal paragraph handling
        elif len(current_chunk) + len(para) + 2 > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para
        else:
            current_chunk = (current_chunk + "\n\n" + para).strip() if current_chunk else para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return [c for c in chunks if len(c) > 100]


def infer_topic(url):
    """Extrae el topic de la URL: 2 segmentos para secciones, 1 para noticias."""
    from urllib.parse import urlparse, unquote
    
    try:
        path = urlparse(url).path
        segments = [unquote(s) for s in path.strip("/").split("/") if s]
        
        if not segments:
            return "root"
        
        # Si es noticias, solo 1 segmento (cada noticia es única)
        if segments[0] == "noticias":
            return segments[0]
        
        # Para demás secciones, hasta 2 segmentos
        return "/".join(segments[:2])
    except:
        pass
    
    return "root"


def process_documents(documents):
    all_chunks = []
    
    for doc in documents:
        url = doc.get("url", "")
        content = doc.get("contenido", "")
        
        if not content or not is_relevant(content):
            continue
        
        content = clean_text(content)
        if len(content) < 100:
            continue
        
        chunks = split_text(content)
        if not chunks:
            continue
        
        for idx, chunk_text in enumerate(chunks, start=1):
            all_chunks.append({
                "source_url": url,
                "topic": infer_topic(url),
                "contenido": chunk_text,
            })
    
    return all_chunks


def main():
    print(f"Leyendo dataset desde: {INPUT_FILE}")
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    print(f"Documentos leídos: {len(documents)}")
    
    chunks = process_documents(documents)
    print(f"Chunks generados: {len(chunks)}")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    print(f"Guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
