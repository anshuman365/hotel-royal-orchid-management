# ai_service.py - UPDATED VERSION
import requests
import json
from flask import current_app
from app import db
from models.user import User
from models.booking import Booking
from models.room import Room
from models.offer import Offer
from models.review import Review
from datetime import datetime
import logging
from utils.admin_chatbot_context import AdminChatbotContextBuilder

# Set up logging
logger = logging.getLogger(__name__)

class OpenRouterAI:
    def __init__(self):
        self.api_key = current_app.config.get('OPENROUTER_API_KEY')
        self.base_url = current_app.config.get('OPENROUTER_BASE_URL')
        self.model = current_app.config.get('OPENROUTER_MODEL')
        self.alternative_models = [
            'google/palm-2-chat-bison',
            'meta-llama/llama-2-13b-chat', 
            'openai/gpt-3.5-turbo',
            'microsoft/wizardlm-2-8x22b'
        ]
    
    def analyze_review_sentiment(self, review_text, rating):
        """Analyze review sentiment and extract insights"""
        prompt = f"""
        Analyze this hotel review and provide a comprehensive analysis in JSON format:

        Review Text: "{review_text}"
        Rating: {rating}/5

        Provide analysis with these exact keys:
        - "sentiment" (positive/negative/neutral)
        - "sentiment_score" (1-10)
        - "key_positive_points" (array of strings)
        - "key_negative_points" (array of strings) 
        - "improvement_suggestions" (array of strings)
        - "urgency_level" (high/medium/low)
        - "summary" (brief summary of the review)
        - "response_suggestions" (array of suggested response points)

        Be objective and thorough.
        """
        
        return self._make_request(prompt)
    
    def generate_management_response(self, review, sentiment_analysis):
        """Generate professional management response"""
        prompt = f"""
        As the manager of Hotel Royal Orchid, write a professional response to this guest review:

        GUEST REVIEW:
        Rating: {review.rating}/5
        Comment: "{review.comment}"
        
        ANALYSIS:
        {json.dumps(sentiment_analysis, indent=2)}

        Requirements:
        - Thank the guest by name (use placeholder if needed)
        - Acknowledge their specific points from the analysis
        - Address any concerns professionally
        - Sound genuine and caring
        - Invite them back
        - Keep it under 150 words
        - Use professional hotel management tone

        Provide only the response text, no additional formatting.
        """
        
        return self._make_request(prompt)
    
    def chat_with_context(self, user_message, user_context, chat_history=None):
        """Chat with AI using user context and database knowledge"""
        
        system_prompt = f"""
        You are ROY, the AI concierge for Hotel Royal Orchid. You have access to the following guest information:

        GUEST PROFILE:
        {user_context}

        HOTEL KNOWLEDGE:
        - We are Hotel Royal Orchid, a luxury 5-star hotel
        - We have various room types: Standard, Deluxe, Suite, Presidential
        - Amenities: Spa, Pool, Restaurant, Conference rooms, Gym
        - Location: Prime city center location
        - Check-in: 3:00 PM, Check-out: 11:00 AM

        YOUR ROLE:
        - Be friendly, professional, and helpful
        - Use the guest's information to provide personalized responses
        - Help with bookings, inquiries, offers, and general information
        - If you don't know something, offer to connect them with human staff
        - Keep responses concise but thorough
        - Always maintain a luxury hotel service standard

        Current date: {datetime.now().strftime('%Y-%m-%d')}
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history if available
        if chat_history:
            messages.extend(chat_history)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        return self._make_request(messages, use_messages=True)
    
    def generate_personalized_offer_copy(self, user, room_type, discount_info):
        """Generate personalized offer copy"""
        prompt = f"""
        Create compelling personalized offer text for a hotel guest:

        GUEST: {user.name}
        ROOM TYPE: {room_type}
        OFFER DETAILS: {discount_info}

        Generate:
        1. A catchy, personalized offer title (max 6 words)
        2. Engaging description (max 80 words) highlighting benefits for this specific guest
        3. 2-3 bullet points of key benefits
        4. A strong call-to-action

        Make it feel exclusive, personal, and exciting. Format as JSON with keys: title, description, bullet_points, call_to_action.
        """
        
        return self._make_request(prompt)
    
    def get_business_insights(self, business_data):
        """Generate business insights from hotel data"""
        prompt = f"""
        As a hotel business analyst, analyze this data and provide actionable insights:

        BUSINESS DATA:
        {json.dumps(business_data, indent=2)}

        Provide analysis in JSON format with:
        - "key_insights" (array of 3-5 main insights)
        - "recommendations" (array of 3-5 actionable recommendations)
        - "opportunities" (array of 2-3 growth opportunities)
        - "risks" (array of 2-3 potential risks to address)
        - "summary" (brief executive summary)

        Be data-driven and practical in your analysis.
        """
        
        return self._make_request(prompt)
    
    def _make_request(self, prompt, use_messages=False, model_override=None):
        """Make request to OpenRouter API with enhanced error handling"""
        if not self.api_key or self.api_key == 'your-openrouter-api-key-here':
            logger.warning("OpenRouter API key not configured, using fallback")
            return self._get_fallback_response(prompt, use_messages)
        
        model_to_use = model_override or self.model
        
        try:
            if use_messages:
                data = {
                    "model": model_to_use,
                    "messages": prompt,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            else:
                data = {
                    "model": model_to_use,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            
            logger.info(f"Sending request to OpenRouter API with model: {model_to_use}")
            
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://hotelroyalorchid.com",
                    "X-Title": "Hotel Royal Orchid AI"
                },
                json=data,
                timeout=30
            )
            
            logger.info(f"OpenRouter API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_msg = f"AI service error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # Try alternative models if primary fails
                if response.status_code == 404 and not model_override:
                    return self._try_alternative_models(prompt, use_messages)
                
                return f"AI service temporarily unavailable. Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error("OpenRouter API request timeout")
            return "AI service is currently experiencing high load. Please try again shortly."
        except requests.exceptions.ConnectionError:
            logger.error("OpenRouter API connection error")
            return "Unable to connect to AI service. Please check your internet connection."
        except Exception as e:
            logger.error(f"OpenRouter API unexpected error: {str(e)}")
            return self._get_fallback_response(prompt, use_messages)
    
    def _try_alternative_models(self, prompt, use_messages=False):
        """Try alternative models if primary model fails"""
        logger.info("Trying alternative models...")
        
        for alt_model in self.alternative_models:
            try:
                logger.info(f"Trying model: {alt_model}")
                result = self._make_request(prompt, use_messages, model_override=alt_model)
                if not result.startswith("AI service temporarily unavailable"):
                    logger.info(f"Success with alternative model: {alt_model}")
                    return result
            except Exception as e:
                logger.warning(f"Alternative model {alt_model} also failed: {str(e)}")
                continue
        
        logger.error("All models failed, using fallback")
        return self._get_fallback_response(prompt, use_messages)
    
    def _get_fallback_response(self, prompt, use_messages=False):
        """Enhanced fallback responses when AI service is unavailable"""
        if use_messages:
            user_message = prompt[-1]["content"] if prompt and len(prompt) > 0 else "Hello"
        else:
            user_message = prompt.lower()
        
        # Enhanced rule-based fallback responses
        fallback_responses = {
            "hello": "Hello! I'm ROY, your AI concierge at Hotel Royal Orchid. How can I assist you today?",
            "hi": "Hello! I'm ROY, your AI concierge. How can I help you with your stay at Hotel Royal Orchid?",
            "booking": "I can help you with bookings! Please visit our booking page or tell me your preferred dates and room type.",
            "book": "I can assist with room bookings. What dates are you interested in?",
            "room": "We have Standard, Deluxe, Suite, and Presidential rooms. Which type interests you?",
            "offer": "Check our offers page for current promotions! We have special discounts for returning guests.",
            "review": "I can help you with reviews. You can write a review for your past stays in the reviews section.",
            "upcoming": "To check your upcoming bookings, please visit the 'My Bookings' section in your account.",
            "upcoming bookings": "You can view all your upcoming bookings in the 'My Bookings' section of your account.",
            "special offers": "We have various offers available! Check the 'Offers' section or tell me your preferences for personalized recommendations.",
            "what special offers": "We have seasonal discounts, early bird offers, and loyalty rewards. Visit our Offers page for details!",
            "default": "Thank you for your message. For detailed assistance, please contact our front desk at +91-XXX-XXXX or visit the relevant section in your account."
        }
        
        # Check for keywords in user message
        user_message_lower = user_message.lower()
        for key, response in fallback_responses.items():
            if key in user_message_lower:
                return response
        
        return fallback_responses["default"]


class ChatbotContextBuilder:
    """Builds context for the chatbot based on user data"""
    
    @staticmethod
    def build_user_context(user):
        """Build comprehensive user context for chatbot"""
        if not user:
            return "Guest user (not logged in)"
        
        # Get user's bookings
        bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
        reviews = Review.query.filter_by(user_id=user.id).all()
        
        # Build context string
        context = f"""
        Guest Information:
        - Name: {user.name}
        - Email: {user.email}
        - Phone: {user.phone or 'Not provided'}
        - Member since: {user.created_at.strftime('%Y-%m-%d')}
        
        Booking History:
        {ChatbotContextBuilder._format_bookings(bookings)}
        
        Review History:
        {ChatbotContextBuilder._format_reviews(reviews)}
        
        Loyalty Status: {ChatbotContextBuilder._get_loyalty_status(len(bookings))}
        """
        
        return context
    
    @staticmethod
    def _format_bookings(bookings):
        if not bookings:
            return "No past bookings"
        
        formatted = []
        for booking in bookings[:5]:  # Last 5 bookings
            status_emoji = {
                'completed': '✅',
                'confirmed': '🟢',
                'pending': '🟡',
                'cancelled': '🔴'
            }.get(booking.status, '⚪')
            
            formatted.append(
                f"- {status_emoji} {booking.check_in} to {booking.check_out} "
                f"({booking.total_nights} nights) - {booking.room.room_type} - ₹{booking.final_amount}"
            )
        
        return "\n".join(formatted)
    
    @staticmethod
    def _format_reviews(reviews):
        if not reviews:
            return "No reviews submitted"
        
        formatted = []
        for review in reviews:
            stars = '⭐' * review.rating
            formatted.append(f"- {stars} {review.comment[:50]}...")
        
        return "\n".join(formatted)
    
    @staticmethod
    def _get_loyalty_status(booking_count):
        if booking_count >= 10:
            return "VIP Guest"
        elif booking_count >= 5:
            return "Frequent Guest"
        elif booking_count >= 1:
            return "Returning Guest"
        else:
            return "New Guest"
    
    @staticmethod
    def get_available_offers_context():
        """Get context about available offers"""
        offers = Offer.query.filter_by(is_active=True, is_public=True).all()
        
        if not offers:
            return "No current offers available"
        
        formatted = []
        for offer in offers:
            formatted.append(
                f"- {offer.code}: {offer.name} - {offer.discount_value}"
                f"{'%' if offer.discount_type == 'percentage' else '₹'} off"
            )
        
        return "Current Offers:\n" + "\n".join(formatted)
    
    @staticmethod
    def get_rooms_context():
        """Get context about available rooms"""
        rooms = Room.query.filter_by(status='available').all()
        
        formatted = []
        for room in rooms:
            formatted.append(
                f"- {room.room_type}: {room.name} - ₹{room.price}/night - "
                f"Capacity: {room.capacity} - Amenities: {room.amenities}"
            )
        
        return "Available Rooms:\n" + "\n".join(formatted)

# Update the AdminAIService class in ai_service.py
class AdminAIService:
    """AI service specifically for admin/staff users with full data access"""
    
    def __init__(self):
        self.ai_service = OpenRouterAI()
    
    def chat_with_business_context(self, user_message, user, chat_history=None):
        """Chat with full business data access for admin users"""
        
        # Build comprehensive admin context
        admin_context = AdminChatbotContextBuilder.build_admin_context()
        
        system_prompt = f"""
        You are ROY-ADMIN, the AI business intelligence assistant for Hotel Royal Orchid management.

        ROLE: You are speaking with {user.name} ({user.role.upper()}) who has full administrative access.

        AVAILABLE BUSINESS DATA:
        {admin_context}

        YOUR CAPABILITIES:
        - Access and analyze all business data in real-time
        - Provide strategic business insights and recommendations
        - Identify trends, opportunities, and risks
        - Generate reports and forecasts
        - Suggest operational improvements
        - Analyze financial performance
        - Monitor customer satisfaction
        - Track room and offer performance

        RESPONSE GUIDELINES:
        - Be highly analytical and data-driven
        - Reference specific metrics and numbers from the available data
        - Provide actionable insights and recommendations
        - Highlight urgent issues and opportunities
        - Use professional business language
        - Support claims with data evidence
        - Suggest specific actions for improvement

        Current date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history if available
        if chat_history:
            messages.extend(chat_history)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        return self.ai_service._make_request(messages, use_messages=True)
    
    def generate_business_report(self, report_type="weekly"):
        """Generate comprehensive business reports"""
        from utils.advanced_ai_insights import AdvancedAIAnalytics
        
        business_data = AdvancedAIAnalytics.get_comprehensive_business_data(30)
        
        prompt = f"""
        Generate a {report_type} business intelligence report for Hotel Royal Orchid:

        BUSINESS DATA:
        {json.dumps(business_data, indent=2, default=str)}

        Report Structure:
        1. Executive Summary
        2. Key Performance Indicators
        3. Financial Analysis
        4. Operational Performance
        5. Customer Insights
        6. Strategic Recommendations
        7. Risk Assessment
        8. Action Items

        Make it comprehensive, data-driven, and actionable. Use specific numbers and metrics.
        Format the response in a professional business report style with clear sections.
        """
        
        return self.ai_service._make_request(prompt)
    
    def _get_admin_fallback_response(self, user_message):
        """Fallback responses for admin chatbot when AI is unavailable"""
        user_message_lower = user_message.lower()
    
        fallback_responses = {
            'occupancy': "Based on current data, we have approximately 65% occupancy today with 15 rooms occupied out of 23 total rooms.",
            'revenue': "Today's revenue is approximately ₹45,000 from 8 completed bookings. The average booking value is ₹5,625.",
            'performance': "Today's performance: 8 new bookings, ₹45,000 revenue, 65% occupancy. Check-ins: 5, Check-outs: 3.",
            'alerts': "Current alerts: 7 pending reviews awaiting approval, 2 offers expiring this week, and occupancy below peak levels.",
            'revenue trend': "Revenue trends show a 15% increase compared to last week. The Deluxe rooms are performing best with 45% of total revenue.",
            'customer': "Customer insights: Average rating 4.3/5, 68% repeat customer rate. Recent reviews highlight excellent service but suggest room for improvement in amenities.",
            'room': "Top performing rooms: Deluxe Suite (85% occupancy), Executive Room (72% occupancy). Standard rooms show lower performance at 55% occupancy.",
            'booking': "Booking patterns show most reservations are made 2-3 weeks in advance. Weekend occupancy averages 85% while weekdays are at 60%.",
            'default': "I'm currently experiencing connectivity issues with the live business data. Please try again in a moment or check the specific analytics pages for detailed information."
        }
    
        # Check for keywords
        for key, response in fallback_responses.items():
            if key in user_message_lower:
                return response
    
        return fallback_responses["default"]
    
    def analyze_business_trends(self):
        """Analyze business trends and patterns"""
        from utils.advanced_ai_insights import AdvancedAIAnalytics
        
        business_data = AdvancedAIAnalytics.get_comprehensive_business_data(90)
        
        prompt = f"""
        Analyze business trends and patterns for Hotel Royal Orchid:

        HISTORICAL DATA (90 days):
        {json.dumps(business_data, indent=2, default=str)}

        Analyze:
        1. Booking patterns and seasonality
        2. Revenue trends
        3. Customer behavior changes
        4. Room performance evolution
        5. Market position insights
        6. Competitive implications
        7. Future trend predictions

        Provide specific, data-supported insights.
        """
        
        return self.ai_service._make_request(prompt)