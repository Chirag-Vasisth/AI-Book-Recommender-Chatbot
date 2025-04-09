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

# Enhanced System prompt template with point-form response requirement
SYSTEM_PROMPT = """
You are BookBot, the ultimate book recommendation and information assistant. Your responses MUST follow these rules:

1. RESPONSE FORMAT:
- Always use bullet points
- Each book recommendation should have:
  • Title: "*Title*" by Author (Year)
  • Genre/Field: 
  • Key Details: 
  • Publisher/Pages: 
  • Why Recommended: 

2. DOMAIN EXPERTISE:
- Academic/Professional books
- Fiction (all genres)
- Non-fiction
- Specialized texts

3. REQUIRED DETAILS:
- For fiction: themes, content notes
- For academic: level, prerequisites
- Always include publication year
- Mention comparable titles when relevant

4. EXAMPLE FORMAT:
• "*Clean Code*" by Robert Martin (2008)
  - Genre: Computer Science
  - Details: Essential programming practices
  - Publisher: Prentice Hall, 464 pages
  - Why: Best for professional developers

• "*The Hobbit*" by J.R.R. Tolkien (1937)
  - Genre: Fantasy
  - Themes: Adventure, heroism
  - Publisher: Allen & Unwin, 310 pages
  - Similar to: Lord of the Rings series

Current Context:
- Language: {language}
- Mood: {mood}
- Date: {current_date}
- Featured: {featured_book}

IMPORTANT: If query is not book-related, respond ONLY with:
"I specialize exclusively in books and reading. Please ask about books."
"""

# Featured books by day of week (point format)
FEATURED_BOOKS = {
    0: """• "*Clean Code*" by Robert Martin (2008)
  - Genre: Computer Science
  - Details: Essential programming practices
  - Publisher: Prentice Hall, 464 pages""",
    
    1: """• "*The Emperor of All Maladies*" by Siddhartha Mukherjee (2010)
  - Genre: Medicine
  - Details: Biography of cancer
  - Publisher: Scribner, 592 pages""",
    
    2: """• "*To Kill a Mockingbird*" by Harper Lee (1960)
  - Genre: Fiction
  - Themes: Racial injustice
  - Publisher: J.B. Lippincott, 336 pages""",
    
    3: """• "*The Lean Startup*" by Eric Ries (2011)
  - Genre: Business
  - Details: Modern methodology
  - Publisher: Crown Business, 336 pages""",
    
    4: """• "*Structure and Interpretation of Computer Programs*" by Abelson & Sussman (1996)
  - Genre: Computer Science
  - Level: Advanced
  - Publisher: MIT Press, 657 pages""",
    
    5: """• "*Beloved*" by Toni Morrison (1987)
  - Genre: Fiction
  - Awards: Pulitzer Prize
  - Publisher: Alfred A. Knopf, 324 pages""",
    
    6: """• "*The Right Stuff*" by Tom Wolfe (1979)
  - Genre: Non-fiction
  - Subject: Early astronauts
  - Publisher: Farrar, Straus and Giroux, 448 pages"""
}

# Mood context mapping
MOOD_CONTEXT = {
    'default': 'general inquiry',
    'adventurous': 'looking for challenging or expansive works',
    'romantic': 'interested in emotional or relationship-focused works',
    'mysterious': 'seeking complex or puzzle-like works',
    'thoughtful': 'wanting intellectually substantial material',
    'technical': 'seeking professional or academic material'
}

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        mood = data.get('mood', 'default')
        language = data.get('language', 'en')
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Strict book-related check
        if not is_book_related(user_message):
            return jsonify({
                'response': 'I specialize exclusively in books and reading. Please ask about books.',
                'is_book_related': False
            })
        
        # Get current context
        now = datetime.now()
        current_date = now.strftime("%A, %B %d, %Y")
        featured_book = FEATURED_BOOKS.get(now.weekday(), FEATURED_BOOKS[0])
        mood_context = MOOD_CONTEXT.get(mood, MOOD_CONTEXT['default'])
        
        # Prepare system prompt
        system_prompt = SYSTEM_PROMPT.format(
            language=language,
            mood=mood_context,
            current_date=current_date,
            featured_book=featured_book
        )
        
        # Prepare conversation
        messages = [{'role': 'user', 'parts': [system_prompt]}]
        
        for msg in conversation_history:
            role = 'user' if msg['role'] == 'user' else 'model'
            messages.append({'role': role, 'parts': [msg['content']]})
        
        messages.append({'role': 'user', 'parts': [user_message]})
        
        # Generate response
        try:
            response = model.generate_content(messages)
            
            if not response or not hasattr(response, 'text'):
                return jsonify({
                    'error': 'Empty response from model',
                    'details': 'The model did not generate any text'
                }), 500
            
            # Format validation
            response_text = response.text
            if not is_properly_formatted(response_text):
                response_text = format_as_bullets(response_text)
                
            return jsonify({
                'response': response_text,
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

def is_book_related(message):
    """Strict check for book-related queries"""
    message_lower = message.lower()
    book_keywords = [
        'book', 'textbook', 'novel', 'read', 'author', 'publish',
        'literature', 'fiction', 'non-fiction', 'genre', 'chapter',
        'reference', 'academic', 'study', 'learn', 'research',
        'story', 'writer', 'reading', 'library', 'publisher',
        'edition', 'volume', 'page', 'bookshelf', 'bookstore'
    ]
    return any(keyword in message_lower for keyword in book_keywords)

def is_properly_formatted(response):
    """Check if response follows bullet point format"""
    return response.strip().startswith('•') or response.strip().startswith('*')

def format_as_bullets(text):
    """Convert paragraph to bullet points"""
    points = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(f'• {point}' for point in points)

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
            'book': FEATURED_BOOKS[0]
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
        feedback_text = data.get('feedbackText', '')
        
        app.logger.info(f"Feedback for {message_id}: {'positive' if is_positive else 'negative'} - {feedback_text}")
        
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
