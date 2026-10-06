class ValidationError(ValueError):
    """Raised when business input fails an explicit quality check."""


def require_text(value: str, field_name: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{field_name} cannot be blank.")
    return value


def non_negative_int(value, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an integer.") from exc
    if parsed < 0:
        raise ValidationError(f"{field_name} cannot be negative.")
    return parsed


def positive_int(value, field_name: str) -> int:
    parsed = non_negative_int(value, field_name)
    if parsed == 0:
        raise ValidationError(f"{field_name} must be greater than zero.")
    return parsed


def non_negative_float(value, field_name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be numeric.") from exc
    if parsed < 0:
        raise ValidationError(f"{field_name} cannot be negative.")
    return parsed


def validate_movement(movement_type: str, quantity: int, current_stock: int) -> None:
    if movement_type not in {"IN", "OUT"}:
        raise ValidationError("Movement type must be IN or OUT.")
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    if movement_type == "OUT" and quantity > current_stock:
        raise ValidationError("OUT quantity cannot exceed current stock.")
