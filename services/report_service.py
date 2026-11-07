from database.db import get_conn
from utils.logger import log_audit


class ReportService:
    def __init__(self, username: str = "admin"):
        self.username = username

    def dashboard_metrics(self):
        conn = get_conn()
        metrics = {
            "total_products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "low_stock": conn.execute(
                "SELECT COUNT(*) FROM products WHERE quantity<=reorder_level"
            ).fetchone()[0],
            "total_suppliers": conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0],
            "stock_units": conn.execute(
                "SELECT COALESCE(SUM(quantity),0) FROM products"
            ).fetchone()[0],
        }
        conn.close()
        return metrics

    def low_stock_rows(self):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT sku,name,quantity,reorder_level
            FROM products
            WHERE quantity<=reorder_level
            ORDER BY quantity
            """
        ).fetchall()
        conn.close()
        return rows

    def quality_summary(self):
        conn = get_conn()
        summary = {
            "inventory_value": conn.execute(
                "SELECT COALESCE(SUM(quantity*price),0) FROM products"
            ).fetchone()[0],
            "audit_events": conn.execute(
                "SELECT COUNT(*) FROM audit_log"
            ).fetchone()[0],
            "error_events": conn.execute(
                "SELECT COUNT(*) FROM error_log"
            ).fetchone()[0],
            "low_stock": conn.execute(
                "SELECT COUNT(*) FROM products WHERE quantity<=reorder_level"
            ).fetchone()[0],
        }
        conn.close()
        return summary

    def recent_audit(self, limit: int = 8):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT username,action,entity,details,created_at
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return rows

    def recent_errors(self, limit: int = 8):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT username,error_code,module,message,created_at
            FROM error_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return rows

    def category_distribution(self):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT COALESCE(c.name, 'Uncategorized') AS category,
                   COUNT(p.id) AS product_count,
                   COALESCE(SUM(p.quantity), 0) AS total_units,
                   COALESCE(SUM(p.quantity * p.price), 0.0) AS total_value
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY total_value DESC
            """
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def movement_summary(self, limit: int = 10):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT m.id, m.movement_type, m.quantity, COALESCE(m.note, '') AS note,
                   m.created_at, p.sku, p.name AS product_name
            FROM stock_movements m
            JOIN products p ON p.id = m.product_id
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

