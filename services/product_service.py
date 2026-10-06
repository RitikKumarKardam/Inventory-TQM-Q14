from database.db import get_conn
from models.product import ProductData
from utils.logger import log_audit, log_error
from utils.validators import (
    ValidationError,
    non_negative_float,
    non_negative_int,
    require_text,
)


class ProductService:
    def __init__(self, username: str = "admin"):
        self.username = username

    def list_products(self):
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT
                p.id,p.sku,p.name,
                COALESCE(c.name,'-') AS category,
                COALESCE(s.name,'-') AS supplier,
                p.quantity,p.reorder_level,p.price,p.status
            FROM products p
            LEFT JOIN categories c ON c.id=p.category_id
            LEFT JOIN suppliers s ON s.id=p.supplier_id
            ORDER BY p.name
            """
        ).fetchall()
        conn.close()
        return rows

    def get_product(self, product_id: int):
        conn = get_conn()
        row = conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()
        conn.close()
        return row

    def get_form_options(self):
        conn = get_conn()
        categories = conn.execute(
            "SELECT id,name FROM categories ORDER BY name"
        ).fetchall()
        suppliers = conn.execute(
            "SELECT id,name FROM suppliers ORDER BY name"
        ).fetchall()
        conn.close()
        return categories, suppliers

    def save_product(
        self,
        data: ProductData,
        product_id: int | None = None,
    ) -> None:
        sku = require_text(data.sku, "SKU")
        name = require_text(data.name, "Product Name")
        quantity = non_negative_int(data.quantity, "Quantity")
        reorder = non_negative_int(data.reorder_level, "Reorder Level")
        price = non_negative_float(data.price, "Unit Price")

        conn = get_conn()
        try:
            cur = conn.cursor()
            duplicate = cur.execute(
                "SELECT id FROM products WHERE sku=? AND id<>?",
                (sku, product_id or -1),
            ).fetchone()
            if duplicate:
                raise ValidationError("SKU must be unique.")

            if product_id:
                cur.execute(
                    """
                    UPDATE products
                    SET sku=?,name=?,category_id=?,supplier_id=?,quantity=?,
                        reorder_level=?,price=?,status=?,updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (
                        sku,
                        name,
                        data.category_id,
                        data.supplier_id,
                        quantity,
                        reorder,
                        price,
                        data.status,
                        product_id,
                    ),
                )
                action = "UPDATE_PRODUCT"
            else:
                cur.execute(
                    """
                    INSERT INTO products(
                        sku,name,category_id,supplier_id,quantity,reorder_level,price,status
                    ) VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        sku,
                        name,
                        data.category_id,
                        data.supplier_id,
                        quantity,
                        reorder,
                        price,
                        data.status,
                    ),
                )
                action = "CREATE_PRODUCT"

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        log_audit(self.username, action, "Product", sku)

    def delete_product(self, product_id: int) -> None:
        product = self.get_product(product_id)
        if not product:
            raise ValidationError("Product not found.")

        conn = get_conn()
        try:
            conn.execute("DELETE FROM products WHERE id=?", (product_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            log_error(
                self.username,
                "E_PRODUCT_DELETE",
                "ProductService",
                f"Unable to delete product {product_id}",
            )
            raise
        finally:
            conn.close()

        log_audit(self.username, "DELETE_PRODUCT", "Product", product["sku"])
