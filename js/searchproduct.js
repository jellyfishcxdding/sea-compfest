// searchproduct.js — consistent with style.js card template

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const sort = urlParams.get('sort');
    if (sort) {
        const sortDropdown = document.getElementById('sort-dropdown');
        if (sortDropdown) sortDropdown.value = sort;
    }
    loadSearchResults();
});

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
    const query    = urlParams.get('q');
    const category = urlParams.get('category');
    const sort     = urlParams.get('sort');

    // Set UI state
    if (query) {
        const inp = document.getElementById('search-input');
        if (inp) inp.value = query;
    }
    if (sort) {
        const sd = document.getElementById('sort-dropdown');
        if (sd) sd.value = sort;
    }

    // Page title
    const titleEl = document.getElementById('search-results-title');
    if (titleEl) {
        if (query)         titleEl.textContent = `Results for "${query}"`;
        else if (category) titleEl.textContent = `${category.charAt(0).toUpperCase() + category.slice(1)} Products`;
        else               titleEl.textContent = 'All Products';
    }

    const productList = document.getElementById('product-list');
    if (!productList) return;

    // Show skeletons while loading
    if (window.showSkeletons) {
        window.showSkeletons('product-list', 10);
    } else {
        productList.innerHTML = '<p class="text-muted" style="padding:20px">Loading...</p>';
    }

    try {
        let apiUrl = `${API_URL}/products?limit=80`;
        if (query)    apiUrl += `&q=${encodeURIComponent(query)}`;
        if (category) apiUrl += `&category=${encodeURIComponent(category)}`;
        if (sort)     apiUrl += `&sort=${encodeURIComponent(sort)}`;

        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error(`API error ${response.status}`);

        const products = await response.json();
        productList.innerHTML = '';

        if (products.length === 0) {
            productList.innerHTML = `
                <div style="grid-column:1/-1;text-align:center;padding:60px 20px">
                    <p style="font-size:48px;margin-bottom:12px">🔍</p>
                    <p style="font-size:18px;font-weight:600;margin-bottom:8px">No products found</p>
                    <p class="text-muted">Try a different search term or category</p>
                </div>`;
            return;
        }

        // Use the exact same card template as style.js / homepage
        products.forEach((p, i) => {
            const card = document.createElement('div');
            card.className = 'product-card slide-fwd-hover scroll-animate';
            card.style.setProperty('--card-idx', i);
            card.setAttribute('data-product-id', p.id);
            card.onclick = () => window.location.href = `product.html?id=${p.id}`;
            card.style.cursor = 'pointer';
            card.innerHTML = `
                <div class="product-image" style="background-image: url('${p.image_url}');"></div>
                <div class="product-info">
                    <h3 class="product-title">${p.name}</h3>
                    <p class="product-price">Rp ${p.price.toLocaleString()}</p>
                    <div class="store-info">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                            <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                        ${p.store_name || p.store_city || 'SEAPEDIA'}
                    </div>
                </div>`;
            productList.appendChild(card);
        });

        // Trigger scroll-reveal and stagger animations
        if (window.observeElements) window.observeElements();
        if (window.indexProductCards) window.indexProductCards();

    } catch (err) {
        console.error('loadSearchResults error:', err);
        productList.innerHTML = `
            <div style="grid-column:1/-1;text-align:center;padding:60px 20px">
                <p style="font-size:48px;margin-bottom:12px">⚠️</p>
                <p style="font-size:18px;font-weight:600;margin-bottom:8px">Could not load products</p>
                <p class="text-muted">Make sure the SEAPEDIA backend is running on port 5000</p>
                <button class="btn btn-outline" onclick="loadSearchResults()" style="margin-top:16px">Try Again</button>
            </div>`;
    }
}
