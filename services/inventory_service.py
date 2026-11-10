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
            SELECT m.id,m.product_id,p.sku,p.name,m.movement_type,m.quantity,
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

    def delete_movement(self, movement_id: int) -> None:
        conn = get_conn()
        try:
            cur = conn.cursor()
            movement = cur.execute(
                "SELECT id, product_id, movement_type, quantity, note FROM stock_movements WHERE id=?",
                (movement_id,),
            ).fetchone()
            if not movement:
                raise ValidationError("Movement transaction was not found.")

            product = cur.execute(
                "SELECT id, sku, name, quantity FROM products WHERE id=?",
                (movement["product_id"],),
            ).fetchone()
            if not product:
                raise ValidationError("Associated product was not found.")

            # Revert stock quantity
            if movement["movement_type"] == "IN":
                if product["quantity"] < movement["quantity"]:
                    raise ValidationError(
                        f"Cannot delete movement: Available warehouse stock ({product['quantity']} units) "
                        f"is less than inward quantity ({movement['quantity']} units) to revert."
                    )
                new_quantity = product["quantity"] - movement["quantity"]
            else:
                new_quantity = product["quantity"] + movement["quantity"]

            cur.execute(
                "UPDATE products SET quantity=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (new_quantity, product["id"]),
            )
            cur.execute("DELETE FROM stock_movements WHERE id=?", (movement_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            log_error(
                self.username,
                "E_DELETE_MOVEMENT",
                "InventoryService",
                f"Error deleting movement {movement_id}",
            )
            raise
        finally:
            conn.close()

        log_audit(
            self.username,
            "DELETE_STOCK_MOVEMENT",
            "Stock",
            f"movement_id={movement_id}, product_id={movement['product_id']}, reverted_qty={movement['quantity']}",
        )

    def edit_movement(
        self,
        movement_id: int,
        product_id: int,
        movement_type: str,
        quantity: int,
        note: str,
    ) -> None:
        quantity = positive_int(quantity, "Quantity")
        if movement_type not in ("IN", "OUT"):
            raise ValidationError("Movement type must be IN or OUT.")

        conn = get_conn()
        try:
            cur = conn.cursor()
            old_mov = cur.execute(
                "SELECT id, product_id, movement_type, quantity, note FROM stock_movements WHERE id=?",
                (movement_id,),
            ).fetchone()
            if not old_mov:
                raise ValidationError("Movement transaction was not found.")

            old_prod = cur.execute(
                "SELECT id, sku, name, quantity FROM products WHERE id=?",
                (old_mov["product_id"],),
            ).fetchone()
            if not old_prod:
                raise ValidationError("Original product for this movement was not found.")

            # Revert the old movement
            reverted_old_qty = (
                old_prod["quantity"] - old_mov["quantity"]
                if old_mov["movement_type"] == "IN"
                else old_prod["quantity"] + old_mov["quantity"]
            )
            if reverted_old_qty < 0:
                raise ValidationError(
                    f"Cannot edit movement: Reverting previous transaction would make warehouse stock negative ({reverted_old_qty})."
                )

            if product_id == old_mov["product_id"]:
                # Same product: validate and apply new movement onto reverted base
                validate_movement(movement_type, quantity, reverted_old_qty)
                final_qty = (
                    reverted_old_qty + quantity
                    if movement_type == "IN"
                    else reverted_old_qty - quantity
                )
                cur.execute(
                    "UPDATE products SET quantity=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (final_qty, product_id),
                )
            else:
                # Target product changed: update old product with reverted qty, then validate and update new product
                new_prod = cur.execute(
                    "SELECT id, sku, name, quantity FROM products WHERE id=?",
                    (product_id,),
                ).fetchone()
                if not new_prod:
                    raise ValidationError("New target product was not found.")

                validate_movement(movement_type, quantity, new_prod["quantity"])
                new_final_qty = (
                    new_prod["quantity"] + quantity
                    if movement_type == "IN"
                    else new_prod["quantity"] - quantity
                )
                cur.execute(
                    "UPDATE products SET quantity=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (reverted_old_qty, old_mov["product_id"]),
                )
                cur.execute(
                    "UPDATE products SET quantity=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (new_final_qty, product_id),
                )

            cur.execute(
                """
                UPDATE stock_movements
                SET product_id=?, movement_type=?, quantity=?, note=?
                WHERE id=?
                """,
                (product_id, movement_type, quantity, (note or "").strip(), movement_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            log_error(
                self.username,
                "E_EDIT_MOVEMENT",
                "InventoryService",
                f"Error editing movement {movement_id}",
            )
            raise
        finally:
            conn.close()

        log_audit(
            self.username,
            "EDIT_STOCK_MOVEMENT",
            "Stock",
            f"movement_id={movement_id}, product_id={product_id}, type={movement_type}, qty={quantity}",
        )
