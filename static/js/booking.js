// Booking system specific JavaScript

class BookingSystem {
    constructor() {
        this.currentStep = 1;
        this.bookingData = {};
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadRoomData();
    }
    
    bindEvents() {
        // Step navigation
        document.querySelectorAll('[data-step]').forEach(button => {
            button.addEventListener('click', (e) => {
                const step = parseInt(e.target.getAttribute('data-step'));
                this.goToStep(step);
            });
        });
        
        // Date change handlers
        const checkInInput = document.getElementById('check-in');
        const checkOutInput = document.getElementById('check-out');
        
        if (checkInInput && checkOutInput) {
            checkInInput.addEventListener('change', () => this.updatePricing());
            checkOutInput.addEventListener('change', () => this.updatePricing());
        }
        
        // Guest count changes
        const guestInputs = document.querySelectorAll('select[name="adults"], select[name="children"]');
        guestInputs.forEach(input => {
            input.addEventListener('change', () => this.updatePricing());
        });
        
        // Coupon application
        const applyCouponBtn = document.getElementById('apply-coupon');
        if (applyCouponBtn) {
            applyCouponBtn.addEventListener('click', () => this.applyCoupon());
        }
    }
    
    loadRoomData() {
        const roomId = this.getRoomId();
        if (roomId) {
            fetch(`/api/rooms/${roomId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.roomData = data.room;
                        this.updatePricing();
                    }
                })
                .catch(error => {
                    console.error('Error loading room data:', error);
                });
        }
    }
    
    getRoomId() {
        // Extract room ID from URL or data attribute
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('room_id') || document.getElementById('room-id')?.value;
    }
    
    updatePricing() {
        const checkIn = document.getElementById('check-in')?.value;
        const checkOut = document.getElementById('check-out')?.value;
        const adults = parseInt(document.querySelector('select[name="adults"]')?.value || 1);
        const children = parseInt(document.querySelector('select[name="children"]')?.value || 0);
        
        if (!checkIn || !checkOut || !this.roomData) return;
        
        const checkInDate = new Date(checkIn);
        const checkOutDate = new Date(checkOut);
        const nights = Math.ceil((checkOutDate - checkInDate) / (1000 * 60 * 60 * 24));
        
        if (nights <= 0) return;
        
        const baseAmount = this.roomData.price * nights;
        const taxAmount = baseAmount * 0.18; // 18% GST
        const totalAmount = baseAmount + taxAmount;
        
        this.updatePriceDisplay(baseAmount, taxAmount, totalAmount, nights);
    }
    
    updatePriceDisplay(baseAmount, taxAmount, totalAmount, nights) {
        const elements = {
            baseAmount: document.getElementById('base-amount'),
            taxAmount: document.getElementById('tax-amount'),
            totalAmount: document.getElementById('total-amount'),
            nights: document.getElementById('total-nights')
        };
        
        if (elements.baseAmount) elements.baseAmount.textContent = baseAmount.toFixed(2);
        if (elements.taxAmount) elements.taxAmount.textContent = taxAmount.toFixed(2);
        if (elements.totalAmount) elements.totalAmount.textContent = totalAmount.toFixed(2);
        if (elements.nights) elements.nights.textContent = nights;
        
        // Store for coupon calculations
        this.currentTotal = totalAmount;
    }
    
    applyCoupon() {
        const couponCode = document.querySelector('input[name="coupon_code"]')?.value;
        
        if (!couponCode) {
            showNotification('Please enter a coupon code', 'error');
            return;
        }
        
        if (!this.currentTotal) {
            showNotification('Please select dates first', 'error');
            return;
        }
        
        const applyBtn = document.getElementById('apply-coupon');
        const originalText = applyBtn.textContent;
        
        // Show loading state
        applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        applyBtn.disabled = true;
        
        fetch('/api/offers/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                coupon_code: couponCode,
                total_amount: this.currentTotal
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.applyDiscount(data.discount, data.final_amount);
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
    
    applyDiscount(discount, finalAmount) {
        const discountRow = document.getElementById('discount-row');
        const discountAmount = document.getElementById('discount-amount');
        const totalAmount = document.getElementById('total-amount');
        
        if (discountRow && discountAmount && totalAmount) {
            discountAmount.textContent = discount.toFixed(2);
            totalAmount.textContent = finalAmount.toFixed(2);
            discountRow.style.display = 'flex';
        }
        
        this.appliedDiscount = discount;
        this.finalAmount = finalAmount;
    }
    
    goToStep(step) {
        // Validate current step before proceeding
        if (!this.validateStep(this.currentStep)) {
            return;
        }
        
        // Hide current step
        document.querySelector(`[data-step-content="${this.currentStep}"]`)?.classList.add('hidden');
        
        // Show new step
        document.querySelector(`[data-step-content="${step}"]`)?.classList.remove('hidden');
        
        // Update step indicators
        this.updateStepIndicators(step);
        
        this.currentStep = step;
    }
    
    validateStep(step) {
        switch (step) {
            case 1:
                return this.validateBookingDetails();
            case 2:
                return this.validateGuestInformation();
            case 3:
                return this.validatePayment();
            default:
                return true;
        }
    }
    
    validateBookingDetails() {
        const checkIn = document.getElementById('check-in')?.value;
        const checkOut = document.getElementById('check-out')?.value;
        
        if (!checkIn || !checkOut) {
            showNotification('Please select check-in and check-out dates', 'error');
            return false;
        }
        
        const checkInDate = new Date(checkIn);
        const checkOutDate = new Date(checkOut);
        
        if (checkOutDate <= checkInDate) {
            showNotification('Check-out date must be after check-in date', 'error');
            return false;
        }
        
        return true;
    }
    
    validateGuestInformation() {
        const requiredFields = ['guest_name', 'guest_email', 'guest_phone'];
        
        for (const field of requiredFields) {
            const input = document.querySelector(`[name="${field}"]`);
            if (input && !input.value.trim()) {
                showNotification(`Please fill in ${field.replace('_', ' ')}`, 'error');
                input.focus();
                return false;
            }
        }
        
        return true;
    }
    
    validatePayment() {
        // Payment validation would be handled by the payment gateway
        return true;
    }
    
    updateStepIndicators(step) {
        document.querySelectorAll('.step-indicator').forEach(indicator => {
            indicator.classList.remove('active', 'completed');
        });
        
        for (let i = 1; i <= step; i++) {
            const indicator = document.querySelector(`[data-step-indicator="${i}"]`);
            if (indicator) {
                if (i === step) {
                    indicator.classList.add('active');
                } else {
                    indicator.classList.add('completed');
                }
            }
        }
    }
    
    // Payment integration
    initializePayment() {
        // This would integrate with Razorpay or other payment gateways
        const options = {
            key: document.getElementById('razorpay-key').value,
            amount: this.finalAmount * 100, // Amount in paise
            currency: 'INR',
            name: 'Hotel Royal Orchid',
            description: 'Room Booking',
            image: '/static/images/logo.png',
            handler: (response) => {
                this.handlePaymentSuccess(response);
            },
            prefill: {
                name: document.querySelector('[name="guest_name"]').value,
                email: document.querySelector('[name="guest_email"]').value,
                contact: document.querySelector('[name="guest_phone"]').value
            },
            theme: {
                color: '#d97706'
            }
        };
        
        const rzp = new Razorpay(options);
        rzp.open();
    }
    
    handlePaymentSuccess(response) {
        // Submit the booking form
        document.getElementById('booking-form').submit();
    }
}

// Initialize booking system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.bookingSystem = new BookingSystem();
});