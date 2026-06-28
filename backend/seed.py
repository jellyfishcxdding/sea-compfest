import sqlite3
import random
import bcrypt
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')

AUTH_DB = os.path.join(DATA_DIR, 'auth.db')
SELLER_DB = os.path.join(DATA_DIR, 'seller.db')
INVENTORY_DB = os.path.join(DATA_DIR, 'inventory.db')
TRANSACTIONS_DB = os.path.join(DATA_DIR, 'transactions.db')

def get_bridged_db():
    conn = sqlite3.connect(AUTH_DB)
    c = conn.cursor()
    c.execute(f"ATTACH DATABASE '{SELLER_DB}' AS seller")
    c.execute(f"ATTACH DATABASE '{INVENTORY_DB}' AS inventory")
    c.execute(f"ATTACH DATABASE '{TRANSACTIONS_DB}' AS transactions")
    return conn

def create_schema(conn):
    c = conn.cursor()
    
    # 1. AUTH DB Schema
    c.execute('DROP TABLE IF EXISTS user_roles')
    c.execute('DROP TABLE IF EXISTS wallets')
    c.execute('DROP TABLE IF EXISTS users')
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE user_roles (
            user_id INTEGER,
            role TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE wallets (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # 2. SELLER DB Schema
    c.execute('DROP TABLE IF EXISTS seller.stores')
    c.execute('''
        CREATE TABLE seller.stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            name TEXT UNIQUE NOT NULL,
            city TEXT,
            rating REAL,
            description TEXT,
            image_url TEXT
        )
    ''')
    
    # 3. INVENTORY DB Schema
    c.execute('DROP TABLE IF EXISTS inventory.products')
    c.execute('''
        CREATE TABLE inventory.products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER,
            name TEXT,
            description TEXT,
            price REAL,
            stock INTEGER,
            image_url TEXT,
            FOREIGN KEY(store_id) REFERENCES stores(id)
        )
    ''')
    
    # 3. TRANSACTIONS DB Schema
    c.execute('DROP TABLE IF EXISTS transactions.order_items')
    c.execute('DROP TABLE IF EXISTS transactions.orders')
    c.execute('DROP TABLE IF EXISTS transactions.cart_items')
    c.execute('DROP TABLE IF EXISTS transactions.app_reviews')
    
    c.execute('''
        CREATE TABLE transactions.cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            qty INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE transactions.orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            store_id INTEGER,
            total_price REAL,
            delivery_fee REAL,
            payment_method TEXT,
            status TEXT DEFAULT 'Sedang Dikemas',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE transactions.order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            qty INTEGER,
            price_at_time REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')
    c.execute('''
        CREATE TABLE transactions.app_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

def seed_data(conn):
    c = conn.cursor()
    print("Seeding dummy users...")
    pw = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('buyer', pw))
    buyer_id = c.lastrowid
    c.execute('INSERT INTO user_roles (user_id, role) VALUES (?, ?)', (buyer_id, 'Buyer'))
    c.execute('INSERT INTO wallets (user_id, balance) VALUES (?, ?)', (buyer_id, 5000000))
    
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('seller', pw))
    seller_id = c.lastrowid
    c.execute('INSERT INTO user_roles (user_id, role) VALUES (?, ?)', (seller_id, 'Seller'))
    c.execute('INSERT INTO wallets (user_id, balance) VALUES (?, ?)', (seller_id, 0))
    
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('driver', pw))
    driver_id = c.lastrowid
    c.execute('INSERT INTO user_roles (user_id, role) VALUES (?, ?)', (driver_id, 'Driver'))
    c.execute('INSERT INTO wallets (user_id, balance) VALUES (?, ?)', (driver_id, 0))
    
    print("Generating 100 stores...")
    prefixes = ['Eco', 'Tech', 'Style', 'Smart', 'Global', 'Fast', 'Mega', 'Super', 'Best', 'Pro', 'Ocean', 'Sky', 'Urban', 'Zen', 'Prime']
    suffixes = ['Life', 'Store', 'Shop', 'Mart', 'Hub', 'Zone', 'World', 'Boutique', 'Gear', 'Market', 'Goods', 'Works', 'Emporium', 'Bazaar']
    cities = ['Jakarta Pusat', 'Jakarta Selatan', 'Surabaya', 'Bandung', 'Medan', 'Bali', 'Yogyakarta', 'Semarang']
    
    store_images = [
        'https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=300&q=80',
        'https://images.unsplash.com/photo-1534452203293-494d7ddbf7e0?auto=format&fit=crop&w=300&q=80',
        'https://images.unsplash.com/photo-1588666309990-d68f08e3d4a6?auto=format&fit=crop&w=300&q=80',
        'https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=300&q=80'
    ]

    prod_map = {
        'Fjallraven Foldsack Backpack': 'https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_.jpg',
        'Mens Casual T-Shirt': 'https://fakestoreapi.com/img/71-3HjGNDUL._AC_SY879._SX._UX._SY._UY_.jpg',
        'Mens Cotton Jacket': 'https://fakestoreapi.com/img/71li-ujtlVG._AC_UX679_.jpg',
        'Mens Casual Slim Fit': 'https://fakestoreapi.com/img/71YXzeOuslL._AC_UY879_.jpg',
        'Womens Legends Naga Gold': 'https://fakestoreapi.com/img/71pWzhdJNwL._AC_UL640_QL65_ML3_.jpg',
        'Solid Gold Petite Micropave': 'https://fakestoreapi.com/img/61sbMiUnoGL._AC_UL640_QL65_ML3_.jpg',
        'White Gold Plated Princess': 'https://fakestoreapi.com/img/71YAIFU48IL._AC_UL640_QL65_ML3_.jpg',
        'WD 2TB Portable Hard Drive': 'https://fakestoreapi.com/img/61IBBVJvSDL._AC_SY879_.jpg',
        'SanDisk SSD PLUS 1TB': 'https://fakestoreapi.com/img/61U7T1koQqL._AC_SX679_.jpg',
        'Silicon Power 256GB SSD': 'https://fakestoreapi.com/img/71kWymZ+c+L._AC_SX679_.jpg',
        'WD 4TB Gaming Drive': 'https://fakestoreapi.com/img/61mtL65D4cG._AC_SX679_.jpg',
        'Acer 21.5 inches Full HD': 'https://fakestoreapi.com/img/81QpkIctqPL._AC_SX679_.jpg',
        'Samsung 49-Inch Curved Monitor': 'https://fakestoreapi.com/img/81Zt42O02K._AC_SX679_.jpg',
        'Womens 3-in-1 Snowboard Jacket': 'https://fakestoreapi.com/img/51Y5NI-I5jL._AC_UX679_.jpg'
    }

    prod_names = list(prod_map.keys())

    store_ids = []
    for i in range(1, 101):
        name = random.choice(prefixes) + random.choice(suffixes) + str(i)
        city = random.choice(cities)
        rating = round(random.uniform(4.0, 5.0), 1)
        desc = f"Welcome to {name}! We are a premium store located in {city} providing top-tier products."
        store_image = random.choice(store_images)
        c.execute('INSERT INTO seller.stores (seller_id, name, city, rating, description, image_url) VALUES (?, ?, ?, ?, ?, ?)', (seller_id, name, city, rating, desc, store_image))
        store_ids.append(c.lastrowid)
        
    print("Generating 10,000 products (100 per store)...")
    products_to_insert = []
    for s_id in store_ids:
        for j in range(100):
            base_name = random.choice(prod_names)
            p_name = base_name + f' Pro Max {j}'
            desc = "High quality premium product from our store."
            price = random.randint(15, 250) * 1000
            stock = random.randint(10, 500)
            img = prod_map[base_name]
            products_to_insert.append((s_id, p_name, desc, price, stock, img))
            
    c.executemany('INSERT INTO inventory.products (store_id, name, description, price, stock, image_url) VALUES (?, ?, ?, ?, ?, ?)', products_to_insert)

    print("Seeding some app reviews...")
    c.execute("INSERT INTO transactions.app_reviews (name, rating, comment) VALUES ('Gracia', 5, 'Like Amazon, but green! Love it.')")
    c.execute("INSERT INTO transactions.app_reviews (name, rating, comment) VALUES ('Budi', 4, 'Very fast and responsive.')")

if __name__ == '__main__':
    # Cleanup old seapedia.db if it exists, although we use data/ now.
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Remove old unified DB if it exists to avoid confusion
    if os.path.exists('data/seapedia.db'):
        os.remove('data/seapedia.db')
        
    conn = get_bridged_db()
    create_schema(conn)
    seed_data(conn)
    conn.commit()
    conn.close()
    print("Bridged Databases (auth.db, seller.db, inventory.db, transactions.db) seeded successfully!")
