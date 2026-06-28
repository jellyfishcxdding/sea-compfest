// JS for searchproduct.html

document.addEventListener('DOMContentLoaded', () => {
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
