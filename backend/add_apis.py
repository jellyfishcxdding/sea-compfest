import os

backend_path = "C:\\Users\\Gracia\\OneDrive - Bina Nusantara\\activity\\COMPFEST\\seapedia\\backend\\app.py"

with open(backend_path, 'r', encoding='utf-8') as f:
    content = f.read()

# APIs to add for Level 2 (Seller Store & Product CRUD) and Level 3 (Cart)

new_apis = """

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

"""

# Ensure transactions.cart and transactions.wallet_history tables exist
table_setup = """
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
"""

# Inject before the final `if __name__ == '__main__':` block
if "if __name__ == '__main__':" in content:
    content = content.replace("if __name__ == '__main__':", new_apis + "\n\n" + table_setup + "\n\nif __name__ == '__main__':")
    with open(backend_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected Level 2 and Level 3 APIs into app.py securely.")
else:
    print("Could not find __main__ block.")
