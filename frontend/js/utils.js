// =====================================================
// API CONFIGURATION & HELPERS
// =====================================================

const API_BASE_URL = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000/api'
    : '/api';

/**
 * Helper for GET requests to the backend
 * @param {string} endpoint - API endpoint (e.g., '/compare')
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} - JSON response
 */
async function apiGet(endpoint, params = {}) {
    const url = new URL(`${API_BASE_URL}${endpoint}`);
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

    const response = await fetch(url);
    if (!response.ok) {
        let errMsg = `API Error: ${response.statusText}`;
        try {
            const err = await response.json();
            errMsg = err.detail || errMsg;
        } catch (_) { }
        throw new Error(errMsg);
    }
    return await response.json();
}

/**
 * Helper for POST requests to the backend
 * @param {string} endpoint - API endpoint
 * @param {Object} body - Request body
 * @returns {Promise<Object>} - JSON response
 */
async function apiPost(endpoint, body) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        let errMsg = `API Error: ${response.statusText}`;
        try {
            const err = await response.json();
            errMsg = err.detail || errMsg;
        } catch (_) { }
        throw new Error(errMsg);
    }

    return await response.json();
}

/**
 * Helper for PUT requests to the backend
 * @param {string} endpoint - API endpoint
 * @param {Object} body - Request body
 * @returns {Promise<Object>} - JSON response
 */
async function apiPut(endpoint, body) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        let errMsg = `API Error: ${response.statusText}`;
        try {
            const err = await response.json();
            errMsg = err.detail || errMsg;
        } catch (_) { }
        throw new Error(errMsg);
    }

    return await response.json();
}

// =====================================================
// AUTHENTICATION UTILITIES
// =====================================================

/**
 * Check if user is currently logged in
 * @returns {boolean} - True if user is logged in
 */
function isLoggedIn() {
    const userData = localStorage.getItem('userData') || sessionStorage.getItem('userData');
    if (!userData) return false;

    try {
        const user = JSON.parse(userData);
        return user && user.loggedIn === true;
    } catch (e) {
        return false;
    }
}

/**
 * Get current user data
 * @returns {Object|null} - User data object or null
 */
function getUserData() {
    const userData = localStorage.getItem('userData') || sessionStorage.getItem('userData');
    if (!userData) return null;

    try {
        return JSON.parse(userData);
    } catch (e) {
        return null;
    }
}

/**
 * Logout user and clear session
 */
function logout() {
    sessionStorage.removeItem('userData');
    window.location.href = 'index.html';
}

/**
 * Require authentication - redirect to login if not logged in
 * @param {string} returnUrl - URL to return to after login
 */
function requireAuth(returnUrl = null) {
    if (!isLoggedIn()) {
        const redirect = returnUrl || window.location.href;
        window.location.href = `login.html?redirect=${encodeURIComponent(redirect)}`;
        return false;
    }
    return true;
}

// =====================================================
// NOTIFICATION SYSTEM
// =====================================================

/**
 * Show notification toast
 * @param {string} message - Message to display
 * @param {string} type - Type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in ms (default 4000)
 */
function showNotification(message, type = 'info', duration = 4000) {
    // Remove existing notification if any
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

    const iconSvgs = {
        success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
        warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        info: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
    };

    notification.innerHTML = `
    <span class="notification-icon">${iconSvgs[type] || iconSvgs.info}</span>
    <span class="notification-message">${message}</span>
  `;

    // Add styles
    const styles = {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '16px 24px',
        borderRadius: '12px',
        color: 'white',
        fontWeight: '500',
        fontSize: '14px',
        zIndex: '10000',
        animation: 'slideInRight 0.3s ease-out',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
        maxWidth: '400px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
    };

    Object.assign(notification.style, styles);

    // Set background color based on type
    const backgrounds = {
        success: 'linear-gradient(135deg, #10b981, #059669)',
        error: 'linear-gradient(135deg, #ef4444, #dc2626)',
        warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
        info: 'linear-gradient(135deg, #667eea, #764ba2)'
    };

    notification.style.background = backgrounds[type] || backgrounds.info;

    // Add animation keyframes if not already added
    if (!document.querySelector('#notification-animations')) {
        const styleSheet = document.createElement('style');
        styleSheet.id = 'notification-animations';
        styleSheet.textContent = `
      @keyframes slideInRight {
        from {
          opacity: 0;
          transform: translateX(100px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }
      @keyframes slideOutRight {
        from {
          opacity: 1;
          transform: translateX(0);
        }
        to {
          opacity: 0;
          transform: translateX(100px);
        }
      }
    `;
        document.head.appendChild(styleSheet);
    }

    // Add to page
    document.body.appendChild(notification);

    // Remove after duration
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}


// =====================================================
// ALERT HELPERS (BACKEND INTEGRATED)
// =====================================================

/**
 * Get alerts from backend
 * @returns {Promise<Array>} - Array of alert objects
 */
async function getAlerts() {
    if (!isLoggedIn()) return [];

    try {
        const userData = getUserData();
        const alerts = await apiGet('/alerts', { email: userData.email });

        // Transform backend format to frontend format
        return alerts.map(a => ({
            id: a.id,
            product: a.query,
            targetPrice: a.target_price,
            email: a.email,
            active: a.is_active,
            createdAt: a.created_at || new Date().toISOString()
        }));
    } catch (e) {
        console.error('Failed to fetch alerts:', e);
        return [];
    }
}

