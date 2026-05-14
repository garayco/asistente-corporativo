import logging
import json
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from config import LOCALAI_BASE_URL, LOCALAI_API_KEY, CHAT_MODEL
from prompts.router import ROUTER_SYSTEM_PROMPT
from prompts.assistant import ASSISTANT_PROMPT_TEMPLATE

from data_retriever import get_corporate_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    route_decision: str
    data_context: str
    final_response: str
    data_found: bool

def get_llm(config: RunnableConfig, temperature: float = 0.0):
    """
    Función auxiliar para instanciar el LLM según la configuración enviada desde la interfaz.
    """
    params = config.get("configurable", {})
    provider = params.get("provider", "LocalAI")
    
    if provider == "Google AI Studio":
        api_key = params.get("api_key", "")
        model = params.get("model", "gemma-4-26b-a4b-it")
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
            max_tokens=params.get("max_tokens", 2048)
        )
    else:
        # Fallback a LocalAI / OpenAI
        return ChatOpenAI(
            model=params.get("model", CHAT_MODEL),
            temperature=temperature,
            api_key=params.get("api_key", LOCALAI_API_KEY),
            base_url=params.get("base_url", LOCALAI_BASE_URL),
            max_tokens=params.get("max_tokens", 2048)
        )


def get_rag_context() -> str:
    """
    Recupera el contenido completo de la base de conocimiento documental (Markdown).
    
    Returns:
        str: Contenido del archivo de conocimiento.
    """
    print("🛠️ EJECUTANDO: Recuperando información de base_conocimiento.md...")
    with open("data/base_conocimiento.md", "r", encoding="utf-8") as f:
        return f.read()

def execute_rag_node(state: AgentState) -> dict:
    """
    Nodo encargado de ejecutar la recuperación vía RAG (documental).
    
    Args:
        state (AgentState): Estado actual del agente.
        
    Returns:
        dict: Actualización del estado con el contexto recuperado.
    """
    rag_data = get_rag_context()
    return {"data_context": rag_data}

def execute_data_node(state: AgentState) -> dict:
    """
    Nodo encargado de ejecutar la recuperación de datos estructurados (JSON).
    Utiliza el módulo data_retriever para la búsqueda determinista.
    
    Args:
        state (AgentState): Estado actual del agente.
        
    Returns:
        dict: Actualización del estado con el contexto y flag de éxito.
    """
    print(f"🛠️ EJECUTANDO: get_corporate_data...")
    latest_message = state["messages"][-1].content
    result = get_corporate_data(latest_message)
    
    return {
        "data_context": result["context"], 
        "data_found": result["found"]
    }

def decide_next_step(state: AgentState) -> str:
    """
    Función de enrutamiento condicional. Lee la decisión del router y define el siguiente nodo.
    
    Args:
        state (AgentState): Estado actual con la decisión del enrutador.
        
    Returns:
        str: Nombre de la arista (edge) a seguir.
    """
    decision = state["route_decision"]

    if decision == "RAG":
        return "go_to_rag"
    elif decision == "DATOS":
        return "go_to_data"
    else:
        return "go_to_response"

def check_data_success(state: AgentState) -> str:
    """
    Verifica si la herramienta de datos encontró información. 
    Si falla, redirige al sistema RAG como respaldo.
    
    Args:
        state (AgentState): Estado con el flag 'data_found'.
        
    Returns:
        str: Siguiente paso en el flujo.
    """
    if state.get("data_found", False):
        print("Success data found -> go to response")
        return "go_to_response"
    else:
        print("data not found -> go to rag")
        return "go_to_rag"

def router_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Nodo principal de decisión. Utiliza el LLM para clasificar la intención del usuario.
    
    Args:
        state (AgentState): Estado con el historial de mensajes.
        config (RunnableConfig): Configuración dinámica enviada desde la interfaz.
        
    Returns:
        dict: Decisión de enrutamiento ('RAG', 'DATOS', 'DIRECTO').
    """
    system_prompt = ROUTER_SYSTEM_PROMPT
    
    user_prompt = state.get("messages", [])[-1].content if state.get("messages") else "N/A"
    print(f"\n👤 Usuario: {user_prompt}")
    
    llm = get_llm(config, temperature=0.0)
    
    # Extraemos el proveedor para aplicar lógica condicional de historial
    provider = config.get("configurable", {}).get("provider", "LocalAI")
    
    if provider == "Google AI Studio":
        # Modelos grandes pueden deducir información del historial sin confundirse
        messages_for_llm = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    else:
        # Modelos pequeños requieren aislar la pregunta para evitar confusión de roles
        messages_for_llm = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Petición del usuario a clasificar: {user_prompt}")
        ]

    llm_response = llm.invoke(messages_for_llm)
    
    # Manejo de respuesta tipo lista
    content = llm_response.content
    if isinstance(content, list):
        # Filtramos solo los bloques de texto, ignorando los de 'thinking'
        content = "".join([
            c.get("text", "") for c in content 
            if isinstance(c, dict) and c.get("type") == "text"
        ])
    
    decision = str(content).strip().upper()
    
    # Limpieza de seguridad para modelos locales
    if "RAG" in decision: decision = "RAG"
    elif "DATOS" in decision: decision = "DATOS"
    else: decision = "DIRECTO"
    
    print(f"🧠 ENRUTADOR DECIDIÓ: {decision}")
    
    # IMPORTANTE: Reiniciamos el contexto de datos al inicio de cada turno 
    # para evitar que persista información de la pregunta anterior.
    return {
        "route_decision": decision,
        "data_context": "", 
        "data_found": False
    }

def generate_response_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Genera la respuesta final al usuario integrando el contexto y el historial.
    
    Args:
        state (AgentState): Estado completo con contexto y mensajes previos.
        config (RunnableConfig): Configuración dinámica enviada desde la interfaz.
        
    Returns:
        dict: Respuesta final y actualización del historial de mensajes.
    """
    context = state.get("data_context", "No se usó ninguna base de datos.")
    decision = state.get("route_decision", "DIRECTO")
    
    system_prompt = ASSISTANT_PROMPT_TEMPLATE.format(
        decision=decision,
        context=context
    )
    
    llm = get_llm(config, temperature=0.1)
    
    messages_for_llm = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    final_response = llm.invoke(messages_for_llm)
    
    # Extract text content for state (optional, but good for final_response key)
    content = final_response.content
    if isinstance(content, list):
        content = "".join([
            c.get("text", "") for c in content 
            if isinstance(c, dict) and c.get("type") == "text"
        ])
    
    return {
        "final_response": str(content),
        "messages": [final_response]
    }

# --- 5. GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

# Add nodes (the blocks of code that do the work)
workflow.add_node("router", router_node)
workflow.add_node("rag_tool_node", execute_rag_node)
workflow.add_node("data_tool_node", execute_data_node)
workflow.add_node("generate_response", generate_response_node)

# Connections 
workflow.add_edge(START, "router")

# Conditional connection
workflow.add_conditional_edges(
    "router", 
    decide_next_step, 
    {
        "go_to_rag": "rag_tool_node",
        "go_to_data": "data_tool_node",
        "go_to_response": "generate_response"
    }
)
workflow.add_conditional_edges(
    "data_tool_node", 
    check_data_success, 
    {
        "go_to_rag": "rag_tool_node",
        "go_to_response": "generate_response"
    }
)

# Fallback edges from the conditional edges
workflow.add_edge("rag_tool_node", "generate_response")
workflow.add_edge("generate_response", END)

# Compilamos el grafo con el checkpointer de memoria
memory_saver = MemorySaver()
agent_executor = workflow.compile(checkpointer=memory_saver)
