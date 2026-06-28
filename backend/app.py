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
    q = request.args.get('q', '').lower()
    category = request.args.get('category', '').lower()
    limit = request.args.get('limit', 50)
    
    conn = get_db()
    c = conn.cursor()
    
    base_query = '''
        SELECT p.*, s.name as store_name, s.city as store_city 
        FROM inventory.products p 
        JOIN seller.stores s ON p.store_id = s.id 
        WHERE 1=1
    '''
    params = []
    
    if store_id:
        base_query += ' AND p.store_id = ?'
        params.append(store_id)
        
    if q:
        base_query += ' AND LOWER(p.name) LIKE ?'
        params.append(f'%{q}%')
        
    if category:
        # Since we don't have a category column in dummy data, we just fake it by matching the name
        base_query += ' AND LOWER(p.name) LIKE ?'
        params.append(f'%{category}%')
        
    base_query += ' ORDER BY RANDOM() LIMIT ?'
    params.append(limit)
    
    c.execute(base_query, params)
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
    delivery_fee = data.get('delivery_fee', 10000)

    if not user_id or not cart:
        return jsonify({'error': 'Invalid checkout data'}), 400

    conn = get_db()
    c = conn.cursor()
    
    try:
        stores_map = {}
        for item in cart:
            store_id = item.get('store_id')
            if store_id not in stores_map:
                stores_map[store_id] = []
            stores_map[store_id].append(item)
            
        total_payment = 0
        orders_to_create = []

        for store_id, items in stores_map.items():
            store_total = sum(item.get('price', 0) * item.get('qty', 1) for item in items)
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

if __name__ == '__main__':
    print("Amazon-Class SEAPEDIA Backend running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)

