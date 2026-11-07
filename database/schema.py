from database.db import get_conn


def init_db() -> None:
    """Create the database schema without removing existing academic data."""
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Admin',
            email TEXT UNIQUE,
            provider TEXT DEFAULT 'local',
            avatar_url TEXT
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category_id INTEGER,
            supplier_id INTEGER,
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            reorder_level INTEGER NOT NULL DEFAULT 5 CHECK(reorder_level >= 0),
            price REAL NOT NULL DEFAULT 0 CHECK(price >= 0),
            status TEXT NOT NULL DEFAULT 'Active',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL CHECK(movement_type IN ('IN','OUT')),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT NOT NULL,
            entity TEXT,
            details TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            error_code TEXT NOT NULL,
            module TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
        CREATE INDEX IF NOT EXISTS idx_products_low_stock ON products(quantity, reorder_level);
        CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at);
        CREATE INDEX IF NOT EXISTS idx_error_created_at ON error_log(created_at);

        CREATE TABLE IF NOT EXISTS inspection_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_number TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            supplier_id INTEGER,
            sample_size INTEGER NOT NULL DEFAULT 10,
            defects_found INTEGER NOT NULL DEFAULT 0,
            defect_type TEXT,
            inspection_status TEXT NOT NULL DEFAULT 'PASSED',
            inspector_name TEXT NOT NULL DEFAULT 'Ritik Kumar',
            remarks TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS fmea_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            failure_mode TEXT NOT NULL,
            cause TEXT NOT NULL,
            effect TEXT NOT NULL,
            severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 10),
            occurrence INTEGER NOT NULL CHECK(occurrence BETWEEN 1 AND 10),
            detection INTEGER NOT NULL CHECK(detection BETWEEN 1 AND 10),
            rpn INTEGER NOT NULL,
            recommended_action TEXT,
            action_taken TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pdca_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase TEXT NOT NULL CHECK(phase IN ('Plan', 'Do', 'Check', 'Act')),
            action TEXT NOT NULL,
            evidence TEXT,
            owner TEXT NOT NULL DEFAULT 'Ritik Kumar',
            status TEXT NOT NULL DEFAULT 'Complete',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS defect_log_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            defect_type TEXT NOT NULL,
            frequency INTEGER NOT NULL,
            cumulative_pct REAL NOT NULL,
            category TEXT DEFAULT 'Navigation',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vendor_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            quality_score REAL NOT NULL DEFAULT 95.0,
            delivery_score REAL NOT NULL DEFAULT 90.0,
            compliance_score REAL NOT NULL DEFAULT 98.0,
            evaluation_notes TEXT,
            evaluated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
        );
        """
    )
    for col, defn in [
        ("email", "TEXT UNIQUE"),
        ("provider", "TEXT DEFAULT 'local'"),
        ("avatar_url", "TEXT"),
    ]:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
        except Exception:
            pass

    cur.execute(
        "INSERT OR IGNORE INTO users(username,password,role,email,provider) VALUES('admin','admin123','Admin','admin@amrapali.ac.in','local')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO users(username,password,role,email,provider) VALUES('member','member123','Member','member@amrapali.ac.in','local')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO users(username,password,role,email,provider) VALUES('ritik','ritik123','Member','ritikkumar2520301005@gmail.com','google')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO users(username,password,role,email,provider) VALUES('ritikkumarhempur5','ritik123','Member','ritikkumarhempur5@gmail.com','google')"
    )
    conn.commit()
    conn.close()


def seed_demo() -> None:
    """Insert stable demonstration data only when it is missing."""
    init_db()
    conn = get_conn()
    cur = conn.cursor()

    categories = ["Electronics", "Stationery", "Networking", "Accessories"]
    for category in categories:
        cur.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (category,))

    suppliers = [
        ("TechSource India", "9876543210", "sales@techsource.example", "Dehradun"),
        ("OfficePro Supplies", "9876501234", "officepro@example", "Haridwar"),
        ("NetLink Systems", "9811122233", "contact@netlink.example", "Delhi"),
    ]
    for supplier in suppliers:
        cur.execute("SELECT id FROM suppliers WHERE name=?", (supplier[0],))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO suppliers(name,phone,email,address) VALUES(?,?,?,?)",
                supplier,
            )

    categories_by_name = {
        row["name"]: row["id"]
        for row in cur.execute("SELECT id,name FROM categories")
    }
    suppliers_by_name = {
        row["name"]: row["id"]
        for row in cur.execute("SELECT id,name FROM suppliers")
    }

    products = [
        (
            "ITM-1001",
            "Wireless Mouse",
            categories_by_name["Accessories"],
            suppliers_by_name["TechSource India"],
            34,
            10,
            799,
            "Active",
        ),
        (
            "ITM-1002",
            "USB Keyboard",
            categories_by_name["Accessories"],
            suppliers_by_name["TechSource India"],
            8,
            10,
            999,
            "Active",
        ),
        (
            "ITM-1003",
            "A4 Printer Paper",
            categories_by_name["Stationery"],
            suppliers_by_name["OfficePro Supplies"],
            120,
            30,
            320,
            "Active",
        ),
        (
            "ITM-1004",
            "Ethernet Cable",
            categories_by_name["Networking"],
            suppliers_by_name["NetLink Systems"],
            52,
            15,
            180,
            "Active",
        ),
        (
            "ITM-1005",
            "Wi-Fi Router",
            categories_by_name["Networking"],
            suppliers_by_name["NetLink Systems"],
            5,
            8,
            2499,
            "Active",
        ),
    ]

    for product in products:
        cur.execute("SELECT id FROM products WHERE sku=?", (product[0],))
        if cur.fetchone() is None:
            cur.execute(
                """
                INSERT INTO products(
                    sku,name,category_id,supplier_id,quantity,reorder_level,price,status
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                product,
            )

    _seed_tqm_demo(cur)

    conn.commit()
    conn.close()


