// Calendar functionality for booking system

class BookingCalendar {
    constructor(options = {}) {
        this.options = {
            container: '#calendar',
            monthsToShow: 2,
            ...options
        };
        this.selectedDates = {
            checkIn: null,
            checkOut: null
        };
        this.unavailableDates = [];
        this.init();
    }
    
    init() {
        this.container = document.querySelector(this.options.container);
        if (!this.container) return;
        
        this.loadUnavailableDates();
        this.render();
        this.bindEvents();
    }
    
    loadUnavailableDates() {
        // This would typically fetch unavailable dates from the API
        // For now, we'll simulate some unavailable dates
        const today = new Date();
        this.unavailableDates = [
            today.getTime() + (3 * 24 * 60 * 60 * 1000), // 3 days from today
            today.getTime() + (7 * 24 * 60 * 60 * 1000), // 7 days from today
            today.getTime() + (10 * 24 * 60 * 60 * 1000) // 10 days from today
        ];
    }
    
    render() {
        const months = [];
        const today = new Date();
        
        for (let i = 0; i < this.options.monthsToShow; i++) {
            const monthDate = new Date(today.getFullYear(), today.getMonth() + i, 1);
            months.push(this.renderMonth(monthDate));
        }
        
        this.container.innerHTML = `
            <div class="calendar-header">
                <button class="calendar-nav prev" data-direction="prev">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <div class="calendar-title"></div>
                <button class="calendar-nav next" data-direction="next">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
            <div class="calendar-months">
                ${months.join('')}
            </div>
            <div class="calendar-legend">
                <div class="legend-item">
                    <div class="legend-color available"></div>
                    <span>Available</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color unavailable"></div>
                    <span>Unavailable</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color selected"></div>
                    <span>Selected</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color in-range"></div>
                    <span>In Range</span>
                </div>
            </div>
        `;
        
        this.updateTitle();
    }
    
    renderMonth(date) {
        const monthName = date.toLocaleString('default', { month: 'long', year: 'numeric' });
        const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
        const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startingDay = firstDay.getDay();
        
        let days = '';
        
        // Add empty cells for days before the first day of the month
        for (let i = 0; i < startingDay; i++) {
            days += '<div class="calendar-day empty"></div>';
        }
        
        // Add days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const currentDate = new Date(date.getFullYear(), date.getMonth(), day);
            const isToday = this.isToday(currentDate);
            const isPast = this.isPastDate(currentDate);
            const isUnavailable = this.isUnavailable(currentDate);
            const isSelected = this.isSelected(currentDate);
            const isInRange = this.isInRange(currentDate);
            
            let dayClass = 'calendar-day';
            if (isToday) dayClass += ' today';
            if (isPast) dayClass += ' past';
            if (isUnavailable) dayClass += ' unavailable';
            if (isSelected) dayClass += ' selected';
            if (isInRange) dayClass += ' in-range';
            
            days += `
                <div class="${dayClass}" data-date="${currentDate.getTime()}">
                    ${day}
                </div>
            `;
        }
        
