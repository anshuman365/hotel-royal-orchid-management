// Main JavaScript for Hotel Royal Orchid

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initMobileMenu();
    initDatePickers();
    initImageLazyLoading();
    initSmoothScrolling();
    initFormValidations();
    initBookingSystem();
    initGallery();
});

// Mobile menu functionality
function initMobileMenu() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
            mobileMenu.classList.toggle('block');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('#mobile-menu') && !event.target.closest('#mobile-menu-button')) {
            if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                mobileMenu.classList.add('hidden');
                mobileMenu.classList.remove('block');
            }
        }
    });
}

// Date picker initialization
function initDatePickers() {
    // Check if Flatpickr is available
    if (typeof flatpickr !== 'undefined') {
        const dateInputs = document.querySelectorAll('.date-picker');
        
        dateInputs.forEach(input => {
            flatpickr(input, {
                minDate: 'today',
                dateFormat: 'Y-m-d',
                disableMobile: true
            });
        });
        
        // Range date picker for booking
        const checkInInput = document.getElementById('check-in');
        const checkOutInput = document.getElementById('check-out');
        
        if (checkInInput && checkOutInput) {
            const checkInPicker = flatpickr(checkInInput, {
                minDate: 'today',
                dateFormat: 'Y-m-d',
                onChange: function(selectedDates) {
                    if (selectedDates.length > 0) {
                        checkOutPicker.set('minDate', selectedDates[0].fp_incr(1));
                    }
                }
            });
            
            const checkOutPicker = flatpickr(checkOutInput, {
                minDate: new Date().fp_incr(1),
                dateFormat: 'Y-m-d'
            });
        }
    }
}

// Lazy loading for images
function initImageLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Form validation
function initFormValidations() {
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showInputError(input, 'This field is required');
            isValid = false;
        } else {
            clearInputError(input);
            
            // Email validation
            if (input.type === 'email' && !isValidEmail(input.value)) {
                showInputError(input, 'Please enter a valid email address');
                isValid = false;
            }
            
            // Phone validation
            if (input.type === 'tel' && !isValidPhone(input.value)) {
                showInputError(input, 'Please enter a valid phone number');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
}

function showInputError(input, message) {
    clearInputError(input);
    
    input.classList.add('border-red-500');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-red-500 text-sm mt-1';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

function clearInputError(input) {
    input.classList.remove('border-red-500');
    
    const existingError = input.parentNode.querySelector('.text-red-500');
    if (existingError) {
        existingError.remove();
    }
}

// Booking system functionality
function initBookingSystem() {
    // Availability check
    const availabilityForm = document.getElementById('availability-form');
    if (availabilityForm) {
        availabilityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            checkAvailability(this);
        });
    }
    
    // Coupon application
    const applyCouponBtn = document.getElementById('apply-coupon');
    if (applyCouponBtn) {
        applyCouponBtn.addEventListener('click', applyCoupon);
    }
}

function checkAvailability(form) {
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Checking...';
    submitBtn.disabled = true;
    
    fetch(`/api/rooms/availability?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = `/rooms?${params.toString()}`;
            } else {
                alert('No rooms available for the selected dates. Please try different dates.');
            }
        })
        .catch(error => {
            console.error('Error checking availability:', error);
            alert('Error checking availability. Please try again.');
        })
        .finally(() => {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        });
}

function applyCoupon() {
    const couponCode = document.querySelector('input[name="coupon_code"]').value;
    const totalAmount = parseFloat(document.getElementById('total-amount').textContent);
    
    if (!couponCode) {
        showNotification('Please enter a coupon code', 'error');
        return;
    }
    
    // Show loading state
    const applyBtn = document.getElementById('apply-coupon');
    const originalText = applyBtn.textContent;
    applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    applyBtn.disabled = true;
    
    fetch('/api/offers/validate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            coupon_code: couponCode,
            total_amount: totalAmount
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateBookingSummary(data.discount, data.final_amount);
            showNotification(data.message, 'success');
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error applying coupon:', error);
        showNotification('Error applying coupon. Please try again.', 'error');
    })
    .finally(() => {
        applyBtn.textContent = originalText;
        applyBtn.disabled = false;
    });
}

function updateBookingSummary(discount, finalAmount) {
    const discountRow = document.getElementById('discount-row');
    const discountAmount = document.getElementById('discount-amount');
    const totalAmount = document.getElementById('total-amount');
    
    discountAmount.textContent = discount.toFixed(2);
    totalAmount.textContent = finalAmount.toFixed(2);
    discountRow.style.display = 'flex';
}

// Gallery functionality
function initGallery() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(btn => {
                btn.classList.remove('active', 'bg-amber-600', 'text-white');
                btn.classList.add('bg-gray-200', 'text-gray-700');
            });
            
            // Add active class to clicked button
            this.classList.add('active', 'bg-amber-600', 'text-white');
            this.classList.remove('bg-gray-200', 'text-gray-700');
            
            const filter = this.getAttribute('data-filter');
            
            galleryItems.forEach(item => {
                if (filter === 'all' || item.getAttribute('data-category') === filter) {
                    item.style.display = 'block';
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'scale(1)';
                    }, 50);
                } else {
                    item.style.opacity = '0';
                    item.style.transform = 'scale(0.8)';
                    setTimeout(() => {
                        item.style.display = 'none';
                    }, 300);
                }
            });
        });
    });
}

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.custom-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `custom-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform transition duration-300 translate-x-full`;
    
    // Set styles based on type
    const styles = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white',
        info: 'bg-blue-500 text-white'
    };
    
    notification.className += ` ${styles[type] || styles.info}`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${getNotificationIcon(type)} mr-3"></i>
            <span>${message}</span>
            <button class="ml-4" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

// Export functions for global access
window.showNotification = showNotification;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;