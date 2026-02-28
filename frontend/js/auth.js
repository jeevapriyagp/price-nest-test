// =====================================================
// LOGIN FORM HANDLER
// =====================================================
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const rememberEl = document.getElementById('remember');
    const remember = rememberEl ? rememberEl.checked : false;

    // Form validation
    if (!email || !password) {
      showNotification('Please fill in all fields', 'error');
      return;
    }

    // Email validation
    if (!isValidEmail(email)) {
      showNotification('Please enter a valid email address', 'error');
      return;
    }

    // Actual login
    fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    })
      .then(async response => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Login failed');
        }
        return data;
      })
      .then(data => {
        showNotification('Login successful! Redirecting...', 'success');

        const userData = {
          firstName: data.user.first_name,
          lastName: data.user.last_name,
          email: data.user.email,
          loggedIn: true,
          created_at: data.user.created_at  // actual account creation date from DB
        };

        sessionStorage.setItem('userData', JSON.stringify(userData));

        setTimeout(() => {
          window.location.href = 'index.html';
        }, 1500);
      })
      .catch(error => {
        showNotification(error.message, 'error');
      });
  });
}

// =====================================================
// SIGNUP FORM HANDLER
// =====================================================
const signupForm = document.getElementById('signupForm');
if (signupForm) {
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirmPassword');
  const strengthFill = document.getElementById('strengthFill');
  const strengthText = document.getElementById('strengthText');

  // Password strength checker
  if (passwordInput) {
    passwordInput.addEventListener('input', function () {
      const password = this.value;
      const strength = calculatePasswordStrength(password);

      // Update strength bar
      strengthFill.style.width = strength.percentage + '%';
      strengthFill.style.background = strength.color;
      strengthText.textContent = strength.text;
      strengthText.style.color = strength.color;
    });
  }

  // Form submission
  signupForm.addEventListener('submit', function (e) {
    e.preventDefault();

    const firstName = document.getElementById('firstName').value;
    const lastName = document.getElementById('lastName').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const terms = document.getElementById('terms').checked;

    // Validation
    if (!firstName || !lastName || !email || !password || !confirmPassword) {
      showNotification('Please fill in all fields', 'error');
      return;
    }

    if (!isValidEmail(email)) {
      showNotification('Please enter a valid email address', 'error');
      return;
    }

    if (password.length < 8) {
      showNotification('Password must be at least 8 characters long', 'error');
      return;
    }

    if (password !== confirmPassword) {
      showNotification('Passwords do not match', 'error');
      return;
    }

    if (!terms) {
      showNotification('Please accept the terms and privacy policy', 'error');
      return;
    }

    // Actual signup
    fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        email: email,
        password: password
      }),
    })
      .then(async response => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Signup failed');
        }
        return data;
      })
      .then(data => {
        showNotification('Account created successfully! Redirecting...', 'success');

        const userData = {
          firstName: data.user.first_name,
          lastName: data.user.last_name,
          email: data.user.email,
          loggedIn: true,
          created_at: data.user.created_at
        };

        sessionStorage.setItem('userData', JSON.stringify(userData));

        setTimeout(() => {
          window.location.href = 'index.html';
        }, 1500);
      })
      .catch(error => {
        showNotification(error.message, 'error');
      });
  });
}

// =====================================================
// HELPER FUNCTIONS
// =====================================================

// Email validation
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Password strength calculator
function calculatePasswordStrength(password) {
  let strength = 0;

  if (password.length === 0) {
    return {
      percentage: 0,
      text: 'Enter a password',
      color: '#6b7280'
    };
  }

  // Length check
  if (password.length >= 8) strength += 25;
  if (password.length >= 12) strength += 15;

  // Contains lowercase
  if (/[a-z]/.test(password)) strength += 15;

  // Contains uppercase
  if (/[A-Z]/.test(password)) strength += 15;

  // Contains numbers
  if (/[0-9]/.test(password)) strength += 15;

  // Contains special characters
  if (/[^a-zA-Z0-9]/.test(password)) strength += 15;

  // Determine strength level
  if (strength < 40) {
    return {
      percentage: strength,
      text: 'Weak password',
      color: '#ef4444'
    };
  } else if (strength < 70) {
    return {
      percentage: strength,
      text: 'Medium password',
      color: '#f59e0b'
    };
  } else {
    return {
      percentage: strength,
      text: 'Strong password',
      color: '#10b981'
    };
  }
}

