"""Compatibility wrapper; database work now lives under database/."""
from database.compat import DB_PATH, get_conn, init_db, seed_demo

__all__ = ["DB_PATH", "get_conn", "init_db", "seed_demo"]
