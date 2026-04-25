import logging
import os
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


PROJECT_DIR = Path(__file__).resolve().parent
PROMPT_FILE_PATH = PROJECT_DIR / "scraping" / "output" / "tq_system_prompt.md"
DEFAULT_BASE_URL = os.getenv("LOCALAI_BASE_URL", "http://localhost:8080/v1/")
DEFAULT_API_KEY = os.getenv("LOCALAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("LOCALAI_MODEL", "gemma-3-12b-it-Q4_K_M.gguf")
MAX_HISTORY_MESSAGES = 8


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


@st.cache_data(show_spinner=False)
def load_system_prompt(path: str) -> str:
    """Carga el system prompt desde el archivo markdown (ya incluye la base de conocimientos)."""
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de prompting: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def build_messages(chat_history: list[dict[str, str]]) -> list[dict[str, str]]:
    """Construye los mensajes cargando el system prompt desde el archivo .md."""
    system_prompt = load_system_prompt(str(PROMPT_FILE_PATH))
    
    # Filtrar mensajes para asegurar alternancia user/assistant
    filtered_history = []
    prev_role = None
    
    for msg in chat_history:
        role = msg.get("role")
        content = msg.get("content", "").strip()
        
        # Saltar mensajes vacíos o del rol system (ya tenemos el nuestro)
        if not content or role == "system":
            continue
        
        # Si es el mismo rol que el anterior, saltarlo
        if role == prev_role:
            logging.warning(f"Saltando mensaje duplicado: {role}")
            continue
        
        filtered_history.append(msg)
        prev_role = role
    
    recent_history = filtered_history[-MAX_HISTORY_MESSAGES:]

    if recent_history and recent_history[0]["role"] == "assistant":
        recent_history.pop(0)
        logging.info("Se eliminó un mensaje de assistant al inicio para mantener la alternancia.")

    logging.info(f"Mensajes enviados: {[m['role'] for m in recent_history]}")

    return [{"role": "system", "content": system_prompt}] + recent_history


def stream_localai_response(
    base_url: str,
    api_key: str,
    model_name: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
):
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
        base_url=base_url,
        streaming=True,
        model_kwargs={"stream_options": {"include_usage": True}}
    )
    logging.info("Enviando completación a LocalAI (modelo: %s)...", model_name)
    start_time = time.time()

    # Convert dict messages to Langchain messages
    lc_messages = []
    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "system":
            lc_messages.append(SystemMessage(content=content))
        elif role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))

    for chunk in llm.stream(lc_messages):
        if chunk.content:
            yield {"type": "token", "content": chunk.content}

        # Check if usage metadata is available in LangChain chunks
        usage = getattr(chunk, "usage_metadata", None)
        if usage and usage.get("total_tokens", 0) > 0:
            usage_dict = {
                "prompt_tokens": usage.get("input_tokens"),
                "completion_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
            }
            yield {"type": "usage", "content": usage_dict}

    logging.info("Respuesta recibida en %.2f segundos.", time.time() - start_time)


def format_chat_for_export(messages: list[dict[str, str]]) -> str:
    """Convierte el historial de mensajes en texto estructurado tipo Markdown."""
    lines = []
    lines.append("# Historial de Conversación - Asistente Corporativo TQ")
    lines.append(f"*Fecha de exportación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    lines.append("---\n")
    
    for msg in messages:
        role = "**Usuario:**" if msg["role"] == "user" else " **Asistente:**"
        content = msg.get("content", "")
        lines.append(f"{role}\n{content}\n")
        lines.append("---\n")
        
    return "\n".join(lines)


def main() -> None:
    st.set_page_config(
        page_title="Asistente Corporativo TQ",
        layout="wide",
    )

    st.title("Asistente Corporativo Grupo Empresarial Tecnoquímicas")

    # Limpiar historial si tiene mensajes duplicados o mal formados
    if "messages" in st.session_state:
        cleaned = []
        prev_role = None
        for msg in st.session_state.get("messages", []):
            role = msg.get("role")
            content = msg.get("content", "").strip()
            if not content or role == prev_role:
                continue
            cleaned.append(msg)
            prev_role = role
        st.session_state.messages = cleaned

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("Configuración")
        base_url = st.text_input("LocalAI base URL", value=DEFAULT_BASE_URL)
        api_key = st.text_input("API key", value=DEFAULT_API_KEY, type="password")
        model_name = st.text_input("Modelo", value=DEFAULT_MODEL)
        temperature = st.slider("Temperatura", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
        max_tokens = st.number_input("Máximo de tokens de salida", min_value=128, max_value=8192, value=2048, step=128)

        st.divider()
        st.caption(f"Prompt: `{PROMPT_FILE_PATH}`")
        
        # Botones de acción del chat
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Limpiar chat"):
                st.session_state.messages = []
                st.rerun()
                
        with col2:
            # Solo mostrar botón de exportación si hay mensajes
            if st.session_state.messages:
                export_text = format_chat_for_export(st.session_state.messages)
                st.download_button(
                    label="Exportar MD",
                    data=export_text,
                    file_name=f"chat_tq_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown"
                )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("usage"):
                st.caption(message["usage"])

    user_question = st.chat_input("Escribe una pregunta sobre Grupo Empresarial Tecnoquímicas")
    if not user_question:
        return

    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    messages = build_messages(st.session_state.messages)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        usage_placeholder = st.empty()
        full_response = ""
        final_usage_text = ""

        try:
            with st.spinner(""):
                for item in stream_localai_response(
                    base_url=base_url,
                    api_key=api_key,
                    model_name=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=int(max_tokens),
                ):
                    if not isinstance(item, dict):
                        # Fallback for unexpected string items
                        full_response += str(item)
                        response_placeholder.markdown(full_response)
                        continue

                    if item.get("type") == "token":
                        full_response += item.get("content", "")
                        response_placeholder.markdown(full_response)
                    elif item.get("type") == "usage":
                        u = item.get("content", {})
                        final_usage_text = f"Tokens — prompt: {u.get('prompt_tokens')}, completion: {u.get('completion_tokens')}, total: {u.get('total_tokens')}"
                        usage_placeholder.caption(final_usage_text)
        except Exception as error:
            logging.exception("Error consultando LocalAI")
            full_response = f"Error consultando LocalAI: {error}"
            response_placeholder.error(full_response)

    # Solo guardar si hay contenido real
    if full_response and not full_response.startswith("Error consultando LocalAI"):
        msg_to_save = {"role": "assistant", "content": full_response}
        if final_usage_text:
            msg_to_save["usage"] = final_usage_text
        st.session_state.messages.append(msg_to_save)
        # Forzar un rerun para que el botón de descarga se actualice con el nuevo mensaje
        st.rerun()

if __name__ == "__main__":
    main()