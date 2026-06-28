"""
Phase 3 & 4 DB migration — safe to re-run
Run from: seapedia\ root
"""
import sqlite3, os, datetime

TDB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'transactions.db')
print("Connecting to:", TDB)

conn = sqlite3.connect(TDB)
c    = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS discounts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    code             TEXT    UNIQUE NOT NULL COLLATE NOCASE,
    discount_percent INTEGER NOT NULL CHECK(discount_percent BETWEEN 1 AND 100),
    min_purchase     REAL    NOT NULL DEFAULT 0,
    valid_until      DATETIME NOT NULL,
    is_active        INTEGER  DEFAULT 1
)''')

c.execute('''CREATE TABLE IF NOT EXISTS driver_earnings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id  INTEGER NOT NULL,
    order_id   INTEGER NOT NULL,
    amount     REAL    NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

for col, defn in [
    ('status',          "TEXT    DEFAULT 'Sedang Dikemas'"),
    ('driver_id',       "INTEGER DEFAULT NULL"),
    ('voucher_code',    "TEXT    DEFAULT NULL"),
    ('discount_amount', "REAL    DEFAULT 0"),
]:
    try:
        c.execute(f"ALTER TABLE orders ADD COLUMN {col} {defn}")
        print(f"  + Added column: {col}")
    except Exception as e:
        print(f"  ~ {col}: {e}")

c.execute("UPDATE orders SET status = 'Sedang Dikemas' WHERE status IS NULL OR status = ''")

future = (datetime.datetime.now() + datetime.timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
for code, pct, min_p in [('SEAPEDIA10', 10, 0), ('HEMAT20', 20, 50000), ('NEWUSER15', 15, 0)]:
    try:
        c.execute('INSERT INTO discounts (code,discount_percent,min_purchase,valid_until) VALUES (?,?,?,?)',
                  (code, pct, min_p, future))
        print(f"  + Seeded voucher: {code}")
    except:
        print(f"  ~ Voucher {code} already exists")

conn.commit()
conn.close()
print("Phase 3-4 DB migration complete!")