/**
 * Add new alert (Backend)
 * @param {Object} alert - Alert object { product, targetPrice, email }
 */
async function addAlert(alert) {
    if (!isLoggedIn()) throw new Error("Must be logged in");

    const payload = {
        email: alert.email,
        query: alert.product,
        target_price: alert.targetPrice,
        notify_method: "email"
    };

    const response = await apiPost('/alerts', payload);
    return response.alert;
}

/**
 * Delete alert by ID (Backend)
 * @param {string|number} alertId - Alert ID to delete
 */
async function deleteAlert(alertId) {
    if (!isLoggedIn()) return false;

    try {
        const response = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
            method: 'DELETE'
        });
        return response.ok;
    } catch (e) {
        console.error('Failed to delete alert:', e);
        return false;
    }
}

/**
 * Update alert status (Backend)
 * @param {string|number} alertId 
 * @param {boolean} isActive 
 */
async function updateAlertStatus(alertId, isActive) {
    if (!isLoggedIn()) return false;

    try {
        const res = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });

        if (!res.ok) throw new Error('Failed to update status');
        return true;
    } catch (e) {
        console.error('Failed to update alert status:', e);
        return false;
    }
}

// =====================================================
// WISHLIST STORAGE (DATABASE BACKED)
// =====================================================

// Local cache of wishlist product IDs to avoid frequent API calls for button states
let wishlistCache = [];
let wishlistSynced = false;

/**
 * Sync wishlist from backend (always fetches fresh data)
 * @returns {Promise<Array>} - Array of product objects
 */
async function syncWishlist() {
    if (!isLoggedIn()) return [];

    try {
        const userData = getUserData();
        const data = await apiGet('/wishlist', { email: userData.email });
        const wishlist = data.wishlist || [];
        wishlistCache = wishlist.map(p => p.id);
        wishlistSynced = true;
        return wishlist;
    } catch (e) {
        console.error('Failed to sync wishlist:', e);
        return [];
    }
}

/**
 * Get wishlist — uses cache if already synced, otherwise fetches from backend.
 * @returns {Promise<Array>} - Array of product objects
 */
async function getWishlist() {
    // If we've already synced this session, return a lightweight re-fetch
    // only when the component actually needs the full list (wishlist page).
    // For nav badge counts this avoids a redundant API round-trip.
    if (wishlistSynced) {
        // Return cached product stubs (id only) — enough for badge counts
        return wishlistCache.map(id => ({ id }));
    }
    return await syncWishlist();
}

/**
 * Add product to wishlist (Backend)
 * @param {Object} product - Product object
 */
async function addToWishlist(product) {
    if (!isLoggedIn()) return false;

    // Normalize to int to keep wishlistCache consistent
    const pid = typeof product.id === 'string' ? parseInt(product.id) : product.id;

    try {
        const userData = getUserData();
        await apiPost('/wishlist', {
            email: userData.email,
            product_id: pid
        });

        if (!wishlistCache.includes(pid)) {
            wishlistCache.push(pid);
        }

        showNotification('Added to wishlist!', 'success');
        return true;
    } catch (e) {
        console.error('Failed to add to wishlist:', e);
        showNotification('Failed to add to wishlist', 'error');
        return false;
    }
}

/**
 * Remove product from wishlist (Backend)
 * @param {number|string} productId - Product ID to remove
 */
async function removeFromWishlist(productId) {
    if (!isLoggedIn()) return false;

    const pid = typeof productId === 'string' ? parseInt(productId) : productId;

    try {
        const userData = getUserData();
        await fetch(`${API_BASE_URL}/wishlist`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: userData.email,
                product_id: pid
            })
        });

        wishlistCache = wishlistCache.filter(id => id !== pid);
        // Mark as needing re-sync so full product list is refreshed next time
        wishlistSynced = false;
        showNotification('Removed from wishlist', 'success');
        return true;
    } catch (e) {
        console.error('Failed to remove from wishlist:', e);
        showNotification('Failed to remove from wishlist', 'error');
        return false;
    }
}

/**
 * Check if product is in wishlist cache
 * @param {number|string} productId - Product ID to check
 * @returns {boolean}
 */
function isInWishlist(productId) {
    const pid = typeof productId === 'string' ? parseInt(productId) : productId;
    return wishlistCache.includes(pid);
}

// =====================================================
// URL UTILITIES
// =====================================================

/**
 * Get URL parameter value
 * @param {string} param - Parameter name
 * @returns {string|null} - Parameter value or null
 */
function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code (default: INR)
 * @returns {string} - Formatted currency string
 */
function formatCurrency(amount, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
}

/**
 * Format date
 * @param {string|Date} date - Date to format
 * @returns {string} - Formatted date string
 */
function formatDate(date) {
    const d = new Date(date);
    return d.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param {string|Date} date - Date to format
 * @returns {string} - Relative time string
 */
function formatRelativeTime(date) {
    const d = new Date(date);
    const now = new Date();
    const diff = now - d;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
}
