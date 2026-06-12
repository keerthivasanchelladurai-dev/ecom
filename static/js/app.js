/* ══════════════════════════════════════════════════════════════
   ShopVerse — Client-Side JavaScript
   ══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    initFlashMessages();
    initMobileMenu();
    initQuantitySelectors();
    initSearchDebounce();
    initSortSelect();
    initPaymentOptions();
});

/* ── Toast Notification System ─────────────────────────────── */
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
        <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/* ── Flash Messages Auto-dismiss ───────────────────────────── */
function initFlashMessages() {
    document.querySelectorAll('.flash-message').forEach(msg => {
        // Click to dismiss
        msg.addEventListener('click', () => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(40px)';
            setTimeout(() => msg.remove(), 300);
        });

        // Auto-dismiss after 4s
        setTimeout(() => {
            if (msg.parentNode) {
                msg.style.opacity = '0';
                msg.style.transform = 'translateX(40px)';
                setTimeout(() => msg.remove(), 300);
            }
        }, 4000);
    });
}

/* ── Mobile Menu ───────────────────────────────────────────── */
function initMobileMenu() {
    const hamburger = document.getElementById('hamburger');
    const navDropdown = document.querySelector('.nav-dropdown');

    if (hamburger && navDropdown) {
        hamburger.addEventListener('click', () => {
            navDropdown.classList.toggle('active');
        });
    }
}

/* ── Quantity Selectors ────────────────────────────────────── */
function initQuantitySelectors() {
    document.querySelectorAll('.quantity-selector').forEach(selector => {
        const minusBtn = selector.querySelector('.qty-minus');
        const plusBtn = selector.querySelector('.qty-plus');
        const input = selector.querySelector('.qty-input');

        if (minusBtn && plusBtn && input) {
            minusBtn.addEventListener('click', () => {
                const val = parseInt(input.value) || 1;
                if (val > 1) input.value = val - 1;
            });

            plusBtn.addEventListener('click', () => {
                const val = parseInt(input.value) || 1;
                const max = parseInt(input.getAttribute('max')) || 99;
                if (val < max) input.value = val + 1;
            });
        }
    });
}

/* ── AJAX Add to Cart ──────────────────────────────────────── */
function addToCart(productId, quantity = 1) {
    const formData = new FormData();
    formData.append('quantity', quantity);

    fetch(`/cart/add/${productId}`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            showToast(data.message, 'success');
        }
    })
    .catch(() => {
        showToast('Please log in to add items to cart.', 'error');
    });
}

/* ── AJAX Update Cart ──────────────────────────────────────── */
function updateCartQuantity(itemId, quantity) {
    const formData = new FormData();
    formData.append('quantity', quantity);

    fetch(`/cart/update/${itemId}`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            // Reload to update totals
            location.reload();
        }
    });
}

/* ── AJAX Remove from Cart ─────────────────────────────────── */
function removeFromCart(itemId) {
    fetch(`/cart/remove/${itemId}`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            const row = document.getElementById(`cart-item-${itemId}`);
            if (row) {
                row.style.opacity = '0';
                row.style.transform = 'translateX(-20px)';
                row.style.transition = 'all 0.3s ease';
                setTimeout(() => {
                    row.remove();
                    location.reload();
                }, 300);
            }
        }
    });
}

/* ── AJAX Toggle Wishlist ──────────────────────────────────── */
function toggleWishlist(productId, btn) {
    fetch(`/wishlist/toggle/${productId}`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (btn) {
                btn.classList.toggle('wishlisted', data.added);
                btn.innerHTML = data.added ? '♥' : '♡';
            }
            showToast(data.message, 'success');
        }
    })
    .catch(() => {
        showToast('Please log in to use wishlist.', 'error');
    });
}

/* ── Update Cart Badge ─────────────────────────────────────── */
function updateCartBadge(count) {
    const badge = document.getElementById('cart-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
        // Animate
        badge.style.transform = 'scale(1.3)';
        setTimeout(() => badge.style.transform = 'scale(1)', 200);
    }
}

/* ── Search Debounce ───────────────────────────────────────── */
function initSearchDebounce() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    let timeout;
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/products?q=${encodeURIComponent(query)}`;
            }
        }
    });
}

/* ── Sort Select ───────────────────────────────────────────── */
function initSortSelect() {
    const sortSelect = document.getElementById('sort-select');
    if (!sortSelect) return;

    sortSelect.addEventListener('change', () => {
        const url = new URL(window.location);
        url.searchParams.set('sort', sortSelect.value);
        url.searchParams.delete('page');
        window.location.href = url.toString();
    });
}

/* ── Payment Options ───────────────────────────────────────── */
function initPaymentOptions() {
    document.querySelectorAll('.payment-option').forEach(option => {
        option.addEventListener('click', () => {
            document.querySelectorAll('.payment-option').forEach(o => o.classList.remove('selected'));
            option.classList.add('selected');
            const radio = option.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });
}

/* ── Print Invoice ─────────────────────────────────────────── */
function printInvoice() {
    window.print();
}

/* ── Confirm Delete ────────────────────────────────────────── */
function confirmDelete(form, name) {
    if (confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
        form.submit();
    }
}
