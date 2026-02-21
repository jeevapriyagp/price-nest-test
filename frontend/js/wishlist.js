// =====================================================
// WISHLIST PAGE - INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', async function () {
  // Check authentication
  if (!isLoggedIn()) {
    window.location.href = 'login.html';
    return;
  }

  // Update navigation
  await updateNavigation();

  // Load wishlist
  loadWishlistItems();
});

// =====================================================
// NAVIGATION UPDATE
// =====================================================

async function updateNavigation() {
  const navButtons = document.getElementById('navButtons');
  const userData = getUserData();
  const firstName = userData.firstName || 'User';
  const alerts = await getAlerts();
  const alertsCount = alerts.length;
  const wishlist = await getWishlist();
  const wishlistCount = wishlist.length;

  navButtons.innerHTML = `
    <button class="nav-icon-btn" onclick="window.location.href='alerts.html'" title="Alerts">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
      </svg>
      ${alertsCount > 0 ? `<span class="badge">${alertsCount}</span>` : ''}
    </button>
    
    <button class="nav-icon-btn" onclick="window.location.href='wishlist.html'" title="Wishlist">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
      </svg>
      ${wishlistCount > 0 ? `<span class="badge">${wishlistCount}</span>` : ''}
    </button>
    
    <button class="btn primary" onclick="window.location.href='profile.html'">
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
      </svg>
      ${firstName}
    </button>
  `;
}

// =====================================================
// LOAD AND DISPLAY WISHLIST
// =====================================================

async function loadWishlistItems() {
  const container = document.getElementById('wishlistContainer');
  if (!container) return;

  container.innerHTML = '<div class="spinner"></div>';
  // Use syncWishlist (not getWishlist) to always get full product objects
  // getWishlist() returns ID-only stubs when cache is warm, which is enough
  // for badge counts but not for rendering cards.
  const wishlist = await syncWishlist();

  if (wishlist.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
          </svg>
        </div>
        <div class="empty-state-title">Your wishlist is empty</div>
        <div class="empty-state-text">
          Start adding products to your wishlist to track their prices
        </div>
        <button class="btn primary" onclick="window.location.href='index.html'">
          Start Shopping
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="wishlist-grid">
      ${wishlist.map(item => createWishlistCard(item)).join('')}
    </div>
  `;
}

function createWishlistCard(item) {
  return `
    <div class="wishlist-item">
      <img src="${item.image || 'https://via.placeholder.com/300x200?text=No+Image'}" alt="${item.title}" class="wishlist-item-image" />
      
      <div class="wishlist-item-store">${item.source}</div>
      <div class="wishlist-item-name">${item.title}</div>
      
      <div class="wishlist-item-price">${formatCurrency(item.price)}</div>
      <div class="wishlist-item-added">Added ${formatDate(item.created_at)}</div>
      
      <div class="wishlist-item-actions">
        <a href="${item.link || '#'}" target="_blank" class="btn primary">View Deal</a>
        <button class="btn btn-remove" onclick="handleRemoveItem('${item.id}')">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          Remove
        </button>
      </div>
    </div>
  `;
}

// =====================================================
// WISHLIST ACTIONS
// =====================================================

async function handleRemoveItem(productId) {
  if (confirm('Remove this item from your wishlist?')) {
    await removeFromWishlist(productId);
    await loadWishlistItems();
    await updateNavigation();
  }
}
