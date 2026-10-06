from dataclasses import dataclass


@dataclass(frozen=True)
class ProductData:
    sku: str
    name: str
    quantity: int
    reorder_level: int
    price: float
    category_id: int | None = None
    supplier_id: int | None = None
    status: str = "Active"
