const API_URL = 'http://127.0.0.1:5000/api';

function showToast(message, isError = false) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.style.background = isError ? '#d32f2f' : 'var(--primary-color)';
    toast.style.color = 'white';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = 'var(--box-shadow)';
    toast.style.fontSize = '14px';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
}

function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

// Global Custom Popup
function showCustomPopup(title, message, callback) {
    let overlay = document.getElementById('custom-popup-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'custom-popup-overlay';
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal-content" style="text-align: center; max-width: 350px;">
                <h3 id="custom-popup-title" class="mb-2"></h3>
                <p id="custom-popup-message" class="text-muted mb-4"></p>
                <button class="btn btn-primary" id="custom-popup-btn" style="width: 100%;">OK</button>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    document.getElementById('custom-popup-title').innerText = title;
    document.getElementById('custom-popup-message').innerText = message;
    
    const btn = document.getElementById('custom-popup-btn');
    btn.onclick = () => {
        overlay.classList.remove('active');
        if(callback) callback();
    };
    
    // Slight delay to allow DOM insertion reflow if it was just created
    setTimeout(() => overlay.classList.add('active'), 10);
}

// Load Products (Homepage & Search)
async function loadProducts(limit = 12) {
    const list = document.getElementById('product-list');
    if (!list) return;
    
    // Check if there are search params in the URL
    const params = new URLSearchParams(window.location.search);
    const q = params.get('q') || '';
    const category = params.get('category') || '';
    
    let url = `${API_URL}/products?limit=${limit}`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;

    try {
        const res = await fetch(url);
        const products = await res.json();
        list.innerHTML = '';
        
        if (products.length === 0) {
            list.innerHTML = '<p class="text-muted" style="grid-column: 1 / -1; text-align: center; padding: 40px;">No products found.</p>';
            return;
        }
        
        products.forEach(p => {
            list.innerHTML += `
            <div class="product-card slide-fwd-hover" data-product-id="${p.id}" onclick="window.location.href='product.html?id=${p.id}'" style="cursor: pointer;">
                <div class="product-image" style="background-image: url('${p.image_url}');"></div>
                <div class="product-info">
                    <h3 class="product-title">${p.name}</h3>
                    <p class="product-price">Rp ${p.price.toLocaleString()}</p>
                    <div class="store-info">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path></svg>
                        ${p.store_city || 'City'}
                    </div>
                </div>
            </div>`;
        });
    } catch(e) { console.error("Error loading products", e); }
}

// Load Stores (Search page)
async function loadStores() {
    const list = document.getElementById('store-grid');
    if (!list) return;
    try {
        const res = await fetch(`${API_URL}/stores?limit=20`); 
        const stores = await res.json();
        list.innerHTML = '';
        stores.forEach((s, i) => {
            const initial = s.name.charAt(0).toUpperCase();
            let badge = i % 3 === 0 ? `<span class="badge" style="background:#e8f5e9; color:var(--primary-color); margin-top: 8px;">Official Store</span>` : '';
            list.innerHTML += `
            <div class="store-card" data-store-id="${s.id}">
                <div class="store-avatar">${initial}</div>
                <div>
                    <h3 style="font-size: 18px; margin-bottom: 4px;">${s.name}</h3>
                    <p class="text-muted" style="font-size: 14px;">${s.city} • ★ ${s.rating}</p>
                    ${badge}
                </div>
            </div>`;
        });
    } catch(e) { console.error(e); }
}

// Load Specific Store (Toko page)
async function loadStoreProfile() {
    const title = document.getElementById('store-name-title');
    const avatarContainer = document.getElementById('store-avatar-container');
    const description = document.getElementById('store-description');
    const subtitle = document.getElementById('store-subtitle');
    const list = document.getElementById('store-product-grid');
    
    if (!title || !list) return;
    
    const params = new URLSearchParams(window.location.search);
    const storeId = params.get('store_id');
    if (!storeId) return;

    try {
        const sRes = await fetch(`${API_URL}/stores/${storeId}`);
        const store = await sRes.json();
        title.innerText = store.name;
        
        if (store.image_url) {
            avatarContainer.style.backgroundImage = `url('${store.image_url}')`;
            avatarContainer.innerText = '';
        } else {
            avatarContainer.style.backgroundImage = 'none';
            avatarContainer.innerText = store.name.charAt(0).toUpperCase();
        }
        
        if (store.description) {
            description.innerText = store.description;
        }

        subtitle.innerHTML = `<span class="badge" style="background:#e8f5e9; color:var(--primary-color);">Official Store</span> <span class="text-muted" style="font-size:14px;">★ ${store.rating} Rating</span> <span class="text-muted" style="font-size:14px;">📍 ${store.city}</span>`;
        
        const pRes = await fetch(`${API_URL}/products?store_id=${storeId}`);
        const products = await pRes.json();
        list.innerHTML = '';
        products.forEach(p => {
            list.innerHTML += `
            <div class="product-card" data-product-id="${p.id}">
                <div class="product-image" style="background-image: url('${p.image_url}');"></div>
                <div class="product-info">
                    <h3 class="product-title">${p.name}</h3>
                    <p class="product-price">Rp ${p.price.toLocaleString()}</p>
                    <div class="store-info">Stock: ${p.stock}</div>
                </div>
            </div>`;
        });
    } catch(e) { console.error(e); }
}

// Load Reviews
async function loadReviews() {
    const list = document.getElementById('review-list');
    if (!list) return;
    try {
        const res = await fetch(`${API_URL}/reviews`);
        const reviews = await res.json();
        list.innerHTML = '';
        reviews.forEach(r => {
            const safeComment = r.comment.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            const safeName = r.name.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            list.innerHTML += `
                <div style="background:var(--background-light); padding:16px; border-radius:8px;" class="scroll-animate">
                    <div class="flex justify-between">
                        <strong style="font-size:14px;">${safeName}</strong>
                        <span style="color: #ffb300; font-size:14px;">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</span>
                    </div>
                    <p class="mt-2 text-muted" style="font-size:14px;">${safeComment}</p>
                </div>
            `;
        });
    } catch(e) {}
}

async function submitReview(e) {
    e.preventDefault();
    const name = document.getElementById('review-name').value;
    const rating = document.getElementById('review-rating').value;
    const comment = document.getElementById('review-comment').value;
    try {
        await fetch(`${API_URL}/reviews`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, rating, comment }) });
        showToast('Review submitted!');
        document.getElementById('review-form').reset();
        loadReviews();
    } catch(err) { showToast('Error', true); }
}

