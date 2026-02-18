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
  const wishlistCount = getWishlist().length;

  navButtons.innerHTML = `
    <button class="nav-icon-btn" onclick="window.location.href='alerts.html'">
      🔔
      ${alertsCount > 0 ? `<span class="badge">${alertsCount}</span>` : ''}
    </button>

    <button class="nav-icon-btn" onclick="window.location.href='wishlist.html'">
      ❤️
      ${wishlistCount > 0 ? `<span class="badge">${wishlistCount}</span>` : ''}
    </button>

    <button class="btn primary" onclick="window.location.href='profile.html'">
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
    container.innerHTML = `<p>No alerts yet</p>`;
    return;
  }

  container.innerHTML = `
    <div class="alerts-grid">
      ${alerts.map(alert => createAlertCard(alert)).join('')}
    </div>
  `;
}


// =====================================================
// CARD
// =====================================================

function createAlertCard(alert) {
  return `
    <div class="alert-card">
      <h3>${alert.product}</h3>
      <p>Target: ₹${alert.targetPrice}</p>
      <p>Status: ${alert.active ? 'Active' : 'Inactive'}</p>

      <button onclick="toggleAlertStatus(${alert.id}, ${alert.active})">
        ${alert.active ? 'Pause' : 'Activate'}
      </button>

      <button onclick="handleDeleteAlert(${alert.id})">
        Delete
      </button>
    </div>
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
