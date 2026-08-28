import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'inventory.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Admin'
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
    ''')
    cur.execute("INSERT OR IGNORE INTO users(username,password,role) VALUES('admin','admin123','Admin')")
    conn.commit()
    conn.close()


def seed_demo():
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    categories = ['Electronics', 'Stationery', 'Networking', 'Accessories']
    for c in categories:
        cur.execute('INSERT OR IGNORE INTO categories(name) VALUES(?)', (c,))
    suppliers = [
        ('TechSource India', '9876543210', 'sales@techsource.example', 'Dehradun'),
        ('OfficePro Supplies', '9876501234', 'officepro@example', 'Haridwar'),
        ('NetLink Systems', '9811122233', 'contact@netlink.example', 'Delhi'),
    ]
    for row in suppliers:
        cur.execute('SELECT id FROM suppliers WHERE name=?', (row[0],))
        if not cur.fetchone():
            cur.execute('INSERT INTO suppliers(name,phone,email,address) VALUES(?,?,?,?)', row)
    cat = {r['name']: r['id'] for r in cur.execute('SELECT id,name FROM categories')}
    sup = {r['name']: r['id'] for r in cur.execute('SELECT id,name FROM suppliers')}
    products = [
        ('ITM-1001','Wireless Mouse',cat['Accessories'],sup['TechSource India'],34,10,799,'Active'),
        ('ITM-1002','USB Keyboard',cat['Accessories'],sup['TechSource India'],8,10,999,'Active'),
        ('ITM-1003','A4 Printer Paper',cat['Stationery'],sup['OfficePro Supplies'],120,30,320,'Active'),
        ('ITM-1004','Ethernet Cable',cat['Networking'],sup['NetLink Systems'],52,15,180,'Active'),
        ('ITM-1005','Wi-Fi Router',cat['Networking'],sup['NetLink Systems'],5,8,2499,'Active'),
    ]
    for p in products:
        cur.execute('SELECT id FROM products WHERE sku=?', (p[0],))
        if not cur.fetchone():
            cur.execute('''INSERT INTO products(sku,name,category_id,supplier_id,quantity,reorder_level,price,status)
                           VALUES(?,?,?,?,?,?,?,?)''', p)
    conn.commit()
    conn.close()
