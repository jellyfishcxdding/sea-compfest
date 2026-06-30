"""
init_db.py  —  Run this once on Render to initialise the SQLite databases.
Render's free tier has an ephemeral disk, so we seed fresh data on each start.
Called automatically by the startup script before gunicorn.
"""
from pathlib import Path
import sqlite3

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# ── auth.db ──────────────────────────────────────────────────────
auth_db = str(DATA_DIR / 'auth.db')
conn = sqlite3.connect(auth_db)
c = conn.cursor()
c.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS user_roles (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id  INTEGER NOT NULL REFERENCES users(id),
        role     TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS wallets (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
        balance REAL DEFAULT 0
    );
''')
conn.commit(); conn.close()

# ── seller.db ────────────────────────────────────────────────────
seller_db = str(DATA_DIR / 'seller.db')
conn = sqlite3.connect(seller_db)
c = conn.cursor()
c.executescript('''
    CREATE TABLE IF NOT EXISTS stores (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id   INTEGER NOT NULL,
        name        TEXT UNIQUE NOT NULL,
        city        TEXT,
        description TEXT,
        image_url   TEXT,
        rating      REAL DEFAULT 5.0
    );
''')
conn.commit(); conn.close()

# ── inventory.db ─────────────────────────────────────────────────
inv_db = str(DATA_DIR / 'inventory.db')
conn = sqlite3.connect(inv_db)
c = conn.cursor()
c.executescript('''
    CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id    INTEGER NOT NULL,
        name        TEXT NOT NULL,
        description TEXT,
        price       REAL NOT NULL,
        stock       INTEGER DEFAULT 0,
        image_url   TEXT,
        category    TEXT DEFAULT 'electronics',
        rating      REAL DEFAULT 5.0,
        sold_count  INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS product_reviews (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id    INTEGER NOT NULL,
        username   TEXT NOT NULL,
        rating     INTEGER NOT NULL,
        comment    TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS discounts (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        code             TEXT UNIQUE NOT NULL,
        discount_percent REAL NOT NULL,
        min_purchase     REAL DEFAULT 0,
        valid_until      TEXT
    );
    CREATE TABLE IF NOT EXISTS promos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id  INTEGER,
        discount    REAL NOT NULL,
        description TEXT,
        valid_until TEXT
    );
''')
conn.commit(); conn.close()

# ── transactions.db ──────────────────────────────────────────────
trans_db = str(DATA_DIR / 'transactions.db')
conn = sqlite3.connect(trans_db)
c = conn.cursor()
c.executescript('''
    CREATE TABLE IF NOT EXISTS orders (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id        INTEGER NOT NULL,
        store_id        INTEGER NOT NULL,
        status          TEXT DEFAULT 'Sedang Dikemas',
        payment_method  TEXT,
        delivery_method TEXT DEFAULT 'Regular',
        delivery_fee    REAL DEFAULT 10000,
        discount_amount REAL DEFAULT 0,
        subtotal        REAL DEFAULT 0,
        ppn_amount      REAL DEFAULT 0,
        total_price     REAL NOT NULL,
        voucher_code    TEXT,
        driver_id       INTEGER,
        created_at      TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id   INTEGER NOT NULL REFERENCES orders(id),
        product_id INTEGER NOT NULL,
        quantity   INTEGER NOT NULL,
        price      REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS wallet_transactions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL,
        amount      REAL NOT NULL,
        type        TEXT NOT NULL,
        description TEXT,
        created_at  TEXT DEFAULT (datetime('now'))
    );
''')
conn.commit(); conn.close()

print("Databases initialised in", DATA_DIR)
