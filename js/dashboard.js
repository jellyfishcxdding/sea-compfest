document.addEventListener('DOMContentLoaded', async () => {
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const token = localStorage.getItem('seapedia_token');
    
    if (!user) {
        window.location.href = 'login.html';
        return;
    }
    
    document.getElementById('buyer-name').innerText = `Welcome, ${user.username}`;
    
    try {
        // Load Wallet
        const wRes = await fetch(`${API_URL}/wallet/${user.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const wData = await wRes.json();
        document.getElementById('wallet-balance').innerText = `Rp ${wData.balance.toLocaleString()}`;

        // Load Recent Activity (Orders)
        const oRes = await fetch(`${API_URL}/orders/buyer/${user.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const orders = await oRes.json();
        
        const list = document.getElementById('recent-activity-list');
        list.innerHTML = '';
        
        if (orders.length === 0) {
            list.innerHTML = "<p class='text-muted' style='padding: 20px;'>No recent activity.</p>";
            return;
        }

        orders.slice(0, 3).forEach(o => {
            list.innerHTML += `
                <div class="card scroll-animate" style="border: 1px solid var(--border-color); padding: 16px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="font-size: 15px; margin-bottom: 4px;">Purchase from ${o.store_name}</h4>
                        <p class="text-muted" style="font-size: 13px;">${new Date(o.created_at).toLocaleDateString()}</p>
                    </div>
                    <div style="text-align: right;">
                        <span class="badge" style="background: #e3f2fd; color: #1976d2;">${o.status}</span>
                        <p style="font-weight: 600; margin-top: 8px;">Rp ${o.total_price.toLocaleString()}</p>
                    </div>
                </div>
            `;
        });
        
        // Load Wishlist
        const wlRes = await fetch(`${API_URL}/wishlist/${user.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const wishlist = await wlRes.json();
        const wlList = document.getElementById('wishlist-activity-list');
        if (wlList) {
            wlList.innerHTML = '';
            if (wishlist.length === 0) {
                wlList.innerHTML = "<p class='text-muted' style='padding: 20px;'>Your wishlist is empty.</p>";
            } else {
                wishlist.forEach(w => {
                    wlList.innerHTML += `
                        <div class="card scroll-animate" style="border: 1px solid var(--border-color); padding: 16px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div class="flex gap-3 align-center">
                                <img src="${w.image_url}" style="width:50px; height:50px; border-radius:8px; object-fit:cover;">
                                <div>
                                    <h4 style="font-size: 15px; margin-bottom: 4px;">${w.name}</h4>
                                    <p class="text-muted" style="font-size: 13px;">Rp ${w.price.toLocaleString()}</p>
                                </div>
                            </div>
                            <button class="btn btn-outline" style="border-color:var(--primary-color); color:var(--primary-color);" onclick="window.location.href='product.html?id=${w.id}'">View</button>
                        </div>
                    `;
                });
            }
        }
        
        if (window.observeElements) window.observeElements();
        
    } catch(e) { console.error(e); }
});
