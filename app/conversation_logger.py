import json
from datetime import datetime
from pathlib import Path
from typing import Optional


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "conversations.jsonl"


def log_conversation(
    user_id: str,
    message: str,
    response: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
) -> None:
    LOG_DIR.mkdir(exist_ok=True)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_id": user_id,
        "message": message,
        "response": response,
        "status": status,
        "error": error,
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")