        return `
            <div class="calendar-month" data-month="${date.getTime()}">
                <div class="month-header">${monthName}</div>
                <div class="week-days">
                    <div>Sun</div>
                    <div>Mon</div>
                    <div>Tue</div>
                    <div>Wed</div>
                    <div>Thu</div>
                    <div>Fri</div>
                    <div>Sat</div>
                </div>
                <div class="month-days">
                    ${days}
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Date selection
        this.container.addEventListener('click', (e) => {
            const dayElement = e.target.closest('.calendar-day');
            if (!dayElement || dayElement.classList.contains('empty') || 
                dayElement.classList.contains('unavailable') || 
                dayElement.classList.contains('past')) return;
            
            const date = parseInt(dayElement.getAttribute('data-date'));
            this.selectDate(new Date(date));
        });
        
        // Navigation
        this.container.addEventListener('click', (e) => {
            const navButton = e.target.closest('.calendar-nav');
            if (navButton) {
                const direction = navButton.getAttribute('data-direction');
                this.navigate(direction);
            }
        });
    }
    
    selectDate(date) {
        if (!this.selectedDates.checkIn || (this.selectedDates.checkIn && this.selectedDates.checkOut)) {
            // Start new selection
            this.selectedDates = {
                checkIn: date,
                checkOut: null
            };
        } else {
            // Complete selection
            if (date > this.selectedDates.checkIn) {
                this.selectedDates.checkOut = date;
            } else {
                // If selected date is before check-in, swap them
                this.selectedDates = {
                    checkIn: date,
                    checkOut: this.selectedDates.checkIn
                };
            }
            
            // Trigger change event
            this.onDatesSelected();
        }
        
        this.highlightSelectedRange();
        this.updateInputs();
    }
    
    highlightSelectedRange() {
        // Remove previous highlights
        this.container.querySelectorAll('.in-range, .selected').forEach(el => {
            el.classList.remove('in-range', 'selected');
        });
        
        if (this.selectedDates.checkIn) {
            const checkInElement = this.container.querySelector(`[data-date="${this.selectedDates.checkIn.getTime()}"]`);
            if (checkInElement) {
                checkInElement.classList.add('selected');
            }
        }
        
        if (this.selectedDates.checkOut) {
            const checkOutElement = this.container.querySelector(`[data-date="${this.selectedDates.checkOut.getTime()}"]`);
            if (checkOutElement) {
                checkOutElement.classList.add('selected');
            }
            
            // Highlight range
            if (this.selectedDates.checkIn && this.selectedDates.checkOut) {
                const startTime = this.selectedDates.checkIn.getTime();
                const endTime = this.selectedDates.checkOut.getTime();
                
                this.container.querySelectorAll('.calendar-day').forEach(dayElement => {
                    const dayTime = parseInt(dayElement.getAttribute('data-date'));
                    if (dayTime > startTime && dayTime < endTime) {
                        dayElement.classList.add('in-range');
                    }
                });
            }
        }
    }
    
    updateInputs() {
        const checkInInput = document.getElementById('check-in');
        const checkOutInput = document.getElementById('check-out');
        
        if (checkInInput && this.selectedDates.checkIn) {
            checkInInput.value = this.formatDateForInput(this.selectedDates.checkIn);
        }
        
        if (checkOutInput && this.selectedDates.checkOut) {
            checkOutInput.value = this.formatDateForInput(this.selectedDates.checkOut);
        }
    }
    
    formatDateForInput(date) {
        return date.toISOString().split('T')[0];
    }
    
    onDatesSelected() {
        // Custom event for when dates are selected
        const event = new CustomEvent('datesSelected', {
            detail: {
                checkIn: this.selectedDates.checkIn,
                checkOut: this.selectedDates.checkOut
            }
        });
        this.container.dispatchEvent(event);
    }
    
    navigate(direction) {
        // This would navigate to previous/next months
        // Implementation depends on your specific needs
        console.log(`Navigate ${direction}`);
    }
    
    updateTitle() {
        const titleElement = this.container.querySelector('.calendar-title');
        if (titleElement) {
            const today = new Date();
            const endDate = new Date(today.getFullYear(), today.getMonth() + this.options.monthsToShow, 0);
            titleElement.textContent = `Select Dates (${today.toLocaleDateString()} - ${endDate.toLocaleDateString()})`;
        }
    }
    
    // Utility methods
    isToday(date) {
        const today = new Date();
        return date.toDateString() === today.toDateString();
    }
    
    isPastDate(date) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return date < today;
    }
    
    isUnavailable(date) {
        return this.unavailableDates.includes(date.getTime());
    }
    
    isSelected(date) {
        return (this.selectedDates.checkIn && date.getTime() === this.selectedDates.checkIn.getTime()) ||
               (this.selectedDates.checkOut && date.getTime() === this.selectedDates.checkOut.getTime());
    }
    
    isInRange(date) {
        if (!this.selectedDates.checkIn || !this.selectedDates.checkOut) return false;
        
        const time = date.getTime();
        return time > this.selectedDates.checkIn.getTime() && time < this.selectedDates.checkOut.getTime();
    }
    
    // Public methods
    setUnavailableDates(dates) {
        this.unavailableDates = dates.map(date => new Date(date).getTime());
        this.render();
    }
    
    getSelectedDates() {
        return { ...this.selectedDates };
    }
    
    clearSelection() {
        this.selectedDates = {
            checkIn: null,
            checkOut: null
        };
        this.highlightSelectedRange();
        this.updateInputs();
    }
}

// Initialize calendar when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const calendarContainer = document.getElementById('booking-calendar');
    if (calendarContainer) {
        window.bookingCalendar = new BookingCalendar({
            container: '#booking-calendar',
            monthsToShow: 2
        });
        
        // Listen for date selection
        calendarContainer.addEventListener('datesSelected', function(e) {
            const { checkIn, checkOut } = e.detail;
            console.log('Selected dates:', checkIn, checkOut);
            
            // You can trigger additional actions here, like updating pricing
            if (window.bookingSystem) {
                window.bookingSystem.updatePricing();
            }
        });
    }
});

// Flatpickr integration for simpler date picking
function initFlatpickr() {
    if (typeof flatpickr !== 'undefined') {
        // Check-in date picker
        const checkInInput = document.getElementById('check-in');
        if (checkInInput) {
            flatpickr(checkInInput, {
                minDate: 'today',
                dateFormat: 'Y-m-d',
                onChange: function(selectedDates, dateStr, instance) {
                    const checkOutInput = document.getElementById('check-out');
                    if (checkOutInput && selectedDates.length > 0) {
                        const minCheckOut = new Date(selectedDates[0]);
                        minCheckOut.setDate(minCheckOut.getDate() + 1);
                        
                        if (checkOutInput._flatpickr) {
                            checkOutInput._flatpickr.set('minDate', minCheckOut);
                        }
                    }
                    
                    // Update any connected systems
                    if (window.bookingSystem) {
                        window.bookingSystem.updatePricing();
                    }
                }
            });
        }
        
        // Check-out date picker
        const checkOutInput = document.getElementById('check-out');
        if (checkOutInput) {
            flatpickr(checkOutInput, {
                minDate: new Date().fp_incr(1),
                dateFormat: 'Y-m-d',
                onChange: function() {
                    if (window.bookingSystem) {
                        window.bookingSystem.updatePricing();
                    }
                }
            });
        }
    }
}

// Call this when the page loads
document.addEventListener('DOMContentLoaded', initFlatpickr);