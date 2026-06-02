from typing import Literal, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=3,
        description="Identificador único del usuario para auditoría, límites o consumo de tokens.",
    )
    thread_id: str = Field(
        ...,
        min_length=3,
        description="Identificador del hilo de conversación para mantener la memoria del chat.",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Mensaje enviado por el usuario.",
    )
    provider: Literal["LocalAI", "Google AI Studio"] = "Google AI Studio"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2048


class ChatResponse(BaseModel):
    user_id: str
    thread_id: str
    response: str
    status: str = "ok"


class HealthResponse(BaseModel):
    status: str
    service: str