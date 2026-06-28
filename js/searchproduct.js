// JS for searchproduct.html

document.addEventListener('DOMContentLoaded', () => {
    setupNav();
    const urlParams = new URLSearchParams(window.location.search);
    const sort = urlParams.get('sort');
    if (sort) {
        const sortDropdown = document.getElementById('sort-dropdown');
        if (sortDropdown) {
            sortDropdown.value = sort;
        }
    }
    loadSearchResults();
});

function setupNav() {
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const navLinks = document.getElementById('nav-links');
    
    if (user) {
        navLinks.innerHTML = `
            <div class="cart-icon" onclick="window.location.href='cart.html'">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
            </div>
            <button class="btn btn-outline" onclick="window.location.href='dashboard.html'">Dashboard</button>
            <button class="btn btn-primary" onclick="logout()">Logout</button>
        `;
    } else {
        navLinks.innerHTML = `
            <button class="btn btn-outline" onclick="window.location.href='login.html'">Login</button>
            <button class="btn btn-primary" onclick="window.location.href='login.html'">Sign Up</button>
        `;
    }
}

function logout() {
    localStorage.removeItem('seapedia_user');
    localStorage.removeItem('seapedia_token');
    localStorage.removeItem('seapedia_active_role');
    window.location.href = 'index.html';
}

function handleSearch(event) {
    event.preventDefault();
    const query = document.getElementById('search-input').value;
    window.location.href = `searchproduct.html?q=${encodeURIComponent(query)}`;
}

function handleSortChange(sortValue) {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set('sort', sortValue);
    window.location.search = urlParams.toString();
}

async function loadSearchResults() {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    const category = urlParams.get('category');
    const sort = urlParams.get('sort');
    
    // Set UI state
    if (query) document.getElementById('search-input').value = query;
    if (sort) document.getElementById('sort-dropdown').value = sort;
    
    let titleText = 'All Products';
    if (query) titleText = `Search results for "${query}"`;
    else if (category) titleText = `${category.charAt(0).toUpperCase() + category.slice(1)} Products`;
    document.getElementById('search-results-title').textContent = titleText;
    
    const productList = document.getElementById('product-list');
    productList.innerHTML = '<p>Loading...</p>';
    
    try {
        let apiUrl = 'http://127.0.0.1:5000/api/products?';
        if (query) apiUrl += `q=${encodeURIComponent(query)}&`;
        if (category) apiUrl += `category=${encodeURIComponent(category)}&`;
        if (sort) apiUrl += `sort=${encodeURIComponent(sort)}`;
        
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error('Failed to fetch');
        
        const products = await response.json();
        
        if (products.length === 0) {
            productList.innerHTML = '<p>No products found matching your criteria.</p>';
            return;
        }
        
        productList.innerHTML = products.map(p => `
            <div class="product-card" onclick="window.location.href='product.html?id=${p.id}'">
                <img src="${p.image_url}" alt="${p.name}">
                <div class="product-info">
                    <h3 class="product-title">${p.name}</h3>
                    <div class="product-price">Rp ${p.price.toLocaleString()}</div>
                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 8px; display: flex; align-items: center; gap: 4px;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                        ${p.store_name}
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (err) {
        console.error(err);
        productList.innerHTML = '<p>Error loading products.</p>';
    }
}
