"""
seed_demo.py — Phase 6 Demo Prep
Creates one user per role (Buyer, Seller, Driver, Admin) if they don't already exist.
Adds demo vouchers. Safe to re-run.
Uses pathlib — no os module.
"""
from pathlib import Path
import sqlite3, bcrypt, datetime

AUTH_DB  = Path(__file__).resolve().parent / 'data' / 'auth.db'
TRANS_DB = Path(__file__).resolve().parent / 'data' / 'transactions.db'

# ── connect ──────────────────────────────────────────────────────
conn = sqlite3.connect(str(AUTH_DB))
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute(f"ATTACH DATABASE '{TRANS_DB}' AS transactions")

DEMO_USERS = [
    ('buyer_demo',  'demo1234', ['Buyer']),
    ('seller_demo', 'demo1234', ['Seller']),
    ('driver_demo', 'demo1234', ['Driver']),
    ('admin_demo',  'demo1234', ['Admin']),
]

for username, password, roles in DEMO_USERS:
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    if c.fetchone():
        print(f'  ~ {username} already exists')
        continue
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, pw_hash))
    uid = c.lastrowid
    for role in roles:
        c.execute('INSERT INTO user_roles (user_id, role) VALUES (?, ?)', (uid, role))
    c.execute('INSERT INTO wallets (user_id, balance) VALUES (?, 500000)', (uid,))
    print(f'  + Created {username} with roles {roles} and Rp 500,000 balance')

# ── demo vouchers ─────────────────────────────────────────────────
future = (datetime.datetime.now() + datetime.timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
for code, pct, min_p in [('SEAPEDIA10', 10, 0), ('HEMAT20', 20, 50000), ('NEWUSER15', 15, 0)]:
    try:
        c.execute('''
            INSERT INTO transactions.discounts (code, discount_percent, min_purchase, valid_until)
            VALUES (?, ?, ?, ?)
        ''', (code, pct, min_p, future))
        print(f'  + Voucher {code} ({pct}% off)')
    except Exception:
        print(f'  ~ Voucher {code} already exists')

conn.commit()
conn.close()
print('\nDemo seed complete.')
print('\nDemo credentials (all use password: demo1234):')
print('  Buyer:  buyer_demo')
print('  Seller: seller_demo')
print('  Driver: driver_demo')
print('  Admin:  admin_demo')
