import tkinter as tk
from tkinter import ttk, messagebox

from config.settings import APP_NAME, QUALITY_GOAL, Q14_TARGETS
from database.schema import init_db
from models.product import ProductData
from services.inventory_service import InventoryService
from services.product_service import ProductService
from services.report_service import ReportService
from services.supplier_service import SupplierService
from utils.logger import log_audit, log_error
from utils.validators import ValidationError


APP_TITLE = f"{APP_NAME} - TQM Q14"


class InventoryApp(tk.Tk):
    """Desktop UI layer. UI shows data and calls services; it does not run SQL."""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(1000, 650)
        self.configure(bg="#eef2f7")

        init_db()
        self.current_user = "admin"
        self.current_page = "Home"
        self.breadcrumb = tk.StringVar(value="Home")
        self.page_title = tk.StringVar(value="Inventory Dashboard")
        self.status = tk.StringVar(value="Ready")

        self.product_service = ProductService(self.current_user)
        self.inventory_service = InventoryService(self.current_user)
        self.report_service = ReportService(self.current_user)
        self.supplier_service = SupplierService(self.current_user)

        self._build_shell()
        self.show_home()

    # ============================================================
    # MAIN SHELL
    # ============================================================

    def _build_shell(self):
        top = tk.Frame(self, bg="#143d59", height=70)
        top.pack(fill="x")

        tk.Label(
            top,
            text="INVENTORY MANAGEMENT SYSTEM",
            bg="#143d59",
            fg="white",
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left", padx=22)

        tk.Label(
            top,
            text=f"Admin | {QUALITY_GOAL}",
            bg="#143d59",
            fg="#dbeafe",
            font=("Segoe UI", 10),
        ).pack(side="right", padx=22)

        nav = tk.Frame(self, bg="white", height=48, bd=1, relief="solid")
        nav.pack(fill="x")

        for text, command in [
            ("Home", self.show_home),
            ("Products", self.show_products),
            ("Suppliers", self.show_suppliers),
            ("Stock", self.show_stock),
            ("Reports", self.show_reports),
        ]:
            ttk.Button(nav, text=text, command=command).pack(
                side="left", padx=5, pady=7
            )

        ttk.Button(nav, text="⌨ Shortcuts", command=self.show_shortcuts).pack(
            side="right", padx=5, pady=7
        )
        ttk.Button(nav, text="Logout", command=self.destroy).pack(
            side="right", padx=5, pady=7
        )

        crumb = tk.Frame(self, bg="#f7fafc")
        crumb.pack(fill="x", padx=18, pady=(12, 4))
        tk.Label(
            crumb,
            text="Navigation:",
            bg="#f7fafc",
            fg="#64748b",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")
        tk.Label(
            crumb,
            textvariable=self.breadcrumb,
            bg="#f7fafc",
            fg="#1e3a8a",
            font=("Segoe UI", 9),
        ).pack(side="left", padx=8)

        titlebar = tk.Frame(self, bg="#eef2f7")
        titlebar.pack(fill="x", padx=18, pady=(3, 5))
        tk.Label(
            titlebar,
            textvariable=self.page_title,
            bg="#eef2f7",
            fg="#0f172a",
            font=("Segoe UI", 22, "bold"),
        ).pack(side="left")
        ttk.Button(titlebar, text="← Home", command=self.show_home).pack(side="right")

        self.content = tk.Frame(self, bg="#eef2f7")
        self.content.pack(fill="both", expand=True, padx=18, pady=10)

        # Windows/Linux + macOS shortcuts.
        bindings = [
            ("<Control-h>", self.show_home),
            ("<Control-p>", self.show_products),
            ("<Control-s>", self.show_stock),
            ("<Control-r>", self.show_reports),
            ("<Command-h>", self.show_home),
            ("<Command-p>", self.show_products),
            ("<Command-s>", self.show_stock),
            ("<Command-r>", self.show_reports),
        ]
        for sequence, command in bindings:
            self.bind_all(sequence, lambda _event, cmd=command: cmd())
        self.bind("<F1>", lambda _event: self.show_shortcuts())

    def _clear(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _set_page(self, name: str, title: str):
        self.current_page = name
        self.breadcrumb.set(f"Home  ›  {name}")
        self.page_title.set(title)
        self.status.set(f"Viewing {name}")
        self._clear()
        try:
            log_audit(self.current_user, "PAGE_VIEW", name, "Navigation page viewed")
        except Exception:
            # Logging should never stop the UI from opening a page.
            pass

    def _show_error(self, error_code: str, module: str, message: str):
        log_error(self.current_user, error_code, module, message)
        messagebox.showerror("Quality Check", message)

    def _tile(self, parent, title, value, column, command=None):
        card = tk.Frame(parent, bg="white", bd=1, relief="solid")
        card.grid(row=0, column=column, padx=7, pady=7, sticky="nsew")
        tk.Label(
            card,
            text=title,
            bg="white",
            fg="#64748b",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=16, pady=(15, 5))
        tk.Label(
            card,
            text=value,
            bg="white",
            fg="#0f172a",
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w", padx=16, pady=(0, 15))
        if command:
            ttk.Button(card, text="Open", command=command).pack(
                anchor="e", padx=12, pady=(0, 12)
            )
        return card

    # ============================================================
    # DASHBOARD
    # ============================================================

    def show_home(self):
        self._set_page("Home", "Inventory Dashboard")
        metrics = self.report_service.dashboard_metrics()

        grid = tk.Frame(self.content, bg="#eef2f7")
        grid.pack(fill="x")
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)

        self._tile(grid, "Total Products", metrics["total_products"], 0, self.show_products)
        # Q14: direct route to the low-stock quality report.
        self._tile(grid, "Low Stock Alerts", metrics["low_stock"], 1, self.show_low_stock_items)
        self._tile(grid, "Total Suppliers", metrics["total_suppliers"], 2, self.show_suppliers)
        self._tile(grid, "Units in Stock", metrics["stock_units"], 3, self.show_stock)

        quick = tk.Frame(self.content, bg="white", bd=1, relief="solid")
        quick.pack(fill="both", expand=True, pady=12)
        tk.Label(
            quick,
            text="Quick Navigation",
            bg="white",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 10))

        actions = [
            ("Manage Products", self.show_products),
            ("Manage Suppliers", self.show_suppliers),
            ("Record Stock Movement", self.show_stock),
            ("View Quality Reports", self.show_reports),
            ("Keyboard Shortcuts", self.show_shortcuts),
        ]
        for label, command in actions:
            ttk.Button(quick, text=f"  {label}", command=command).pack(
                fill="x", padx=18, pady=5, ipady=6
            )

    # ============================================================
    # SHORTCUTS
    # ============================================================

    def show_shortcuts(self):
        self._set_page("Help", "Navigation Shortcuts")
        data = [
            ("Ctrl + H / ⌘ + H", "Home Dashboard"),
            ("Ctrl + P / ⌘ + P", "Products"),
            ("Ctrl + S / ⌘ + S", "Stock Movements"),
            ("Ctrl + R / ⌘ + R", "Reports"),
            ("F1", "Shortcut Help"),
            ("Home button", "Return to dashboard"),
            ("Top navigation", "Jump between major modules"),
            ("Breadcrumb trail", "Show current navigation path"),
        ]

        table = ttk.Treeview(
            self.content,
            columns=("shortcut", "purpose"),
            show="headings",
            height=12,
        )
        table.pack(fill="x", padx=10, pady=10)
        table.heading("shortcut", text="Shortcut / Navigation")
        table.heading("purpose", text="Purpose")
        table.column("shortcut", width=300)
        table.column("purpose", width=700)
        for row in data:
            table.insert("", "end", values=row)

        tk.Label(
            self.content,
            text=(
                "Q14 measurable targets: "
                f"{Q14_TARGETS['major_module_access']}; "
                f"{Q14_TARGETS['breadcrumb_visibility']}; "
                f"{Q14_TARGETS['top_navigation']}; "
                f"{Q14_TARGETS['home_return']}; "
                f"{Q14_TARGETS['keyboard_navigation']}."
            ),
            bg="#eef2f7",
            fg="#475569",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", padx=12, pady=6)

    # ============================================================
    # PRODUCTS
    # ============================================================

    def show_products(self):
        self._set_page("Products", "Product Management")

        bar = tk.Frame(self.content, bg="#eef2f7")
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Add Product", command=self.product_dialog).pack(side="left")
        ttk.Button(bar, text="Refresh", command=self.show_products).pack(side="left", padx=7)
        ttk.Button(
            bar,
            text="Delete Selected",
            command=lambda: self.delete_product(tree),
        ).pack(side="left", padx=7)

        columns = (
            "id",
            "sku",
            "name",
            "category",
            "supplier",
            "quantity",
            "reorder",
            "price",
            "status",
        )
        tree = ttk.Treeview(self.content, columns=columns, show="headings")
        tree.pack(fill="both", expand=True)

        headers = {
            "id": "ID",
            "sku": "SKU",
            "name": "Product",
            "category": "Category",
            "supplier": "Supplier",
            "quantity": "Qty",
            "reorder": "Reorder",
            "price": "Price",
            "status": "Status",
        }
        widths = {
            "id": 55,
            "sku": 110,
            "name": 220,
            "category": 130,
            "supplier": 160,
            "quantity": 70,
            "reorder": 75,
            "price": 90,
            "status": 90,
        }
        for column in columns:
            tree.heading(column, text=headers[column])
            tree.column(column, width=widths[column])

        for row in self.product_service.list_products():
            tree.insert("", "end", values=tuple(row))

        tree.bind(
            "<Double-1>",
            lambda _event: self._edit_selected_product(tree),
        )
        self.product_tree = tree

    def _edit_selected_product(self, tree):
        item = tree.focus()
        if item:
            values = tree.item(item, "values")
            self.product_dialog(int(values[0]))

    def delete_product(self, tree):
        item = tree.focus()
        if not item:
            messagebox.showwarning("Selection", "Select a product first.")
            return
        values = tree.item(item, "values")
        if not messagebox.askyesno("Confirm Delete", f"Delete product {values[1]}?"):
            return
        try:
            self.product_service.delete_product(int(values[0]))
            self.show_products()
        except Exception as exc:
            self._show_error("E_PRODUCT_DELETE", "Products", str(exc))

    def product_dialog(self, product_id=None):
        win = tk.Toplevel(self)
        win.title("Product")
        win.geometry("520x470")
        win.transient(self)
        win.grab_set()

        fields = [
            ("SKU", "sku"),
            ("Product Name", "name"),
            ("Quantity", "quantity"),
            ("Reorder Level", "reorder"),
            ("Unit Price", "price"),
        ]
        entries = {}
        for row_no, (label, key) in enumerate(fields):
            tk.Label(win, text=label, font=("Segoe UI", 10, "bold")).grid(
                row=row_no, column=0, sticky="w", padx=20, pady=10
            )
            entry = tk.Entry(win, width=40)
            entry.grid(row=row_no, column=1, padx=20, pady=10)
            entries[key] = entry

        categories, suppliers = self.product_service.get_form_options()

        tk.Label(win, text="Category", font=("Segoe UI", 10, "bold")).grid(
            row=5, column=0, sticky="w", padx=20, pady=10
        )
        category = ttk.Combobox(
            win,
            values=[f"{row[0]} - {row[1]}" for row in categories],
            state="readonly",
            width=37,
        )
        category.grid(row=5, column=1, padx=20, pady=10)

        tk.Label(win, text="Supplier", font=("Segoe UI", 10, "bold")).grid(
            row=6, column=0, sticky="w", padx=20, pady=10
        )
        supplier = ttk.Combobox(
            win,
            values=[f"{row[0]} - {row[1]}" for row in suppliers],
            state="readonly",
            width=37,
        )
        supplier.grid(row=6, column=1, padx=20, pady=10)

        if product_id:
            row = self.product_service.get_product(product_id)
            if row:
                for key in entries:
                    entries[key].insert(
                        0, row["reorder_level"] if key == "reorder" else row[key]
                    )
                if row["category_id"]:
                    category.set(
                        next(
                            (
                                f"{item[0]} - {item[1]}"
                                for item in categories
                                if item[0] == row["category_id"]
                            ),
                            "",
                        )
                    )
                if row["supplier_id"]:
                    supplier.set(
                        next(
                            (
                                f"{item[0]} - {item[1]}"
                                for item in suppliers
                                if item[0] == row["supplier_id"]
                            ),
                            "",
                        )
                    )

        def save():
            try:
                category_id = int(category.get().split(" - ")[0]) if category.get() else None
                supplier_id = int(supplier.get().split(" - ")[0]) if supplier.get() else None
                data = ProductData(
                    sku=entries["sku"].get(),
                    name=entries["name"].get(),
                    quantity=entries["quantity"].get(),
                    reorder_level=entries["reorder"].get(),
                    price=entries["price"].get(),
                    category_id=category_id,
                    supplier_id=supplier_id,
                )
                self.product_service.save_product(data, product_id)
                win.destroy()
                self.show_products()
            except Exception as exc:
                self._show_error("E_PRODUCT_VALIDATION", "Products", str(exc))

        ttk.Button(win, text="Save", command=save).grid(
            row=8, column=1, sticky="e", padx=20, pady=20
        )

    # ============================================================
    # SUPPLIERS
    # ============================================================

    def show_suppliers(self):
        self._set_page("Suppliers", "Supplier Management")
        ttk.Button(self.content, text="Refresh", command=self.show_suppliers).pack(
            anchor="w", pady=(0, 8)
        )

        tree = ttk.Treeview(
            self.content,
            columns=("id", "name", "phone", "email", "address"),
            show="headings",
        )
        tree.pack(fill="both", expand=True)

        for column, heading, width in [
            ("id", "ID", 60),
            ("name", "Supplier", 250),
            ("phone", "Phone", 150),
            ("email", "Email", 260),
            ("address", "Address", 250),
        ]:
            tree.heading(column, text=heading)
            tree.column(column, width=width)

        for row in self.supplier_service.list_suppliers():
            tree.insert("", "end", values=tuple(row))

    # ============================================================
    # STOCK
    # ============================================================

    def show_stock(self):
        self._set_page("Stock", "Stock Movement")
        bar = tk.Frame(self.content, bg="#eef2f7")
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Record Movement", command=self.stock_dialog).pack(side="left")
        ttk.Button(bar, text="Refresh", command=self.show_stock).pack(side="left", padx=7)

        tree = ttk.Treeview(
            self.content,
            columns=("id", "sku", "name", "type", "qty", "note", "date"),
            show="headings",
        )
        tree.pack(fill="both", expand=True)

        for column, heading, width in [
            ("id", "ID", 55),
            ("sku", "SKU", 110),
            ("name", "Product", 230),
            ("type", "Type", 75),
            ("qty", "Qty", 70),
            ("note", "Note", 300),
            ("date", "Date", 170),
        ]:
            tree.heading(column, text=heading)
            tree.column(column, width=width)

        for row in self.inventory_service.list_stock_movements():
            tree.insert("", "end", values=tuple(row))

    def stock_dialog(self):
        win = tk.Toplevel(self)
        win.title("Stock Movement")
        win.geometry("460x280")
        win.grab_set()

        products = self.inventory_service.list_products_for_movement()

        tk.Label(win, text="Product").grid(row=0, column=0, padx=20, pady=15, sticky="w")
        product = ttk.Combobox(
            win,
            values=[f"{row[0]} - {row[1]} - {row[2]}" for row in products],
            state="readonly",
            width=30,
        )
        product.grid(row=0, column=1)

        tk.Label(win, text="Type").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        movement_type = ttk.Combobox(
            win, values=["IN", "OUT"], state="readonly", width=30
        )
        movement_type.grid(row=1, column=1)
        movement_type.current(0)

        tk.Label(win, text="Quantity").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        quantity = tk.Entry(win, width=33)
        quantity.grid(row=2, column=1)

        tk.Label(win, text="Note").grid(row=3, column=0, padx=20, pady=10, sticky="w")
        note = tk.Entry(win, width=33)
        note.grid(row=3, column=1)

        def save():
            try:
                if not product.get():
                    raise ValidationError("Please select a product.")
                product_id = int(product.get().split(" - ")[0])
                self.inventory_service.record_movement(
                    product_id,
                    movement_type.get(),
                    quantity.get(),
                    note.get(),
                )
                win.destroy()
                self.show_stock()
            except Exception as exc:
                self._show_error("E_STOCK_MOVEMENT", "Stock", str(exc))

        ttk.Button(win, text="Save Movement", command=save).grid(
            row=4, column=1, sticky="e", padx=20, pady=15
        )

    # ============================================================
    # REPORTS / QUALITY DASHBOARD
    # ============================================================

    def show_reports(self):
        self._set_page("Reports", "Quality & Inventory Reports")
        summary = self.report_service.quality_summary()
        low_stock = self.report_service.low_stock_rows()

        metrics = tk.Frame(self.content, bg="#eef2f7")
        metrics.pack(fill="x")
        for i in range(4):
            metrics.grid_columnconfigure(i, weight=1)
        self._tile(metrics, "Inventory Value", f"₹{summary['inventory_value']:,.2f}", 0)
        self._tile(metrics, "Low Stock Items", summary["low_stock"], 1, self.show_low_stock_items)
        self._tile(metrics, "Audit Events", summary["audit_events"], 2, self.show_audit_events)
        self._tile(metrics, "Error Events", summary["error_events"], 3, self.show_error_events)

        box = tk.Frame(self.content, bg="white", bd=1, relief="solid")
        box.pack(fill="both", expand=True, pady=12)
        tk.Label(
            box,
            text="Low Stock Exceptions",
            bg="white",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", padx=16, pady=14)

        tree = ttk.Treeview(
            box,
            columns=("sku", "name", "qty", "reorder"),
            show="headings",
            height=8,
        )
        tree.pack(fill="x", padx=16)
        for column, heading, width in [
            ("sku", "SKU", 120),
            ("name", "Product", 320),
            ("qty", "Qty", 100),
            ("reorder", "Reorder Level", 150),
        ]:
            tree.heading(column, text=heading)
            tree.column(column, width=width)
        for row in low_stock:
            tree.insert("", "end", values=tuple(row))

        audit = self.report_service.recent_audit(6)
        audit_box = tk.Frame(box, bg="white")
        audit_box.pack(fill="x", padx=16, pady=(16, 8))
        tk.Label(
            audit_box,
            text="Recent Quality / Audit Trail",
            bg="white",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")
        for row in audit:
            tk.Label(
                audit_box,
                text=f"{row['created_at']} | {row['action']} | {row['entity']} | {row['details'] or ''}",
                bg="white",
                fg="#475569",
                anchor="w",
            ).pack(fill="x", pady=1)

    # ============================================================
    # AUDIT EVENTS
    # ============================================================

    def show_audit_events(self):
        self._set_page("Audit Events", "Audit Event Details")

        rows = self.report_service.recent_audit(20)

        box = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid"
        )
        box.pack(
            fill="both",
            expand=True,
            pady=12
        )

        tk.Label(
            box,
            text="Recent Audit Events",
            bg="white",
            font=("Segoe UI", 14, "bold")
        ).pack(
            anchor="w",
            padx=16,
            pady=14
        )

        tree = ttk.Treeview(
            box,
            columns=("user", "action", "entity", "details", "time"),
            show="headings",
            height=14,
        )
        tree.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=(0, 16),
        )

        for column, heading, width in [
            ("user", "User", 120),
            ("action", "Action", 150),
            ("entity", "Entity", 140),
            ("details", "Details", 360),
            ("time", "Time", 180),
        ]:
            tree.heading(column, text=heading)
            tree.column(column, width=width, anchor="w")

        for row in rows:
            tree.insert(
                "",
                "end",
                values=(
                    row["username"],
                    row["action"],
                    row["entity"],
                    row["details"] or "",
                    row["created_at"],
                ),
            )

    def show_low_stock_items(self):
        self._set_page("Low Stock Items", "Low Stock Item Details")

        rows = self.report_service.low_stock_rows()

        box = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid",
        )
        box.pack(
            fill="both",
            expand=True,
        )

        tk.Label(
            box,
            text="Low Stock Item Details",
            bg="white",
            font=("Segoe UI", 14, "bold"),
        ).pack(
            anchor="w",
            padx=16,
            pady=14,
        )

        tree = ttk.Treeview(
            box,
            columns=("sku", "product", "qty", "reorder"),
            show="headings",
        )
        tree.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=(0, 16),
        )

        columns = [
            ("sku", "SKU", 160),
            ("product", "Product", 320),
            ("qty", "Qty", 120),
            ("reorder", "Reorder Level", 160),
        ]

        for column, heading, width in columns:
            tree.heading(column, text=heading)
            tree.column(column, width=width)

        for row in rows:
            tree.insert(
                "",
                "end",
                values=(
                    row["sku"],
                    row["name"],
                    row["quantity"],
                    row["reorder_level"],
                ),
            )

    def show_error_events(self):
        self._set_page("Error Events", "Error Event Details")

        rows = self.report_service.recent_errors(20)

        box = tk.Frame(
            self.content,
            bg="white",
            bd=1,
            relief="solid",
        )
        box.pack(
            fill="both",
            expand=True,
        )

        tk.Label(
            box,
            text="Recent Error Events",
            bg="white",
            font=("Segoe UI", 14, "bold"),
        ).pack(
            anchor="w",
            padx=16,
            pady=14,
        )

        tree = ttk.Treeview(
            box,
            columns=("user", "code", "module", "message", "time"),
            show="headings",
        )
        tree.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=(0, 16),
        )

        columns = [
            ("user", "User", 120),
            ("code", "Error Code", 120),
            ("module", "Module", 140),
            ("message", "Message", 360),
            ("time", "Time", 180),
        ]

        for column, heading, width in columns:
            tree.heading(column, text=heading)
            tree.column(column, width=width)

        for row in rows:
            tree.insert(
                "",
                "end",
                values=(
                    row["username"],
                    row["error_code"],
                    row["module"],
                    row["message"],
                    row["created_at"],
                ),
            )

