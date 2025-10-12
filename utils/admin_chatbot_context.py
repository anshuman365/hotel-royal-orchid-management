# utils/admin_chatbot_context.py
from datetime import datetime, timedelta
from app import db
from models.user import User
from models.booking import Booking
from models.room import Room
from models.offer import Offer
from models.review import Review
from models.payment import Payment
import json

class AdminChatbotContextBuilder:
    """Builds comprehensive business context for admin chatbot"""
    
    @staticmethod
    def build_admin_context():
        """Build comprehensive admin context with full business data"""
        
        # Real-time metrics
        current_time = datetime.utcnow()
        today = current_time.date()
        
        context = f"""
        HOTEL ROYAL ORCHID - ADMIN DASHBOARD DATA
        Last Updated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
        
        {AdminChatbotContextBuilder._get_business_overview()}
        
        {AdminChatbotContextBuilder._get_today_metrics(today)}
        
        {AdminChatbotContextBuilder._get_financial_metrics()}
        
        {AdminChatbotContextBuilder._get_operational_metrics()}
        
        {AdminChatbotContextBuilder._get_customer_insights()}
        
        {AdminChatbotContextBuilder._get_room_performance()}
        
        {AdminChatbotContextBuilder._get_offer_performance()}
        
        {AdminChatbotContextBuilder._get_review_sentiments()}
        
        {AdminChatbotContextBuilder._get_alerts_and_issues()}
        
        {AdminChatbotContextBuilder._get_upcoming_events()}
        """
        
        return context
    
    @staticmethod
    def _get_business_overview():
        """Get comprehensive business overview"""
        total_rooms = Room.query.count()
        available_rooms = Room.query.filter_by(status='available').count()
        total_bookings = Booking.query.count()
        total_users = User.query.count()
        total_reviews = Review.query.count()
        
        # Current month metrics
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_bookings = Booking.query.filter(Booking.created_at >= month_start).count()
        monthly_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.created_at >= month_start,
            Payment.payment_status == 'completed'
        ).scalar() or 0
        
        return f"""
        BUSINESS OVERVIEW:
        - Total Rooms: {total_rooms} (Available: {available_rooms})
        - Total Bookings: {total_bookings}
        - Registered Users: {total_users}
        - Customer Reviews: {total_reviews}
        - This Month: {monthly_bookings} bookings, ₹{monthly_revenue:,.2f} revenue
        """
    
    @staticmethod
    def _get_today_metrics(today):
        """Get today's operational metrics"""
        today_checkins = Booking.query.filter_by(check_in=today, status='confirmed').count()
        today_checkouts = Booking.query.filter_by(check_out=today, status='confirmed').count()
        today_bookings = Booking.query.filter(
            db.func.date(Booking.created_at) == today
        ).count()
        
        # Occupancy for today
        occupied_rooms = Booking.query.filter(
            Booking.check_in <= today,
            Booking.check_out > today,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
        
        total_rooms = Room.query.count()
        today_occupancy = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
        
        return f"""
        TODAY'S METRICS ({today.strftime('%Y-%m-%d')}):
        - Check-ins: {today_checkins}
        - Check-outs: {today_checkouts}
        - New Bookings: {today_bookings}
        - Current Occupancy: {today_occupancy:.1f}% ({occupied_rooms}/{total_rooms} rooms)
        """
    
    @staticmethod
    def _get_financial_metrics():
        """Get financial performance metrics"""
        # Last 30 days revenue
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.created_at >= thirty_days_ago,
            Payment.payment_status == 'completed'
        ).scalar() or 0
        
        # Revenue by room type
        revenue_by_type = db.session.query(
            Room.room_type, 
            db.func.sum(Booking.final_amount)
        ).join(Booking).filter(
            Booking.created_at >= thirty_days_ago
        ).group_by(Room.room_type).all()
        
        revenue_breakdown = "\n".join([f"    - {room_type}: ₹{revenue:,.2f}" for room_type, revenue in revenue_by_type])
        
        return f"""
        FINANCIAL PERFORMANCE (Last 30 Days):
        - Total Revenue: ₹{recent_revenue:,.2f}
        - Revenue by Room Type:
        {revenue_breakdown}
        """
    
    @staticmethod
    def _get_operational_metrics():
        """Get operational efficiency metrics"""
        # Booking status distribution
        status_counts = db.session.query(
            Booking.status, 
            db.func.count(Booking.id)
        ).group_by(Booking.status).all()
        
        status_distribution = "\n".join([f"    - {status}: {count}" for status, count in status_counts])
        
        # Average stay duration
        avg_stay = db.session.query(db.func.avg(Booking.total_nights)).scalar() or 0
        
        return f"""
        OPERATIONAL METRICS:
        - Booking Status Distribution:
        {status_distribution}
        - Average Stay Duration: {avg_stay:.1f} nights
        """
    
    @staticmethod
    def _get_customer_insights():
        """Get customer behavior insights"""
        # Repeat customer rate
        users_with_bookings = User.query.filter(User.bookings.any()).all()
        repeat_customers = len([u for u in users_with_bookings if len(u.bookings) > 1])
        repeat_rate = (repeat_customers / len(users_with_bookings) * 100) if users_with_bookings else 0
        
        # Average rating
        avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(is_approved=True).scalar() or 0
        
        # Customer segments
        vip_customers = len([u for u in users_with_bookings if len(u.bookings) >= 3])
        
        return f"""
        CUSTOMER INSIGHTS:
        - Total Customers with Bookings: {len(users_with_bookings)}
        - Repeat Customers: {repeat_customers} ({repeat_rate:.1f}%)
        - VIP Customers (3+ bookings): {vip_customers}
        - Average Rating: {avg_rating:.1f}/5
        """
    
    @staticmethod
    def _get_room_performance():
        """Get room performance metrics"""
        rooms = Room.query.all()
        room_performance = []
        
        for room in rooms:
            bookings_count = len(room.bookings)
            total_revenue = sum(booking.final_amount for booking in room.bookings)
            avg_rating = room.get_average_rating()
            
            room_performance.append(
                f"    - {room.name} ({room.room_type}): {bookings_count} bookings, ₹{total_revenue:,.2f}, {avg_rating:.1f}⭐"
            )
        
        return f"""
        ROOM PERFORMANCE:
        {chr(10).join(room_performance)}
        """
    
    @staticmethod
    def _get_offer_performance():
        """Get offer and promotion performance"""
        active_offers = Offer.query.filter_by(is_active=True).all()
        offer_performance = []
        
        for offer in active_offers:
            usage_rate = (offer.used_count / offer.usage_limit * 100) if offer.usage_limit else 0
            offer_performance.append(
                f"    - {offer.code}: {offer.used_count} uses ({usage_rate:.1f}% of limit)"
            )
        
        return f"""
        OFFER PERFORMANCE:
        {chr(10).join(offer_performance) if offer_performance else "    - No active offers"}
        """
    
    @staticmethod
    def _get_review_sentiments():
        """Get review sentiment analysis"""
        recent_reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(10).all()
        
        if not recent_reviews:
            return """
        RECENT REVIEW SENTIMENTS:
            - No recent approved reviews
            """
        
        review_summary = []
        for review in recent_reviews:
            sentiment = "Positive" if review.rating >= 4 else "Neutral" if review.rating == 3 else "Negative"
            review_summary.append(f"    - {review.rating}⭐ {sentiment}: {review.comment[:50]}...")
        
        return f"""
        RECENT REVIEW SENTIMENTS (Last 10):
        {chr(10).join(review_summary)}
        """
    
    @staticmethod
    def _get_alerts_and_issues():
        """Get system alerts and issues"""
        alerts = []
        
        # Low occupancy alert
        today = datetime.utcnow().date()
        occupied_rooms = Booking.query.filter(
            Booking.check_in <= today,
            Booking.check_out > today,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
        
        total_rooms = Room.query.count()
        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
        
        if occupancy_rate < 30:
            alerts.append("LOW OCCUPANCY ALERT: Current occupancy below 30%")
        
        # Pending reviews alert
        pending_reviews = Review.query.filter_by(is_approved=False).count()
        if pending_reviews > 5:
            alerts.append(f"REVIEW BACKLOG: {pending_reviews} reviews pending approval")
        
        # Expiring offers alert
        expiring_offers = Offer.query.filter(
            Offer.valid_until <= datetime.utcnow() + timedelta(days=7),
            Offer.is_active == True
        ).count()
        
        if expiring_offers > 0:
            alerts.append(f"EXPIRING OFFERS: {expiring_offers} offers expiring soon")
        
        return f"""
        ALERTS & ISSUES:
        {chr(10).join([f"    - {alert}" for alert in alerts]) if alerts else "    - No critical alerts"}
        """
    
    @staticmethod
    def _get_upcoming_events():
        """Get upcoming events and schedules"""
        # Next 7 days check-ins
        next_week = datetime.utcnow().date() + timedelta(days=7)
        upcoming_checkins = Booking.query.filter(
            Booking.check_in <= next_week,
            Booking.check_in >= datetime.utcnow().date(),
            Booking.status == 'confirmed'
        ).order_by(Booking.check_in).all()
        
        events = []
        for booking in upcoming_checkins[:5]:  # Show next 5
            events.append(f"    - {booking.check_in}: {booking.user.name} - {booking.room.name}")
        
        return f"""
        UPCOMING EVENTS (Next 7 Days):
        {chr(10).join(events) if events else "    - No upcoming check-ins"}
        """
    
    @staticmethod
    def build_admin_context_safe():
        """Safe version that handles errors gracefully"""
        try:
            return AdminChatbotContextBuilder.build_admin_context()
        except Exception as e:
            print(f"Error building admin context: {e}")
            return f"""
            HOTEL ROYAL ORCHID - ADMIN DASHBOARD DATA
            Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            
            BASIC OVERVIEW:
            - System temporarily unable to load detailed metrics
            - Please check database connection
        
            ALERTS:
            - Data loading issue detected
            """