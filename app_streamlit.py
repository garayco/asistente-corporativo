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
    st.markdown("### 🗺️ Navegación")
    app_mode = st.radio(
        "Seleccione la vista:",
        ["💬 Chat de Pruebas", "📊 Monitor"],
        index=0
    )
    st.markdown("---")
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

# Función auxiliar para leer archivos JSONL de forma segura
def read_jsonl(filepath):
    path = Path(filepath)
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line.strip()))
                except Exception:
                    pass
    return records

if app_mode == "💬 Chat de Pruebas":
    # Inicializar historial de chat en session_state si no existe
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar el historial de chat guardado
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

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
                
        # Guardar la respuesta en el estado de la sesión
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "tools": tools_used
        })

else:
    # VISTA: Monitor
    st.markdown("## 📊 Monitor de Observabilidad y Auditoría en Vivo")
    st.markdown(
        "Esta vista permite analizar en tiempo real el comportamiento técnico del agente, "
        "mostrando el uso de herramientas, leads capturados y escalamientos de chat."
    )

    # 1. Cargar datos
    import json
    conversations = read_jsonl("logs/conversations.jsonl")
    leads = read_jsonl("logs/leads.jsonl")
    escalations = read_jsonl("logs/escalations.jsonl")

    # 2. Computar Métricas Clave
    total_msgs = len(conversations)
    unique_threads = len(set(c.get("thread_id") or c.get("user_id") for c in conversations))
    
    # Contar herramientas utilizadas
    rag_calls = 0
    db_calls = 0
    leads_calls = 0
    escalations_calls = 0
    
    for c in conversations:
        for tool in c.get("tools_used", []):
            if "buscar_base" in tool:
                rag_calls += 1
            elif "consultar_datos" in tool:
                db_calls += 1
            elif "registrar_lead" in tool:
                leads_calls += 1
            elif "escalar" in tool:
                escalations_calls += 1

    # Fila de métricas principales
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Total Mensajes", total_msgs)
    with m_col2:
        st.metric("Hilos de Chat Únicos", unique_threads)
    with m_col3:
        st.metric("Leads Registrados", len(leads))
    with m_col4:
        st.metric("Escalamientos a Humano", len(escalations))

    # Fila de herramientas
    st.markdown("### ⚙️ Uso de Herramientas (Enrutamiento del Agente)")
    h_col1, h_col2, h_col3, h_col4 = st.columns(4)
    with h_col1:
        st.info(f"📚 **RAG (Docs):** {rag_calls}")
    with h_col2:
        st.success(f"🗃️ **Base de Datos (JSON):** {db_calls}")
    with h_col3:
        st.warning(f"📝 **Registros de Lead:** {leads_calls}")
    with h_col4:
        st.error(f"👤 **Escalamiento Humano:** {escalations_calls}")

    # Tabs para ver detalles
    tab_logs, tab_leads, tab_escalations = st.tabs([
        "📜 Historial de Chats (Últimos)", 
        "📝 Leads Recientes", 
        "🚨 Solicitudes de Escalamiento"
    ])

    with tab_logs:
        st.markdown("#### Historial Reciente (Log de Auditoría)")
        if not conversations:
            st.info("No hay logs conversacionales registrados aún.")
        else:
            # Mostrar los últimos 15 mensajes primero
            for c in reversed(conversations[-15:]):
                time_str = c.get("timestamp", "N/A")
                user = c.get("user_id", "N/A")
                msg_txt = c.get("message", "")
                resp_txt = c.get("response", "")
                tools = c.get("tools_used", [])

                with st.expander(f"🕒 {time_str} | Usuario: {user} | Pregunta: '{msg_txt[:40]}...'"):
                    st.write(f"**Usuario:** {msg_txt}")
                    
                    # Mostrar herramientas usadas de forma llamativa
                    if tools:
                        st.markdown("**Herramientas Invocadas por el Agente:**")
                        tools_html = "".join([f'<span class="tool-tag">🛠️ {t}</span>' for t in tools])
                        st.markdown(tools_html, unsafe_allow_html=True)
                    else:
                        st.markdown("*El agente respondió sin invocar herramientas (Respuesta Directa).*")
                    
                    st.write(f"**Respuesta del Agente:** {resp_txt}")

    with tab_leads:
        st.markdown("#### Clientes Potenciales Registrados (Leads)")
        if not leads:
            st.info("No se han registrado leads todavía.")
        else:
            for l in reversed(leads):
                st.markdown(
                    f"👤 **Nombre:** {l.get('nombre')} | 📱 **Teléfono:** {l.get('telefono')} | "
                    f"🎯 **Interés:** {l.get('interes')} | 🕒 {l.get('timestamp')}"
                )
                st.markdown("---")

    with tab_escalations:
        st.markdown("#### Solicitudes de Intervención Humana")
        if not escalations:
            st.info("No hay solicitudes de escalamiento activas.")
        else:
            for e in reversed(escalations):
                prio_color = "🔴" if e.get("prioridad") == "alta" else "🟡"
                st.markdown(
                    f"{prio_color} **Prioridad:** {e.get('prioridad').upper()} | "
                    f"📱 **Teléfono:** {e.get('telefono')} | 📝 **Motivo:** {e.get('motivo')} | "
                    f"🕒 {e.get('timestamp')}"
                )
                st.markdown("---")


