from models.offer import Offer
from models.user import User
from models.booking import Booking
from datetime import datetime, date, timedelta
import random
import json

class SmartOfferEngine:
    """Enhanced intelligent offer recommendation engine"""
    
    @staticmethod
    def generate_personalized_offers(user, booking_data=None, room=None):
        """Generate personalized offers with better targeting using scoring system"""
        # Get all available offers
        all_offers = Offer.get_available_offers(user, booking_data, room)
        
        # Score and prioritize offers
        scored_offers = []
        for offer in all_offers:
            score = SmartOfferEngine._calculate_offer_score(offer, user, booking_data, room)
            scored_offers.append((offer, score))
        
        # Sort by score and return top offers
        scored_offers.sort(key=lambda x: x[1], reverse=True)
        return [offer for offer, score in scored_offers[:8]]  # Return top 8 offers
    
    @staticmethod
    def _calculate_offer_score(offer, user, booking_data, room):
        """Calculate comprehensive relevance score for an offer"""
        score = offer.priority * 10  # Base score from priority
        
        # User type matching (high weight)
        if offer.target_user_type != 'all' and user:
            user_match_score = SmartOfferEngine._calculate_user_match_score(offer, user)
            score += user_match_score
        
        # Booking context matching (medium weight)
        if booking_data:
            booking_match_score = SmartOfferEngine._calculate_booking_match_score(offer, booking_data)
            score += booking_match_score
        
        # Room type matching (high weight)
        if room and offer.target_rooms:
            room_match_score = SmartOfferEngine._calculate_room_match_score(offer, room)
            score += room_match_score
        
        # Season and timing matching (medium weight)
        timing_match_score = SmartOfferEngine._calculate_timing_match_score(offer, booking_data)
        score += timing_match_score
        
        # Bonus for auto-apply offers
        if offer.auto_apply:
            score += 15
        
        return max(score, 0)  # Ensure non-negative score
    
    @staticmethod
    def _calculate_user_match_score(offer, user):
        """Calculate score based on user type matching"""
        from models.booking import Booking
        
        if offer.target_user_type == 'all':
            return 10
        
        completed_bookings = Booking.query.filter_by(
            user_id=user.id, 
            status='completed'
        ).count()
        
        if offer.target_user_type == 'new_user' and completed_bookings == 0:
            return 25
        elif offer.target_user_type == 'returning_user' and completed_bookings >= 1:
            return 20
        elif offer.target_user_type == 'vip' and completed_bookings >= 3:
            return 30
        
        return -20  # Penalty for mismatch
    
    @staticmethod
    def _calculate_booking_match_score(offer, booking_data):
        """Calculate score based on booking context matching"""
        score = 0
        
        # Stay duration matching
        if booking_data.get('check_in') and booking_data.get('check_out'):
            nights = (booking_data['check_out'] - booking_data['check_in']).days
            
            # Minimum stay requirement
            if offer.min_stay_nights and nights >= offer.min_stay_nights:
                score += 15
            elif offer.min_stay_nights and nights < offer.min_stay_nights:
                score -= 10
            
            # Maximum stay limit
            if offer.max_stay_nights and nights <= offer.max_stay_nights:
                score += 10
            elif offer.max_stay_nights and nights > offer.max_stay_nights:
                score -= 10
        
        # Amount matching
        total_amount = booking_data.get('total_amount', 0)
        if offer.min_amount and total_amount >= offer.min_amount:
            score += 12
        elif offer.min_amount and total_amount < offer.min_amount:
            score -= 8
        
        return score
    
    @staticmethod
    def _calculate_room_match_score(offer, room):
        """Calculate score based on room matching"""
        try:
            target_data = json.loads(offer.target_rooms)
            room_types = target_data.get('room_types', [])
            room_ids = target_data.get('room_ids', [])
            
            # Exact room ID match (highest priority)
            if room_ids and room.id in room_ids:
                return 30
            
            # Room type match
            if room_types and room.room_type in room_types:
                return 25
            
            # No match but targeting is specified
            if room_types or room_ids:
                return -15
                
        except:
            pass
        
        return 0  # No room targeting specified
    
    @staticmethod
    def _calculate_timing_match_score(offer, booking_data):
        """Calculate score based on season and timing matching"""
        score = 0
        current_date = date.today()
        
        # Season matching
        if offer.season_type != 'all':
            season_match = SmartOfferEngine._check_season_match(offer.season_type, booking_data)
            score += 15 if season_match else -10
        
        # Day of week matching
        if offer.day_of_week != 'all' and booking_data and booking_data.get('check_in'):
            day_match = SmartOfferEngine._check_day_match(offer.day_of_week, booking_data['check_in'])
            score += 12 if day_match else -8
        
        # Advance booking matching
        if booking_data and booking_data.get('check_in'):
            days_in_advance = (booking_data['check_in'] - current_date).days
            
            # Minimum advance days
            if offer.advance_booking_days > 0:
                if days_in_advance >= offer.advance_booking_days:
                    score += 10
                else:
                    score -= 8
            
            # Maximum advance days
            if offer.max_advance_booking_days:
                if days_in_advance <= offer.max_advance_booking_days:
                    score += 8
                else:
                    score -= 6
        
        # Last-minute deals bonus
        if booking_data and booking_data.get('check_in'):
            days_until_checkin = (booking_data['check_in'] - current_date).days
            if days_until_checkin <= 3 and offer.advance_booking_days <= 3:
                score += 20  # High bonus for last-minute matching
        
        return score
    
    @staticmethod
    def _check_season_match(season_type, booking_data):
        """Check if booking matches season type"""
        if not booking_data or not booking_data.get('check_in'):
            return False
        
        check_in = booking_data['check_in']
        month = check_in.month
        
        if season_type == 'peak':
            return month in [12, 1, 6, 7]  # Dec, Jan, Jun, Jul
        elif season_type == 'off_peak':
            return month in [2, 3, 9, 10]  # Feb, Mar, Sep, Oct
        elif season_type == 'festival':
            return month in [10, 11, 12]  # Festival months
        
        return True
    
    @staticmethod
    def _check_day_match(day_type, check_in_date):
        """Check if booking day matches day type"""
        weekday = check_in_date.weekday()
        
        if day_type == 'weekend':
            return weekday >= 5
        elif day_type == 'weekday':
            return weekday < 5
        
        return True
    
    @staticmethod
    def get_offer_analytics():
        """Get comprehensive analytics about offer performance"""
        from models.offer import Offer
        from models.booking import Booking
        
        offers = Offer.query.all()
        analytics = []
        
        for offer in offers:
            # Calculate usage rate
            usage_rate = (offer.used_count / offer.usage_limit * 100) if offer.usage_limit else 0
            
            # Get recent usage (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_bookings = Booking.query.filter(
                Booking.coupon_code == offer.code,
                Booking.created_at >= thirty_days_ago
            ).count()
            
            # Calculate revenue impact
            revenue_impact = SmartOfferEngine._calculate_revenue_impact(offer)
            
            # Calculate conversion rate
            conversion_rate = SmartOfferEngine._calculate_conversion_rate(offer)
            
            analytics.append({
                'offer': offer,
                'usage_rate': round(usage_rate, 1),
                'recent_usage': recent_bookings,
                'effectiveness': SmartOfferEngine._calculate_effectiveness(offer),
                'revenue_impact': revenue_impact,
                'conversion_rate': conversion_rate,
                'status': SmartOfferEngine._get_offer_status(offer)
            })
        
        return analytics
    
    @staticmethod
    def _calculate_revenue_impact(offer):
        """Calculate the revenue impact of an offer"""
        from models.booking import Booking
        
        # Get bookings that used this offer
        offer_bookings = Booking.query.filter_by(coupon_code=offer.code).all()
        
        if not offer_bookings:
            return 0
        
        total_discount = sum(booking.discount_amount for booking in offer_bookings)
        total_revenue = sum(booking.final_amount for booking in offer_bookings)
        
        # Calculate net revenue impact (revenue - discounts)
        net_revenue = total_revenue - total_discount
        
        return {
            'total_bookings': len(offer_bookings),
            'total_discount': total_discount,
            'total_revenue': total_revenue,
            'net_revenue': net_revenue,
            'average_discount_per_booking': total_discount / len(offer_bookings) if offer_bookings else 0
        }
    
    @staticmethod
    def _calculate_conversion_rate(offer):
        """Calculate offer conversion rate"""
        from models.booking import Booking
        
        # Count how many times the offer was applied vs how many times it was available
        # This is a simplified version - in production, you'd track offer views/impressions
        
        applied_count = Booking.query.filter_by(coupon_code=offer.code).count()
        
        # For demo purposes, we'll estimate available count based on active period
        if offer.usage_limit:
            available_count = offer.usage_limit
        else:
            # Estimate based on days active
            days_active = (datetime.utcnow() - offer.created_at).days
            available_count = max(days_active * 10, 100)  # Rough estimate
        
        conversion_rate = (applied_count / available_count * 100) if available_count > 0 else 0
        return round(conversion_rate, 1)
    
    @staticmethod
    def _calculate_effectiveness(offer):
        """Calculate comprehensive offer effectiveness score (0-100)"""
        effectiveness = 0
        
        # Usage component (40%)
        if offer.usage_limit:
            usage_component = min((offer.used_count / offer.usage_limit) * 40, 40)
        else:
            usage_component = min(offer.used_count * 2, 40)  # Cap at 40
        
        # Recency component (30%)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_usage = Booking.query.filter(
            Booking.coupon_code == offer.code,
            Booking.created_at >= thirty_days_ago
        ).count()
        
        recency_component = min(recent_usage * 3, 30)  # Up to 30 points
        
        # Time remaining component (30%)
        if offer.valid_until > datetime.utcnow():
            total_duration = (offer.valid_until - offer.created_at).days
            remaining_duration = (offer.valid_until - datetime.utcnow()).days
            time_component = (remaining_duration / total_duration) * 30 if total_duration > 0 else 0
        else:
            time_component = 0
        
        effectiveness = usage_component + recency_component + time_component
        return round(effectiveness, 1)
    
    @staticmethod
    def _get_offer_status(offer):
        """Get human-readable offer status"""
        now = datetime.utcnow()
        
        if not offer.is_active:
            return "Inactive"
        elif offer.valid_until < now:
            return "Expired"
        elif offer.usage_limit and offer.used_count >= offer.usage_limit:
            return "Limit Reached"
        elif offer.valid_from > now:
            return "Scheduled"
        else:
            return "Active"
    
    @staticmethod
    def generate_offer_insights():
        """Generate business insights from offer data"""
        analytics = SmartOfferEngine.get_offer_analytics()
        
        insights = {
            'top_performing_offers': [],
            'underperforming_offers': [],
            'recommendations': []
        }
        
        for data in analytics:
            if data['effectiveness'] >= 70:
                insights['top_performing_offers'].append(data)
            elif data['effectiveness'] <= 30 and data['offer'].is_active:
                insights['underperforming_offers'].append(data)
        
        # Generate recommendations
        if insights['underperforming_offers']:
            insights['recommendations'].append(
                f"Consider updating or deactivating {len(insights['underperforming_offers'])} underperforming offers"
            )
        
        active_offers = [data for data in analytics if data['status'] == 'Active']
        if len(active_offers) < 3:
            insights['recommendations'].append(
                "Consider creating more active offers to increase booking incentives"
            )
        
        return insights
    
    @staticmethod
    def create_dynamic_offer(user, booking_trends):
        """Create dynamic offers based on booking trends and user behavior"""
        # Analyze booking trends to create targeted offers
        if booking_trends.get('low_occupancy_days'):
            return SmartOfferEngine._create_occupancy_boost_offer(booking_trends['low_occupancy_days'])
        
        if booking_trends.get('user_preferences'):
            return SmartOfferEngine._create_preference_based_offer(user, booking_trends['user_preferences'])
        
        return None
    
    @staticmethod
    def _create_occupancy_boost_offer(low_occupancy_days):
        """Create offers to boost occupancy on specific days"""
        # This would create dynamic offers for low-occupancy periods
        # Implementation would depend on your specific business logic
        pass
    
    @staticmethod
    def _create_preference_based_offer(user, user_preferences):
        """Create offers based on user preferences"""
        # This would create offers matching user's preferred room types, seasons, etc.
        # Implementation would depend on your specific business logic
        pass
    
    @staticmethod
    def get_offer_suggestions(user, booking_history):
        """Get personalized offer suggestions for a user"""
        suggestions = []
        
        # Analyze user's booking patterns
        if booking_history:
            avg_booking_value = sum(booking.final_amount for booking in booking_history) / len(booking_history)
            preferred_room_types = list(set(booking.room.room_type for booking in booking_history))
            
            # Suggest offers based on user's spending pattern
            if avg_booking_value > 10000:  # High-value customer
                suggestions.append("Consider creating VIP exclusive offers for high-value customers")
            
            # Suggest room-type specific offers
            if preferred_room_types:
                suggestions.append(f"Create targeted offers for {', '.join(preferred_room_types)} rooms")
        
        return suggestions
    
    @staticmethod
    def predict_offer_success(offer, user_segment):
        """Predict the potential success of an offer for a user segment"""
        # This is a simplified prediction model
        # In production, you'd use machine learning with historical data
        
        base_success_rate = 0.3  # 30% base success rate
        
        # Adjust based on discount value
        if offer.discount_type == 'percentage' and offer.discount_value >= 20:
            base_success_rate += 0.2
        elif offer.discount_type == 'fixed' and offer.discount_value >= 2000:
            base_success_rate += 0.15
        
        # Adjust based on user segment
        if user_segment == 'new_user':
            base_success_rate += 0.1
        elif user_segment == 'vip':
            base_success_rate += 0.25
        
        # Adjust based on season
        current_month = datetime.now().month
        if offer.season_type != 'all':
            if SmartOfferEngine._check_season_match(offer.season_type, {'check_in': date.today()}):
                base_success_rate += 0.1
            else:
                base_success_rate -= 0.15
        
        return min(max(base_success_rate, 0), 1)  # Clamp between 0 and 1

    @staticmethod
    def generate_ai_offers_batch(user_segment, count=5):
        """Generate multiple AI-powered offers for a user segment"""
        from utils.ai_service import OpenRouterAI
    
        ai_service = OpenRouterAI()
        offers = []
    
        prompt = f"""
        Generate {count} compelling hotel offers for {user_segment} customers.
    
        Requirements for each offer:
        - Catchy title (max 5 words)
        - Brief description (max 2 sentences)
        - Appropriate discount (10-30%)
        - Clear target audience
        - Season/occasion relevance
    
        Return as JSON array with: title, description, discount, target, season
        """
    
        try:
            response = ai_service._make_request(prompt)
            # Parse the AI response and create offer objects
            # Implementation depends on AI response format
            return offers
        except Exception as e:
            print(f"AI offer generation failed: {e}")
            return []

