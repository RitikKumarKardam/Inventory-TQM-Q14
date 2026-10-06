from dataclasses import dataclass


@dataclass(frozen=True)
class SupplierData:
    id: int
    name: str
    phone: str = ""
    email: str = ""
    address: str = ""
