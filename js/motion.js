/* ============================================================
   motion.js — purely additive UI life layer
   No logic changes. Attach after style.js on every page.
   ============================================================ */

/* ── 1. Ripple effect on all .btn clicks ── */
document.addEventListener('click', function (e) {
  const btn = e.target.closest('.btn');
  if (!btn) return;
  const ripple = document.createElement('span');
  ripple.className = 'ripple';
  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height) * 1.6;
  ripple.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - rect.left - size / 2}px;top:${e.clientY - rect.top - size / 2}px`;
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
});

/* ── 2. Scroll-reveal observer ── */
const _revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        _revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
);

function observeElements() {
  document.querySelectorAll('.scroll-animate').forEach(el => _revealObserver.observe(el));
}
// expose globally so dynamic injections can call it
window.observeElements = observeElements;
// initial pass
document.addEventListener('DOMContentLoaded', observeElements);

/* ── 3. Skeleton loader helper ── */
function showSkeletons(containerId, count = 5) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = Array.from({ length: count }, () => `
    <div class="skeleton-card">
      <div class="skeleton skeleton-img"></div>
      <div class="skeleton skeleton-text"></div>
      <div class="skeleton skeleton-text short"></div>
      <div class="skeleton skeleton-text price"></div>
    </div>
  `).join('');
}
window.showSkeletons = showSkeletons;

/* ── 4. Product card stagger index (set CSS var --card-idx) ── */
function indexProductCards() {
  document.querySelectorAll('.product-card').forEach((card, i) => {
    card.style.setProperty('--card-idx', i);
  });
}
window.indexProductCards = indexProductCards;

// Watch for new cards injected by JS (e.g. after fetch)
const _cardObserver = new MutationObserver(() => {
  indexProductCards();
  observeElements();
});
document.addEventListener('DOMContentLoaded', () => {
  const grid = document.getElementById('product-list');
  if (grid) _cardObserver.observe(grid, { childList: true });
  indexProductCards();
});

/* ── 5. Cart icon pulse when item added ── */
window._pulseCart = function () {
  const icon = document.querySelector('.cart-icon');
  if (!icon) return;
  icon.classList.remove('pulse');
  // Force reflow
  void icon.offsetWidth;
  icon.classList.add('pulse');
  setTimeout(() => icon.classList.remove('pulse'), 600);
};

/* ── 6. Active category pill ── */
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const cat = (params.get('category') || '').toLowerCase();
  document.querySelectorAll('.category-list li a').forEach(link => {
    const href = link.getAttribute('href') || '';
    const match = href.toLowerCase().includes(`category=${cat}`);
    if (cat && match) link.classList.add('active');
  });
});

/* ── 7. Floating mobile cart button ── */
document.addEventListener('DOMContentLoaded', () => {
  // Only inject if not already there
  if (!document.getElementById('floating-cart')) {
    const fab = document.createElement('button');
    fab.id = 'floating-cart';
    fab.setAttribute('aria-label', 'Open cart');
    fab.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
      </svg>
      <span id="floating-cart-badge" style="display:none;">0</span>
    `;
    fab.onclick = () => window.location.href = 'cart.html';
    document.body.appendChild(fab);
  }

  // sync badge
  function syncFloatingCart() {
    try {
      const cart = JSON.parse(localStorage.getItem('seapedia_cart')) || [];
      const count = cart.reduce((a, i) => a + (i.qty || 1), 0);
      const badge = document.getElementById('floating-cart-badge');
      if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
      }
    } catch (e) {}
  }
  syncFloatingCart();
  window._syncFloatingCart = syncFloatingCart;
  window.addEventListener('storage', syncFloatingCart);
});

/* ── 8. Smooth number counter for .stat-value elements ── */
function animateCounter(el) {
  const target = parseFloat(el.dataset.target || el.textContent.replace(/[^0-9.]/g, ''));
  if (isNaN(target)) return;
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const duration = 900;
  const start = performance.now();
  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const value = Math.round(eased * target);
    el.textContent = prefix + value.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

const _counterObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      _counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.stat-value[data-target]').forEach(el => _counterObserver.observe(el));
});

/* ── 9. Upgraded showToast (override, keeps same signature) ── */
window.showToast = function (message, isError = false) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  const icon = isError
    ? `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
    : `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>`;
  toast.style.cssText = isError
    ? 'background:#d32f2f;color:white;'
    : 'background:var(--primary-color);color:white;';
  toast.innerHTML = icon + `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'seap-toast-out 0.3s ease forwards';
    setTimeout(() => toast.remove(), 320);
  }, 3000);
};
