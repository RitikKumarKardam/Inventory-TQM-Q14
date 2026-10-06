"""Backward-compatible imports for earlier project code/tests."""
from database.db import DB_PATH, get_conn
from database.schema import init_db, seed_demo

__all__ = ["DB_PATH", "get_conn", "init_db", "seed_demo"]
