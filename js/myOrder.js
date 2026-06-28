document.addEventListener('DOMContentLoaded', async () => {
    updateNavForAuth();
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const token = localStorage.getItem('seapedia_token');
    if (!user) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const res = await fetch(`${API_URL}/orders/buyer/${user.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const orders = await res.json();
        
        const list = document.getElementById('orders-list');
        list.innerHTML = '';
        
        if (orders.length === 0) {
            list.innerHTML = "<p class='text-muted' style='text-align: center; padding: 40px;'>You have no transaction history.</p>";
            return;
        }

        orders.forEach(order => {
            let itemsHtml = '';
            order.items.forEach(item => {
                itemsHtml += `
                    <div class="flex gap-3 mb-3 pb-3" style="border-bottom: 1px solid var(--border-color);">
                        <img src="${item.image_url}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">
                        <div>
                            <h4 style="font-size: 15px; margin-bottom: 4px;">${item.name}</h4>
                            <p class="text-muted" style="font-size: 13px;">${item.qty} x Rp ${item.price_at_time.toLocaleString()}</p>
                            <p style="font-weight: 600; margin-top: 4px;">Rp ${(item.price_at_time * item.qty).toLocaleString()}</p>
                        </div>
                    </div>
                `;
            });

            // Set badge color based on status
            let badgeBg = '#e3f2fd'; let badgeCol = '#1976d2';
            if (order.status === 'Selesai') { badgeBg = '#e8f5e9'; badgeCol = '#00aa5b'; }
            else if (order.status === 'Dibatalkan') { badgeBg = '#ffebee'; badgeCol = '#d32f2f'; }
            else if (order.status === 'Sedang Dikirim') { badgeBg = '#fff8e1'; badgeCol = '#ffb300'; }

            list.innerHTML += `
                <div class="order-card scroll-animate" style="background: white; padding: 24px; border-radius: 16px; box-shadow: var(--box-shadow); margin-bottom: 24px;">
                    <div class="flex justify-between align-center mb-3">
                        <div class="flex align-center gap-2">
                            <strong>${order.store_name}</strong>
                            <span class="text-muted" style="font-size: 14px;">• ${new Date(order.created_at).toLocaleDateString()}</span>
                        </div>
                        <span class="badge" style="background: ${badgeBg}; color: ${badgeCol}; padding: 6px 12px; font-weight: 600;">${order.status}</span>
                    </div>
                    
                    ${itemsHtml}
                    
                    <div class="flex justify-between align-center mt-3">
                        <span class="text-muted">Total Payment</span>
                        <strong style="color: var(--primary-color); font-size: 18px;">Rp ${order.total_price.toLocaleString()}</strong>
                    </div>
                </div>
            `;
        });
        
        // Re-observe animations
        if (window.observeElements) window.observeElements();

    } catch(e) {
        console.error(e);
        document.getElementById('orders-list').innerHTML = "<p class='text-muted'>Error loading orders.</p>";
    }
});
