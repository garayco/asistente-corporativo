import trafilatura
import json
import time

def extraer_contenido(urls):
    dataset = []
    for url in urls:
        print(f"Procesando: {url}")
        try:
            descargado = trafilatura.fetch_url(url)
            if descargado:
                texto = trafilatura.extract(descargado, include_tables=True, include_comments=False)
                if texto:
                    dataset.append({
                        "url": url,
                        "contenido": texto
                    })
        except Exception as e:
            print(f"Error procesando {url}: {e}")
        
        # Delay para evitar bloqueos
        time.sleep(1)
    return dataset

# Cargar URLs del archivo
with open("output/extracted_urls.txt", "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

# Extraer contenido
datos_extraidos = extraer_contenido(urls)

# Guardar en JSON
with open("output/dataset.json", "w", encoding="utf-8") as f:
    json.dump(datos_extraidos, f, ensure_ascii=False, indent=4)

print(f"Procesadas {len(datos_extraidos)} páginas. Datos guardados en output/dataset.json")