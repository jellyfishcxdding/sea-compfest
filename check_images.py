import sqlite3

conn = sqlite3.connect('data/inventory.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("""
    SELECT id, name, image_url FROM products
    WHERE name LIKE '%Bird%'
       OR name LIKE '%Jeans%'
       OR name LIKE '%Polish%'
       OR name LIKE '%Seed%'
    ORDER BY name
""")
rows = c.fetchall()
for r in rows:
    print(r['id'], '|', r['name'], '|', r['image_url'][:70])
conn.close()
