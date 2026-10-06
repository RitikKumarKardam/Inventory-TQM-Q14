from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "inventory.db"
APP_NAME = "Inventory Management System"
QUALITY_GOAL = "Q14 - Improve Navigation"
VERSION = "2.0"
DEFAULT_USER = "admin"
DEFAULT_ROLE = "Admin"

# Measurable navigation quality targets inspired by the teacher reference.
Q14_TARGETS = {
    "major_module_access": "within 2 clicks",
    "breadcrumb_visibility": "visible on every page",
    "top_navigation": "available on major pages",
    "home_return": "returns to dashboard",
    "keyboard_navigation": "Ctrl/Cmd shortcuts + F1",
}
