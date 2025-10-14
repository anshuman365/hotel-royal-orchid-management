# © 2025 Anshuman Singh. All Rights Reserved.
# Unauthorized use prohibited.
# chatbot.py - UPDATED VERSION
from flask import Blueprint, render_template, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app import db
from utils.ai_service import OpenRouterAI, ChatbotContextBuilder
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chatbot')
@login_required
def chatbot_page():
    """Main chatbot interface"""
    return render_template('chatbot.html')

@chatbot_bp.route('/api/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    """Send message to chatbot and get response with enhanced error handling"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Empty message'})
        
        logger.info(f"Chat message from user {current_user.id}: {user_message}")
        
        # Get or initialize chat history
        chat_history = session.get('chat_history', [])
        
        # Build user context
        user_context = ChatbotContextBuilder.build_user_context(current_user)
        
        # Add hotel context
        hotel_context = f"""
        {user_context}
        
        {ChatbotContextBuilder.get_available_offers_context()}
        
        {ChatbotContextBuilder.get_rooms_context()}
        """
        
        # Get AI response
        ai_service = OpenRouterAI()
        ai_response = ai_service.chat_with_context(user_message, hotel_context, chat_history)
        
        # Update chat history (keep last 10 messages)
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": ai_response})
        
        # Keep only last 20 messages (10 exchanges)
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        session['chat_history'] = chat_history
        session.modified = True
        
        logger.info(f"AI response generated successfully for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().strftime('%H:%M')
        })
        
    except Exception as e:
        logger.error(f"Chat service error for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Chat service error: {str(e)}',
            'response': 'I apologize, but I\'m having trouble responding right now. Please try again in a moment or contact our front desk for immediate assistance.'
        })

@chatbot_bp.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat_history():
    """Clear chat history"""
    session.pop('chat_history', None)
    logger.info(f"Chat history cleared for user {current_user.id}")
    return jsonify({'success': True, 'message': 'Chat history cleared'})

@chatbot_bp.route('/api/chat/history', methods=['GET'])
@login_required
def get_chat_history():
    """Get chat history"""
    chat_history = session.get('chat_history', [])
    return jsonify({'success': True, 'history': chat_history})

@chatbot_bp.route('/api/chat/quick-questions', methods=['GET'])
@login_required
def get_quick_questions():
    """Get suggested quick questions based on user context"""
    user_context = ChatbotContextBuilder.build_user_context(current_user)
    
    # Analyze user context to suggest relevant questions
    suggestions = [
        "What are my upcoming bookings?",
        "What special offers do I qualify for?",
        "Can I modify my booking?",
        "What are your cancellation policies?",
        "What amenities do you have?",
        "How do I write a review?",
        "What's the check-in time?",
        "Do you have airport shuttle service?"
    ]
    
    # Add personalized suggestions based on user history
    bookings = current_user.bookings
    if bookings:
        suggestions.append("How do I write a review for my recent stay?")
        suggestions.append("Can I get a receipt for my previous booking?")
    
    if len(bookings) > 1:
        suggestions.append("Do I get any loyalty discounts?")
        suggestions.append("What are my past room preferences?")
    
    # Remove duplicates and return
    unique_suggestions = list(dict.fromkeys(suggestions))
    return jsonify({'success': True, 'suggestions': unique_suggestions[:8]})  # Limit to 8

@chatbot_bp.route('/api/chat/debug', methods=['GET'])
@login_required
def debug_chat_service():
    """Debug endpoint to check AI service status"""
    try:
        ai_service = OpenRouterAI()
        test_response = ai_service.chat_with_context("Test message", "Test user context")
        
        return jsonify({
            'success': True,
            'status': 'AI service is working',
            'test_response': test_response[:100] + "..." if len(test_response) > 100 else test_response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'AI service error',
            'error': str(e)
        })

# Update your chatbot.py routes
@chatbot_bp.route('/api/admin/chat/send', methods=['POST'])
@login_required
def send_admin_chat_message():
    """Send message to admin chatbot with full business access"""
    try:
        if not current_user.is_staff():
            return jsonify({'success': False, 'error': 'Admin access required'})
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Empty message'})
        
        # Get or initialize admin chat history
        admin_chat_history = session.get('admin_chat_history', [])
        
        # Use admin AI service with full business context
        from utils.admin_chatbot_context import AdminAIService
        admin_ai = AdminAIService()
        ai_response = admin_ai.chat_with_business_context(user_message, current_user, admin_chat_history)
        
        # Update admin chat history
        admin_chat_history.append({"role": "user", "content": user_message})
        admin_chat_history.append({"role": "assistant", "content": ai_response})
        
        # Keep only last 20 messages
        if len(admin_chat_history) > 20:
            admin_chat_history = admin_chat_history[-20:]
        
        session['admin_chat_history'] = admin_chat_history
        session.modified = True
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().strftime('%H:%M'),
            'is_admin': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Admin chat service error: {str(e)}'
        })

@chatbot_bp.route('/api/admin/chat/generate-report', methods=['POST'])
@login_required
def generate_business_report():
    """Generate AI business report"""
    try:
        if not current_user.is_staff():
            return jsonify({'success': False, 'error': 'Admin access required'})
        
        data = request.get_json()
        report_type = data.get('report_type', 'weekly')
        
        from utils.admin_chatbot_context import AdminAIService
        admin_ai = AdminAIService()
        report = admin_ai.generate_business_report(report_type)
        
        return jsonify({
            'success': True,
            'report': report,
            'report_type': report_type,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Report generation failed: {str(e)}'
        })