def _seed_tqm_demo(cur) -> None:
    """Populate TQM artifacts, inspection logs, and supplier ratings if empty."""
    import csv
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    art = root / "artifacts"

    # 1. Defect Log (Pareto Analysis source)
    cur.execute("SELECT COUNT(*) FROM defect_log_records")
    if cur.fetchone()[0] == 0:
        defect_file = art / "defect_log.csv"
        if defect_file.exists():
            with open(defect_file, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    cur.execute(
                        """
                        INSERT INTO defect_log_records(defect_type, frequency, cumulative_pct, category)
                        VALUES(?, ?, ?, 'Navigation')
                        """,
                        (row["Defect Type"], int(row["Frequency"]), float(row["Cumulative %"])),
                    )
        else:
            default_defects = [
                ("No clear return path", 14, 28.0),
                ("Module hidden from nav", 10, 48.0),
                ("Too many clicks", 8, 64.0),
                ("Shortcut unavailable", 6, 76.0),
                ("Breadcrumb absent", 5, 86.0),
                ("Inconsistent labels", 3, 92.0),
                ("Dashboard tile unclear", 2, 96.0),
                ("Other", 2, 100.0),
            ]
            for name, freq, cum in default_defects:
                cur.execute(
                    "INSERT INTO defect_log_records(defect_type, frequency, cumulative_pct) VALUES(?,?,?)",
                    (name, freq, cum),
                )

    # 2. FMEA Matrix
    cur.execute("SELECT COUNT(*) FROM fmea_records")
    if cur.fetchone()[0] == 0:
        fmea_file = art / "fmea_matrix.csv"
        if fmea_file.exists():
            with open(fmea_file, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    s = int(row["Severity"])
                    o = int(row["Occurrence"])
                    d = int(row["Detection"])
                    rpn = int(row["RPN"])
                    cur.execute(
                        """
                        INSERT INTO fmea_records(
                            failure_mode, cause, effect, severity, occurrence, detection, rpn,
                            recommended_action, action_taken
                        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row["Failure Mode"],
                            row["Cause"],
                            row["Effect"],
                            s,
                            o,
                            d,
                            rpn,
                            "Implement Q14 design standard",
                            "Resolved in Q14 UI release",
                        ),
                    )

    # 3. PDCA Log
    cur.execute("SELECT COUNT(*) FROM pdca_records")
    if cur.fetchone()[0] == 0:
        pdca_file = art / "pdca_log.csv"
        if pdca_file.exists():
            with open(pdca_file, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    cur.execute(
                        """
                        INSERT INTO pdca_records(phase, action, evidence, owner, status)
                        VALUES(?, ?, ?, ?, ?)
                        """,
                        (
                            row["Phase"],
                            row["Action"],
                            row["Evidence"],
                            row.get("Owner", "Ritik Kumar"),
                            row.get("Status", "Complete"),
                        ),
                    )

    # 4. Supplier Vendor Ratings
    cur.execute("SELECT COUNT(*) FROM vendor_ratings")
    if cur.fetchone()[0] == 0:
        suppliers = cur.execute("SELECT id, name FROM suppliers").fetchall()
        default_ratings = {
            "TechSource India": (96.5, 94.0, 98.0, "Grade A - Preferred Electronic Accessories Vendor"),
            "OfficePro Supplies": (98.0, 97.5, 99.0, "Grade A+ - ISO 9001 Certified Stationery Supplier"),
            "NetLink Systems": (89.0, 85.0, 91.0, "Grade B - Monitored Networking Vendor (Lead-time review required)"),
        }
        for s_id, s_name in suppliers:
            if s_name in default_ratings:
                q, d, c, note = default_ratings[s_name]
                cur.execute(
                    """
                    INSERT INTO vendor_ratings(supplier_id, quality_score, delivery_score, compliance_score, evaluation_notes)
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (s_id, q, d, c, note),
                )

    # 5. Incoming Quality Inspections (GRN Quality Control)
    cur.execute("SELECT COUNT(*) FROM inspection_records")
    if cur.fetchone()[0] == 0:
        products = {row["sku"]: row["id"] for row in cur.execute("SELECT id, sku FROM products")}
        suppliers = {row["name"]: row["id"] for row in cur.execute("SELECT id, name FROM suppliers")}
        sample_inspections = [
            (
                "LOT-2026-A101",
                products.get("ITM-1001", 1),
                suppliers.get("TechSource India", 1),
                25,
                0,
                "None",
                "PASSED",
                "Ritik Kumar",
                "AQL 0.65 Level II sampling passed. Zero defects observed.",
            ),
            (
                "LOT-2026-A102",
                products.get("ITM-1002", 2),
                suppliers.get("TechSource India", 1),
                15,
                1,
                "Key switch minor friction",
                "PASSED",
                "Ritik Kumar",
                "Minor cosmetic/tactile defect within allowable statistical limit.",
            ),
            (
                "LOT-2026-B201",
                products.get("ITM-1005", 5),
                suppliers.get("NetLink Systems", 3),
                10,
                2,
                "Firmware handshake latency",
                "QUARANTINE",
                "Ritik Kumar",
                "Defect rate 20% exceeds critical threshold. Batch isolated for vendor RMA review.",
            ),
            (
                "LOT-2026-C301",
                products.get("ITM-1003", 3),
                suppliers.get("OfficePro Supplies", 2),
                50,
                0,
                "None",
                "PASSED",
                "Ritik Kumar",
                "Paper brightness 98% ISO, 80 GSM certified by lab test.",
            ),
        ]
        for item in sample_inspections:
            cur.execute(
                """
                INSERT INTO inspection_records(
                    lot_number, product_id, supplier_id, sample_size, defects_found,
                    defect_type, inspection_status, inspector_name, remarks
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                item,
            )

