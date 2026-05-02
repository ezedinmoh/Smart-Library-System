// ===== Show/Hide Forms =====
function showForm(formType) {
    // Hide all forms
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('signupForm').classList.add('hidden');
    document.getElementById('forgotForm').classList.add('hidden');
    document.getElementById('successMessage').classList.add('hidden');
    
    // Show selected form
    if (formType === 'login') {
        document.getElementById('loginForm').classList.remove('hidden');
        document.title = 'Sign In - Smart Library Management System';
    } else if (formType === 'signup') {
        document.getElementById('signupForm').classList.remove('hidden');
        document.title = 'Sign Up - Smart Library Management System';
    } else if (formType === 'forgot') {
        document.getElementById('forgotForm').classList.remove('hidden');
        document.title = 'Reset Password - Smart Library Management System';
    } else if (formType === 'success') {
        document.getElementById('successMessage').classList.remove('hidden');
        document.title = 'Check Your Email - Smart Library Management System';
    }
}

// Check URL hash on page load
window.addEventListener('load', () => {
    const hash = window.location.hash;
    if (hash === '#signup') {
        showForm('signup');
    } else if (hash === '#forgot') {
        showForm('forgot');
    } else {
        showForm('login');
    }
});

// ===== Toggle Password Visibility =====
function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    const type = input.getAttribute('type');
    
    if (type === 'password') {
        input.setAttribute('type', 'text');
        button.classList.add('active');
    } else {
        input.setAttribute('type', 'password');
        button.classList.remove('active');
    }
}

// ===== Password Strength Checker =====
function checkPasswordStrength(password) {
    const strengthBars = document.querySelector('.password-strength');
    const strengthText = document.querySelector('.strength-text');
    const requirements = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    // Update requirement indicators
    Object.keys(requirements).forEach(req => {
        const element = document.querySelector(`[data-requirement="${req}"]`);
        if (element) {
            if (requirements[req]) {
                element.classList.add('met');
            } else {
                element.classList.remove('met');
            }
        }
    });
    
    // Calculate strength
    const metCount = Object.values(requirements).filter(Boolean).length;
    
    // Remove all strength classes
    strengthBars.classList.remove('strength-weak', 'strength-medium', 'strength-strong', 'strength-very-strong');
    
    if (password.length === 0) {
        strengthText.textContent = 'Password Strength';
        strengthText.style.color = 'var(--text-muted)';
    } else if (metCount <= 1) {
        strengthBars.classList.add('strength-weak');
        strengthText.textContent = 'Weak';
        strengthText.style.color = 'var(--error)';
    } else if (metCount === 2) {
        strengthBars.classList.add('strength-medium');
        strengthText.textContent = 'Medium';
        strengthText.style.color = 'var(--warning)';
    } else if (metCount === 3) {
        strengthBars.classList.add('strength-strong');
        strengthText.textContent = 'Strong';
        strengthText.style.color = '#22c55e';
    } else {
        strengthBars.classList.add('strength-very-strong');
        strengthText.textContent = 'Very Strong';
        strengthText.style.color = 'var(--primary)';
    }
    
    return metCount;
}

// ===== Password Match Checker =====
function checkPasswordMatch() {
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('confirmPassword');
    const errorMessage = confirmPassword.closest('.form-group').querySelector('.error-message');
    
    if (confirmPassword.value.length > 0) {
        if (password === confirmPassword.value) {
            confirmPassword.classList.add('valid');
            confirmPassword.classList.remove('invalid');
            errorMessage.textContent = '';
        } else {
            confirmPassword.classList.add('invalid');
            confirmPassword.classList.remove('valid');
            errorMessage.textContent = 'Passwords do not match';
        }
    } else {
        confirmPassword.classList.remove('valid', 'invalid');
        errorMessage.textContent = '';
    }
}

// ===== Email Validation =====
function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// ===== Real-time Input Validation =====
document.querySelectorAll('input[type="email"]').forEach(input => {
    input.addEventListener('blur', function() {
        const errorMessage = this.closest('.form-group').querySelector('.error-message');
        
        if (this.value.length > 0) {
            if (validateEmail(this.value)) {
                this.classList.add('valid');
                this.classList.remove('invalid');
                errorMessage.textContent = '';
            } else {
                this.classList.add('invalid');
                this.classList.remove('valid');
                errorMessage.textContent = 'Please enter a valid email address';
            }
        } else {
            this.classList.remove('valid', 'invalid');
            errorMessage.textContent = '';
        }
    });
});

// ===== Name Validation =====
document.querySelectorAll('#firstName, #lastName').forEach(input => {
    input.addEventListener('blur', function() {
        const errorMessage = this.closest('.form-group').querySelector('.error-message');
        
        if (this.value.length > 0) {
            if (this.value.length >= 2) {
                this.classList.add('valid');
                this.classList.remove('invalid');
                errorMessage.textContent = '';
            } else {
                this.classList.add('invalid');
                this.classList.remove('valid');
                errorMessage.textContent = 'Name must be at least 2 characters';
            }
        } else {
            this.classList.remove('valid', 'invalid');
            errorMessage.textContent = '';
        }
    });
});

