const API_URL = 'http://127.0.0.1:5000/api';

let grandTotal = 0;

async function renderCheckout() {
    const container = document.getElementById('checkout-items-container');
    let cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
    
    if (cart.length === 0) {
        window.location.href = 'cart.html';
        return;
    }

    let html = '';
    let itemsTotal = 0;
    let totalQty = 0;

    cart.forEach((item) => {
        const itemTotal = item.price * item.qty;
        itemsTotal += itemTotal;
        totalQty += item.qty;

        html += `
        <div class="card mb-3">
            <h3 class="mb-2">Store: ${item.store_name || 'SEAPEDIA Store'}</h3>
            <div class="flex gap-3 align-center py-2">
                <div style="width: 60px; height: 60px; background-image: url('${item.image_url}'); background-size: cover; background-position: center; border-radius: 8px;"></div>
                <div style="flex-grow: 1;">
                    <h4 style="margin:0; font-size: 14px;">${item.name}</h4>
                    <p style="margin:4px 0; color:var(--text-muted); font-size:12px;">${item.qty} items x Rp ${item.price.toLocaleString()}</p>
                </div>
                <div style="margin-left: auto; font-weight:700;">Rp ${itemTotal.toLocaleString()}</div>
            </div>
        </div>`;
    });

    container.innerHTML = html;
    
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    let walletBalance = 0;
    if (user && user.id) {
        try {
            const res = await fetch(`${API_URL}/wallet/${user.id}`);
            const data = await res.json();
            if (data.balance !== undefined) {
                walletBalance = data.balance;
            }
        } catch(e) {
            console.error('Failed to fetch wallet:', e);
        }
    } else {
        walletBalance = 5000000;
    }
    
    document.getElementById('checkout-wallet-balance').innerText = `Rp ${walletBalance.toLocaleString()}`;

    const deliveryFee = 10000;
    grandTotal = itemsTotal + deliveryFee;

    document.getElementById('summary-qty').innerText = totalQty;
    document.getElementById('summary-price').innerText = `Rp ${itemsTotal.toLocaleString()}`;
    document.getElementById('summary-total').innerText = `Rp ${grandTotal.toLocaleString()}`;
}

async function processCheckout() {
    const method = document.querySelector('input[name="payment_method"]:checked').value;
    const btn = document.getElementById('pay-btn');
    const user = JSON.parse(localStorage.getItem('seapedia_user'));
    const userId = user ? user.id : 1;
    const cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];

    btn.disabled = true;
    btn.innerText = 'Processing...';
    
    try {
        const res = await fetch(`${API_URL}/checkout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                cart,
                payment_method: method,
                delivery_fee: 10000
            })
        });

        const data = await res.json();

        if (!res.ok) {
            showCustomPopup('Checkout Failed', data.error || 'An error occurred during checkout.');
            btn.disabled = false;
            btn.innerText = 'Pay & Checkout';
            return;
        }

        if (method === 'card') {
            showCustomPopup('Redirecting...', 'Connecting to Secure Bank API Gateway for Credit/Debit processing...', () => {
                completeCheckout();
            });
        } else if (method === 'wallet') {
            showCustomPopup('Processing SEAPEDIA Pay', `Successfully deducted Rp ${grandTotal.toLocaleString()} from your wallet.`, () => {
                completeCheckout();
            });
        } else if (method === 'cod') {
            showCustomPopup('Order Confirmed', 'Please prepare exact cash when the driver arrives.', () => {
                completeCheckout();
            });
        }
    } catch(e) {
        console.error(e);
        showCustomPopup('Error', 'Could not reach server.');
        btn.disabled = false;
        btn.innerText = 'Pay & Checkout';
    }
}

function completeCheckout() {
    localStorage.removeItem('seapedia_cart');
    window.location.href = 'myOrder.html';
}

window.addEventListener('DOMContentLoaded', () => {
    updateNavForAuth();
    renderCheckout();

    const payBtn = document.getElementById('pay-btn');
    if (payBtn) {
        payBtn.addEventListener('click', processCheckout);
    }
});
