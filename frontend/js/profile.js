// =====================================================
// PROFILE PAGE - INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', async function () {
  // Check authentication
  if (!isLoggedIn()) {
    window.location.href = 'login.html';
    return;
  }

  // Update navigation
  await updateNavigation();

  // Load profile data
  await loadProfile();

  // Initialize form
  initializeForm();
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
// LOAD PROFILE DATA
// =====================================================

async function loadProfile() {
  const userData = getUserData();

  if (!userData) {
    window.location.href = 'login.html';
    return;
  }

  // Update profile header
  document.getElementById('profileName').textContent =
    `${userData.firstName || ''} ${userData.lastName || ''}`.trim() || 'User';
  document.getElementById('profileEmail').textContent = userData.email || '';

  // Update display values
  document.getElementById('dispFirstName').textContent = userData.firstName || '-';
  document.getElementById('dispLastName').textContent = userData.lastName || '-';
  document.getElementById('dispEmail').textContent = userData.email || '-';

  // Populate form inputs
  document.getElementById('firstName').value = userData.firstName || '';
  document.getElementById('lastName').value = userData.lastName || '';
  document.getElementById('email').value = userData.email || '';

  // Update stats (await async functions)
  const alerts = await getAlerts();
  document.getElementById('alertsCount').textContent = alerts.length;
  const wishlist = await getWishlist();
  document.getElementById('wishlistCount').textContent = wishlist.length;

  // Calculate member since
  if (userData.created_at) {
    const memberDate = new Date(userData.created_at);
    const monthYear = memberDate.toLocaleDateString('en-IN', {
      month: 'short',
      year: 'numeric'
    });
    document.getElementById('memberSince').textContent = monthYear;
  }
}

// =====================================================
// EDIT MODE TOGGLE
// =====================================================

function toggleEditMode(isEditing) {
  const profileView = document.getElementById('profileView');
  const profileForm = document.getElementById('profileForm');
  const editBtn = document.getElementById('editDetailsBtn');

  if (isEditing) {
    profileView.classList.add('hidden');
    profileForm.classList.remove('hidden');
    editBtn.classList.add('hidden');
  } else {
    profileView.classList.remove('hidden');
    profileForm.classList.add('hidden');
    editBtn.classList.remove('hidden');
    // Reset form to latest data
    loadProfile();
  }
}

// =====================================================
// FORM HANDLING
// =====================================================

function initializeForm() {
  const form = document.getElementById('profileForm');

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const userData = getUserData();
    const firstName = document.getElementById('firstName').value.trim();
    const lastName = document.getElementById('lastName').value.trim();
    const email = userData.email;

    try {
      // Persist to backend
      const result = await apiPut('/auth/profile', {
        email: email,
        first_name: firstName,
        last_name: lastName
      });

      // Update session data
      userData.firstName = result.user.first_name;
      userData.lastName = result.user.last_name;
      sessionStorage.setItem('userData', JSON.stringify(userData));

      showNotification('Profile updated successfully!', 'success');

      // Exit edit mode first
      toggleEditMode(false);

      // Reload UI
      await loadProfile();
      await updateNavigation();
    } catch (err) {
      showNotification('Failed to update profile: ' + err.message, 'error');
    }
  });
}

// =====================================================
// LOGOUT
// =====================================================

function handleLogout() {
  if (confirm('Are you sure you want to logout?')) {
    logout();
  }
}