// ===== Login Form Handler =====
function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail');
    const password = document.getElementById('loginPassword');
    let isValid = true;
    
    // Validate email
    if (!validateEmail(email.value)) {
        email.classList.add('invalid');
        email.closest('.form-group').querySelector('.error-message').textContent = 'Please enter a valid email address';
        isValid = false;
    } else {
        email.classList.add('valid');
        email.classList.remove('invalid');
    }
    
    // Validate password
    if (password.value.length < 6) {
        password.classList.add('invalid');
        password.closest('.form-group').querySelector('.error-message').textContent = 'Password must be at least 6 characters';
        isValid = false;
    } else {
        password.classList.add('valid');
        password.classList.remove('invalid');
    }
    
    if (isValid) {
        // Simulate login - in a real app, this would send data to a server
        const btn = e.target.querySelector('button[type="submit"]');
        btn.innerHTML = '<span class="spinner"></span> Signing in...';
        btn.disabled = true;
        
        setTimeout(() => {
            alert('Login successful!\n\nIn a real application, you would be redirected to your dashboard based on your role.');
            btn.innerHTML = 'Sign In <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>';
            btn.disabled = false;
        }, 1500);
    }
    
    return false;
}

// ===== Signup Form Handler =====
function handleSignup(e) {
    e.preventDefault();
    
    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const email = document.getElementById('signupEmail');
    const password = document.getElementById('signupPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    const agreeTerms = document.getElementById('agreeTerms');
    const role = document.querySelector('input[name="role"]:checked');
    
    let isValid = true;
    
    // Validate first name
    if (firstName.value.length < 2) {
        firstName.classList.add('invalid');
        firstName.closest('.form-group').querySelector('.error-message').textContent = 'First name is required';
        isValid = false;
    } else {
        firstName.classList.add('valid');
        firstName.classList.remove('invalid');
    }
    
    // Validate last name
    if (lastName.value.length < 2) {
        lastName.classList.add('invalid');
        lastName.closest('.form-group').querySelector('.error-message').textContent = 'Last name is required';
        isValid = false;
    } else {
        lastName.classList.add('valid');
        lastName.classList.remove('invalid');
    }
    
    // Validate email
    if (!validateEmail(email.value)) {
        email.classList.add('invalid');
        email.closest('.form-group').querySelector('.error-message').textContent = 'Please enter a valid email address';
        isValid = false;
    } else {
        email.classList.add('valid');
        email.classList.remove('invalid');
    }
    
    // Validate password strength
    const strengthScore = checkPasswordStrength(password.value);
    if (strengthScore < 3) {
        password.classList.add('invalid');
        password.closest('.form-group').querySelector('.error-message').textContent = 'Password is too weak';
        isValid = false;
    } else {
        password.classList.add('valid');
        password.classList.remove('invalid');
    }
    
    // Validate password match
    if (password.value !== confirmPassword.value) {
        confirmPassword.classList.add('invalid');
        confirmPassword.closest('.form-group').querySelector('.error-message').textContent = 'Passwords do not match';
        isValid = false;
    } else if (confirmPassword.value.length > 0) {
        confirmPassword.classList.add('valid');
        confirmPassword.classList.remove('invalid');
    }
    
    // Validate terms agreement
    if (!agreeTerms.checked) {
        alert('Please agree to the Terms of Service and Privacy Policy');
        isValid = false;
    }
    
    if (isValid) {
        // Simulate signup - in a real app, this would send data to a server
        const btn = e.target.querySelector('button[type="submit"]');
        btn.innerHTML = '<span class="spinner"></span> Creating account...';
        btn.disabled = true;
        
        setTimeout(() => {
            const roleText = role.value.charAt(0).toUpperCase() + role.value.slice(1);
            alert(`Account created successfully!\n\nName: ${firstName.value} ${lastName.value}\nEmail: ${email.value}\nRole: ${roleText}\n\nIn a real application, you would receive a verification email and be redirected to your ${roleText.toLowerCase()} dashboard.`);
            btn.innerHTML = 'Create Account <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>';
            btn.disabled = false;
            showForm('login');
        }, 1500);
    }
    
    return false;
}

// ===== Forgot Password Handler =====
function handleForgot(e) {
    e.preventDefault();
    
    const email = document.getElementById('forgotEmail');
    let isValid = true;
    
    // Validate email
    if (!validateEmail(email.value)) {
        email.classList.add('invalid');
        email.closest('.form-group').querySelector('.error-message').textContent = 'Please enter a valid email address';
        isValid = false;
    } else {
        email.classList.add('valid');
        email.classList.remove('invalid');
    }
    
    if (isValid) {
        // Simulate sending reset email
        const btn = e.target.querySelector('button[type="submit"]');
        btn.innerHTML = '<span class="spinner"></span> Sending...';
        btn.disabled = true;
        
        setTimeout(() => {
            btn.innerHTML = 'Send Reset Link <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>';
            btn.disabled = false;
            showForm('success');
        }, 1500);
    }
    
    return false;
}

// ===== Add Spinner Styles =====
const style = document.createElement('style');
style.textContent = `
    .spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 0.8s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
