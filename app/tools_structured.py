import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.rag_langchain import search_knowledge_base
from data_retriever import get_corporate_data


LOG_DIR = Path("logs")
LEADS_FILE = LOG_DIR / "leads.jsonl"
ESCALATIONS_FILE = LOG_DIR / "escalations.jsonl"


class BuscarBaseConocimientoInput(BaseModel):
    query: str = Field(
        ...,
        description="Pregunta del usuario que debe consultarse en la base documental RAG.",
    )


class ConsultarDatosCorporativosInput(BaseModel):
    query: str = Field(
        ...,
        description="Pregunta del usuario sobre datos corporativos estructurados: marcas, productos, horarios, sedes, contacto o métricas.",
    )


class RegistrarLeadInput(BaseModel):
    nombre: str = Field(..., description="Nombre del cliente potencial.")
    telefono: str = Field(..., description="Número de teléfono del cliente potencial.")
    interes: str = Field(..., description="Producto, servicio o necesidad del cliente.")
    canal: Optional[str] = Field("WhatsApp", description="Canal de contacto del usuario.")


class EscalarHumanoInput(BaseModel):
    telefono: str = Field(..., description="Número de teléfono del usuario.")
    motivo: str = Field(..., description="Motivo por el cual debe intervenir un asesor humano.")
    prioridad: Optional[str] = Field("media", description="Prioridad: baja, media o alta.")


@tool(args_schema=BuscarBaseConocimientoInput)
def buscar_base_conocimiento(query: str) -> str:
    """
    Busca información en la base documental de Tecnoquímicas usando RAG.
    Úsala cuando el usuario pregunte por historia, productos, servicios, responsabilidad corporativa,
    información institucional o detalles que puedan estar en documentos largos.
    """
    try:
        return search_knowledge_base(query)
    except Exception as e:
        return (
            "En este momento no pude consultar la base documental. "
            f"Detalle técnico: {str(e)}"
        )


@tool(args_schema=ConsultarDatosCorporativosInput)
def consultar_datos_corporativos(query: str) -> str:
    """
    Consulta datos estructurados de Tecnoquímicas almacenados en JSON.
    Úsala para preguntas sobre marcas, productos, horarios, presencia geográfica, contacto,
    empleados, referencias, sedes o datos concretos de la empresa.
    """
    try:
        result = get_corporate_data(query)

        if not result.get("found"):
            return (
                "No encontré un dato estructurado exacto para esa consulta. "
                "Puedes usar la herramienta buscar_base_conocimiento como respaldo."
            )

        return result.get("context", "")
    except Exception as e:
        return (
            "En este momento no pude consultar los datos corporativos estructurados. "
            f"Detalle técnico: {str(e)}"
        )


@tool(args_schema=RegistrarLeadInput)
def registrar_lead(
    nombre: str,
    telefono: str,
    interes: str,
    canal: str = "WhatsApp",
) -> str:
    """
    Registra un cliente potencial interesado en productos o servicios de Tecnoquímicas.
    Esta herramienta representa una acción sensible porque guarda datos de contacto.
    """
    LOG_DIR.mkdir(exist_ok=True)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "nombre": nombre,
        "telefono": telefono,
        "interes": interes,
        "canal": canal,
        "estado": "pendiente_contacto",
    }

    with LEADS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return (
        "El cliente potencial fue registrado correctamente. "
        "Un asesor podrá revisar la solicitud y contactar al usuario."
    )


@tool(args_schema=EscalarHumanoInput)
def escalar_a_humano(
    telefono: str,
    motivo: str,
    prioridad: str = "media",
) -> str:
    """
    Escala una conversación a un asesor humano cuando el usuario solicita atención personalizada,
    presenta una queja, requiere soporte específico o la consulta no debe ser respondida automáticamente.
    """
    LOG_DIR.mkdir(exist_ok=True)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "telefono": telefono,
        "motivo": motivo,
        "prioridad": prioridad,
        "estado": "pendiente_revision_humana",
    }

    with ESCALATIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return (
        "La conversación fue escalada a un asesor humano. "
        "El equipo podrá revisar el caso y continuar la atención."
    )


STRUCTURED_TOOLS = [
    buscar_base_conocimiento,
    consultar_datos_corporativos,
    registrar_lead,
    escalar_a_humano,
]