import os

css_contents = {
    "cart.css": """
/* Cart Page Specific Styles */
.cart-container {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    margin-top: 24px;
    align-items: start;
}
.cart-item {
    display: flex;
    gap: 16px;
    padding: 16px;
    background: var(--background-white);
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    margin-bottom: 16px;
    transition: var(--transition);
}
.cart-item:hover {
    box-shadow: var(--box-shadow-hover);
}
.cart-item img {
    width: 100px;
    height: 100px;
    object-fit: cover;
    border-radius: 8px;
}
.cart-item-info {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}
.qty-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: auto;
}
.qty-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 1px solid var(--border-color);
    background: var(--background-white);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    transition: var(--transition);
}
.qty-btn:hover {
    background: var(--secondary-color);
    color: var(--primary-color);
    border-color: var(--primary-color);
}
.cart-summary {
    background: var(--background-white);
    padding: 24px;
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    position: sticky;
    top: 90px;
}
@media (max-width: 768px) {
    .cart-container { grid-template-columns: 1fr; }
    .cart-item { flex-direction: column; }
    .cart-item img { width: 100%; height: 200px; }
}
""",
    "checkout.css": """
/* Checkout Page Specific Styles */
.checkout-container {
    max-width: 800px;
    margin: 40px auto;
}
.checkout-card {
    background: var(--background-white);
    padding: 32px;
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    margin-bottom: 24px;
}
.payment-method {
    display: flex;
    align-items: center;
    padding: 16px;
    border: 1.5px solid var(--border-color);
    border-radius: 12px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: var(--transition);
}
.payment-method:hover {
    border-color: var(--primary-color);
    background: var(--secondary-color);
}
.payment-method.selected {
    border-color: var(--primary-color);
    background: var(--primary-color);
    color: white;
}
.summary-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
    font-size: 15px;
}
.summary-row.total {
    font-weight: 800;
    font-size: 18px;
    border-top: 2px dashed var(--border-color);
    padding-top: 16px;
    margin-top: 16px;
}
""",
    "dashboard.css": """
/* Dashboard Specific Styles */
.dashboard-layout {
    display: grid;
    grid-template-columns: 250px 1fr;
    gap: 32px;
    margin-top: 32px;
    margin-bottom: 40px;
}
.sidebar-menu {
    background: var(--background-white);
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    padding: 16px 0;
    position: sticky;
    top: 90px;
}
.sidebar-item {
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--text-dark);
    transition: var(--transition);
    cursor: pointer;
    font-weight: 500;
}
.sidebar-item:hover, .sidebar-item.active {
    background: var(--secondary-color);
    color: var(--primary-color);
    border-left: 4px solid var(--primary-color);
}
.stat-card {
    background: var(--background-white);
    padding: 24px;
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: var(--transition);
}
.stat-card:hover { transform: translateY(-4px); box-shadow: var(--box-shadow-hover); }
.stat-value { font-size: 32px; font-weight: 800; color: var(--primary-color); }
.stat-label { font-size: 14px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;}
@media (max-width: 768px) {
    .dashboard-layout { grid-template-columns: 1fr; }
    .sidebar-menu { display: flex; overflow-x: auto; padding: 8px; }
    .sidebar-item { border-left: none !important; border-bottom: 4px solid transparent; }
    .sidebar-item.active { border-bottom: 4px solid var(--primary-color); }
}
""",
    "index.css": """
/* Homepage Specific Styles */
.hero-section {
    position: relative;
    overflow: hidden;
    margin-bottom: 40px;
}
.category-bubble {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px;
    border-radius: 16px;
    background: var(--background-white);
    box-shadow: var(--box-shadow);
    min-width: 100px;
    transition: var(--transition);
    cursor: pointer;
}
.category-bubble:hover {
    transform: translateY(-5px);
    box-shadow: var(--box-shadow-hover);
    color: var(--primary-color);
}
.category-bubble svg { color: var(--primary-color); margin-bottom: 8px; }
""",
    "login.css": """
/* Login & Auth Pages */
.auth-container {
    min-height: calc(100vh - 80px);
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #e8f5e9 0%, #f5f7f9 100%);
    padding: 20px;
}
.auth-card {
    background: var(--background-white);
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    width: 100%;
    max-width: 450px;
}
.auth-header {
    text-align: center;
    margin-bottom: 32px;
}
.auth-header h1 { font-size: 28px; font-weight: 800; color: var(--primary-color); margin-bottom: 8px;}
.auth-header p { color: var(--text-muted); }
.role-selector {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}
.role-btn {
    padding: 12px;
    text-align: center;
    border: 2px solid var(--border-color);
    border-radius: 12px;
    cursor: pointer;
    transition: var(--transition);
    font-weight: 600;
}
.role-btn input { display: none; }
.role-btn:has(input:checked) {
    border-color: var(--primary-color);
    background: var(--secondary-color);
    color: var(--primary-color);
}
""",
    "myOrder.css": """
/* My Orders specific styles */
.order-card {
    background: var(--background-white);
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    margin-bottom: 20px;
    overflow: hidden;
    border: 1px solid var(--border-color);
}
.order-header {
    padding: 16px 24px;
    background: var(--background-light);
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
}
.order-status {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
}
.status-pending { background: #fff3e0; color: #f57c00; }
.status-shipping { background: #e3f2fd; color: #1976d2; }
.status-completed { background: #e8f5e9; color: #388e3c; }
.order-items {
    padding: 24px;
}
.order-total {
    padding: 16px 24px;
    background: #fafafa;
    text-align: right;
    font-weight: 800;
    font-size: 18px;
    border-top: 1px solid var(--border-color);
}
""",
    "product.css": """
/* Product Detail Page */
.product-detail-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 40px;
    margin-top: 40px;
    margin-bottom: 60px;
}
.product-gallery img {
    width: 100%;
    border-radius: 16px;
    box-shadow: var(--box-shadow);
    object-fit: cover;
    aspect-ratio: 1 / 1;
}
.product-info-section h1 {
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 16px;
    line-height: 1.2;
}
.product-price-large {
    font-size: 36px;
    font-weight: 800;
    color: var(--primary-color);
    margin-bottom: 24px;
}
.store-banner {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: var(--secondary-color);
    border-radius: 12px;
    margin-bottom: 32px;
    cursor: pointer;
    transition: var(--transition);
}
.store-banner:hover { transform: translateY(-2px); box-shadow: var(--box-shadow); }
.store-avatar-small {
    width: 48px; height: 48px;
    border-radius: 50%;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: var(--primary-color);
}
.action-buttons {
    display: flex;
    gap: 16px;
    margin-top: 32px;
}
@media (max-width: 768px) {
    .product-detail-layout { grid-template-columns: 1fr; gap: 24px; }
    .product-info-section h1 { font-size: 24px; }
    .product-price-large { font-size: 28px; }
    .action-buttons { flex-direction: column; }
}
""",
    "searchproduct.css": """
/* Search Product Results */
.search-header {
    margin-top: 24px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);
}
.search-filters {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    overflow-x: auto;
    padding-bottom: 8px;
}
.filter-chip {
    padding: 8px 16px;
    border: 1px solid var(--border-color);
    border-radius: 20px;
    font-size: 14px;
    cursor: pointer;
    white-space: nowrap;
    transition: var(--transition);
}
.filter-chip:hover {
    border-color: var(--primary-color);
    color: var(--primary-color);
}
""",
    "searchtoko.css": """
/* Search Store Specific Styles */
.store-list-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 24px;
    margin-top: 24px;
}
.store-card-large {
    background: var(--background-white);
    border-radius: 16px;
    padding: 24px;
    box-shadow: var(--box-shadow);
    display: flex;
    gap: 16px;
    transition: var(--transition);
    cursor: pointer;
    border: 1px solid transparent;
}
.store-card-large:hover {
    transform: translateY(-4px);
    box-shadow: var(--box-shadow-hover);
    border-color: var(--primary-color);
}
.store-avatar-large {
    width: 64px; height: 64px;
    border-radius: 50%;
    background: var(--secondary-color);
    color: var(--primary-color);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; font-weight: 800;
}
""",
    "sellerPage.css": """
/* Seller Management Dashboard */
.seller-header {
    background: linear-gradient(135deg, #31353b 0%, #1f2226 100%);
    color: white;
    padding: 40px 0;
    margin-bottom: 40px;
}
.seller-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-top: -30px;
    position: relative;
    z-index: 10;
}
.management-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--background-white);
    border-radius: var(--border-radius);
    overflow: hidden;
    box-shadow: var(--box-shadow);
}
.management-table th, .management-table td {
    padding: 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}
.management-table th {
    background: var(--background-light);
    font-weight: 600;
    color: var(--text-muted);
}
.management-table tr:hover { background: #f9fafa; }
""",
    "toko.css": """
/* Public Store Profile */
.store-cover {
    height: 250px;
    background: linear-gradient(90deg, var(--primary-color) 0%, #a5d6a7 100%);
    border-radius: 0 0 24px 24px;
    position: relative;
    margin-bottom: 80px;
}
.store-profile-header {
    position: absolute;
    bottom: -50px;
    left: 40px;
    display: flex;
    align-items: flex-end;
    gap: 24px;
}
.store-profile-pic {
    width: 120px; height: 120px;
    border-radius: 50%;
    border: 4px solid white;
    background: white;
    box-shadow: var(--box-shadow);
    display: flex; align-items: center; justify-content: center;
    font-size: 40px; font-weight: 800; color: var(--primary-color);
    overflow: hidden;
}
.store-profile-pic img { width: 100%; height: 100%; object-fit: cover; }
.store-nav {
    display: flex;
    gap: 32px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 32px;
}
.store-nav a {
    padding: 16px 0;
    color: var(--text-muted);
    font-weight: 600;
    border-bottom: 3px solid transparent;
}
.store-nav a.active, .store-nav a:hover {
    color: var(--primary-color);
    border-bottom-color: var(--primary-color);
}
@media (max-width: 768px) {
    .store-profile-header { left: 20px; flex-direction: column; align-items: center; text-align: center; bottom: -80px;}
    .store-cover { margin-bottom: 100px; }
}
"""
}

# Ensure directory exists and write files
os.makedirs('css', exist_ok=True)
for filename, content in css_contents.items():
    path = os.path.join('css', filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + "\\n")
    print(f"Generated {filename}")
