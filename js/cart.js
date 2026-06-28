document.addEventListener('DOMContentLoaded', () => {
    updateNavForAuth();
    loadCartItems();
});

function loadCartItems() {
    const container = document.getElementById('cart-items-container');
    if (!container) return;

    let cart = [];
    try {
        cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    } catch(e) {}

    if (cart.length === 0) {
        container.innerHTML = '<div style="padding: 40px; text-align: center; background: white; border-radius: 12px; box-shadow: var(--box-shadow);"><p class="text-muted mb-4">Your cart is empty.</p><button class="btn btn-primary" onclick="window.location.href=\'index.html\'">Start Shopping</button></div>';
        calculateTotal(cart);
        return;
    }

    container.innerHTML = '';
    cart.forEach(item => {
        container.innerHTML += `
        <div class="cart-item" data-id="${item.id}">
            <img src="${item.image_url}" alt="${item.name}">
            <div class="cart-item-info">
                <h4 style="margin-bottom: 4px; font-size: 16px; color: var(--text-dark);">${item.name}</h4>
                <p style="color: var(--primary-color); font-weight: 800; font-size: 16px;">Rp ${item.price.toLocaleString()}</p>
                <p class="text-muted" style="font-size: 12px; margin-top: 4px;">Store: ${item.store_name || 'Unknown'}</p>
                
                <div class="qty-controls">
                    <button class="qty-btn" onclick="updateCartQty(${item.id}, -1)">-</button>
                    <span style="font-weight: 600; width: 24px; text-align: center;">${item.qty}</span>
                    <button class="qty-btn" onclick="updateCartQty(${item.id}, 1)">+</button>
                    
                    <button class="btn" style="margin-left: auto; color: #ef144a; background: none; padding: 4px;" onclick="removeFromCart(${item.id})">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            </div>
        </div>
        `;
    });

    calculateTotal(cart);
}

window.updateCartQty = function(id, change) {
    let cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    const item = cart.find(i => i.id === id);
    if (item) {
        item.qty += change;
        if (item.qty < 1) item.qty = 1; // Prevent negative/zero
        localStorage.setItem('seapedia_cart', JSON.stringify(cart));
        loadCartItems();
        updateNavForAuth();
    }
};

window.removeFromCart = function(id) {
    let cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    cart = cart.filter(i => i.id !== id);
    localStorage.setItem('seapedia_cart', JSON.stringify(cart));
    loadCartItems();
    updateNavForAuth();
    showToast('Item removed from cart');
};

function calculateTotal(cart) {
    let totalQty = 0;
    let totalPrice = 0;

    cart.forEach(item => {
        totalQty += item.qty;
        totalPrice += (item.price * item.qty);
    });

    const itemsText = document.getElementById('summary-items-text');
    const priceText = document.getElementById('summary-price-text');
    const grandTotalText = document.getElementById('grand-total-text');
    const checkoutBtn = document.getElementById('checkout-btn');

    if (itemsText) itemsText.innerText = `Total Price (${totalQty} items)`;
    if (priceText) priceText.innerText = `Rp ${totalPrice.toLocaleString()}`;
    if (grandTotalText) grandTotalText.innerText = `Rp ${totalPrice.toLocaleString()}`;
    if (checkoutBtn) {
        checkoutBtn.innerText = `Buy (${totalQty})`;
        checkoutBtn.disabled = totalQty === 0;
    }
}
