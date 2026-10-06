"""Application entry point: initialize data, then start the UI."""
from database.schema import seed_demo
from app.app import InventoryApp


def main() -> None:
    seed_demo()
    InventoryApp().mainloop()


if __name__ == "__main__":
    main()
