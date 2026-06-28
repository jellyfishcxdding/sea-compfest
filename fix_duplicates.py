"""
Removes duplicate Phase 3 endpoints from app.py that cause Flask startup crash.
Replaces the old (unprotected) versions with just the legacy driver orders endpoint.
"""
import re

path = r'C:\Users\Gracia\OneDrive - Bina Nusantara\activity\COMPFEST\seapedia\backend\app.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the exact block to remove (the 3 old duplicate endpoints)
old_block = """@app.route('/api/orders/buyer/<int:user_id>', methods=['GET'])
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
    return jsonify({'message': 'Status updated'})"""

replacement = """@app.route('/api/orders/driver', methods=['GET'])
def get_driver_orders():
    \"\"\"Legacy endpoint — kept for backward compat. Phase 4 uses /api/jobs/available.\"\"\"
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT o.id, o.status, o.created_at,
               s.name as store_name, s.city as store_city,
               u.username as buyer_name
        FROM transactions.orders o
        JOIN seller.stores s ON o.store_id = s.id
        JOIN users u ON o.user_id = u.id
        WHERE o.status IN ('Menunggu Pengirim', 'Sedang Dikirim')
        ORDER BY o.created_at ASC
    ''')
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(orders)"""

if old_block in content:
    content = content.replace(old_block, replacement, 1)
    print("✅ Removed duplicate endpoints, kept legacy driver route")
else:
    print("❌ Could not find exact block — checking for partial matches...")
    # Find by function names
    lines = content.split('\n')
    for i, l in enumerate(lines):
        if 'def get_buyer_orders' in l or 'def get_seller_orders' in l or 'def update_order_status' in l:
            print(f"  Line {i+1}: {l.strip()}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done.")
