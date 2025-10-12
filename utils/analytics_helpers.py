# utils/analytics_helpers.py

from datetime import datetime, date, timedelta
from app import db
from models.booking import Booking
from models.payment import Payment
from models.room import Room
from models.user import User
import json
from io import BytesIO, StringIO
import csv

class AnalyticsHelpers:
    """Helper functions for analytics and reporting"""
    
    @staticmethod
    def get_revenue_chart_data(days=30):
        """Get revenue data for chart visualization - FIXED VERSION"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            # Get daily revenue data
            revenue_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                # Use Payment model to get revenue
                daily_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                    Payment.payment_status == 'completed',
                    Payment.created_at >= current_date,
                    Payment.created_at < next_date
                ).scalar() or 0
                
                revenue_data.append({
                    'date': current_date,
                    'revenue': float(daily_revenue)
                })
                
                current_date = next_date
            
            return revenue_data
        
        except Exception as e:
            print(f"Error in get_revenue_chart_data: {e}")
            return []

    @staticmethod
    def get_occupancy_chart_data(days=30):
        """Get occupancy data for chart visualization - FIXED VERSION"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            total_rooms = Room.query.count()
            
            if total_rooms == 0:
                return []
            
            occupancy_data = []
            current_date = start_date
            
            while current_date <= end_date:
                # Count rooms occupied on this date
                occupied_rooms = Booking.query.filter(
                    Booking.check_in <= current_date,
                    Booking.check_out > current_date,
                    Booking.status.in_(['confirmed', 'checked_in', 'checked_out', 'completed'])
                ).count()
                
                occupancy_rate = (occupied_rooms / total_rooms) * 100 if total_rooms > 0 else 0
                
                occupancy_data.append({
                    'date': current_date,
                    'rate': round(occupancy_rate, 1),
                    'occupied': occupied_rooms,
                    'total': total_rooms
                })
                
                current_date += timedelta(days=1)
            
            return occupancy_data
        
        except Exception as e:
            print(f"Error in get_occupancy_chart_data: {e}")
            return []

    @staticmethod
    def format_chart_data(raw_data, value_key):
        """Format raw data for chart.js"""
        if not raw_data:
            return {'labels': [], 'values': []}
            
        labels = [item['date'].strftime('%b %d') for item in raw_data]
        values = [item[value_key] for item in raw_data]
        
        return {
            'labels': labels,
            'values': values
        }

    @staticmethod
    def generate_booking_stats_report(start_date=None, end_date=None):
        """Generate comprehensive booking statistics report - FIXED VERSION"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        try:
            # Basic stats
            total_bookings = Booking.query.filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date
            ).count()
            
            confirmed_bookings = Booking.query.filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date,
                Booking.status == 'confirmed'
            ).count()
            
            completed_bookings = Booking.query.filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date,
                Booking.status == 'completed'
            ).count()
            
            # Revenue stats - FIXED: Use Payment model correctly
            revenue_data = Payment.query.filter(
                Payment.payment_status == 'completed',
                Payment.created_at >= start_date,
                Payment.created_at <= end_date
            ).all()
            
            total_revenue = sum(p.amount for p in revenue_data) if revenue_data else 0
            avg_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0
            
            # Room type performance - FIXED: Handle no bookings case
            room_stats = []
            try:
                room_stats = db.session.query(
                    Room.room_type,
                    db.func.count(Booking.id),
                    db.func.sum(Booking.final_amount)
                ).join(Booking, Room.id == Booking.room_id).filter(
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                ).group_by(Room.room_type).all()
            except Exception as e:
                print(f"Error in room stats query: {e}")
                room_stats = []
            
            room_performance = []
            for room_type, count, revenue in room_stats:
                room_performance.append({
                    'room_type': room_type,
                    'bookings': count,
                    'revenue': float(revenue) if revenue else 0,
                    'avg_revenue': float(revenue) / count if count > 0 else 0
                })
            
            # If no room performance data, create sample structure
            if not room_performance:
                rooms = Room.query.all()
                for room in rooms:
                    room_performance.append({
                        'room_type': room.room_type,
                        'bookings': 0,
                        'revenue': 0.0,
                        'avg_revenue': 0.0
                    })
            
            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_bookings': total_bookings,
                    'confirmed_bookings': confirmed_bookings,
                    'completed_bookings': completed_bookings,
                    'total_revenue': total_revenue,
                    'avg_booking_value': avg_booking_value
                },
                'room_performance': room_performance,
                'revenue_breakdown': AnalyticsHelpers.get_revenue_breakdown(revenue_data)
            }
        
        except Exception as e:
            print(f"Error in generate_booking_stats_report: {e}")
            # Return empty structure with error handling
            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_bookings': 0,
                    'confirmed_bookings': 0,
                    'completed_bookings': 0,
                    'total_revenue': 0,
                    'avg_booking_value': 0
                },
                'room_performance': [],
                'revenue_breakdown': {'payment_methods': {}, 'daily': {}, 'weekly': {}},
                'error': str(e)
            }

    @staticmethod
    def get_revenue_breakdown(payments):
        """Get revenue breakdown by payment method and time periods"""
        payment_methods = {}
        daily_revenue = {}
        weekly_revenue = {}
        
        for payment in payments:
            # Payment method breakdown
            method = payment.payment_method
            payment_methods[method] = payment_methods.get(method, 0) + payment.amount
            
            # Daily breakdown
            payment_date = payment.created_at.date()
            daily_revenue[payment_date] = daily_revenue.get(payment_date, 0) + payment.amount
            
            # Weekly breakdown
            week_start = payment_date - timedelta(days=payment_date.weekday())
            weekly_revenue[week_start] = weekly_revenue.get(week_start, 0) + payment.amount
        
        return {
            'payment_methods': payment_methods,
            'daily': daily_revenue,
            'weekly': weekly_revenue
        }

    @staticmethod
    def generate_csv_report(data, filename):
        """Generate CSV report from data - FIXED VERSION"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        if 'summary' in data:
            writer.writerow(['Metric', 'Value'])
            for key, value in data['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
            
            writer.writerow([])  # Empty row
        
        # Write room performance
        if 'room_performance' in data and data['room_performance']:
            writer.writerow(['Room Performance'])
            writer.writerow(['Room Type', 'Bookings', 'Revenue', 'Average Revenue'])
            for room in data['room_performance']:
                writer.writerow([
                    room['room_type'],
                    room['bookings'],
                    f"₹{room['revenue']:,.2f}",
                    f"₹{room['avg_revenue']:,.2f}"
                ])
        else:
            writer.writerow(['Room Performance'])
            writer.writerow(['No room performance data available'])
        
        # Get CSV data as string and convert to bytes
        csv_string = output.getvalue()
        output.close()
        
        # Create BytesIO from the string data
        bytes_io = BytesIO()
        bytes_io.write(csv_string.encode('utf-8'))
        bytes_io.seek(0)
        
        return bytes_io

    @staticmethod
    def get_guest_demographics():
        """Get guest demographic data"""
        # Age groups (estimated from booking data)
        total_guests = User.query.count()
        guests_with_bookings = User.query.filter(User.bookings.any()).count()
        
        # User registration trend
        registration_trend = db.session.query(
            db.func.date(User.created_at),
            db.func.count(User.id)
        ).filter(
            User.created_at >= date.today() - timedelta(days=90)
        ).group_by(db.func.date(User.created_at)).all()
        
        return {
            'total_guests': total_guests,
            'guests_with_bookings': guests_with_bookings,
            'conversion_rate': (guests_with_bookings / total_guests * 100) if total_guests > 0 else 0,
            'registration_trend': [
                {'date': date, 'count': count} 
                for date, count in registration_trend
            ]
        }

    @staticmethod
    def calculate_forecast(historical_data, periods=30):
        """Simple revenue forecast based on historical data"""
        if len(historical_data) < 7:  # Need at least a week of data
            return []
        
        # Simple moving average forecast
        recent_data = historical_data[-7:]  # Last 7 days
        avg_revenue = sum(item['revenue'] for item in recent_data) / len(recent_data)
        
        forecast = []
        current_date = date.today() + timedelta(days=1)
        
        for i in range(periods):
            # Add some random variation (±20%)
            variation = 1 + (0.4 * (i / periods) - 0.2)  # Gradually increasing trend
            forecast_revenue = avg_revenue * variation
            
            forecast.append({
                'date': current_date + timedelta(days=i),
                'revenue': max(forecast_revenue, 0),
                'is_forecast': True
            })
        
        return forecast

    # Sample data generation methods
    @staticmethod
    def generate_sample_revenue_data(days=30):
        """Generate sample revenue data for demonstration"""
        sample_data = []
        base_date = date.today() - timedelta(days=days-1)
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            # Generate realistic revenue data with some variation
            base_revenue = 5000 + (i * 100)  # Slight upward trend
            daily_variation = (i % 7) * 500   # Weekly pattern
            random_variation = (hash(str(current_date)) % 2000) - 1000  # Random but consistent
            
            revenue = max(base_revenue + daily_variation + random_variation, 1000)
            
            sample_data.append({
                'date': current_date,
                'revenue': revenue
            })
        
        return sample_data

    @staticmethod
    def generate_sample_occupancy_data(days=30):
        """Generate sample occupancy data for demonstration"""
        sample_data = []
        base_date = date.today() - timedelta(days=days-1)
        total_rooms = Room.query.count() or 10  # Fallback if no rooms
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            
            # Generate realistic occupancy with weekly patterns
            base_occupancy = 60  # Base occupancy rate
            weekend_boost = 20 if current_date.weekday() >= 5 else 0  # Higher on weekends
            seasonal_variation = 10 * (i // 7)  # Slight increase over weeks
            random_variation = (hash(str(current_date)) % 15) - 7  # Small random variation
            
            occupancy_rate = base_occupancy + weekend_boost + seasonal_variation + random_variation
            occupancy_rate = max(30, min(95, occupancy_rate))  # Keep between 30-95%
            
            occupied_rooms = int((occupancy_rate / 100) * total_rooms)
            
            sample_data.append({
                'date': current_date,
                'rate': occupancy_rate,
                'occupied': occupied_rooms,
                'total': total_rooms
            })
        
        return sample_data

    @staticmethod
    def generate_sample_chart_data():
        """Generate complete sample chart data"""
        revenue_raw = AnalyticsHelpers.generate_sample_revenue_data(30)
        occupancy_raw = AnalyticsHelpers.generate_sample_occupancy_data(30)
        
        return {
            'revenue_data': AnalyticsHelpers.format_chart_data(revenue_raw, 'revenue'),
            'occupancy_data': AnalyticsHelpers.format_chart_data(occupancy_raw, 'rate')
        }