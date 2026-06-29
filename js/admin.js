/**
 * admin.js — SEAPEDIA Admin Dashboard (Phase 5 + 6)
 * Depends on: style.js (API_URL, showToast)
 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const activeRole = localStorage.getItem('seapedia_active_role');
    if (activeRole !== 'Admin') {
        window.location.replace('index.html');
        return;
    }
    const user = JSON.parse(localStorage.getItem('seapedia_user') || '{}');
    const nameEl = document.getElementById('admin-username');
    if (nameEl) nameEl.textContent = user.username || 'Admin';

    loadAdminStats();
    loadAdminOrders();
    bindOverdueButton();
    bindSidebarNav();
});

function authHeaders() {
    const token = localStorage.getItem('seapedia_token') || '';
    return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function formatRp(n) {
    return 'Rp ' + Number(n).toLocaleString('id-ID');
}

function formatDate(iso) {
    if (!iso) return '—';
    try {
        return new Date(iso).toLocaleDateString('id-ID', {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    } catch (_) { return iso; }
}

window.loadAdminStats = async function() {
    try {
        const res = await fetch(`${API_URL}/admin/stats`, { headers: authHeaders() });
        if (res.status === 403) { showToast('Access denied — Admin only', true); return; }
        if (!res.ok) throw new Error('Stats fetch failed');
        const data = await res.json();
        setText('stat-users',    data.total_users    ?? '—');
        setText('stat-products', data.total_products ?? '—');
        setText('stat-orders',   data.total_orders   ?? '—');
        setText('stat-revenue',  formatRp(data.total_revenue ?? 0));
        setText('stat-pending',  data.pending_orders     ?? '—');
        setText('stat-active',   data.active_deliveries  ?? '—');
    } catch (err) {
        console.error('[admin] loadAdminStats:', err);
        showToast('Failed to load stats — is backend running?', true);
    }
};

const STATUS_CLASS = {
    'Sedang Dikemas':    'badge-warning',
    'Menunggu Pengirim': 'badge-info',
    'Sedang Dikirim':    'badge-primary',
    'Selesai':           'badge-success',
    'Dibatalkan':        'badge-danger'
};

window.loadAdminOrders = async function() {
    const table = document.getElementById('admin-orders-table');
    if (!table) return;
    try {
        const res = await fetch(`${API_URL}/admin/orders`, { headers: authHeaders() });
        if (res.status === 403) { showToast('Access denied — Admin only', true); return; }
        if (!res.ok) throw new Error('Orders fetch failed');
        const orders = await res.json();
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (orders.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 6;
            td.textContent = 'No orders found.';
            td.style.cssText = 'text-align:center;padding:32px;color:var(--text-muted)';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        orders.forEach(o => {
            const tr = document.createElement('tr');

            // Helper: plain text cell
            const td = (txt) => {
                const el = document.createElement('td');
                el.textContent = txt ?? '—';
                return el;
            };

            // Status badge cell (no innerHTML — safe)
            const statusTd = document.createElement('td');
            const badge    = document.createElement('span');
            badge.className = `status-badge ${STATUS_CLASS[o.status] || 'badge-secondary'}`;
            badge.textContent = o.status ?? '—';
            statusTd.appendChild(badge);

            tr.appendChild(td('#' + o.id));
            tr.appendChild(td(o.buyer_name));
            tr.appendChild(td(o.store_name));
            tr.appendChild(statusTd);
            tr.appendChild(td(formatRp(o.total_price)));
            tr.appendChild(td(formatDate(o.created_at)));
            tbody.appendChild(tr);
        });

        if (typeof window.observeElements === 'function') window.observeElements();
    } catch (err) {
        console.error('[admin] loadAdminOrders:', err);
        showToast('Failed to load orders', true);
    }
};

function bindOverdueButton() {
    const btn = document.getElementById('trigger-overdue');
    if (!btn) return;
    btn.addEventListener('click', async () => {
        btn.disabled = true;
        btn.textContent = 'Processing…';
        try {
            const res  = await fetch(`${API_URL}/admin/trigger-overdue`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({})
            });
            const data = await res.json();
            if (!res.ok) { showToast(data.error || 'Trigger failed', true); return; }
            const count = data.cancelled_count ?? 0;
            showToast(
                count > 0
                    ? `${count} overdue order(s) cancelled & refunded`
                    : 'No overdue orders found — all good!'
            );
            loadAdminStats();
            loadAdminOrders();
        } catch (err) {
            console.error('[admin] triggerOverdue:', err);
            showToast('Network error — backend may be down', true);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Trigger Overdue Check';
        }
    });
}

function bindSidebarNav() {
    document.querySelectorAll('[data-section]').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            const target = document.getElementById(link.dataset.section);
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            document.querySelectorAll('[data-section]').forEach(l => l.classList.remove('sidebar-active'));
            link.classList.add('sidebar-active');
        });
    });
}

window.adminLogout = function() {
    localStorage.clear();
    window.location.href = 'index.html';
};
