from database.db import get_conn
from utils.logger import log_audit


class SupplierService:
    def __init__(self, username: str = "admin"):
        self.username = username

    def list_suppliers(self):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT id,name,phone,email,address
            FROM suppliers
            ORDER BY name
            """
        ).fetchall()
        conn.close()
        log_audit(self.username, "VIEW_SUPPLIERS", "Supplier", "Supplier list viewed")
        return rows
