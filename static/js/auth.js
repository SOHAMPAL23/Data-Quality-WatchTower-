// Authentication Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Password visibility toggle
    const togglePasswords = document.querySelectorAll('.password-toggle');
    togglePasswords.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const passwordInput = this.previousElementSibling;
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
        });
    });

    // Password strength indicator
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        if (input.id.includes('password1') || input.id.includes('password')) {
            input.addEventListener('input', function() {
                const strengthMeter = this.parentNode.querySelector('.strength-meter');
                if (strengthMeter) {
                    const strength = calculatePasswordStrength(this.value);
                    updateStrengthMeter(strengthMeter, strength);
                }
            });
        }
    });

    // Form submission handling - FIXED VERSION
    const authForms = document.querySelectorAll('.auth-form');
    authForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Add loading state to submit button
            const submitBtn = this.querySelector('.btn-submit');
            if (submitBtn) {
                // Store the original HTML content
                submitBtn.setAttribute('data-original-html', submitBtn.innerHTML);
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitBtn.disabled = true;
                
                // Re-enable button after 3 seconds (should be enough for redirect)
                setTimeout(() => {
                    if (submitBtn && submitBtn.disabled) {
                        submitBtn.innerHTML = submitBtn.getAttribute('data-original-html') || 'Submit';
                        submitBtn.disabled = false;
                        submitBtn.removeAttribute('data-original-html');
                    }
                }, 3000);
            }
            
            // Allow form to submit normally - don't prevent default
            // The form will submit to the server as expected
        });
    });

    // Initialize particles
    initParticles();

    // Add fade-in animation to form elements
    const formElements = document.querySelectorAll('.form-group, .btn-submit, .btn-oauth, .auth-links');
    formElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(10px)';
        setTimeout(() => {
            element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 200 + (index * 100));
    });
});

// Calculate password strength
function calculatePasswordStrength(password) {
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    
    // Character variety checks
    if (/[a-z]/.test(password)) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    
    return Math.min(strength, 5); // Max strength is 5
}

// Update password strength meter
function updateStrengthMeter(meter, strength) {
    const percentage = (strength / 5) * 100;
    meter.style.width = percentage + '%';
    
    // Update color based on strength
    meter.className = 'strength-meter';
    if (percentage <= 33) {
        meter.classList.add('strength-weak');
    } else if (percentage <= 66) {
        meter.classList.add('strength-medium');
    } else {
        meter.classList.add('strength-strong');
    }
}

// Initialize background particles
function initParticles() {
    const container = document.querySelector('.particles-container');
    if (!container) return;
    
    // Create 30 particles
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        
        // Random size
        const size = Math.random() * 5 + 2;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        
        // Random position
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        
        // Random animation duration
        const duration = Math.random() * 20 + 10;
        particle.style.animationDuration = duration + 's';
        
        // Random delay
        const delay = Math.random() * 5;
        particle.style.animationDelay = delay + 's';
        
        container.appendChild(particle);
    }
}

// Google OAuth login
function loginWithGoogle() {
    // Show loading state
    const googleBtn = document.querySelector('.btn-oauth');
    if (googleBtn) {
        const originalText = googleBtn.innerHTML;
        googleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Redirecting...';
        googleBtn.disabled = true;
        
        // Re-enable button after 3 seconds
        setTimeout(() => {
            googleBtn.innerHTML = originalText;
            googleBtn.disabled = false;
        }, 3000);
    }
    
    // In a real implementation, this would redirect to Google OAuth
    // For demo purposes, we'll just show a message
    setTimeout(() => {
        alert('In a real implementation, this would redirect to Google OAuth');
    }, 1000);
}