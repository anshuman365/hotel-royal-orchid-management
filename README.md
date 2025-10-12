# 🏨 Hotel Royal Orchid Management System

A modern, AI-powered hotel management system built with Flask featuring comprehensive booking management, payment processing, and intelligent analytics.

![Hotel Management](https://img.shields.io/badge/Flask-2.3.3-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🎯 Core Functionality
- **Room Booking System** - Real-time availability & reservations
- **Payment Integration** - Secure payment processing
- **User Authentication** - Role-based access control
- **Review Management** - Customer feedback system

### 🤖 AI-Powered Features
- **Smart Chatbot** - 24/7 customer support
- **AI Analytics** - Business intelligence & insights
- **Predictive Pricing** - Dynamic offer suggestions
- **Review Analysis** - Sentiment analysis

### 📊 Admin Dashboard
- **Advanced Analytics** - Revenue & occupancy reports
- **Room Management** - Inventory control
- **Booking Management** - Reservation handling
- **AI Insights** - Strategic recommendations

## 🛠 Tech Stack

- **Backend:** Python, Flask, SQLAlchemy
- **Frontend:** HTML5, CSS3, JavaScript, Jinja2
- **Database:** SQLite (Production: PostgreSQL ready)
- **AI/ML:** Custom AI services & analytics
- **Payments:** Payment gateway integration
- **Notifications:** Email & SMS services

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation
```bash
# Clone repository
git clone https://github.com/anshuman365/hotel-royal-orchid-management.git
cd hotel-royal-orchid-management

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db upgrade

# Run application
flask run
```

## Environment Setup

Create .env file:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///hotel.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
```

## 📁 Project Structure

```
hotel_royal_orchid/
├── blueprints/          # Flask blueprints
├── models/             # Database models
├── templates/          # HTML templates
├── static/            # CSS, JS, Images
├── utils/             # Utility functions
├── migrations/        # Database migrations
└── instance/          # Database instance
```

## 🎯 Usage

For Guests

1. Browse available rooms
2. Make reservations
3. Process payments
4. Submit reviews

For Administrators

1. Access admin dashboard
2. Manage bookings & rooms
3. View AI analytics
4. Generate reports

## 🤝 Contributing

We welcome contributions! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

Anshuman

· GitHub: @anshuman365

## 🙏 Acknowledgments

· Flask community
· AI/ML libraries used
· Template designers
