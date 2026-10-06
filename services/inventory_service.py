from database.db import get_conn
from utils.logger import log_audit, log_error
from utils.validators import ValidationError, positive_int, validate_movement


class InventoryService:
    def __init__(self, username: str = "admin"):
        self.username = username

    def list_products_for_movement(self):
        conn = get_conn()
        rows = conn.execute(
            "SELECT id,sku,name,quantity FROM products ORDER BY name"
        ).fetchall()
        conn.close()
        return rows

    def list_stock_movements(self):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT m.id,p.sku,p.name,m.movement_type,m.quantity,
                   COALESCE(m.note,'') AS note,m.created_at
            FROM stock_movements m
            JOIN products p ON p.id=m.product_id
            ORDER BY m.id DESC
            """
        ).fetchall()
        conn.close()
        return rows

    def record_movement(
        self,
        product_id: int,
        movement_type: str,
        quantity: int,
        note: str,
    ) -> None:
        quantity = positive_int(quantity, "Quantity")
        conn = get_conn()
        try:
            cur = conn.cursor()
            product = cur.execute(
                "SELECT sku,quantity FROM products WHERE id=?",
                (product_id,),
            ).fetchone()
            if not product:
                raise ValidationError("Selected product was not found.")

            validate_movement(movement_type, quantity, product["quantity"])
            new_quantity = (
                product["quantity"] + quantity
                if movement_type == "IN"
                else product["quantity"] - quantity
            )

            cur.execute(
                """
                UPDATE products
                SET quantity=?,updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (new_quantity, product_id),
            )
            cur.execute(
                """
                INSERT INTO stock_movements(product_id,movement_type,quantity,note)
                VALUES(?,?,?,?)
                """,
                (product_id, movement_type, quantity, (note or "").strip()),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            log_error(
                self.username,
                "E_STOCK_MOVEMENT",
                "InventoryService",
                f"Invalid {movement_type} movement for product {product_id}",
            )
            raise
        finally:
            conn.close()

        log_audit(
            self.username,
            f"STOCK_{movement_type}",
            "Stock",
            f"product_id={product_id}, qty={quantity}",
        )
