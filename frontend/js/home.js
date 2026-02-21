// =====================================================
// HOME PAGE - AUTHENTICATION STATE MANAGEMENT
// =====================================================

// Update navigation based on authentication state
async function updateNavigation() {
  const navButtons = document.getElementById('navButtons');

  if (isLoggedIn()) {
    const userData = getUserData();
    const firstName = userData.firstName || 'User';

    // Get counts for badges
    const alerts = await getAlerts();
    const alertsCount = alerts.length;
    const wishlist = await getWishlist();
    const wishlistCount = wishlist.length;

    // Logged in navigation
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
  } else {
    // Logged out navigation
    navButtons.innerHTML = `
      <a href="login.html"><button class="btn">Login</button></a>
      <a href="signup.html"><button class="btn primary">Sign Up</button></a>
    `;
  }
}

// =====================================================
// SEARCH FUNCTIONALITY
// =====================================================

function handleSearch() {
  const searchInput = document.getElementById('searchInput');
  const query = searchInput.value.trim();

  if (!query) {
    showNotification('Please enter a product name', 'warning');
    return;
  }

  // Redirect to results page with query parameter
  window.location.href = `results.html?q=${encodeURIComponent(query)}`;
}

// Allow Enter key to trigger search
document.addEventListener('DOMContentLoaded', async function () {
  const searchInput = document.getElementById('searchInput');

  if (searchInput) {
    searchInput.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') {
        handleSearch();
      }
    });
  }

  // Update navigation on page load
  await updateNavigation();
});
