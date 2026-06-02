import streamlit as st
import uuid
import os
from pathlib import Path

# Cargar variables de entorno antes de importar componentes del agente
from dotenv import load_dotenv
load_dotenv()

from app.agent.agent_service import ask_agent
from app.api.schemas import ChatRequest
from app.core.conversation_logger import log_conversation

# Configuración de página con estética premium
st.set_page_config(
    page_title="Asistente Corporativo TQ - Panel de Pruebas",
    page_icon="🤖",
    layout="centered",
)

# Estilos CSS personalizados para alinear con la identidad de TQ (Azul y Verde)
st.markdown(
    """
    <style>
        .main {
            background-color: #f9fbfd;
        }
        h1 {
            color: #0b3c5d;
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
        }
        .stButton>button {
            background-color: #328cc1;
            color: white;
            border-radius: 8px;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #0b3c5d;
            color: white;
            transform: scale(1.02);
        }
        .sidebar .sidebar-content {
            background-color: #0b3c5d;
        }
        .stChatInput {
            border-radius: 12px;
        }
        .tool-tag {
            background-color: #e2f0d9;
            color: #385723;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-right: 5px;
            margin-top: 5px;
            border: 1px solid #c5e0b4;
        }
        .header-container {
            display: flex;
            align-items: center;
            border-bottom: 2px solid #328cc1;
            padding-bottom: 10px;
            margin-bottom: 25px;
        }
        .header-title {
            margin-left: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cabecera Corporativa
st.markdown(
    """
    <div class="header-container">
        <span style="font-size: 2.5rem;">🏢</span>
        <div class="header-title">
            <h1 style="margin: 0; padding: 0;">Asistente Corporativo TQ</h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar (Configuración e Información del Hilo de Conversación)
with st.sidebar:
    st.markdown("### ⚙️ Configuración del Test")
    
    # ID de Usuario para simulación
    user_id = st.text_input(
        "ID del Usuario (user_id)",
        value="tester_local",
        help="Identificador del usuario para auditoría de conversaciones.",
    )

    # Entrada de API Key (opcional, si no está en las variables de entorno)
    google_api_key = st.text_input(
        "Google API Key (Opcional)",
        type="password",
        value=os.getenv("GOOGLE_API_KEY", ""),
        help="Clave de API de Google AI Studio. Si no se provee, la app usará la definida en los Secrets de la nube o en el archivo .env local.",
    )
    
    # Generar Thread ID inicial si no existe en la sesión
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())[:8]

    # Entrada de Thread ID (permite continuar hilos previos)
    thread_id = st.text_input(
        "ID del Hilo (thread_id)",
        value=st.session_state.thread_id,
        help="ID del hilo de conversación. Permite al agente recordar el contexto anterior de esta sesión.",
    )
    
    # Botón para refrescar/iniciar un nuevo hilo
    if st.button("🔄 Generar Nuevo Hilo (Limpiar Memoria)"):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Observabilidad")
    st.info(
        "Este panel de pruebas ejecuta directamente la lógica del **agente de producción** "
        "(`app.agent.agent_service`) y replica con total fidelidad el comportamiento de la API REST, "
        "incluyendo el RAG, las herramientas deterministas y el registro de logs."
    )
    
    # Indicar dónde se guardan los logs
    st.markdown(
        f"📂 **Logs locales:** \n`logs/conversations.jsonl`"
    )

# Inicializar historial de chat en session_state si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial de chat guardado
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Si se usaron herramientas en este mensaje del asistente, mostrarlas de forma elegante
        if msg["role"] == "assistant" and msg.get("tools"):
            tools_html = "".join([f'<span class="tool-tag">🛠️ {t}</span>' for t in msg["tools"]])
            st.markdown(f"**Ruta del Agente:** {tools_html}", unsafe_allow_html=True)

# Entrada de texto del usuario
if user_query := st.chat_input("Escribe tu pregunta sobre Tecnoquímicas (e.g. NIT, productos, políticas)..."):
    
    # 1. Agregar y mostrar mensaje del usuario en la UI
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Generar respuesta llamando al servicio del agente
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        with st.spinner("El asistente de TQ está consultando la información..."):
            # Construir payload idéntico a la API
            payload = ChatRequest(
                user_id=user_id,
                thread_id=thread_id,
                message=user_query,
                api_key=google_api_key if google_api_key else None,
            )
            
            # Ejecutar lógica del agente
            response, tools_used = ask_agent(payload)
            
            # Registrar conversación en logs/conversations.jsonl de la misma forma que la API
            log_conversation(
                user_id=user_id,
                message=user_query,
                response=response,
                status="ok",
                tools_used=tools_used,
            )
            
        # Renderizar la respuesta del asistente
        response_placeholder.markdown(response)
        
        # Renderizar de forma elegante las herramientas empleadas si el agente usó alguna
        if tools_used:
            tools_html = "".join([f'<span class="tool-tag">🛠️ {t}</span>' for t in tools_used])
            st.markdown(f"**Ruta del Agente:** {tools_html}", unsafe_allow_html=True)
            
    # Guardar la respuesta en el estado de la sesión
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response,
        "tools": tools_used
    })
