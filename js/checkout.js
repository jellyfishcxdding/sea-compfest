/* ── checkout.js — Phase 3: Voucher Support + Safe Checkout ── */
document.addEventListener('DOMContentLoaded', async () => {
    updateNavForAuth();
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    if (!user) { window.location.href = 'login.html'; return; }

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
                <img src="${item.image_url}" style="width:80px;height:80px;object-fit:cover;border-radius:8px">
                <div>
                    <h4 style="font-size:15px;margin-bottom:4px">${item.name}</h4>
                    <p class="text-muted" style="font-size:13px">${item.qty} &times; Rp ${item.price.toLocaleString()}</p>
                    <p style="font-weight:600;margin-top:4px">Rp ${(item.price * item.qty).toLocaleString()}</p>
                </div>
            </div>`;
    });

    window._checkoutSubtotal = subtotal;
    window._checkoutDiscount = 0;
    window._checkoutVoucher  = '';
    const deliveryFee = 10000;

    const el = (id) => document.getElementById(id);
    if (el('checkout-subtotal')) el('checkout-subtotal').innerText = `Rp ${subtotal.toLocaleString()}`;
    if (el('checkout-discount')) el('checkout-discount').innerText = '-';
    if (el('checkout-total'))    el('checkout-total').innerText    = `Rp ${(subtotal + deliveryFee).toLocaleString()}`;

    // Fetch wallet balance
    try {
        const token = localStorage.getItem('seapedia_token');
        const res   = await fetch(`${API_URL}/wallet/${user.id}`, { headers: { 'Authorization': `Bearer ${token}` } });
        const data  = await res.json();
        if (el('checkout-wallet-balance')) el('checkout-wallet-balance').innerText = `Rp ${data.balance.toLocaleString()}`;
    } catch(e) {}

    // Show available voucher hints
    try {
        const res     = await fetch(`${API_URL}/vouchers`);
        const vouchers = await res.json();
        const hint    = el('voucher-hint');
        if (hint && vouchers.length > 0) {
            hint.innerHTML = '💡 Try: ' + vouchers.map(v =>
                `<span style="cursor:pointer;color:var(--primary-color);font-weight:600;margin-right:8px"
                    onclick="document.getElementById('voucher-input').value='${v.code}'"
                >${v.code} (${v.percent}% off)</span>`
            ).join('');
        }
    } catch(e) {}
});

window.applyVoucher = async function() {
    const input = document.getElementById('voucher-input');
    const code  = (input?.value || '').trim().toUpperCase();
    const token = localStorage.getItem('seapedia_token');
    if (!code) { showToast('Please enter a voucher code', true); return; }

    try {
        const res  = await fetch(`${API_URL}/vouchers/validate`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body:    JSON.stringify({ code, cart_total: window._checkoutSubtotal })
        });
        const data = await res.json();
        const el   = (id) => document.getElementById(id);
        const deliveryFee = 10000;

        if (res.ok) {
            window._checkoutDiscount = data.discount_amount;
            window._checkoutVoucher  = data.code;
            const finalTotal = Math.max(0, window._checkoutSubtotal - data.discount_amount) + deliveryFee;
            if (el('checkout-discount')) el('checkout-discount').innerText = `-Rp ${data.discount_amount.toLocaleString()}`;
            if (el('checkout-total'))    el('checkout-total').innerText    = `Rp ${finalTotal.toLocaleString()}`;
            showToast(`✅ Voucher applied! You save Rp ${data.discount_amount.toLocaleString()}`);
        } else {
            window._checkoutDiscount = 0;
            window._checkoutVoucher  = '';
            showToast(data.error, true);
        }
    } catch(e) { showToast('Failed to validate voucher', true); }
};

window.processCheckout = async function() {
    const user   = JSON.parse(localStorage.getItem('seapedia_user'));
    const token  = localStorage.getItem('seapedia_token');
    const cart   = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    const method = document.getElementById('payment-method')?.value;
    if (cart.length === 0) return;

    try {
        const res  = await fetch(`${API_URL}/checkout`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body:    JSON.stringify({
                user_id:         user.id,
                cart:            cart,
                payment_method:  method,
                delivery_fee:    10000,
                voucher_code:    window._checkoutVoucher  || null,
                discount_amount: window._checkoutDiscount || 0
            })
        });
        const data = await res.json();
        if (res.ok) {
            localStorage.removeItem('seapedia_cart');
            if (window._syncFloatingCart) window._syncFloatingCart();
            showCustomPopup('Payment Successful! 🎉', `Total paid: Rp ${data.total_paid.toLocaleString()}`, () => {
                window.location.href = 'myOrder.html';
            });
        } else {
            showToast(data.error, true);
        }
    } catch(e) { showToast('Checkout failed. Try again.', true); }
};
