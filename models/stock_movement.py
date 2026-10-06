from dataclasses import dataclass


@dataclass(frozen=True)
class StockMovementData:
    product_id: int
    movement_type: str
    quantity: int
    note: str = ""
