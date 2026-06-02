import os

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv(override=True)

try:
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
except Exception:
    PostgresSaver = None
    ConnectionPool = None
    dict_row = None


_pool = None
_checkpointer = None


def get_checkpointer():
    """
    Usa PostgresSaver si DATABASE_URL existe.
    Si no hay DATABASE_URL, usa InMemorySaver para desarrollo local.
    """
    global _pool, _checkpointer

    if _checkpointer is not None:
        return _checkpointer

    database_url = os.getenv("DATABASE_URL")

    if database_url and PostgresSaver and ConnectionPool:
        _pool = ConnectionPool(
            conninfo=database_url,
            max_size=20,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
        )

        _checkpointer = PostgresSaver(_pool)
        _checkpointer.setup()

        return _checkpointer

    _checkpointer = InMemorySaver()
    return _checkpointer