# Add this class to utils/offer_engine.py
class AIOfferEnhancer:
    """AI-powered offer enhancement system"""
    
    @staticmethod
    def generate_personalized_offer(user, room, booking_data=None):
        """Generate AI-powered personalized offer"""
        from utils.ai_service import OpenRouterAI
        
        # Build user context
        user_context = f"""
        User: {user.name}
        Previous Stays: {len(user.bookings)}
        Average Spending: {sum(b.final_amount for b in user.bookings) / len(user.bookings) if user.bookings else 0}
        Preferred Room Type: {max(set([b.room.room_type for b in user.bookings]), key=[b.room.room_type for b in user.bookings].count) if user.bookings else 'None'}
        """
        
        # Build offer context
        offer_context = f"""
        Target Room: {room.name} ({room.room_type})
        Room Price: ₹{room.price}/night
        Room Capacity: {room.capacity}
        Amenities: {room.amenities}
        """
        
        if booking_data:
            offer_context += f"""
            Booking Details: {booking_data.get('check_in')} to {booking_data.get('check_out')}
            Total Nights: {booking_data.get('nights', 1)}
            Total Amount: ₹{booking_data.get('total_amount', 0)}
            """
        
        ai_service = OpenRouterAI()
        prompt = f"""
        Create a highly personalized hotel offer for this guest:
        
        GUEST PROFILE:
        {user_context}
        
        OFFER CONTEXT:
        {offer_context}
        
        Generate a compelling offer that includes:
        1. A catchy, personalized title
        2. A persuasive description targeting this specific guest's preferences
        3. 2-3 key benefits that would appeal to this guest
        4. A sense of urgency and exclusivity
        
        Format as JSON with: title, description, benefits (array), call_to_action
        """
        
        return ai_service._make_request(prompt)
    
    @staticmethod
    def optimize_offer_copy(offer, target_audience):
        """Optimize existing offer copy using AI"""
        from utils.ai_service import OpenRouterAI
        
        ai_service = OpenRouterAI()
        prompt = f"""
        Optimize this hotel offer copy for better conversion:
        
        CURRENT OFFER:
        Name: {offer.name}
        Description: {offer.description}
        Discount: {offer.discount_value}{'%' if offer.discount_type == 'percentage' else '₹'}
        Target: {target_audience}
        
        Create improved versions that are:
        - More compelling and persuasive
        - Better targeted to {target_audience}
        - Create stronger urgency
        - Highlight benefits more effectively
        
        Provide 3 improved versions with explanations.
        """
        
        return ai_service._make_request(prompt)