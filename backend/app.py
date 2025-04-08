from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import google.generativeai as genai
from datetime import datetime
import json
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Gemini
GOOGLE_API_KEY = "AIzaSyAK8obivhQ8T9mF-dGC-SnaZ7GutGQF4e0"
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the model with specific configuration
model = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config={
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
)

# System prompt template
SYSTEM_PROMPT = """
You are BookBot, an expert book recommendation assistant. Your role is to:
1. Recommend books based on user preferences, mood, and reading history
2. Provide thoughtful, personalized book suggestions
3. Maintain a formal and professional tone at all times
4. Only discuss topics related to books, reading, and literature
5. If asked about other topics, politely decline and steer conversation back to books

Guidelines:
- Always respond in the user's preferred language (current: {language})
- Consider the user's current mood: {mood}
- Provide 1-3 book recommendations at a time with brief explanations
- Format book titles in quotes followed by author (e.g., "The Hobbit" by J.R.R. Tolkien)
- For book details, use this format: "Title" by Author (Genre) - brief description
- For out-of-scope requests, respond: "I specialize in book recommendations. Could we discuss your reading preferences instead?"

Current date: {current_date}
Today's featured book: {featured_book}
"""

# Featured books by day of week
FEATURED_BOOKS = {
    0: '"Monday\'s Child" by Harriet Evans (Fiction) - A heartwarming family drama perfect for starting the week',
    1: '"The Martian" by Andy Weir (Sci-Fi) - An exhilarating survival story to energize your Tuesday',
    2: '"The Silent Patient" by Alex Michaelides (Thriller) - A psychological thriller for midweek suspense',
    3: '"Little Women" by Louisa May Alcott (Classic) - A comforting classic for Thursday reflection',
    4: '"The Hitchhiker\'s Guide to the Galaxy" by Douglas Adams (Humor/Sci-Fi) - A funny romp to welcome the weekend',
    5: '"The Night Circus" by Erin Morgenstern (Fantasy) - A magical escape for your Saturday',
    6: '"The Alchemist" by Paulo Coelho (Philosophical Fiction) - Inspirational reading for Sunday'
}

# Mood context mapping
MOOD_CONTEXT = {
    'default': 'neutral',
    'adventurous': 'looking for exciting, adventurous stories',
    'romantic': 'interested in romance and emotional connections',
    'mysterious': 'seeking mystery and suspense',
    'thoughtful': 'wanting thought-provoking and philosophical works'
}

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Ensure request has JSON data
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        mood = data.get('mood', 'default')
        language = data.get('language', 'en')
        
        # Validate input
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Check if message is out of scope
        if is_out_of_scope(user_message):
            return jsonify({
                'response': 'I specialize in book recommendations. Could we discuss your reading preferences instead?'
            })
        
        # Get current date info
        now = datetime.now()
        day_of_week = now.weekday()
        current_date = now.strftime("%A, %B %d, %Y")
        featured_book = FEATURED_BOOKS.get(day_of_week, FEATURED_BOOKS[0])
        
        # Prepare context based on mood
        mood_context = MOOD_CONTEXT.get(mood, MOOD_CONTEXT['default'])
        
        # Prepare system prompt
        system_prompt = SYSTEM_PROMPT.format(
            language=language,
            mood=mood_context,
            current_date=current_date,
            featured_book=featured_book
        )
        
        # Prepare conversation for Gemini
        # First message is system prompt (sent as a user message)
        messages = [{'role': 'user', 'parts': [system_prompt]}]
        
        # Add conversation history - properly formatted for Gemini
        for msg in conversation_history:
            role = 'user' if msg['role'] == 'user' else 'model'
            messages.append({'role': role, 'parts': [msg['content']]})
        
        # Add current message
        messages.append({'role': 'user', 'parts': [user_message]})
        
        # Generate response
        try:
            response = model.generate_content(messages)
            
            if not response or not hasattr(response, 'text'):
                return jsonify({
                    'error': 'Empty response from model',
                    'details': 'The model did not generate any text'
                }), 500
                
            return jsonify({
                'response': response.text,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as model_error:
            app.logger.error(f"Model error: {str(model_error)}")
            return jsonify({
                'error': 'Model processing error',
                'details': str(model_error)
            }), 500
    
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Sorry, I encountered an issue processing your request. Please try again.'
        }), 500

def is_out_of_scope(message):
    """Check if the message is out of scope for a book recommender."""
    message_lower = message.lower()
    out_of_scope_keywords = [
        'sports', 'politics', 'medical advice', 'financial advice', 
        'legal advice', 'programming', 'coding', 'how to build',
        'weather', 'news', 'stock market', 'sports', 'game', 'movie',
        'music', 'recipe', 'cooking', 'travel', 'vacation'
    ]
    return any(keyword in message_lower for keyword in out_of_scope_keywords)

@app.route('/api/daily_book', methods=['GET'])
def get_daily_book():
    try:
        day_of_week = datetime.now().weekday()
        return jsonify({
            'book': FEATURED_BOOKS.get(day_of_week, FEATURED_BOOKS[0]),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error in daily_book endpoint: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve daily book',
            'book': FEATURED_BOOKS[0]  # Fallback
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/feedback', methods=['POST'])
def feedback():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        message_id = data.get('messageId')
        is_positive = data.get('isPositive', False)
        
        # In a production app, you would store this feedback in a database
        app.logger.info(f"Received feedback for message {message_id}: {'positive' if is_positive else 'negative'}")
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback received'
        })
    except Exception as e:
        app.logger.error(f"Error in feedback endpoint: {str(e)}")
        return jsonify({
            'error': 'Failed to process feedback',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)