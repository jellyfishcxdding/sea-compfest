from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import datetime
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'seapedia-super-secret-key'

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Strict Transport Security prevents downgrade attacks
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Content Security Policy (Basic API restriction)
    response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none';"
    return response

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')

AUTH_DB = os.path.join(DATA_DIR, 'auth.db')
SELLER_DB = os.path.join(DATA_DIR, 'seller.db')
INVENTORY_DB = os.path.join(DATA_DIR, 'inventory.db')
TRANSACTIONS_DB = os.path.join(DATA_DIR, 'transactions.db')

def get_db():
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"ATTACH DATABASE '{SELLER_DB}' AS seller")
    c.execute(f"ATTACH DATABASE '{INVENTORY_DB}' AS inventory")
    c.execute(f"ATTACH DATABASE '{TRANSACTIONS_DB}' AS transactions")
    return conn

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    roles = data.get('roles', [])

    if not username or not password or not roles:
        return jsonify({'error': 'Missing required fields'}), 400

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

@app.route('/api/orders/buyer/<int:user_id>', methods=['GET'])
@token_required
def get_buyer_orders(current_user, user_id):
    if current_user['user_id'] != user_id: return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT o.*, s.name as store_name
        FROM transactions.orders o
        JOIN seller.stores s ON o.store_id = s.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    ''', (user_id,))
    orders = [dict(row) for row in c.fetchall()]
    
    for order in orders:
        c.execute('''
            SELECT oi.*, p.name, p.image_url
            FROM transactions.order_items oi
            JOIN inventory.products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],))
        order['items'] = [dict(row) for row in c.fetchall()]
        
    conn.close()
    return jsonify(orders)

@app.route('/api/orders/seller/<int:seller_id>', methods=['GET'])
def get_seller_orders(seller_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM seller.stores WHERE seller_id = ?', (seller_id,))
    store = c.fetchone()
    if not store:
        return jsonify({'error': 'No store found'}), 404
        
    c.execute('''
        SELECT o.*, u.username as buyer_name
        FROM transactions.orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.store_id = ?
        ORDER BY o.created_at DESC
    ''', (store['id'],))
    orders = [dict(row) for row in c.fetchall()]
    
    for order in orders:
        c.execute('''
            SELECT oi.*, p.name 
            FROM transactions.order_items oi
            JOIN inventory.products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],))
        order['items'] = [dict(row) for row in c.fetchall()]
        
    conn.close()
    return jsonify(orders)

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

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.json
    new_status = data.get('status')
    if not new_status:
        return jsonify({'error': 'Missing status'}), 400
        
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE transactions.orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Status updated'})

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
    data = request.json
    user_id = current_user['user_id']
    username = current_user['username']
    rating = int(data.get('rating', 5))
    comment = data.get('comment', '')

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
        return jsonify({'error': 'You must purchase and complete delivery to review this item'}), 403
        
    c.execute('''
        INSERT INTO inventory.product_reviews (product_id, user_id, username, rating, comment)
        VALUES (?, ?, ?, ?, ?)
    ''', (product_id, user_id, username, rating, comment))
    conn.commit()
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
        
    data = request.json
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')
    category = data.get('category', 'electronics')
    image_url = data.get('image_url', '')
    description = data.get('description', '')
    
    if not name or price is None or stock is None:
        return jsonify({'error': 'Missing required product fields'}), 400
        
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


if __name__ == '__main__':
    print("Amazon-Class SEAPEDIA Backend running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)

