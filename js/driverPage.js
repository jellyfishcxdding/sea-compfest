document.addEventListener('DOMContentLoaded', () => {
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const activeRole = localStorage.getItem('seapedia_active_role');
    
    if (!user || activeRole !== 'Driver') {
        window.location.href = 'index.html';
        return;
    }
    
    document.getElementById('driver-name').innerText = `Driver: ${user.username}`;
    window.loadDriverOrders();
});

window.loadDriverOrders = async function() {
    try {
        const res = await fetch(`${API_URL}/orders/driver`);
        const orders = await res.json();
        const list = document.getElementById('driver-orders-list');
        list.innerHTML = '';
        
        if (orders.length === 0) {
            list.innerHTML = "<p class='text-muted text-center' style='padding: 40px;'>No available orders right now.</p>";
            return;
        }

        orders.forEach(o => {
            list.innerHTML += `
                <div class="card scroll-animate" style="border: 1px solid var(--border-color); padding: 16px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="font-size: 16px; margin-bottom: 4px;">Pickup from: ${o.store_name} (${o.store_city})</h3>
                        <p class="text-muted" style="font-size: 14px;">Deliver to: ${o.buyer_name}</p>
                        <p style="font-size: 13px; margin-top: 4px; font-weight: 600; color: #ffb300;">Status: ${o.status}</p>
                    </div>
                    <div>
                        ${o.status === 'Menunggu Pengirim' 
                            ? `<button class="btn btn-primary" onclick="updateOrderStatus(${o.id}, 'Sedang Dikirim')" style="background: #ffb300; border-color: #ffb300;">Accept Order</button>`
                            : `<button class="btn btn-primary" onclick="updateOrderStatus(${o.id}, 'Selesai')" style="background: var(--primary-color);">Complete Delivery</button>`
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
            showToast(`Order marked as ${newStatus}`);
            loadDriverOrders();
        }
    } catch(e) {}
};
