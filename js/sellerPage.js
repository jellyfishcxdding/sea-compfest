/* ── sellerPage.js — Phase 3: Seller Order Processing + Reports ── */
const _sellerUser  = JSON.parse(localStorage.getItem('seapedia_user'));
const _sellerToken = localStorage.getItem('seapedia_token');

document.addEventListener('DOMContentLoaded', () => {
    const activeRole = localStorage.getItem('seapedia_active_role');
    if (!_sellerUser || activeRole !== 'Seller') {
        window.location.href = 'index.html';
        return;
    }
    document.getElementById('seller-name').innerText = `Seller: ${_sellerUser.username}`;
    loadSellerOrders(_sellerUser.id);
    loadSellerReport(_sellerUser.id);
});

function _esc(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function _statusClass(status) {
    if (status === 'Sedang Dikemas')    return 'status-badge status-packed';
    if (status === 'Menunggu Pengirim') return 'status-badge status-pending';
    if (status === 'Sedang Dikirim')    return 'status-badge status-shipped';
    if (status === 'Selesai')           return 'status-badge status-delivered';
    if (status === 'Dibatalkan')        return 'status-badge status-cancelled';
    return 'status-badge status-pending';
}

// Expose globally (called by HTML button)
window.loadSellerOrders = async function(sellerId) {
    if (!sellerId) sellerId = _sellerUser?.id;
    if (!sellerId) return;

    const list = document.getElementById('seller-orders-list');
    list.innerHTML = '<p class="text-muted" style="padding:20px">Loading orders...</p>';

    try {
        const res = await fetch(`${API_URL}/orders/seller/${sellerId}`, {
            headers: { 'Authorization': `Bearer ${_sellerToken}` }
        });

        if (!res.ok) {
            list.innerHTML = "<p class='text-muted text-center' style='padding:40px'>You haven't set up a store yet, or no orders found.</p>";
            return;
        }

        const orders = await res.json();
        list.innerHTML = '';

        if (orders.length === 0) {
            list.innerHTML = "<p class='text-muted text-center' style='padding:40px'>No incoming orders yet. Share your store to get started!</p>";
            return;
        }

        orders.forEach(o => {
            const itemsHtml = (o.items || []).map(item =>
                `<p class="text-muted" style="font-size:13px;margin-bottom:2px">
                    ${_esc(item.name)} &times; ${item.qty}
                    <span style="color:var(--text-dark);font-weight:600">
                        &nbsp;Rp ${(item.price_at_time * item.qty).toLocaleString()}
                    </span>
                </p>`
            ).join('');

            const actionBtn = o.status === 'Sedang Dikemas'
                ? `<button class="btn btn-primary" style="background:#1976d2;border-color:#1976d2"
                        onclick="dispatchOrder(${o.id})">
                        📦 Ready for Pickup
                    </button>`
                : `<span class="${_statusClass(o.status)}">${_esc(o.status)}</span>`;

            const discount = o.discount_amount > 0
                ? `<p style="font-size:12px;color:var(--primary-color)">Voucher saved: Rp ${o.discount_amount.toLocaleString()}</p>`
                : '';

            list.innerHTML += `
            <div class="scroll-animate" style="background:white;border:1px solid var(--border-color);border-radius:14px;padding:20px;margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px">
                    <div style="flex:1">
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                            <strong style="font-size:15px">Order #${o.id}</strong>
                            <span class="text-muted" style="font-size:13px">from ${_esc(o.buyer_name)}</span>
                            <span class="text-muted" style="font-size:12px">${new Date(o.created_at).toLocaleDateString('id-ID')}</span>
                        </div>
                        ${itemsHtml}
                        <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border-color)">
                            ${discount}
                            <p style="font-weight:700;font-size:16px;color:var(--text-dark)">
                                Total: Rp ${o.total_price.toLocaleString()}
                            </p>
                        </div>
                    </div>
                    <div style="text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:8px">
                        ${actionBtn}
                    </div>
                </div>
            </div>`;
        });

        if (window.observeElements) window.observeElements();
    } catch(e) {
        list.innerHTML = "<p class='text-muted text-center' style='padding:40px'>Error loading orders.</p>";
    }
};

window.dispatchOrder = async function(orderId) {
    try {
        const res = await fetch(`${API_URL}/orders/${orderId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${_sellerToken}`
            },
            body: JSON.stringify({ status: 'Menunggu Pengirim' })
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Order dispatched! Waiting for driver.');
            loadSellerOrders(_sellerUser.id);
        } else {
            showToast(data.error || 'Failed to dispatch', true);
        }
    } catch(e) { showToast('Network error', true); }
};

async function loadSellerReport(sellerId) {
    try {
        const res = await fetch(`${API_URL}/reports/seller/${sellerId}`, {
            headers: { 'Authorization': `Bearer ${_sellerToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();

        // Inject stats if the DOM elements exist
        const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setEl('stat-total-orders',   data.total_orders);
        setEl('stat-total-revenue',  `Rp ${data.total_revenue.toLocaleString()}`);
        setEl('stat-completed-rev',  `Rp ${data.completed_revenue.toLocaleString()}`);
        setEl('stat-cancelled',      data.cancelled_count);
    } catch(e) {}
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}
