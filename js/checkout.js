document.addEventListener('DOMContentLoaded', async () => {
    updateNavForAuth();
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    if (!user) {
        window.location.href = 'login.html';
        return;
    }

    const cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    if (cart.length === 0) {
        document.getElementById('checkout-items-list').innerHTML = "<p class='text-muted'>Your cart is empty.</p>";
        return;
    }

    let subtotal = 0;
    const list = document.getElementById('checkout-items-list');
    list.innerHTML = '';
    
    cart.forEach(item => {
        subtotal += (item.price * item.qty);
        list.innerHTML += `
            <div class="flex gap-3 mb-3 pb-3" style="border-bottom: 1px solid var(--border-color);">
                <img src="${item.image_url}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">
                <div>
                    <h4 style="font-size: 15px; margin-bottom: 4px;">${item.name}</h4>
                    <p class="text-muted" style="font-size: 13px;">${item.qty} x Rp ${item.price.toLocaleString()}</p>
                    <p style="font-weight: 600; margin-top: 4px;">Rp ${(item.price * item.qty).toLocaleString()}</p>
                </div>
            </div>
        `;
    });

    const deliveryFee = 10000;
    document.getElementById('checkout-subtotal').innerText = `Rp ${subtotal.toLocaleString()}`;
    document.getElementById('checkout-total').innerText = `Rp ${(subtotal + deliveryFee).toLocaleString()}`;

    // Fetch Wallet Balance
    try {
        const token = localStorage.getItem('seapedia_token');
        const res = await fetch(`${API_URL}/wallet/${user.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        document.getElementById('checkout-wallet-balance').innerText = `Rp ${data.balance.toLocaleString()}`;
    } catch(e) { console.error(e); }
});

window.processCheckout = async function() {
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const token = localStorage.getItem('seapedia_token');
    const cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    const method = document.getElementById('payment-method').value;

    if (cart.length === 0) return;

    try {
        const res = await fetch(`${API_URL}/checkout`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                user_id: user.id,
                cart: cart,
                payment_method: method,
                delivery_fee: 10000
            })
        });

        const data = await res.json();
        if (res.ok) {
            localStorage.removeItem('seapedia_cart');
            showCustomPopup('Payment Successful!', `You paid Rp ${data.total_paid.toLocaleString()}`, () => {
                window.location.href = 'myOrder.html';
            });
        } else {
            showToast(data.error, true);
        }
    } catch (e) {
        showToast('Checkout failed', true);
    }
};
