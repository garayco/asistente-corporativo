import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from streamlit.runtime.scriptrunner import get_script_run_ctx
from agent import agent_executor
from config import (
    LOCALAI_BASE_URL as DEFAULT_BASE_URL,
    LOCALAI_API_KEY as DEFAULT_API_KEY,
    CHAT_MODEL as DEFAULT_MODEL,
    GEMINI_API_KEY as DEFAULT_GEMINI_KEY,
    GEMINI_MODEL as DEFAULT_GEMINI_MODEL
)

def display_tokens(msg: AIMessage):
    """
    Extrae y muestra los metadatos de consumo de tokens en la interfaz.
    
    Args:
        msg (AIMessage): Mensaje del asistente que contiene usage_metadata.
    """
    usage = getattr(msg, "usage_metadata", None)
    if usage:
        i = usage.get("input_tokens", 0)
        o = usage.get("output_tokens", 0)
        t = usage.get("total_tokens", i + o)
        st.caption(f"**Tokens:** {i} (in) | {o} (out) | **{t} total**")

def get_message_text(msg) -> str:
    """Extrae el contenido de texto limpio de un mensaje, manejando listas"""
    if isinstance(msg.content, list):
        return "".join([c.get("text", "") for c in msg.content if isinstance(c, dict) and c.get("type") == "text"])
    return msg.content

st.set_page_config(page_title="Asistente Corporativo TQ", layout="wide")
st.title("Asistente Corporativo Grupo Empresarial Tecnoquímicas")

# 1. Gestión de Sesión y Persistencia
ctx = get_script_run_ctx()
thread_id = ctx.session_id if ctx else "default"

# 2. Barra Lateral (Parámetros de Configuración)
debug_mode = False
with st.sidebar:
    st.header("Configuración")
    
    provider = st.radio("Proveedor LLM", ["LocalAI", "Google AI Studio"])
    
    if provider == "Google AI Studio":
        api_key = st.text_input("Google API Key", value=DEFAULT_GEMINI_KEY, type="password", help="Tu API Key de Google AI Studio")
        model_name = st.text_input("Modelo", value=DEFAULT_GEMINI_MODEL)
        base_url = ""
    else:
        base_url = st.text_input("LocalAI base URL", value=DEFAULT_BASE_URL)
        api_key = st.text_input("API key (Opcional)", value=DEFAULT_API_KEY, type="password")
        model_name = st.text_input("Modelo", value=DEFAULT_MODEL)
        
    temp = st.slider("Temperatura", 0.0, 1.0, 0.1)
    max_tokens = st.number_input("Máximo tokens", 128, 4096, 2048)
    
    # Toggle para visualización de razonamiento interno
    debug_mode = st.toggle("Modo Debug", value=True)
    
    if st.button("Limpiar Chat"):
        st.session_state.clear()
        st.rerun()

# 3. Preparación del Workflow de LangGraph
workflow_config = {
    "configurable": {
        "thread_id": thread_id,
        "provider": provider,
        "model": model_name,
        "temperature": temp,
        "base_url": base_url,
        "api_key": api_key,
        "max_tokens": int(max_tokens)
    }
}

# 4. Renderizado del Historial de Conversación
state = agent_executor.get_state(workflow_config)
messages = state.values.get("messages", []) if state.values else []

for msg in messages:
    if isinstance(msg, (HumanMessage, AIMessage)):
        role = "human" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.write(get_message_text(msg))
            display_tokens(msg)

# 5. Interacción del Usuario y Ejecución del Agente
prompt = st.chat_input("¿Qué deseas saber sobre TQ?", key="chat_input")
if prompt:
    st.chat_message("human").write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Procesando consulta..."):
            # Invocación al agente con el mensaje actual
            response = agent_executor.invoke(
                {"messages": [HumanMessage(content=prompt)]}, 
                config=workflow_config
            )
        
        # Visualización de pensamientos (opcional vía debug_mode)
        if debug_mode:
            with st.expander("🧠 Debug Mode"):
                st.info(f"**Decisión del Enrutador:** {response.get('route_decision', 'N/A')}")
                st.write("**Contexto recuperado:**")
                st.code(response.get('data_context', 'No se recuperó contexto.'), language="markdown")
                if response.get("data_found") is not None:
                    st.write(f"**¿Datos encontrados en JSON?:** {response.get('data_found')}")

        # Renderizado de la respuesta final y estadísticas
        last_msg = response["messages"][-1]
        st.write(get_message_text(last_msg))
        display_tokens(last_msg)