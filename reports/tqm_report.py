from database.db import get_conn


def quality_snapshot() -> dict:
    """Return a small, explainable TQM snapshot for the UI/report layer."""
    conn = get_conn()
    result = {
        "audit_events": conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0],
        "error_events": conn.execute("SELECT COUNT(*) FROM error_log").fetchone()[0],
        "low_stock_items": conn.execute(
            "SELECT COUNT(*) FROM products WHERE quantity<=reorder_level"
        ).fetchone()[0],
        "total_products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
    }
    conn.close()
    return result