// Auth Handlers
async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    const roles = Array.from(document.querySelectorAll('input[name="roles"]:checked')).map(cb => cb.value);
    
    if (roles.length === 0) { showToast('Select at least one role', true); return; }

    const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, roles })
    });
    if (res.ok) {
        showToast('Registered successfully!');
        switchTab('login');
    } else {
        const data = await res.json();
        showToast(data.error, true);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (res.ok) {
        localStorage.setItem('seapedia_token', data.token);
        localStorage.setItem('seapedia_user', JSON.stringify(data.user));
        
        if (data.user.roles.length > 1) {
            showRoleSelection(data.user.roles);
        } else {
            selectActiveRole(data.user.roles[0]);
        }
    } else {
        showToast(data.error, true);
    }
}

function showRoleSelection(roles) {
    const container = document.getElementById('role-selection-container');
    if (!container) return;
    container.innerHTML = '';
    roles.forEach(role => {
        container.innerHTML += `<button class="btn btn-outline" style="padding:16px; font-size:16px;" onclick="selectActiveRole('${role}')">Continue as ${role}</button>`;
    });
    openModal('roleModal');
}

async function selectActiveRole(role) {
    const token = localStorage.getItem('seapedia_token');
    const res = await fetch(`${API_URL}/auth/select-role`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ role })
    });
    const data = await res.json();
    if (res.ok) {
        localStorage.setItem('seapedia_token', data.token);
        localStorage.setItem('seapedia_active_role', data.active_role);
        window.location.href = 'dashboard.html';
    } else {
        showToast('Error', true);
    }
}

// Central UI Updates
function updateNavForAuth() {
    const navLinks = document.getElementById('nav-links');
    if (!navLinks) return;

    let cartCount = 0;
    try {
        const cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
        cartCount = cart.reduce((acc, item) => acc + item.qty, 0);
    } catch(e) {}

    const currentUser = JSON.parse(localStorage.getItem('seapedia_user'));
    
    if (currentUser) {
        navLinks.innerHTML = `
            <div class="cart-icon" data-href="cart.html">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                ${cartCount > 0 ? `<span class="cart-badge">${cartCount}</span>` : ''}
            </div>
            <button class="btn btn-outline" data-href="dashboard.html">Dashboard</button>
        `;
    } else {
        navLinks.innerHTML = `
            <div class="cart-icon" data-href="cart.html">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                ${cartCount > 0 ? `<span class="cart-badge">${cartCount}</span>` : ''}
            </div>
            <button class="btn btn-outline" data-href="login.html">Login</button>
            <button class="btn btn-primary" data-href="login.html">Sign Up</button>
        `;
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}

document.addEventListener('DOMContentLoaded', () => {
    updateNavForAuth();
    loadProducts();
    loadReviews();
    loadStores();
    loadStoreProfile();

    // Wire up search bar if it exists on the page
    const searchInput = document.querySelector('.search-bar input');
    const searchBtn = document.querySelector('.search-bar button');
    
    if (searchInput && searchBtn) {
        const executeSearch = () => {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `searchproduct.html?q=${encodeURIComponent(query)}`;
            }
        };
        
        searchBtn.addEventListener('click', executeSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeSearch();
        });
    }
});

// Global Event Listeners (Event Delegation)
document.addEventListener('click', (e) => {
    // Handle data-href global routing
    const hrefElement = e.target.closest('[data-href]');
    if (hrefElement) {
        window.location.href = hrefElement.getAttribute('data-href');
        return;
    }

    // Product Card Click
    const productCard = e.target.closest('.product-card');
    if (productCard) {
        const productId = productCard.getAttribute('data-product-id');
        if (productId) {
            window.location.href = `product.html?id=${productId}`;
        }
        return;
    }

    // Store Card Click
    const storeCard = e.target.closest('.store-card');
    if (storeCard) {
        const storeId = storeCard.getAttribute('data-store-id');
        if (storeId) {
            window.location.href = `toko.html?store_id=${storeId}`;
        }
        return;
    }
});

// Scroll Animation Observer
document.addEventListener('DOMContentLoaded', () => {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                obs.unobserve(entry.target); // Run once
            }
        });
    }, observerOptions);

    // Function to dynamically apply observer to elements
    window.observeElements = function() {
        const elements = document.querySelectorAll('.product-card, .promo-banner, .category-bubble, .card, .stat-card, .store-card, .cart-item');
        elements.forEach(el => {
            if (!el.classList.contains('scroll-animate')) {
                el.classList.add('scroll-animate');
                observer.observe(el);
            }
        });
    };
    
    // Initial observe
    window.observeElements();
    
    // Override fetch to re-observe after dynamic content loads
    const originalFetch = window.fetch;
    window.fetch = async function() {
        const response = await originalFetch.apply(this, arguments);
        setTimeout(() => window.observeElements(), 300); // Give DOM time to update
        return response;
    };
});
