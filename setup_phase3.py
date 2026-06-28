import sqlite3
import datetime
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TRANSACTIONS_DB = os.path.join(DATA_DIR, 'transactions.db')

conn = sqlite3.connect(TRANSACTIONS_DB)
c = conn.cursor()

# Discounts table
c.execute('''
CREATE TABLE IF NOT EXISTS discounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL COLLATE NOCASE,
    discount_percent INTEGER NOT NULL CHECK(discount_percent BETWEEN 1 AND 100),
    min_purchase REAL NOT NULL DEFAULT 0,
    valid_until DATETIME NOT NULL,
    is_active INTEGER DEFAULT 1
)
''')

# Add driver_id and status to orders if missing
try:
    c.execute("ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'Sedang Dikemas'")
    print("Added status column to orders")
except Exception as e:
    print("status column:", e)

try:
    c.execute("ALTER TABLE orders ADD COLUMN driver_id INTEGER")
    print("Added driver_id column to orders")
except Exception as e:
    print("driver_id column:", e)

try:
    c.execute("ALTER TABLE orders ADD COLUMN voucher_code TEXT")
    print("Added voucher_code column to orders")
except Exception as e:
    print("voucher_code column:", e)

try:
    c.execute("ALTER TABLE orders ADD COLUMN discount_amount REAL DEFAULT 0")
    print("Added discount_amount column to orders")
except Exception as e:
    print("discount_amount column:", e)

# Seed demo discount codes
future = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
codes = [
    ('SEAPEDIA10', 10, 0, future),
    ('HEMAT20', 20, 50000, future),
    ('NEWUSER15', 15, 0, future),
]
for code, pct, min_p, valid in codes:
    try:
        c.execute('INSERT INTO discounts (code, discount_percent, min_purchase, valid_until) VALUES (?, ?, ?, ?)',
                  (code, pct, min_p, valid))
        print(f'Seeded discount: {code}')
    except:
        pass

conn.commit()
conn.close()
print("Phase 3-6 DB setup complete!")
