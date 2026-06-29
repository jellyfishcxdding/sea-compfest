/* ── myOrder.js — Buyer order history with full breakdown & status timeline ── */
document.addEventListener('DOMContentLoaded', async () => {
    updateNavForAuth();
    const user  = JSON.parse(localStorage.getItem('seapedia_user'));
    const token = localStorage.getItem('seapedia_token');
    if (!user) { window.location.href = 'login.html'; return; }

    try {
        const res    = await fetch(`${API_URL}/orders/buyer/${user.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const orders = await res.json();
        const list   = document.getElementById('orders-list');
        list.innerHTML = '';

        if (!Array.isArray(orders) || orders.length === 0) {
            list.innerHTML = "<p class='text-muted' style='text-align:center;padding:40px;'>You have no transaction history.</p>";
            return;
        }

        orders.forEach(order => {
            const safeName = s => String(s || '').replace(/</g,'&lt;').replace(/>/g,'&gt;');

            let itemsHtml = (order.items || []).map(item => `
                <div class="flex gap-3 mb-3 pb-3" style="border-bottom:1px solid var(--border-color);">
                    <img src="${item.image_url}" style="width:80px;height:80px;object-fit:cover;border-radius:8px">
                    <div>
                        <h4 style="font-size:15px;margin-bottom:4px">${safeName(item.name)}</h4>
                        <p class="text-muted" style="font-size:13px">${item.qty} × Rp ${item.price_at_time.toLocaleString()}</p>
                        <p style="font-weight:600;margin-top:4px">Rp ${(item.price_at_time * item.qty).toLocaleString()}</p>
                    </div>
                </div>`).join('');

            // Status color
            const statusColors = {
                'Sedang Dikemas':    ['#e3f2fd', '#1976d2'],
                'Menunggu Pengirim': ['#fff3e0', '#e65100'],
                'Sedang Dikirim':    ['#fff8e1', '#ffb300'],
                'Pesanan Selesai':   ['#e8f5e9', '#00aa5b'],
                'Dikembalikan':      ['#fce4ec', '#c62828'],
                'Dibatalkan':        ['#ffebee', '#d32f2f'],
            };
            const [bg, col] = statusColors[order.status] || ['#f5f5f5', '#666'];

            // Financial breakdown
            const subtotal  = order.subtotal      || 0;
            const discount  = order.discount_amount || 0;
            const ppn       = order.ppn_amount     || 0;
            const delFee    = order.delivery_fee   || 0;
            const total     = order.total_price    || 0;
            const method    = order.delivery_method || 'Regular';

            const voucherRow = discount > 0
                ? `<div class="flex justify-between" style="color:var(--primary-color)"><span>Diskon Voucher</span><span>-Rp ${discount.toLocaleString()}</span></div>`
                : '';

            // Status history timeline
            const historyHtml = (order.status_history || []).map(h => `
                <div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:8px;">
                    <div style="width:10px;height:10px;background:var(--primary-color);border-radius:50%;margin-top:4px;flex-shrink:0;"></div>
                    <div>
                        <p style="font-weight:600;font-size:13px;margin-bottom:2px">${safeName(h.status)}</p>
                        <p class="text-muted" style="font-size:12px">${new Date(h.changed_at).toLocaleString('id-ID')}</p>
                    </div>
                </div>`).join('');

            list.innerHTML += `
                <div class="order-card scroll-animate" style="background:white;padding:24px;border-radius:16px;box-shadow:var(--box-shadow);margin-bottom:24px;">
                    <div class="flex justify-between align-center mb-3">
                        <div class="flex align-center gap-2">
                            <strong>${safeName(order.store_name)}</strong>
                            <span class="text-muted" style="font-size:14px;">• ${new Date(order.created_at).toLocaleDateString('id-ID')}</span>
                            <span class="text-muted" style="font-size:12px;">📦 ${method}</span>
                        </div>
                        <span class="badge" style="background:${bg};color:${col};padding:6px 12px;font-weight:600;">${safeName(order.status)}</span>
                    </div>

                    ${itemsHtml}

                    <div style="background:#f9f9f9;border-radius:8px;padding:12px;margin-top:12px;font-size:14px;">
                        <div class="flex justify-between mb-1"><span class="text-muted">Subtotal</span><span>Rp ${subtotal.toLocaleString()}</span></div>
                        ${voucherRow}
                        <div class="flex justify-between mb-1"><span class="text-muted">Ongkos Kirim (${method})</span><span>Rp ${delFee.toLocaleString()}</span></div>
                        <div class="flex justify-between mb-1"><span class="text-muted">PPN 12%</span><span>Rp ${ppn.toLocaleString()}</span></div>
                        <hr style="border:none;border-top:1px solid var(--border-color);margin:8px 0;">
                        <div class="flex justify-between"><strong>Total</strong><strong style="color:var(--primary-color);font-size:16px;">Rp ${total.toLocaleString()}</strong></div>
                    </div>

                    ${historyHtml ? `
                    <div style="margin-top:16px;">
                        <p style="font-weight:600;font-size:13px;margin-bottom:8px;color:var(--text-muted);">Status Timeline</p>
                        <div style="border-left:2px solid var(--border-color);padding-left:16px;">
                            ${historyHtml}
                        </div>
                    </div>` : ''}
                </div>`;
        });

        if (window.observeElements) window.observeElements();
    } catch(e) {
        console.error(e);
        document.getElementById('orders-list').innerHTML = "<p class='text-muted'>Error loading orders.</p>";
    }
});
