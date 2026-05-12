import json
import logging
from config import PROJECT_DIR

logger = logging.getLogger(__name__)

# Ruta al archivo JSON de datos estructurados
JSON_DATA_PATH = PROJECT_DIR / "data" / "info_corporativa.json"

def get_corporate_data(query: str) -> dict:
    """
    Busca y recupera datos específicos del archivo JSON de forma determinista.
    Filtra la información basándose en un mapeo de palabras clave.
    
    Args:
        query (str): La consulta del usuario.
        
    Returns:
        dict: Un diccionario con el contexto encontrado ('context') y un flag de éxito ('found').
    """
    # 1. Cargar datos
    try:
        if not JSON_DATA_PATH.exists():
            return {"context": "", "found": False}
        with open(JSON_DATA_PATH, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except Exception as e:
        logger.error(f"Error cargando JSON: {e}")
        return {"context": "", "found": False}

    # 2. Definir mapa de conocimiento (Keywords -> Keys del JSON)
    query_lower = query.lower()
    map_knowledge = {
        "datos_basicos": ["nit", "nombre", "fundacion", "sede", "telefono", "quienes", "legal", "contacto", "historia"],
        "presencia_geografica": ["paises", "donde", "exporta", "plantas", "cali", "cauca", "sedes", "ubicacion", "ciudades"],
        "marcas_lideres": ["marcas", "productos", "vende", "mk", "winny", "lua", "yodora", "portafolio", "catalogo"],
        "metricas_clave": ["empleados", "colaboradores", "cuantos", "referencias", "años", "personas", "cantidad", "trayectoria"],
        "horarios_atencion": ["horario", "hora", "abierto", "lunes", "viernes", "atienden", "abren", "cierran", "atencion"]
    }

    # 3. Filtrar información relevante
    contexto_seleccionado = {}
    encontrado = False

    for key, keywords in map_knowledge.items():
        for word in keywords:
            if word in query_lower:
                contexto_seleccionado[key] = json_data.get(key)
                encontrado = True
                break 

    # 4. Formatear resultado
    data_str = json.dumps(contexto_seleccionado, indent=2, ensure_ascii=False) if encontrado else ""
    
    return {
        "context": data_str, 
        "found": encontrado
    }
