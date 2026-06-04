import json
import time
from pathlib import Path

# Configuración de colores ANSI
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

LOG_FILE = Path("logs/conversations.jsonl")

def format_record(record: dict) -> str:
    timestamp = record.get("timestamp", "N/A")
    user_id = record.get("user_id", "N/A")
    message = record.get("message", "")
    response = record.get("response", "")
    status = record.get("status", "ok")
    error = record.get("error")
    tools = record.get("tools_used", [])

    output = []
    output.append(f"{BOLD}{CYAN}┌────────────────────────────────────────────────────────────────────────┐{RESET}")
    output.append(f"{BOLD}{CYAN}│ 📅 [{timestamp}]  👤 Usuario: {user_id:<40} │{RESET}")
    output.append(f"{BOLD}{CYAN}├────────────────────────────────────────────────────────────────────────┤{RESET}")
    
    # Mensaje del usuario
    output.append(f"│ {BOLD}{BLUE}📥 PREGUNTA:{RESET} {message:<58} │")
    output.append(f"{BOLD}{CYAN}├────────────────────────────────────────────────────────────────────────┤{RESET}")

    # Herramientas utilizadas
    if tools:
        tools_str = ", ".join([f"🛠️  {t}" for t in tools])
        output.append(f"│ {BOLD}{YELLOW}⚙️  RUTA/HERRAMIENTAS:{RESET} {tools_str:<51} │")
    else:
        output.append(f"│ {BOLD}{YELLOW}⚙️  RUTA/HERRAMIENTAS:{RESET} Ninguna (Respuesta directa/Memoria)                │")
    
    output.append(f"{BOLD}{CYAN}├────────────────────────────────────────────────────────────────────────┤{RESET}")

    # Respuesta del asistente (manejar saltos de línea para que no rompa el recuadro)
    output.append(f"│ {BOLD}{GREEN}🤖 RESPUESTA ASISTENTE TQ:{RESET}                                             │")
    
    # Formatear la respuesta en líneas de máximo 68 caracteres
    response_lines = []
    if response:
        for raw_line in response.split("\n"):
            # Dividir si es muy larga
            words = raw_line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 68:
                    current_line += (word + " ")
                else:
                    response_lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                response_lines.append(current_line.strip())
    else:
        response_lines.append("[Respuesta Vacía]")

    for r_line in response_lines:
        output.append(f"│   {r_line:<68} │")

    output.append(f"{BOLD}{CYAN}├────────────────────────────────────────────────────────────────────────┤{RESET}")

    # Estado de la transacción
    if status == "ok":
        output.append(f"│ {BOLD}{GREEN}🚦 ESTADO: OK ✅{RESET}{' ':<57} │")
    else:
        output.append(f"│ {BOLD}{RED}🚦 ESTADO: ERROR ❌ ({error or 'Desconocido'}){RESET:<50} │")

    output.append(f"{BOLD}{CYAN}└────────────────────────────────────────────────────────────────────────┘{RESET}\n")
    return "\n".join(output)

def tail_logs():
    print(f"{BOLD}{GREEN}===================================================================={RESET}")
    print(f"{BOLD}{GREEN}      TQ ASSISTANT - VISUALIZADOR DE LOGS EN VIVO (LIVE)            {RESET}")
    print(f"{BOLD}{GREEN}===================================================================={RESET}")
    print(f"Monitoreando {BOLD}{LOG_FILE}{RESET}...\n")

    if not LOG_FILE.exists():
        # Crear archivo si no existe
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.touch()

    # 1. Cargar y mostrar los últimos 5 logs históricos para no iniciar vacío
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            last_lines = lines[-5:]
            if last_lines:
                print(f"{BOLD}{YELLOW}--- Últimas 5 interacciones guardadas: ---{RESET}\n")
                for line in last_lines:
                    try:
                        record = json.loads(line)
                        print(format_record(record))
                    except Exception:
                        pass
    except Exception as e:
        print(f"{RED}Error cargando historial: {e}{RESET}")

    print(f"{BOLD}{CYAN}📡 Esperando nuevas interacciones en tiempo real...{RESET}\n")

    # 2. Entrar en modo tailing
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        # Ir al final para solo escuchar lo nuevo
        f.seek(0, 2)
        
        while True:
            current_position = f.tell()
            line = f.readline()
            if not line:
                # Importante: f.seek(current_position) limpia el estado EOF (End of File) 
                # interno de Python y fuerza al sistema a refrescar el buffer del archivo
                f.seek(current_position)
                time.sleep(0.5)  # Esperar a que se escriba en el archivo
                continue
            
            try:
                record = json.loads(line.strip())
                formatted = format_record(record)
                print(formatted)
            except Exception as e:
                print(f"{RED}Error leyendo log: {e}{RESET}")

if __name__ == "__main__":
    try:
        tail_logs()
    except KeyboardInterrupt:
        print(f"\n{BOLD}{YELLOW}Monitoreo finalizado.{RESET}")
