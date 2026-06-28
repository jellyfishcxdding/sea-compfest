/* ── driverPage.js — Phase 4: Driver Job Flow ── */
const _driverUser  = JSON.parse(localStorage.getItem('seapedia_user'));
const _driverToken = localStorage.getItem('seapedia_token');

document.addEventListener('DOMContentLoaded', () => {
    const activeRole = localStorage.getItem('seapedia_active_role');
    if (!_driverUser || activeRole !== 'Driver') {
        window.location.href = 'index.html';
        return;
    }
    document.getElementById('driver-name').innerText = `Driver: ${_driverUser.username}`;
    loadAvailableJobs();
    loadMyDeliveries();
    loadEarnings();
});

function _statusClass(status) {
    if (status === 'Menunggu Pengirim') return 'status-badge status-packed';
    if (status === 'Sedang Dikirim')    return 'status-badge status-shipped';
    if (status === 'Selesai')           return 'status-badge status-delivered';
    return 'status-badge status-pending';
}

window.loadDriverOrders = loadAvailableJobs;   // backward-compat alias

async function loadAvailableJobs() {
    const list = document.getElementById('driver-orders-list');
    if (!list) return;
    list.innerHTML = '<p class="text-muted" style="padding:20px">Loading...</p>';
    try {
        const res  = await fetch(`${API_URL}/jobs/available`, {
            headers: { 'Authorization': `Bearer ${_driverToken}` }
        });
        if (!res.ok) { list.innerHTML = '<p class="text-muted text-center" style="padding:40px">Unable to load jobs.</p>'; return; }
        const jobs = await res.json();
        list.innerHTML = '';

        if (jobs.length === 0) {
            list.innerHTML = '<p class="text-muted text-center" style="padding:40px">No available orders right now. Check back soon!</p>';
            return;
        }

        jobs.forEach(j => {
            list.innerHTML += `
            <div class="scroll-animate" style="background:white;border:1px solid var(--border-color);border-radius:14px;padding:20px;display:flex;justify-content:space-between;align-items:center;gap:16px">
                <div style="flex:1">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                        <span style="font-size:20px">📦</span>
                        <strong style="font-size:15px">${_esc(j.store_name)}</strong>
                        <span class="text-muted" style="font-size:13px">${_esc(j.store_city)}</span>
                    </div>
                    <p class="text-muted" style="font-size:13px;margin-bottom:6px">Deliver to: <strong>${_esc(j.buyer_name)}</strong></p>
                    <p style="font-size:13px;color:var(--primary-color);font-weight:600">Est. Earnings: Rp ${j.estimated_earnings.toLocaleString()}</p>
                </div>
                <button class="btn btn-primary" style="background:#ff9800;border-color:#ff9800;white-space:nowrap" onclick="acceptJob(${j.id})">
                    Accept Job
                </button>
            </div>`;
        });
        if (window.observeElements) window.observeElements();
    } catch(e) { list.innerHTML = '<p class="text-muted text-center" style="padding:40px">Error loading jobs.</p>'; }
}

async function loadMyDeliveries() {
    const list = document.getElementById('driver-orders-list');
    try {
        const res  = await fetch(`${API_URL}/jobs/mine`, {
            headers: { 'Authorization': `Bearer ${_driverToken}` }
        });
        if (!res.ok) return;
        const jobs = await res.json();
        const active = jobs.filter(j => j.status === 'Sedang Dikirim');
        if (active.length === 0) return;

        // Prepend active deliveries to the list
        let html = '<h3 style="margin-bottom:12px;color:#f97316">🚚 Your Active Deliveries</h3>';
        active.forEach(j => {
            html += `
            <div class="scroll-animate" style="background:#fff8e1;border:1px solid #ffb300;border-radius:14px;padding:20px;display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:12px">
                <div style="flex:1">
                    <p style="font-weight:600;margin-bottom:4px">Pickup: ${_esc(j.store_name)} (${_esc(j.store_city)})</p>
                    <p class="text-muted" style="font-size:13px">Deliver to: ${_esc(j.buyer_name)}</p>
                    <span class="${_statusClass(j.status)}" style="margin-top:8px;display:inline-flex">${j.status}</span>
                </div>
                <button class="btn btn-primary" onclick="completeJob(${j.id})">
                    ✅ Complete
                </button>
            </div>`;
        });
        if (list) list.insertAdjacentHTML('afterbegin', html);
    } catch(e) {}
}

async function loadEarnings() {
    try {
        const res  = await fetch(`${API_URL}/jobs/earnings`, {
            headers: { 'Authorization': `Bearer ${_driverToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        const el = document.getElementById('driver-earnings-total');
        if (el) {
            el.innerHTML = `
                <div class="stat-card" style="margin-bottom:0">
                    <div class="stat-label">Total Deliveries</div>
                    <div class="stat-value" data-target="${data.total_deliveries}">${data.total_deliveries}</div>
                </div>
                <div class="stat-card" style="margin-bottom:0;border-left-color:#ff9800">
                    <div class="stat-label">Total Earned</div>
                    <div class="stat-value" style="color:#ff9800">Rp ${data.total_earned.toLocaleString()}</div>
                </div>`;
        }
    } catch(e) {}
}

window.acceptJob = async function(orderId) {
    try {
        const res  = await fetch(`${API_URL}/jobs/${orderId}/take`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${_driverToken}` }
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message);
            loadAvailableJobs();
            loadMyDeliveries();
        } else {
            showToast(data.error, true);
        }
    } catch(e) { showToast('Failed to accept job', true); }
};

window.completeJob = async function(orderId) {
    try {
        const res  = await fetch(`${API_URL}/jobs/${orderId}/complete`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${_driverToken}` }
        });
        const data = await res.json();
        if (res.ok) {
            showToast(`${data.message} You earned Rp ${data.earnings.toLocaleString()}!`);
            loadAvailableJobs();
            loadMyDeliveries();
            loadEarnings();
        } else {
            showToast(data.error, true);
        }
    } catch(e) { showToast('Failed to complete delivery', true); }
};

function _esc(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}

