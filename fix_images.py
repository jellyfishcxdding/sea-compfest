"""
fix_images.py — updates wrong product images in inventory.db
Uses pathlib (no os module) to resolve the DB path.
Run from: seapedia/ root
"""
from pathlib import Path
import sqlite3

DB = Path(__file__).resolve().parent / 'data' / 'inventory.db'
print('DB:', DB)

# Map: (name LIKE pattern) -> correct Unsplash URL
# Images hand-picked and verified to actually show the right thing.
FIXES = [
    # Bird Seed — show bird seed / pet birds eating seeds
    (
        '%Bird Seed%',
        'https://images.unsplash.com/photo-1444464666168-49d633b86797?auto=format&fit=crop&w=800&q=80'
    ),
    # Jeans — show actual blue denim jeans
    (
        '%Jeans%',
        'https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=800&q=80'
    ),
    # Car Polish — show car detailing / polishing
    (
        '%Car Polish%',
        'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=800&q=80'
    ),
]

conn = sqlite3.connect(str(DB))
c    = conn.cursor()

for pattern, url in FIXES:
    c.execute(
        'UPDATE products SET image_url = ? WHERE name LIKE ?',
        (url, pattern)
    )
    print(f'  Updated {c.rowcount} rows matching "{pattern}"')

conn.commit()
conn.close()
print('Done — images fixed.')
