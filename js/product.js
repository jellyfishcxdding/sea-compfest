document.addEventListener('DOMContentLoaded', async () => {
    updateNavForAuth();
    const params = new URLSearchParams(window.location.search);
    const pId = params.get('id');
    if (!pId) return;

    try {
        const res = await fetch(`${API_URL}/products/${pId}`);
        if (!res.ok) throw new Error("Product not found");
        const p = await res.json();
        
        document.getElementById('product-title').innerText = p.name;
        document.getElementById('product-price').innerText = `Rp ${p.price.toLocaleString()}`;
        document.getElementById('product-stock').innerText = p.stock;
        document.getElementById('product-img').style.backgroundImage = `url('${p.image_url}')`;
        document.getElementById('product-desc').innerText = p.description;
        document.getElementById('product-store-name').innerText = `${p.store_name} (${p.store_city})`;
        document.getElementById('product-store-link').href = `toko.html?store_id=${p.store_id}`;
        
        // Store globally for quick access
        window.currentProduct = p;
        window.currentProductQty = 1; // Default qty
    } catch (e) {
        console.error(e);
        document.getElementById('product-title').innerText = "Product not found.";
    }
});

window.updateProductPageQty = function(change) {
    if (!window.currentProduct) return;
    let newQty = window.currentProductQty + change;
    if (newQty < 1) newQty = 1;
    if (newQty > window.currentProduct.stock) {
        showToast("Cannot exceed available stock");
        newQty = window.currentProduct.stock;
    }
    window.currentProductQty = newQty;
    document.getElementById('product-page-qty').innerText = newQty;
};

window.addToCart = function() {
    if (!window.currentProduct) return;
    let cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    
    const existing = cart.find(i => i.id === window.currentProduct.id);
    if (existing) {
        existing.qty += window.currentProductQty;
    } else {
        cart.push({ ...window.currentProduct, qty: window.currentProductQty });
    }
    
    localStorage.setItem('seapedia_cart', JSON.stringify(cart));
    showCustomPopup('Success!', `${window.currentProductQty}x ${window.currentProduct.name} added to your cart.`);
    updateNavForAuth();
};

window.buyNow = function() {
    if (!window.currentProduct) return;
    addToCart();
    window.location.href = 'checkout.html';
};
