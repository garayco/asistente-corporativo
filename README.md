# Asistente Corporativo TQ

> **Inteligencia Artificial Especializada para el Grupo Empresarial Tecnoquímicas (TQ)**

Este proyecto es una solución integral de **IA Generativa (GenAI)** diseñada para actuar como el Asistente Corporativo oficial de **Tecnoquímicas**. Utiliza una arquitectura avanzada de **RAG (Retrieval-Augmented Generation)** alimentada por una base de conocimientos extraída y estructurada automáticamente desde fuentes oficiales.

---

## Características Principales

*   **Pipeline de Extracción Inteligente:** Sistema de scraping automatizado que recorre sitios corporativos, extrae contenido relevante y lo limpia para su procesamiento.
*   **Estructuración Semántica:** Utiliza modelos de lenguaje avanzados (Gemini/Gemma) para transformar datos crudos en una base de conocimientos estructurada y jerárquica.
*   **Chat Multimotor:** Interfaz interactiva construida en **Streamlit** que permite alternar entre:
    *   **LocalAI:** Ejecución privada y local de modelos (Gemma, etc.) garantizando privacidad de datos.
    *   **Google Gemini:** Potencia y velocidad utilizando las últimas APIs de Google.
*   **Control Total de Contexto:** Sistema de prompts blindado con reglas estrictas de seguridad y fidelidad para evitar alucinaciones y filtraciones de configuración.
*   **Auditoría de Tokens:** Seguimiento en tiempo real del consumo de tokens y métricas de rendimiento de inferencia.

---

## Arquitectura del Sistema

El proyecto se divide en dos fases críticas:

### 1. Preparación de la Base de Conocimientos (Scraping & Processing)
Localizado en la carpeta `/scraping`, este pipeline realiza:
1.  **Extracción de URLs:** Identifica páginas clave del dominio corporativo.
2.  **Scraping de Contenido:** Captura texto limpio omitiendo ruido visual (menús, pies de página).
3.  **Chunking:** Divide la información en fragmentos manejables conservando el contexto.
4.  **Síntesis de IA:** Un "Arquitecto de Datos Semánticos" (LLM) procesa los fragmentos para crear un archivo `tq_system_prompt.md` que contiene toda la sabiduría corporativa estructurada.

### 2. Interfaz de Usuario (Inferencia)
El archivo `chat_tq_localai.py` levanta una aplicación Streamlit que:
- Carga dinámicamente la base de conocimientos más reciente.
- Gestiona el historial de conversación con alternancia inteligente de roles.
- Permite la exportación del historial en formato Markdown.

---

## Instalación y Configuración

### Requisitos Previos
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Recomendado para gestión de dependencias)

### Configuración del Entorno
1. Clonar el repositorio.
2. Crear un archivo `.env` en la raíz con las siguientes variables:
   ```env
   LOCALAI_BASE_URL=http://localhost:8080/v1/
   LOCALAI_API_KEY=tu_api_key_opcional
   LOCALAI_MODEL=gemma-3-12b-it-Q4_K_M.gguf
   GEMINI_API_KEY=tu_google_api_key
   ```
3. Instalar dependencias:
   ```bash
   uv sync
   ```

---

## Modo de Uso

### 1. Generar/Actualizar Base de Conocimientos
Si deseas actualizar la información que conoce el asistente:
```bash
python scraping/scraper_url_extractor.py
python scraping/scraper_trafilatura.py
python scraping/scraper_chunking.py
python scraping/scraper_markdown_summary.py
```

### 2. Iniciar el Asistente
Para abrir la interfaz de chat:
```bash
streamlit run chat_tq_localai.py
```

---

## Estructura del Proyecto

```text
.
├── chat_tq_localai.py       # Aplicación principal (Streamlit)
├── scraping/                # Pipeline de datos
│   ├── scraper_url_extractor.py
│   ├── scraper_trafilatura.py
│   ├── scraper_chunking.py
│   ├── scraper_markdown_summary.py # Generador de Base de Conocimientos
│   └── output/              # Datos procesados y System Prompt
├── pyproject.toml           # Configuración de dependencias
└── .env                     # Variables de entorno
```

---

## Seguridad y Fidelidad
El asistente está configurado bajo el principio de **"Cero Alucinaciones"**. Si una consulta no puede ser respondida con la información contenida en el `<base_conocimiento>`, el modelo declinará educadamente la respuesta en lugar de inventar datos, manteniendo la integridad de la marca **Tecnoquímicas**.

---
*Desarrollado para la Maestría en IA - Proyecto TAAML*
