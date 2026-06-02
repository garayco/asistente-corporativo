from typing import Any, Dict

from app.agent.agent_structured import agent_executor
from app.api.schemas import ChatRequest


import logging

logger = logging.getLogger("agent_debugger")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Silenciar el ruido de librerías externas que hacen peticiones HTTP
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []

        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif "text" in block:
                    texts.append(block.get("text", ""))
            else:
                texts.append(str(block))

        return "".join(texts).strip()

    return str(content)


def _extract_response_and_tools(result: Dict[str, Any]) -> tuple[str, list]:
    messages = result.get("messages", [])
    tools_used = []

    # Extraer historial de herramientas usadas en esta invocación
    for msg in messages:
        # Algunos modelos guardan llamadas en 'tool_calls' (LangChain moderno)
        if getattr(msg, "tool_calls", None):
            for tool in msg.tool_calls:
                tools_used.append(tool.get("name"))

    if messages:
        last_message = messages[-1]
        content = getattr(last_message, "content", None)

        if content:
            return _extract_text(content), tools_used

    return "No pude generar una respuesta en este momento.", tools_used


def ask_agent(payload: ChatRequest) -> tuple[str, list]:
    try:
        logger.info(f"--- NUEVA SOLICITUD ---")
        logger.info(f"User ID: {payload.user_id} | Thread ID: {payload.thread_id}")
        logger.info(f"Pregunta del usuario: '{payload.message}'")

        result = agent_executor.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": payload.message,
                    }
                ]
            },
            config={
                "configurable": {
                    "thread_id": payload.thread_id,
                }
            },
        )

        final_response, tools_used = _extract_response_and_tools(result)
        
        if tools_used:
            logger.info(f"Ruta/Herramientas utilizadas por la IA: {tools_used}")
        else:
            logger.info(f"Ruta/Herramientas: Ninguna (Respondió de forma directa o de memoria)")
            
        logger.info(f"Respuesta final: '{final_response}'\n-----------------------")

        return final_response, tools_used

    except Exception as e:
        logger.error(f"Error en el agente: {str(e)}")
        return (
            "En este momento no pude procesar tu solicitud con el agente. "
            f"Detalle técnico: {str(e)}",
            []
        )