document.addEventListener('DOMContentLoaded', () => {
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const activeRole = localStorage.getItem('seapedia_active_role');
    
    if (!user || activeRole !== 'Seller') {
        window.location.href = 'index.html';
        return;
    }
    
    document.getElementById('seller-name').innerText = `Seller: ${user.username}`;
    window.loadSellerOrders(user.id);
});

window.loadSellerOrders = async function(sellerId) {
    if (!sellerId) {
        const user = JSON.parse(localStorage.getItem('seapedia_user'));
        if(user) sellerId = user.id;
        else return;
    }

    try {
        const token = localStorage.getItem('seapedia_token');
        const res = await fetch(`${API_URL}/orders/seller/${sellerId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const list = document.getElementById('seller-orders-list');
        list.innerHTML = '';

        if (!res.ok) {
            list.innerHTML = "<p class='text-muted text-center'>You haven't set up a store yet.</p>";
            return;
        }

        const orders = await res.json();
        
        if (orders.length === 0) {
            list.innerHTML = "<p class='text-muted text-center' style='padding: 40px;'>No incoming orders.</p>";
            return;
        }

        orders.forEach(o => {
            let itemsHtml = '';
            o.items.forEach(item => {
                itemsHtml += `<p class="text-muted" style="font-size: 13px;">${item.qty}x ${item.name}</p>`;
            });

            list.innerHTML += `
                <div class="card scroll-animate" style="border: 1px solid var(--border-color); padding: 16px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="font-size: 16px; margin-bottom: 4px;">Order from: ${o.buyer_name}</h3>
                        ${itemsHtml}
                        <p style="font-size: 13px; margin-top: 8px; font-weight: 600; color: #1976d2;">Status: ${o.status}</p>
                    </div>
                    <div>
                        ${o.status === 'Sedang Dikemas' 
                            ? `<button class="btn btn-primary" onclick="updateOrderStatus(${o.id}, 'Menunggu Pengirim')" style="background: #1976d2; border-color: #1976d2;">Ready for Pickup</button>`
                            : `<span class="badge" style="background:#e8f5e9; color:#00aa5b;">Dispatched</span>`
                        }
                    </div>
                </div>
            `;
        });
        if (window.observeElements) window.observeElements();
    } catch(e) { console.error(e); }
};

window.updateOrderStatus = async function(orderId, newStatus) {
    try {
        const res = await fetch(`${API_URL}/orders/${orderId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            showToast(`Order updated to ${newStatus}`);
            loadSellerOrders();
        }
    } catch(e) {}
};
