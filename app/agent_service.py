from typing import Any, Dict

from app.agent_structured import agent_executor
from app.schemas import ChatRequest


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


def _extract_response(result: Dict[str, Any]) -> str:
    messages = result.get("messages", [])

    if messages:
        last_message = messages[-1]
        content = getattr(last_message, "content", None)

        if content:
            return _extract_text(content)

    return "No pude generar una respuesta en este momento."


def ask_agent(payload: ChatRequest) -> str:
    try:
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
                    "thread_id": payload.user_id,
                }
            },
        )

        return _extract_response(result)

    except Exception as e:
        return (
            "En este momento no pude procesar tu solicitud con el agente. "
            f"Detalle técnico: {str(e)}"
        )