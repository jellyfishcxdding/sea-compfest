document.addEventListener('DOMContentLoaded', async () => {
    updateNavForAuth();
    const params = new URLSearchParams(window.location.search);
    const pId = params.get('id');

    if (!pId) {
        window.location.href = 'index.html';
        return;
    }

    try {
        const res = await fetch(`${API_URL}/products/${pId}`);
        const p = await res.json();
        if (p.error) {
            document.getElementById('product-name').innerText = "Product Not Found";
            return;
        }

        document.getElementById('product-name').innerText = p.name;
        document.getElementById('product-price').innerText = `Rp ${p.price.toLocaleString()}`;
        document.getElementById('product-store').innerHTML = `Sold by: <a href="toko.html?id=${p.store_id}" style="color:var(--primary-color); font-weight:600;">${p.store_name}</a>`;
        document.getElementById('product-desc').innerText = p.description || "No description available.";
        document.getElementById('product-stock').innerText = p.stock;
        document.getElementById('product-img').style.backgroundImage = `url('${p.image_url}')`;

        window.currentProduct = p;
        window.currentProductQty = 1;
        
        loadProductReviews(pId);
    } catch(e) {
        console.error(e);
        document.getElementById('product-name').innerText = "Error loading product.";
    }
});

window.updateQty = function(change) {
    if(!window.currentProduct) return;
    let newQty = window.currentProductQty + change;
    if (newQty < 1) newQty = 1;
    if (newQty > window.currentProduct.stock) newQty = window.currentProduct.stock;
    window.currentProductQty = newQty;
    document.getElementById('product-qty').innerText = newQty;
};

window.addToCart = function() {
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    if (!user || localStorage.getItem('seapedia_active_role') !== 'Buyer') {
        showToast("Please login as a Buyer to add items to your cart", true);
        return;
    }

    let cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    const existing = cart.find(i => i.id === window.currentProduct.id);
    if (existing) {
        existing.qty += window.currentProductQty;
        if (existing.qty > window.currentProduct.stock) existing.qty = window.currentProduct.stock;
    } else {
        cart.push({ ...window.currentProduct, qty: window.currentProductQty });
    }
    localStorage.setItem('seapedia_cart', JSON.stringify(cart));
    showToast(`${window.currentProduct.name} added to cart!`);
    updateNavForAuth();
};

window.addToWishlist = async function() {
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const token = localStorage.getItem('seapedia_token');
    
    if (!user || localStorage.getItem('seapedia_active_role') !== 'Buyer') {
        showToast("Please login as a Buyer to use the wishlist.", true);
        return;
    }

    try {
        const res = await fetch(`${API_URL}/wishlist`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ user_id: user.id, product_id: window.currentProduct.id })
        });
        const data = await res.json();
        if (res.ok) {
            showToast("❤️ Added to Wishlist!");
        } else {
            showToast(data.error, true);
        }
    } catch(e) {
        showToast("Failed to add to wishlist.", true);
    }
};

window.loadProductReviews = async function(productId) {
    try {
        const res = await fetch(`${API_URL}/products/${productId}/reviews`);
        const reviews = await res.json();
        const list = document.getElementById('product-review-list');
        list.innerHTML = '';

        if (reviews.length === 0) {
            list.innerHTML = "<p class='text-muted' style='padding: 20px;'>No reviews yet. Be the first to review this product after purchasing!</p>";
            return;
        }

        reviews.forEach(r => {
            const safeComment = r.comment.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            const safeName = r.username.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            list.innerHTML += `
                <div style="background:var(--background-light); padding:16px; border-radius:8px;">
                    <div class="flex justify-between">
                        <strong style="font-size:14px;">${safeName}</strong>
                        <span style="color: #ffb300; font-size:14px;">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                    </div>
                    <p class="mt-2 text-muted" style="font-size:14px;">${safeComment}</p>
                    <small class="text-muted" style="font-size:11px; margin-top:8px; display:block;">${new Date(r.created_at).toLocaleDateString()}</small>
                </div>
            `;
        });
    } catch(e) { console.error(e); }
};

window.submitProductReview = async function(e) {
    e.preventDefault();
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const token = localStorage.getItem('seapedia_token');
    
    if (!user || localStorage.getItem('seapedia_active_role') !== 'Buyer') {
        showToast("Please login as a Buyer to leave a review.", true);
        return;
    }

    const rating = document.getElementById('review-rating').value;
    const comment = document.getElementById('review-comment').value;

    try {
        const res = await fetch(`${API_URL}/products/${window.currentProduct.id}/reviews`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ rating, comment })
        });
        const data = await res.json();
        
        if (res.ok) {
            showToast("Review submitted successfully!");
            document.getElementById('product-review-form').reset();
            loadProductReviews(window.currentProduct.id);
        } else {
            showToast(data.error, true);
        }
    } catch(e) {
        showToast("Failed to submit review.", true);
    }
};
