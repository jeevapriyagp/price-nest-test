// =====================================================
// INITIALIZATION
// =====================================================
document.addEventListener('DOMContentLoaded', async function () {

  if (!requireAuth()) return;

  await updateNavigation();
  await loadAlerts();
});


// Note: All API functions (getAlerts, addAlert, deleteAlert, updateAlertStatus) 
// are now managed centrally in js/utils.js


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
// LOAD ALERTS
// =====================================================

async function loadAlerts() {
  const container = document.getElementById('alertsContainer');
  container.innerHTML = '<div class="spinner"></div>';

  const alerts = await getAlerts();

  if (!alerts || alerts.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔔</div>
        <h3 class="empty-state-title">No alerts yet</h3>
        <p class="empty-state-text">You haven't set any price alerts. Search for products to start tracking prices!</p>
        <button class="btn primary" onclick="window.location.href='index.html'">
          Search Products
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="table-container">
      <table class="alerts-table">
        <thead>
          <tr>
            <th>Product Name</th>
            <th>Target Price</th>
            <th>Status</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${alerts.map(alert => createAlertRow(alert)).join('')}
        </tbody>
      </table>
    </div>
  `;
}


// =====================================================
// ROW
// =====================================================

function createAlertRow(alert) {
  const statusClass = alert.active ? 'active' : 'inactive';
  const statusLabel = alert.active ? 'Active' : 'Inactive';

  return `
    <tr>
      <td class="product-name-cell">
        <span class="product-title">${alert.product || 'Unknown Product'}</span>
      </td>
      <td>
        <span class="price-value">₹${alert.targetPrice}</span>
      </td>
      <td>
        <span class="alert-status ${statusClass}">
          <span class="alert-status-dot"></span>
          ${statusLabel}
        </span>
      </td>
      <td class="text-right">
        <div class="alert-actions">
          <button onclick="toggleAlertStatus(${alert.id}, ${alert.active})" title="${alert.active ? 'Pause' : 'Activate'}">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              ${alert.active ? '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>' : '<polygon points="5 3 19 12 5 21 5 3"></polygon>'}
            </svg>
          </button>
          <button class="delete" onclick="handleDeleteAlert(${alert.id})" title="Delete">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </td>
    </tr>
  `;
}


// =====================================================
// ACTIONS
// =====================================================

async function toggleAlertStatus(id, currentStatus) {
  const success = await updateAlertStatus(id, !currentStatus);
  if (success) {
    await loadAlerts();
    await updateNavigation();
  }
}


async function handleDeleteAlert(id) {
  if (!confirm("Delete this alert?")) return;

  const success = await deleteAlert(id);
  if (success) {
    await loadAlerts();
    await updateNavigation();
  }
}
