import sqlite3
from pathlib import Path

from config.settings import DB_PATH

DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    """Open a SQLite connection with row access and foreign-key checks."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def transaction():
    """Return a connection intended for an atomic service operation."""
    return get_conn()
