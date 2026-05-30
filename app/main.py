import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent_service import ask_agent
from app.conversation_logger import log_conversation
from app.schemas import ChatRequest, ChatResponse, HealthResponse


app = FastAPI(
    title="API Asistente Corporativo TQ",
    description="API REST para productizar el agente corporativo y conectarlo con WhatsApp/N8N.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def root():
    return {
        "status": "ok",
        "service": "API Asistente Corporativo TQ",
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": "API Asistente Corporativo TQ",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        response = ask_agent(payload)

        log_conversation(
            user_id=payload.user_id,
            message=payload.message,
            response=response,
            status="ok",
        )

        return ChatResponse(
            user_id=payload.user_id,
            response=response,
            status="ok",
        )

    except Exception as e:
        traceback.print_exc()

    log_conversation(
        user_id=payload.user_id,
        message=payload.message,
        response=None,
        status="error",
        error=str(e),
    )

    raise HTTPException(
        status_code=500,
        detail=str(e),
    )
