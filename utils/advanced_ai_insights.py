# utils/advanced_ai_insights.py
import json
from datetime import datetime, timedelta
from flask import current_app
from app import db
from models.user import User
from models.booking import Booking
from models.room import Room
from models.offer import Offer
from models.review import Review
from models.payment import Payment
from utils.ai_service import OpenRouterAI

class AdvancedAIAnalytics:
    """Advanced AI-powered analytics and insights system"""
    
    @staticmethod
    def get_comprehensive_business_data(days=30):
        """Get comprehensive business data for AI analysis"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Basic metrics
        total_rooms = Room.query.count()
        available_rooms = Room.query.filter_by(status='available').count()
        total_bookings = Booking.query.count()
        total_users = User.query.count()
        
        # Time-based metrics
        recent_bookings = Booking.query.filter(
            Booking.created_at >= start_date
        ).all()
        
        recent_payments = Payment.query.filter(
            Payment.created_at >= start_date,
            Payment.payment_status == 'completed'
        ).all()
        
        recent_reviews = Review.query.filter(
            Review.created_at >= start_date,
            Review.is_approved == True
        ).all()
        
        # Revenue calculations
        total_revenue = sum(p.amount for p in recent_payments)
        avg_booking_value = total_revenue / len(recent_bookings) if recent_bookings else 0
        
        # Occupancy calculations
        occupied_room_nights = sum(
            booking.total_nights for booking in recent_bookings 
            if booking.status in ['confirmed', 'checked_in', 'completed']
        )
        total_room_nights = total_rooms * days
        occupancy_rate = (occupied_room_nights / total_room_nights * 100) if total_room_nights > 0 else 0
        
        # Customer metrics
        repeat_customers = User.query.filter(
            User.bookings.any(Booking.created_at >= start_date)
        ).count()
        
        new_customers = User.query.filter(
            User.created_at >= start_date
        ).count()
        
        # Room performance
        room_performance = []
        for room in Room.query.all():
            room_bookings = [b for b in room.bookings if b.created_at >= start_date]
            room_revenue = sum(b.final_amount for b in room_bookings)
            room_occupancy = len(room_bookings) / days * 100
            
            room_performance.append({
                'name': room.name,
                'type': room.room_type,
                'bookings': len(room_bookings),
                'revenue': room_revenue,
                'occupancy': room_occupancy,
                'rating': room.get_average_rating()
            })
        
        # Offer performance
        offer_performance = []
        for offer in Offer.query.all():
            offer_bookings = Booking.query.filter_by(coupon_code=offer.code).filter(
                Booking.created_at >= start_date
            ).all()
            
            offer_performance.append({
                'code': offer.code,
                'name': offer.name,
                'usage': len(offer_bookings),
                'discount_given': sum(b.discount_amount for b in offer_bookings),
                'revenue_generated': sum(b.final_amount for b in offer_bookings)
            })
        
        # Seasonal trends
        monthly_trends = AdvancedAIAnalytics._get_monthly_trends()
        
        # Customer segmentation
        customer_segments = AdvancedAIAnalytics._get_customer_segments()
        
        return {
            'time_period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days': days
            },
            'basic_metrics': {
                'total_rooms': total_rooms,
                'available_rooms': available_rooms,
                'total_bookings': total_bookings,
                'total_users': total_users,
                'occupancy_rate': round(occupancy_rate, 1),
                'total_revenue': total_revenue,
                'average_booking_value': round(avg_booking_value, 2)
            },
            'customer_metrics': {
                'repeat_customers': repeat_customers,
                'new_customers': new_customers,
                'repeat_rate': (repeat_customers / total_users * 100) if total_users > 0 else 0,
                'average_rating': db.session.query(db.func.avg(Review.rating))
                    .filter(Review.is_approved == True, Review.created_at >= start_date)
                    .scalar() or 0
            },
            'performance_data': {
                'room_performance': room_performance,
                'offer_performance': offer_performance,
                'recent_bookings_count': len(recent_bookings),
                'recent_reviews_count': len(recent_reviews)
            },
            'trends': monthly_trends,
            'customer_segments': customer_segments,
            'revenue_breakdown': AdvancedAIAnalytics._get_revenue_breakdown(start_date, end_date)
        }
    
    @staticmethod
    def _get_monthly_trends():
        """Get monthly booking and revenue trends"""
        trends = []
        for i in range(6):  # Last 6 months
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            monthly_bookings = Booking.query.filter(
                Booking.created_at >= month_start,
                Booking.created_at <= month_end
            ).count()
            
            monthly_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                Payment.created_at >= month_start,
                Payment.created_at <= month_end,
                Payment.payment_status == 'completed'
            ).scalar() or 0
            
            trends.append({
                'month': month_start.strftime('%b %Y'),
                'bookings': monthly_bookings,
                'revenue': monthly_revenue
            })
        
        return list(reversed(trends))
    
    @staticmethod
    def _get_customer_segments():
        """Segment customers by behavior and value"""
        segments = {
            'vip': {'count': 0, 'total_spent': 0, 'avg_rating': 0},
            'frequent': {'count': 0, 'total_spent': 0, 'avg_rating': 0},
            'occasional': {'count': 0, 'total_spent': 0, 'avg_rating': 0},
            'new': {'count': 0, 'total_spent': 0, 'avg_rating': 0}
        }
        
        for user in User.query.all():
            user_bookings = user.bookings
            total_spent = sum(b.final_amount for b in user_bookings)
            booking_count = len(user_bookings)
            avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(user_id=user.id).scalar() or 0
            
            if booking_count >= 5 and total_spent > 50000:
                segment = 'vip'
            elif booking_count >= 3:
                segment = 'frequent'
            elif booking_count >= 1:
                segment = 'occasional'
            else:
                segment = 'new'
            
            segments[segment]['count'] += 1
            segments[segment]['total_spent'] += total_spent
            segments[segment]['avg_rating'] = ((segments[segment]['avg_rating'] * (segments[segment]['count'] - 1)) + avg_rating) / segments[segment]['count'] if segments[segment]['count'] > 0 else 0
        
        return segments
    
    @staticmethod
    def _get_revenue_breakdown(start_date, end_date):
        """Get detailed revenue breakdown"""
        room_types = db.session.query(Room.room_type).distinct().all()
        breakdown = {}
        
        for room_type, in room_types:
            room_revenue = db.session.query(db.func.sum(Booking.final_amount)).join(Room).filter(
                Room.room_type == room_type,
                Booking.created_at >= start_date,
                Booking.created_at <= end_date
            ).scalar() or 0
            
            breakdown[room_type] = room_revenue
        
        return breakdown
    
    @staticmethod
    def generate_strategic_insights(business_data):
        """Generate strategic business insights using AI"""
        ai_service = OpenRouterAI()
        
        prompt = f"""
        As a senior hotel business strategist, analyze this comprehensive hotel data and provide strategic insights:

        COMPREHENSIVE BUSINESS DATA:
        {json.dumps(business_data, indent=2, default=str)}

        Provide a detailed strategic analysis in JSON format with these sections:

        1. "executive_summary" (brief overview of business health)
        2. "performance_analysis" (detailed analysis of key metrics)
        3. "growth_opportunities" (3-5 specific growth opportunities with potential impact)
        4. "risk_assessment" (3-5 potential risks with severity levels)
        5. "strategic_recommendations" (5-7 actionable recommendations with priority levels)
        6. "financial_forecast" (revenue and occupancy forecasts for next quarter)
        7. "competitive_advantages" (key strengths to leverage)
        8. "customer_insights" (behavior patterns and preferences)
        9. "operational_efficiency" (areas for operational improvement)
        10. "technology_recommendations" (tech improvements for business growth)

        Be data-driven, specific, and actionable. Use metrics to support your insights.
        """
        
        return ai_service._make_request(prompt)
    
    @staticmethod
    def generate_predictive_insights():
        """Generate predictive insights for future performance"""
        # This would integrate with machine learning models in production
        # For now, we'll use rule-based predictions
        
        recent_bookings = Booking.query.filter(
            Booking.created_at >= datetime.utcnow() - timedelta(days=90)
        ).all()
        
        # Simple trend analysis
        monthly_growth = AdvancedAIAnalytics._calculate_growth_trends()
        
        predictions = {
            'next_month_occupancy': monthly_growth.get('predicted_occupancy', 0),
            'next_month_revenue': monthly_growth.get('predicted_revenue', 0),
            'seasonal_trends': AdvancedAIAnalytics._get_seasonal_patterns(),
            'high_demand_periods': AdvancedAIAnalytics._identify_high_demand_periods(),
            'opportunity_periods': AdvancedAIAnalytics._identify_opportunity_periods()
        }
        
        return predictions
    
    @staticmethod
    def _calculate_growth_trends():
        """Calculate growth trends for predictions"""
        # Simplified trend calculation
        recent_months = []
        for i in range(3):
            month = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            bookings = Booking.query.filter(
                db.extract('month', Booking.created_at) == month.month,
                db.extract('year', Booking.created_at) == month.year
            ).count()
            
            revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                db.extract('month', Payment.created_at) == month.month,
                db.extract('year', Payment.created_at) == month.year,
                Payment.payment_status == 'completed'
            ).scalar() or 0
            
            recent_months.append({'bookings': bookings, 'revenue': revenue})
        
        # Simple average growth (in production, use proper forecasting)
        avg_growth = 1.05  # 5% growth assumption
        
        return {
            'predicted_occupancy': min(95, recent_months[0].get('bookings', 0) * avg_growth),
            'predicted_revenue': recent_months[0].get('revenue', 0) * avg_growth
        }
    
    @staticmethod
    def _get_seasonal_patterns():
        """Identify seasonal booking patterns"""
        # This would be more sophisticated in production
        return {
            'peak_season': ['December', 'January', 'June', 'July'],
            'off_peak': ['February', 'September'],
            'festive_periods': ['October', 'November']
        }
    
    @staticmethod
    def _identify_high_demand_periods():
        """Identify periods of high demand"""
        return [
            'Christmas and New Year period (Dec 20 - Jan 5)',
            'Summer vacation (June - July)',
            'Festival season (October)'
        ]
    
    @staticmethod
    def _identify_opportunity_periods():
        """Identify periods with opportunity for improvement"""
        return [
            'February - March (typically lower occupancy)',
            'Weekday bookings (currently underutilized)',
            'Last-minute bookings segment'
        ]