import sqlite3
import os

try:
    conn = sqlite3.connect('data/seller.db')
    c = conn.cursor()
    c.execute("ALTER TABLE stores ADD COLUMN description TEXT DEFAULT 'A premium store offering the best products on SEAPEDIA.'")
    conn.commit()
    conn.close()
    print('Added description to stores')
except Exception as e:
    print('Store description failed:', e)

try:
    conn = sqlite3.connect('data/transactions.db')
    c = conn.cursor()
    c.execute("ALTER TABLE orders ADD COLUMN driver_id INTEGER")
    conn.commit()
    conn.close()
    print('Added driver_id to orders')
except Exception as e:
    print('Driver_id failed:', e)
