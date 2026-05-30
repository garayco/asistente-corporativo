from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.messages import HumanMessage
import uvicorn

from agent import agent_executor
from config import (
    LOCALAI_BASE_URL,
    LOCALAI_API_KEY,
    CHAT_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL
)

app = FastAPI(
    title="API de Asistente Corporativo TQ",
    description="API construida con FastAPI para exponer el agente corporativo basado en LangGraph y conectarlo con plataformas de automatización como n8n.",
    version="1.0.0"
)

# Habilitar CORS para que n8n u otros servicios externos puedan consultar el API sin restricciones de seguridad de navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str = Field(..., description="La consulta o mensaje del usuario para el agente.")
    thread_id: str = Field("default", description="Identificador único del hilo de chat para mantener la memoria.")
    provider: str = Field("LocalAI", description="Proveedor del LLM ('LocalAI' o 'Google AI Studio').")
    model: Optional[str] = Field(None, description="Modelo a utilizar. Si no se provee, se usará el por defecto según el proveedor.")
    temperature: float = Field(0.1, description="Temperatura de generación (0.0 a 1.0).")
    max_tokens: int = Field(2048, description="Número máximo de tokens a generar.")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Respuesta final generada por el agente.")
    route_decision: str = Field(..., description="Decisión de enrutamiento tomada por el agente ('RAG', 'DATOS', 'DIRECTO').")
    data_found: bool = Field(..., description="Indica si se encontraron datos estructurados en la consulta de base de datos.")
    thread_id: str = Field(..., description="El identificador del hilo de conversación asociado.")

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Resolver el modelo por defecto si no fue provisto en la petición
        model_name = request.model
        if not model_name:
            model_name = GEMINI_MODEL if request.provider == "Google AI Studio" else CHAT_MODEL
            
        api_key = GEMINI_API_KEY if request.provider == "Google AI Studio" else LOCALAI_API_KEY
        base_url = "" if request.provider == "Google AI Studio" else LOCALAI_BASE_URL

        # Configuración dinámica del workflow del agente (igual a chat_tq_localai.py)
        workflow_config = {
            "configurable": {
                "thread_id": request.thread_id,
                "provider": request.provider,
                "model": model_name,
                "temperature": request.temperature,
                "base_url": base_url,
                "api_key": api_key,
                "max_tokens": request.max_tokens
            }
        }

        # Ejecución del agente con el mensaje recibido
        response = agent_executor.invoke(
            {"messages": [HumanMessage(content=request.message)]}, 
            config=workflow_config
        )

        # Extracción de la respuesta final y metadatos del estado resultante del grafo
        final_response = response.get("final_response", "")
        route_decision = response.get("route_decision", "DIRECTO")
        data_found = response.get("data_found", False)

        return ChatResponse(
            response=final_response,
            route_decision=route_decision,
            data_found=data_found,
            thread_id=request.thread_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando el agente: {str(e)}")

@app.get("/health")
async def health_check():
    """Endpoint simple para verificar el estado de salud del servicio API."""
    return {"status": "ok", "service": "Asistente Corporativo TQ"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
