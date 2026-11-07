from database.db import get_conn
from utils.logger import log_audit, log_error
from utils.validators import ValidationError, require_text


class SupplierService:
    def __init__(self, username: str = "admin"):
        self.username = username

    def list_suppliers(self):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT s.id, s.name, s.phone, s.email, s.address,
                   COUNT(p.id) AS product_count
            FROM suppliers s
            LEFT JOIN products p ON p.supplier_id = s.id
            GROUP BY s.id
            ORDER BY s.name
            """
        ).fetchall()
        conn.close()
        log_audit(self.username, "VIEW_SUPPLIERS", "Supplier", "Supplier list viewed")
        return rows

    def get_supplier(self, supplier_id: int):
        conn = get_conn()
        row = conn.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
        conn.close()
        return row

    def create_supplier(self, name: str, phone: str = "", email: str = "", address: str = "") -> int:
        name = require_text(name, "Supplier Name")
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO suppliers(name, phone, email, address) VALUES(?, ?, ?, ?)",
                (name, (phone or "").strip(), (email or "").strip(), (address or "").strip()),
            )
            s_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()

        log_audit(self.username, "CREATE_SUPPLIER", "Supplier", f"id={s_id}, name={name}")
        return s_id

