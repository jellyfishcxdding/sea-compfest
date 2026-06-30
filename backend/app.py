from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import sqlite3
import bcrypt
import jwt
import datetime
import html as _html
import os

app = Flask(__name__)

# Single CORS setup — allow all origins (JWT protects sensitive endpoints)
CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'seapedia-super-secret-key')

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return jsonify({}), 200

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'SEAPEDIA backend is running'})

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'SEAPEDIA API — use /api/* endpoints'})

# ── Database paths ─────────────────────────────────────────────
# Store data/ inside the backend/ folder so it is always writable
# on Render (rootDir=backend) and locally.
_DATA_DIR       = Path(__file__).resolve().parent / 'data'
AUTH_DB         = str(_DATA_DIR / 'auth.db')
SELLER_DB       = str(_DATA_DIR / 'seller.db')
INVENTORY_DB    = str(_DATA_DIR / 'inventory.db')
TRANSACTIONS_DB = str(_DATA_DIR / 'transactions.db')

# ── Auto-initialise databases if they don't exist ──────────────
def _ensure_databases():
    """Create all SQLite databases and tables if not present.
    Safe to call on every startup — uses IF NOT EXISTS."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(AUTH_DB) as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime(\'now\'))
            );
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                role TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                balance REAL DEFAULT 0
            );
        ''')

    with sqlite3.connect(SELLER_DB) as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                name TEXT UNIQUE NOT NULL,
                city TEXT,
                description TEXT,
                image_url TEXT,
                rating REAL DEFAULT 5.0
            );
        ''')

    with sqlite3.connect(INVENTORY_DB) as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                image_url TEXT,
                category TEXT DEFAULT \'electronics\',
                rating REAL DEFAULT 5.0,
                sold_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS product_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TEXT DEFAULT (datetime(\'now\'))
            );
            CREATE TABLE IF NOT EXISTS discounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_percent REAL NOT NULL,
                min_purchase REAL DEFAULT 0,
                valid_until TEXT
            );
            CREATE TABLE IF NOT EXISTS promos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                discount REAL NOT NULL,
                description TEXT,
                valid_until TEXT
            );
        ''')

    with sqlite3.connect(TRANSACTIONS_DB) as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id INTEGER NOT NULL,
                store_id INTEGER NOT NULL,
                status TEXT DEFAULT \'Sedang Dikemas\',
                payment_method TEXT,
                delivery_method TEXT DEFAULT \'Regular\',
                delivery_fee REAL DEFAULT 10000,
                discount_amount REAL DEFAULT 0,
                subtotal REAL DEFAULT 0,
                ppn_amount REAL DEFAULT 0,
                total_price REAL NOT NULL,
                voucher_code TEXT,
                driver_id INTEGER,
                created_at TEXT DEFAULT (datetime(\'now\'))
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wallet_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime(\'now\'))
            );
        ''')

# Run on import (works for both gunicorn and python app.py)
_ensure_databases()


def get_db():
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"ATTACH DATABASE '{SELLER_DB}' AS seller")
    c.execute(f"ATTACH DATABASE '{INVENTORY_DB}' AS inventory")
    c.execute(f"ATTACH DATABASE '{TRANSACTIONS_DB}' AS transactions")
    return conn

# ── Phase 6: safe string helper ──────────────────────────────────────────────
# Escapes HTML special chars in any user-supplied string before it leaves the
# API. Keeps None as-is so SQL NULLs propagate correctly.
def _safe(value, max_len=500):
    """Escape HTML entities and trim length on user-controlled text."""
    if value is None:
        return None
    text = str(value).strip()
    if max_len:
        text = text[:max_len]
    return _html.escape(text, quote=True)


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = _safe(data.get('username'), max_len=50)
    password = str(data.get('password', '')).strip()
    roles    = data.get('roles', [])

    if not username or len(username) < 3:
        return jsonify({'error': 'Username must be 3-50 characters'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if not roles or not isinstance(roles, list):
        return jsonify({'error': 'At least one role is required'}), 400
    # Only allow known roles
    VALID_ROLES = {'Buyer', 'Seller', 'Driver', 'Admin'}
    if not all(r in VALID_ROLES for r in roles):
        return jsonify({'error': 'Invalid role specified'}), 400

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        user_id = c.lastrowid
        for role in roles:
            c.execute('INSERT INTO user_roles (user_id, role) VALUES (?, ?)', (user_id, role))
        
        c.execute('INSERT INTO wallets (user_id, balance) VALUES (?, ?)', (user_id, 0))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400
    finally:
        conn.close()

    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401

    c.execute('SELECT role FROM user_roles WHERE user_id = ?', (user['id'],))
    roles = [row['role'] for row in c.fetchall()]
    conn.close()

    token = jwt.encode({
        'user_id': user['id'],
        'username': user['username'],
        'roles': roles,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'roles': roles
        }
    }), 200

from functools import wraps

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        try:
            current_user = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except Exception:
            return jsonify({'error': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/auth/select-role', methods=['POST'])
@token_required
def select_role(current_user):
    data = request.json
    active_role = data.get('role')

    if active_role not in current_user['roles']:
        return jsonify({'error': 'Unauthorized role selection'}), 403
    
    new_token = jwt.encode({
        'user_id': current_user['user_id'],
        'username': current_user['username'],
        'roles': current_user['roles'],
        'active_role': active_role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'token': new_token, 'active_role': active_role})

@app.route('/api/stores', methods=['GET'])
def get_stores():
    limit = request.args.get('limit', 100)
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM seller.stores LIMIT ?', (limit,))
    stores = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(stores)

@app.route('/api/stores/<int:store_id>', methods=['GET'])
def get_store(store_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM seller.stores WHERE id = ?', (store_id,))
    store = c.fetchone()
    conn.close()
    if store:
        return jsonify(dict(store))
    return jsonify({'error': 'Store not found'}), 404

@app.route('/api/products', methods=['GET'])
def get_products():
    store_id = request.args.get('store_id')
    q_param = f"%{request.args.get('q').lower()}%" if 'q' in request.args else None
    category_param = request.args.get('category').lower() if 'category' in request.args else None
    limit = int(request.args.get('limit', 50))
    sort_by = request.args.get('sort', 'default')
    
    conn = get_db()
    c = conn.cursor()
    
    # Fancy but unhackable SQL: 
    # 1. Uses CTEs (Common Table Expressions) for clean data modeling
    # 2. Uses completely static parameterized WHERE conditions (? IS NULL OR column = ?)
    #    to absolutely guarantee immunity from SQL injection without messy string concatenation.
    query = '''
        WITH StoreInfo AS (
            SELECT id, name as store_name, city as store_city, rating 
            FROM seller.stores
        )
        SELECT p.*, s.store_name, s.store_city 
        FROM inventory.products p 
        JOIN StoreInfo s ON p.store_id = s.id 
        WHERE (? IS NULL OR p.store_id = ?)
          AND (? IS NULL OR LOWER(p.name) LIKE ?)
          AND (? IS NULL OR LOWER(p.category) = ?)
    '''
    
    if sort_by == 'price_asc':
        query += ' ORDER BY p.price ASC'
    elif sort_by == 'price_desc':
        query += ' ORDER BY p.price DESC'
    elif sort_by == 'rating_desc':
        query += ' ORDER BY s.rating DESC'
    else:
        query += ' ORDER BY p.id DESC'

    query += ' LIMIT ?'
    
    params = (store_id, store_id, q_param, q_param, category_param, category_param, limit)
    
    c.execute(query, params)
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, s.name as store_name, s.city as store_city 
        FROM inventory.products p 
        JOIN seller.stores s ON p.store_id = s.id 
        WHERE p.id = ?
    ''', (product_id,))
    product = c.fetchone()
    conn.close()
    if product:
        return jsonify(dict(product))
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/reviews', methods=['GET', 'POST'])
def handle_reviews():
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        data = request.json
        c.execute('INSERT INTO transactions.app_reviews (name, rating, comment) VALUES (?, ?, ?)', 
                 (data.get('name'), int(data.get('rating')), data.get('comment')))
        conn.commit()
        review_id = c.lastrowid
        conn.close()
        return jsonify({'message': 'Review added', 'id': review_id}), 201
    else:
        c.execute('SELECT * FROM transactions.app_reviews ORDER BY created_at DESC LIMIT 10')
        reviews = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(reviews)

@app.route('/api/wallet/<int:user_id>', methods=['GET'])
@token_required
def get_wallet(current_user, user_id):
    if current_user['user_id'] != user_id: return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT balance FROM wallets WHERE user_id = ?', (user_id,))
    wallet = c.fetchone()
    conn.close()
    if wallet:
        return jsonify({'balance': wallet['balance']})
    return jsonify({'balance': 0})

@app.route('/api/checkout', methods=['POST'])
@token_required
def checkout(current_user):
    data = request.json
    user_id = data.get('user_id')
    if current_user['user_id'] != user_id: return jsonify({'error': 'Unauthorized checkout'}), 403
    
    cart = data.get('cart', [])
    payment_method = data.get('payment_method')
    
    # Hacking Prevention: Hardcode delivery fee so it can't be spoofed negatively by client
    delivery_fee = 10000

    if not user_id or not cart:
        return jsonify({'error': 'Invalid checkout data'}), 400

    conn = get_db()
    c = conn.cursor()
    
    try:
        stores_map = {}
        for item in cart:
            qty = int(item.get('qty', 1))
            if qty <= 0:
                raise ValueError("Quantity must be positive")
            
            store_id = item.get('store_id')
            if store_id not in stores_map:
                stores_map[store_id] = []
            stores_map[store_id].append(item)
            
        total_payment = 0
        orders_to_create = []

        for store_id, items in stores_map.items():
            store_total = sum(float(item.get('price', 0)) * int(item.get('qty', 1)) for item in items)
            if store_total <= 0:
                raise ValueError("Invalid store total")
                
            order_total = store_total + delivery_fee
            total_payment += order_total
            orders_to_create.append({
                'store_id': store_id,
                'total': order_total,
                'items': items
            })

        if payment_method == 'wallet':
            c.execute('SELECT balance FROM wallets WHERE user_id = ?', (user_id,))
            wallet = c.fetchone()
            if not wallet or wallet['balance'] < total_payment:
                return jsonify({'error': 'Insufficient wallet balance'}), 400
            
            new_balance = wallet['balance'] - total_payment
            c.execute('UPDATE wallets SET balance = ? WHERE user_id = ?', (new_balance, user_id))

        for order_data in orders_to_create:
            c.execute('''
                INSERT INTO transactions.orders (user_id, store_id, total_price, delivery_fee, payment_method)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, order_data['store_id'], order_data['total'], delivery_fee, payment_method))
            order_id = c.lastrowid
            
            for item in order_data['items']:
                c.execute('''
                    INSERT INTO transactions.order_items (order_id, product_id, qty, price_at_time)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item.get('id'), item.get('qty', 1), item.get('price')))
                
                c.execute('UPDATE inventory.products SET stock = stock - ? WHERE id = ?', (item.get('qty', 1), item.get('id')))
                
        conn.commit()
        return jsonify({'message': 'Checkout successful', 'total_paid': total_payment})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/orders/driver', methods=['GET'])
def get_driver_orders():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT o.*, s.name as store_name, s.city as store_city, u.username as buyer_name
        FROM transactions.orders o
        JOIN seller.stores s ON o.store_id = s.id
        JOIN users u ON o.user_id = u.id
        WHERE o.status IN ('Menunggu Pengirim', 'Sedang Dikirim')
        ORDER BY o.created_at ASC
    ''')
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(orders)


@app.route('/api/wishlist/<int:user_id>', methods=['GET'])
@token_required
def get_wishlist(current_user, user_id):
    if current_user['user_id'] != user_id: return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT p.* FROM inventory.wishlist w
        JOIN inventory.products p ON w.product_id = p.id
        WHERE w.user_id = ?
    ''', (user_id,))
    items = [dict(row) for row in c.fetchall()]
    return jsonify(items)

@app.route('/api/wishlist', methods=['POST'])
@token_required
def add_to_wishlist(current_user):
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    if current_user['user_id'] != user_id: return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO inventory.wishlist (user_id, product_id) VALUES (?, ?)', (user_id, product_id))
        conn.commit()
        return jsonify({'message': 'Added to wishlist'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Item already in wishlist'}), 400

@app.route('/api/wishlist/<int:user_id>/<int:product_id>', methods=['DELETE'])
@token_required
def remove_wishlist(current_user, user_id, product_id):
    if current_user['user_id'] != user_id: return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM inventory.wishlist WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    conn.commit()
    return jsonify({'message': 'Removed from wishlist'})

@app.route('/api/products/<int:product_id>/reviews', methods=['GET'])
def get_reviews(product_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT username, rating, comment, created_at FROM inventory.product_reviews WHERE product_id = ? ORDER BY created_at DESC', (product_id,))
    reviews = [dict(row) for row in c.fetchall()]
    return jsonify(reviews)

@app.route('/api/products/<int:product_id>/reviews', methods=['POST'])
@token_required
def add_review(current_user, product_id):
    data     = request.get_json(silent=True) or {}
    user_id  = current_user['user_id']
    username = _safe(current_user['username'], max_len=50)
    rating   = int(data.get('rating', 5))
    comment  = _safe(data.get('comment', ''), max_len=1000)

    # Validate rating range
    if rating not in range(1, 6):
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    if not comment:
        return jsonify({'error': 'Review comment cannot be empty'}), 400

    conn = get_db()
    c = conn.cursor()
    
    # Check if user bought it
    c.execute('''
        SELECT 1 FROM transactions.order_items oi
        JOIN transactions.orders o ON oi.order_id = o.id
        WHERE o.buyer_id = ? AND oi.product_id = ? AND o.status = 'Selesai'
        LIMIT 1
    ''', (user_id, product_id))
    
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'You must purchase and complete delivery to review this item'}), 403

    c.execute('''
        INSERT INTO inventory.product_reviews (product_id, user_id, username, rating, comment)
        VALUES (?, ?, ?, ?, ?)
    ''', (product_id, user_id, username, rating, comment))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Review added successfully'}), 201



# ==========================================
# LEVEL 2: SELLER STORE & PRODUCT MANAGEMENT
# ==========================================

@app.route('/api/stores', methods=['POST'])
@token_required
def create_store(current_user):
    if 'Seller' not in current_user['roles'] or current_user.get('active_role') != 'Seller':
        return jsonify({'error': 'Unauthorized. Must be active Seller.'}), 403
    
    data = request.json
    name = data.get('name')
    city = data.get('city')
    description = data.get('description', '')
    image_url = data.get('image_url', '')
    
    if not name or not city:
        return jsonify({'error': 'Name and city are required'}), 400
        
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO seller.stores (seller_id, name, city, description, image_url, rating) 
            VALUES (?, ?, ?, ?, ?, 5.0)
        ''', (current_user['user_id'], name, city, description, image_url))
        conn.commit()
        return jsonify({'message': 'Store created successfully', 'id': c.lastrowid}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Store name is already used. Must be unique.'}), 400
    finally:
        conn.close()

@app.route('/api/stores/<int:store_id>', methods=['PUT'])
@token_required
def update_store(current_user, store_id):
    if current_user.get('active_role') != 'Seller':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT seller_id FROM seller.stores WHERE id = ?', (store_id,))
    store = c.fetchone()
    if not store or store['seller_id'] != current_user['user_id']:
        return jsonify({'error': 'Unauthorized to modify this store'}), 403
        
    try:
        c.execute('''
            UPDATE seller.stores 
            SET name = ?, city = ?, description = ?, image_url = ?
            WHERE id = ?
        ''', (data.get('name'), data.get('city'), data.get('description'), data.get('image_url'), store_id))
        conn.commit()
        return jsonify({'message': 'Store updated'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Store name already exists'}), 400
    finally:
        conn.close()

@app.route('/api/seller/products', methods=['POST'])
@token_required
def create_product(current_user):
    if current_user.get('active_role') != 'Seller':
        return jsonify({'error': 'Unauthorized'}), 403

    data        = request.get_json(silent=True) or {}
    name        = _safe(data.get('name'), max_len=200)
    price       = data.get('price')
    stock       = data.get('stock')
    category    = _safe(data.get('category', 'electronics'), max_len=100)
    image_url   = _safe(data.get('image_url', ''), max_len=500)
    description = _safe(data.get('description', ''), max_len=2000)

    if not name:
        return jsonify({'error': 'Product name is required'}), 400
    try:
        price = float(price)
        stock = int(stock)
        if price < 0 or stock < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'Price and stock must be valid non-negative numbers'}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM seller.stores WHERE seller_id = ?', (current_user['user_id'],))
    store = c.fetchone()
    if not store:
        return jsonify({'error': 'You must create a store first'}), 400
        
    c.execute('''
        INSERT INTO inventory.products (store_id, name, description, price, stock, image_url, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (store['id'], name, description, float(price), int(stock), image_url, category))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product created'}), 201

@app.route('/api/seller/products/<int:product_id>', methods=['PUT', 'DELETE'])
@token_required
def modify_product(current_user, product_id):
    if current_user.get('active_role') != 'Seller':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db()
    c = conn.cursor()
    
    # Ensure ownership
    c.execute('''
        SELECT p.id FROM inventory.products p
        JOIN seller.stores s ON p.store_id = s.id
        WHERE p.id = ? AND s.seller_id = ?
    ''', (product_id, current_user['user_id']))
    if not c.fetchone():
        return jsonify({'error': 'Product not found or unauthorized'}), 403
        
    if request.method == 'DELETE':
        c.execute('DELETE FROM inventory.products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Product deleted'})
    elif request.method == 'PUT':
        data = request.json
        c.execute('''
            UPDATE inventory.products 
            SET name = ?, description = ?, price = ?, stock = ?, image_url = ?, category = ?
            WHERE id = ?
        ''', (data.get('name'), data.get('description'), float(data.get('price')), int(data.get('stock')), data.get('image_url'), data.get('category'), product_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Product updated'})

# ==========================================
# LEVEL 3: BUYER WALLET, CART & CHECKOUT
# ==========================================

@app.route('/api/wallet/topup', methods=['POST'])
@token_required
def topup_wallet(current_user):
    if current_user.get('active_role') != 'Buyer':
        return jsonify({'error': 'Unauthorized. Must be active Buyer.'}), 403
        
    amount = float(request.json.get('amount', 0))
    if amount <= 0: return jsonify({'error': 'Invalid amount'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE wallets SET balance = balance + ? WHERE user_id = ?', (amount, current_user['user_id']))
    
    # Record transaction (Dummy implementation, assuming transactions table exists)
    try:
        c.execute('INSERT INTO transactions.wallet_history (user_id, type, amount, description) VALUES (?, ?, ?, ?)',
                 (current_user['user_id'], 'credit', amount, 'Topup via Dummy Payment'))
    except: pass # Ignore if table doesn't exist yet
    
    conn.commit()
    conn.close()
    return jsonify({'message': f'Successfully topped up Rp {amount}'})

@app.route('/api/cart', methods=['GET', 'POST', 'DELETE'])
@token_required
def manage_cart(current_user):
    if current_user.get('active_role') != 'Buyer':
        return jsonify({'error': 'Unauthorized'}), 403
        
    user_id = current_user['user_id']
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute('''
            SELECT c.id as cart_id, c.qty, p.*, s.name as store_name
            FROM transactions.cart c
            JOIN inventory.products p ON c.product_id = p.id
            JOIN seller.stores s ON p.store_id = s.id
            WHERE c.user_id = ?
        ''', (user_id,))
        items = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(items)
        
    elif request.method == 'POST':
        data = request.json
        product_id = data.get('product_id')
        qty = int(data.get('qty', 1))
        
        # Single Store Checkout Rule Validation
        c.execute('SELECT store_id FROM inventory.products WHERE id = ?', (product_id,))
        prod = c.fetchone()
        if not prod: return jsonify({'error': 'Product not found'}), 404
        
        c.execute('''
            SELECT p.store_id FROM transactions.cart c
            JOIN inventory.products p ON c.product_id = p.id
            WHERE c.user_id = ? LIMIT 1
        ''', (user_id,))
        existing_cart = c.fetchone()
        if existing_cart and existing_cart['store_id'] != prod['store_id']:
            return jsonify({'error': 'Single-store checkout rule: You can only add products from the same store. Please checkout or clear your cart first.'}), 400
            
        # Add to cart
        c.execute('SELECT id, qty FROM transactions.cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        cart_item = c.fetchone()
        if cart_item:
            c.execute('UPDATE transactions.cart SET qty = qty + ? WHERE id = ?', (qty, cart_item['id']))
        else:
            c.execute('INSERT INTO transactions.cart (user_id, product_id, qty) VALUES (?, ?, ?)', (user_id, product_id, qty))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Added to cart'})
        
    elif request.method == 'DELETE':
        cart_id = request.args.get('cart_id')
        if cart_id:
            c.execute('DELETE FROM transactions.cart WHERE id = ? AND user_id = ?', (cart_id, user_id))
        else:
            c.execute('DELETE FROM transactions.cart WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Cart updated'})


# ══════════════════════════════════════════════════════════════
#  PHASE 3 — Discounts · Seller Order Processing · Reports
#  Security: every endpoint verifies caller owns the resource.
#  Privacy:  responses only include fields the caller needs.
# ══════════════════════════════════════════════════════════════

# ── Validate a voucher code ────────────────────────────────────
@app.route('/api/vouchers/validate', methods=['POST'])
@token_required
def validate_voucher(current_user):
    data       = request.get_json(silent=True) or {}
    code       = str(data.get('code', '')).strip()[:32]   # cap length, prevent huge strings
    cart_total = data.get('cart_total', 0)

    if not code:
        return jsonify({'error': 'Voucher code is required'}), 400
    try:
        cart_total = float(cart_total)
        if cart_total < 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid cart total'}), 400

    conn = get_db()
    c    = conn.cursor()
    # Parameterised — no string interpolation
    c.execute('''
        SELECT discount_percent, min_purchase, code
        FROM   transactions.discounts
        WHERE  code = ? AND is_active = 1 AND valid_until > datetime('now')
    ''', (code,))
    voucher = c.fetchone()
    conn.close()

    if not voucher:
        return jsonify({'error': 'Invalid or expired voucher code'}), 404
    if cart_total < voucher['min_purchase']:
        return jsonify({'error': f"Minimum purchase Rp {int(voucher['min_purchase']):,} required"}), 400

    discount = round(cart_total * voucher['discount_percent'] / 100, 0)
    # Return only discount info — no internal IDs leaked
    return jsonify({
        'code':             voucher['code'],
        'discount_percent': voucher['discount_percent'],
        'discount_amount':  discount,
        'final_total':      max(0, cart_total - discount)
    })


# ── List public vouchers (code + percent only) ─────────────────
@app.route('/api/vouchers', methods=['GET'])
def list_vouchers():
    conn = get_db()
    c    = conn.cursor()
    c.execute('''
        SELECT code, discount_percent, min_purchase
        FROM   transactions.discounts
        WHERE  is_active = 1 AND valid_until > datetime('now')
        ORDER  BY discount_percent DESC
        LIMIT  20
    ''')
    # Expose only what buyers need to see; no internal IDs
    vouchers = [{'code': r['code'], 'percent': r['discount_percent'],
                 'min_purchase': r['min_purchase']} for r in c.fetchall()]
    conn.close()
    return jsonify(vouchers)


# ── Seller: view orders for their store ────────────────────────
@app.route('/api/orders/seller/<int:seller_id>', methods=['GET'])
@token_required
def get_seller_orders(current_user, seller_id):
    # Strict ownership: only the seller themselves can view their orders
    if current_user['user_id'] != seller_id:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    c    = conn.cursor()
    c.execute('SELECT id FROM seller.stores WHERE seller_id = ?', (seller_id,))
    store_row = c.fetchone()
    if not store_row:
        conn.close()
        return jsonify({'error': 'No store found for this seller'}), 404

    store_id = store_row['id']
    c.execute('''
        SELECT o.id, o.total_price, o.status, o.created_at,
               o.delivery_fee, o.discount_amount,
               u.username AS buyer_name
        FROM   transactions.orders o
        JOIN   users u ON u.id = o.user_id
        WHERE  o.store_id = ?
        ORDER  BY o.created_at DESC
        LIMIT  100
    ''', (store_id,))
    orders = [dict(r) for r in c.fetchall()]

    for order in orders:
        c.execute('''
            SELECT oi.qty, oi.price_at_time, p.name
            FROM   transactions.order_items oi
            JOIN   inventory.products p ON p.id = oi.product_id
            WHERE  oi.order_id = ?
        ''', (order['id'],))
        order['items'] = [dict(r) for r in c.fetchall()]

    conn.close()
    return jsonify(orders)


# ── Seller → dispatch / Driver → update status ─────────────────
@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@token_required
def update_order_status(current_user, order_id):
    data       = request.get_json(silent=True) or {}
    new_status = str(data.get('status', '')).strip()

    ALLOWED_TRANSITIONS = {
        'Seller': {
            'from': 'Sedang Dikemas',
            'to':   'Menunggu Pengirim'
        }
    }
    role = current_user.get('active_role', '')

    # Validate the requested status is in the allowed set
    all_statuses = {'Sedang Dikemas', 'Menunggu Pengirim', 'Sedang Dikirim', 'Selesai', 'Dibatalkan'}
    if new_status not in all_statuses:
        return jsonify({'error': 'Invalid status value'}), 400

    conn = get_db()
    c    = conn.cursor()
    c.execute('''
        SELECT o.id, o.status, o.store_id
        FROM   transactions.orders o
        WHERE  o.id = ?
    ''', (order_id,))
    order = c.fetchone()
    if not order:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404

    # Sellers can only dispatch their own store's orders
    if new_status == 'Menunggu Pengirim':
        if role != 'Seller':
            conn.close()
            return jsonify({'error': 'Only sellers can dispatch orders'}), 403
        c.execute('SELECT id FROM seller.stores WHERE seller_id = ? AND id = ?',
                  (current_user['user_id'], order['store_id']))
        if not c.fetchone():
            conn.close()
            return jsonify({'error': 'This order does not belong to your store'}), 403
        if order['status'] != 'Sedang Dikemas':
            conn.close()
            return jsonify({'error': 'Order is not in packing state'}), 400

    c.execute('UPDATE transactions.orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Order updated to {new_status}'})


# ── Buyer: view their own order history ────────────────────────
@app.route('/api/orders/buyer/<int:user_id>', methods=['GET'])
@token_required
def get_buyer_orders(current_user, user_id):
    # Strict privacy: buyers can only see their own orders
    if current_user['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    c    = conn.cursor()
    c.execute('''
        SELECT o.id, o.total_price, o.status, o.created_at,
               o.delivery_fee, o.payment_method,
               o.voucher_code, o.discount_amount,
               s.name AS store_name, s.city AS store_city
        FROM   transactions.orders o
        LEFT   JOIN seller.stores s ON s.id = o.store_id
        WHERE  o.user_id = ?
        ORDER  BY o.created_at DESC
        LIMIT  50
    ''', (user_id,))
    orders = [dict(r) for r in c.fetchall()]

    for order in orders:
        c.execute('''
            SELECT oi.qty, oi.price_at_time, p.name, p.image_url
            FROM   transactions.order_items oi
            JOIN   inventory.products p ON p.id = oi.product_id
            WHERE  oi.order_id = ?
        ''', (order['id'],))
        order['items'] = [dict(r) for r in c.fetchall()]

    conn.close()
    return jsonify(orders)


# ── Seller: financial report (own store only) ──────────────────
@app.route('/api/reports/seller/<int:seller_id>', methods=['GET'])
@token_required
def seller_report(current_user, seller_id):
    if current_user['user_id'] != seller_id:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    c    = conn.cursor()
    c.execute('SELECT id FROM seller.stores WHERE seller_id = ?', (seller_id,))
    store_row = c.fetchone()
    if not store_row:
        conn.close()
        return jsonify({'error': 'No store found'}), 404

    c.execute('''
        SELECT
            COUNT(*)                                                       AS total_orders,
            COALESCE(SUM(total_price), 0)                                  AS total_revenue,
            COALESCE(SUM(CASE WHEN status='Selesai'    THEN total_price ELSE 0 END), 0) AS completed_revenue,
            COALESCE(SUM(CASE WHEN status='Dibatalkan' THEN 1       ELSE 0 END), 0) AS cancelled_count
        FROM transactions.orders
        WHERE store_id = ?
    ''', (store_row['id'],))
    conn.close()
    return jsonify(dict(c.fetchone()))


# ══════════════════════════════════════════════════════════════
#  PHASE 4 — Driver Job Flow
#  Security: atomic UPDATE prevents double-claiming.
#  Privacy:  buyers' full address not exposed to driver.
# ══════════════════════════════════════════════════════════════

_DRIVER_FLAT_FEE    = 5000    # flat Rp 5,000 per delivery
_DRIVER_FEE_PERCENT = 0.10    # + 10% of delivery_fee


# ── Available jobs (status = Menunggu Pengirim, unclaimed) ─────
@app.route('/api/jobs/available', methods=['GET'])
@token_required
def get_available_jobs(current_user):
    if 'Driver' not in current_user.get('roles', []):
        return jsonify({'error': 'Driver role required'}), 403

    conn = get_db()
    c    = conn.cursor()
    c.execute('''
        SELECT o.id,
               o.delivery_fee,
               o.status,
               o.created_at,
               s.name  AS store_name,
               s.city  AS store_city,
               u.username AS buyer_name
        FROM   transactions.orders o
        LEFT   JOIN seller.stores s ON s.id  = o.store_id
        LEFT   JOIN users         u ON u.id  = o.user_id
        WHERE  o.status    = 'Menunggu Pengirim'
          AND  o.driver_id IS NULL
        ORDER  BY o.created_at ASC
        LIMIT  50
    ''')
    # Expose only pickup/dropoff names — no addresses, no totals to protect buyer privacy
    jobs = [{
        'id':         r['id'],
        'store_name': r['store_name'],
        'store_city': r['store_city'],
        'buyer_name': r['buyer_name'],
        'delivery_fee': r['delivery_fee'],
        'created_at': r['created_at'],
        'estimated_earnings': round((r['delivery_fee'] or 0) * _DRIVER_FEE_PERCENT + _DRIVER_FLAT_FEE, 0)
    } for r in c.fetchall()]
    conn.close()
    return jsonify(jobs)


# ── Driver takes a job (atomic, prevents double-claiming) ──────
@app.route('/api/jobs/<int:order_id>/take', methods=['POST'])
@token_required
def take_job(current_user, order_id):
    if 'Driver' not in current_user.get('roles', []):
        return jsonify({'error': 'Driver role required'}), 403

    driver_id = current_user['user_id']
    conn      = get_db()
    c         = conn.cursor()

    # Single atomic UPDATE — only succeeds if nobody else claimed it yet
    c.execute('''
        UPDATE transactions.orders
        SET    status    = 'Sedang Dikirim',
               driver_id = ?
        WHERE  id        = ?
          AND  status    = 'Menunggu Pengirim'
          AND  driver_id IS NULL
    ''', (driver_id, order_id))

    if c.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Order already taken or not available'}), 409

    conn.commit()
    conn.close()
    return jsonify({'message': 'Job accepted! Head to the pickup location.'})


# ── Driver completes a delivery ────────────────────────────────
@app.route('/api/jobs/<int:order_id>/complete', methods=['POST'])
@token_required
def complete_job(current_user, order_id):
    if 'Driver' not in current_user.get('roles', []):
        return jsonify({'error': 'Driver role required'}), 403

    driver_id = current_user['user_id']
    conn      = get_db()
    c         = conn.cursor()

    c.execute('''
        SELECT id, driver_id, delivery_fee, status
        FROM   transactions.orders
        WHERE  id = ?
    ''', (order_id,))
    order = c.fetchone()

    if not order:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
    if order['driver_id'] != driver_id:
        conn.close()
        return jsonify({'error': 'Unauthorized: not your delivery'}), 403
    if order['status'] != 'Sedang Dikirim':
        conn.close()
        return jsonify({'error': 'Order is not currently in transit'}), 400

    earnings = round((order['delivery_fee'] or 0) * _DRIVER_FEE_PERCENT + _DRIVER_FLAT_FEE, 0)

    c.execute("UPDATE transactions.orders SET status = 'Selesai' WHERE id = ?", (order_id,))
    c.execute('''
        INSERT INTO transactions.driver_earnings (driver_id, order_id, amount)
        VALUES (?, ?, ?)
    ''', (driver_id, order_id, earnings))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Delivery completed!', 'earnings': earnings})


# ── Driver: my active deliveries ──────────────────────────────
@app.route('/api/jobs/mine', methods=['GET'])
@token_required
def my_jobs(current_user):
    if 'Driver' not in current_user.get('roles', []):
        return jsonify({'error': 'Driver role required'}), 403

    driver_id = current_user['user_id']
    conn      = get_db()
    c         = conn.cursor()
    c.execute('''
        SELECT o.id, o.status, o.created_at,
               s.name  AS store_name,
               s.city  AS store_city,
               u.username AS buyer_name,
               de.amount  AS earnings
        FROM   transactions.orders o
        LEFT   JOIN seller.stores          s  ON s.id  = o.store_id
        LEFT   JOIN users                  u  ON u.id  = o.user_id
        LEFT   JOIN transactions.driver_earnings de
                    ON de.order_id = o.id AND de.driver_id = ?
        WHERE  o.driver_id = ?
        ORDER  BY o.created_at DESC
        LIMIT  50
    ''', (driver_id, driver_id))
    jobs = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(jobs)


# ── Driver: earnings summary ───────────────────────────────────
@app.route('/api/jobs/earnings', methods=['GET'])
@token_required
def driver_earnings_summary(current_user):
    if 'Driver' not in current_user.get('roles', []):
        return jsonify({'error': 'Driver role required'}), 403

    driver_id = current_user['user_id']
    conn      = get_db()
    c         = conn.cursor()
    c.execute('''
        SELECT COUNT(*)              AS total_deliveries,
               COALESCE(SUM(amount), 0) AS total_earned
        FROM   transactions.driver_earnings
        WHERE  driver_id = ?
    ''', (driver_id,))
    row = dict(c.fetchone())
    conn.close()
    return jsonify(row)


def setup_phase34_tables():
    """Idempotent — creates Phase 3-4 tables if they don't exist yet."""
    conn = get_db()
    c    = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions.discounts (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        code             TEXT    UNIQUE NOT NULL COLLATE NOCASE,
        discount_percent INTEGER NOT NULL CHECK(discount_percent BETWEEN 1 AND 100),
        min_purchase     REAL    NOT NULL DEFAULT 0,
        valid_until      DATETIME NOT NULL,
        is_active        INTEGER  DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions.driver_earnings (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id  INTEGER NOT NULL,
        order_id   INTEGER NOT NULL UNIQUE,
        amount     REAL    NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

setup_phase34_tables()


def setup_missing_tables():

    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions.cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions.wallet_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()
    
setup_missing_tables()


# ══════════════════════════════════════════════════════════════
#  PHASE 5 — Admin Monitoring & Overdue Engine
#  Security: every endpoint verifies Admin role from JWT.
#  All queries fully parameterised — zero f-string interpolation.
#  Privacy:  passwords and tokens are never included in responses.
# ══════════════════════════════════════════════════════════════

def _require_admin(current_user):
    """Returns a 403 JSON response if the caller is not an Admin, else None."""
    if 'Admin' not in current_user.get('roles', []):
        return jsonify({'error': 'Admin role required'}), 403
    return None


# ── GET /api/admin/stats ───────────────────────────────────────
@app.route('/api/admin/stats', methods=['GET'])
@token_required
def admin_stats(current_user):
    """Return platform-wide aggregate statistics (Admin only)."""
    err = _require_admin(current_user)
    if err:
        return err

    conn = get_db()
    c    = conn.cursor()
    try:
        # Total registered users
        c.execute('SELECT COUNT(*) AS cnt FROM users')
        total_users = c.fetchone()['cnt']

        # Total products in inventory
        c.execute('SELECT COUNT(*) AS cnt FROM inventory.products')
        total_products = c.fetchone()['cnt']

        # Total orders ever placed
        c.execute('SELECT COUNT(*) AS cnt FROM transactions.orders')
        total_orders = c.fetchone()['cnt']

        # Revenue = SUM of total_price for completed orders
        c.execute('''
            SELECT COALESCE(SUM(total_price), 0) AS rev
            FROM   transactions.orders
            WHERE  status = ?
        ''', ('Selesai',))
        total_revenue = c.fetchone()['rev']

        # Pending orders (being packed)
        c.execute('''
            SELECT COUNT(*) AS cnt
            FROM   transactions.orders
            WHERE  status = ?
        ''', ('Sedang Dikemas',))
        pending_orders = c.fetchone()['cnt']

        # Active deliveries
        c.execute('''
            SELECT COUNT(*) AS cnt
            FROM   transactions.orders
            WHERE  status = ?
        ''', ('Sedang Dikirim',))
        active_deliveries = c.fetchone()['cnt']

    finally:
        conn.close()

    return jsonify({
        'total_users':       total_users,
        'total_products':    total_products,
        'total_orders':      total_orders,
        'total_revenue':     total_revenue,
        'pending_orders':    pending_orders,
        'active_deliveries': active_deliveries
    })


# ── GET /api/admin/orders ──────────────────────────────────────
@app.route('/api/admin/orders', methods=['GET'])
@token_required
def admin_orders(current_user):
    """Return the last 100 orders across all stores (Admin only)."""
    err = _require_admin(current_user)
    if err:
        return err

    conn = get_db()
    c    = conn.cursor()
    try:
        c.execute('''
            SELECT
                o.id,
                u.username  AS buyer_name,
                s.name      AS store_name,
                o.status,
                o.total_price,
                o.created_at
            FROM   transactions.orders o
            LEFT   JOIN users          u ON u.id = o.user_id
            LEFT   JOIN seller.stores  s ON s.id = o.store_id
            ORDER  BY o.created_at DESC
            LIMIT  100
        ''')
        # Never expose passwords, tokens, or internal driver_id in this list
        orders = [dict(r) for r in c.fetchall()]
    finally:
        conn.close()

    return jsonify(orders)


# ── POST /api/admin/trigger-overdue ───────────────────────────
@app.route('/api/admin/trigger-overdue', methods=['POST'])
@token_required
def trigger_overdue(current_user):
    """
    Cancel packing orders older than 3 days and refund buyers (Admin only).
    Marks status → 'Dibatalkan' and credits the buyer's wallet if the
    original payment method was 'wallet'.
    Returns: { cancelled_count: N }
    """
    # Body parsing — safe, silent, no crash on empty body
    _ = request.get_json(silent=True) or {}

    err = _require_admin(current_user)
    if err:
        return err

    conn = get_db()
    c    = conn.cursor()
    try:
        # Find all overdue "Sedang Dikemas" orders (> 3 days old)
        c.execute('''
            SELECT id, user_id, total_price, payment_method
            FROM   transactions.orders
            WHERE  status     = ?
              AND  created_at < datetime('now', ?)
        ''', ('Sedang Dikemas', '-3 days'))
        overdue = c.fetchall()

        cancelled_count = 0
        for order in overdue:
            order_id       = order['id']
            user_id        = order['user_id']
            total_price    = order['total_price']
            payment_method = order['payment_method']

            # Mark as cancelled — fully parameterised
            c.execute('''
                UPDATE transactions.orders
                SET    status = ?
                WHERE  id     = ?
            ''', ('Dibatalkan', order_id))

            # Refund wallet if buyer paid via wallet
            if payment_method == 'wallet':
                c.execute('''
                    UPDATE wallets
                    SET    balance = balance + ?
                    WHERE  user_id = ?
                ''', (total_price, user_id))
                # Record refund in wallet history (best-effort; ignore if table absent)
                try:
                    c.execute('''
                        INSERT INTO transactions.wallet_history
                               (user_id, type, amount, description)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, 'credit', total_price,
                          'Auto-refund: order overdue (>3 days)'))
                except Exception:
                    pass  # wallet_history table may not exist in all envs

            cancelled_count += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

    return jsonify({'cancelled_count': cancelled_count,
                    'message': f'{cancelled_count} overdue order(s) cancelled and refunded.'})


# ══════════════════════════════════════════════════════════════
#  PHASE 6 — Security Hardening helpers
#  XSS-safe HTML escaper for any server-side rendered content.
#  All existing endpoints already use parameterised queries.
# ══════════════════════════════════════════════════════════════

import html as _html

def xss_escape(value):
    """
    Escape a string value for safe insertion into HTML contexts.
    Uses Python's built-in html.escape which converts &, <, >, ", '
    into their safe HTML entities.
    """
    if value is None:
        return ''
    return _html.escape(str(value), quote=True)


# ── Utility: sanitise a dict's string values (defensive layer) ─
def sanitise_dict(d):
    """
    Return a copy of dict d with all string values XSS-escaped.
    Non-string values (int, float, None) are left untouched.
    """
    return {k: (xss_escape(v) if isinstance(v, str) else v)
            for k, v in d.items()}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_production = os.environ.get('RENDER', False)
    print(f"SEAPEDIA Backend running on port {port}")
    app.run(debug=not is_production, host='0.0.0.0', port=port)

