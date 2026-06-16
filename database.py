"""
database.py
Handles SQLite connection, table creation, and seeding of default data.
"""

import sqlite3
import hashlib
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "shop.db")


def get_connection():
    """Return a SQLite connection with foreign keys enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    """Simple SHA-256 hash for password storage."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    """Create all tables if they don't exist and seed default data."""
    conn = get_connection()
    cur = conn.cursor()

    # Outlets table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS outlets (
            outlet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outlet_name TEXT NOT NULL,
            location TEXT
        )
    """)

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('owner', 'manager')),
            outlet_id INTEGER,
            FOREIGN KEY (outlet_id) REFERENCES outlets(outlet_id)
        )
    """)

    # Items table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outlet_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            current_stock INTEGER NOT NULL DEFAULT 0,
            reorder_level INTEGER NOT NULL DEFAULT 5,
            FOREIGN KEY (outlet_id) REFERENCES outlets(outlet_id)
        )
    """)

    # Bills table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outlet_id INTEGER NOT NULL,
            bill_date TEXT NOT NULL,
            bill_time TEXT NOT NULL,
            total_amount REAL NOT NULL,
            payment_mode TEXT NOT NULL,
            FOREIGN KEY (outlet_id) REFERENCES outlets(outlet_id)
        )
    """)

    # Bill items table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_at_sale REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(bill_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id)
        )
    """)

    conn.commit()

    # ---- Seed default data only if empty ----
    cur.execute("SELECT COUNT(*) FROM outlets")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO outlets (outlet_name, location) VALUES (?, ?)",
            [
                ("Main Branch", "Nagpur - Sitabuldi"),
                ("Second Branch", "Nagpur - Sadar"),
            ],
        )
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # Default owner login -> username: admin / password: admin123
        cur.execute(
            "INSERT INTO users (username, password_hash, role, outlet_id) VALUES (?, ?, ?, ?)",
            ("admin", hash_password("admin123"), "owner", None),
        )
        # Default manager for outlet 1 -> username: manager1 / password: manager123
        cur.execute(
            "INSERT INTO users (username, password_hash, role, outlet_id) VALUES (?, ?, ?, ?)",
            ("manager1", hash_password("manager123"), "manager", 1),
        )
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM items")
    if cur.fetchone()[0] == 0:
        sample_items = [
            (1, "Tea Packet 250g", "Grocery", 60.0, 50, 10),
            (1, "Rice 1kg", "Grocery", 55.0, 100, 20),
            (1, "Soap", "Personal Care", 30.0, 80, 15),
            (1, "Biscuit Pack", "Snacks", 20.0, 120, 25),
            (2, "Tea Packet 250g", "Grocery", 62.0, 40, 10),
            (2, "Rice 1kg", "Grocery", 57.0, 90, 20),
            (2, "Soap", "Personal Care", 32.0, 70, 15),
            (2, "Biscuit Pack", "Snacks", 22.0, 100, 25),
        ]
        cur.executemany(
            "INSERT INTO items (outlet_id, item_name, category, price, current_stock, reorder_level) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            sample_items,
        )
        conn.commit()

    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DB_PATH)
