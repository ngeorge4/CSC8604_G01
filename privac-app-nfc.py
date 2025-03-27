"""
Privacy-Pac Flask Application
Author: recker1103
Current Date: 2025-03-23 20:02:12 UTC
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, g, Response
from flask_socketio import SocketIO
import sqlite3
import os
import time
import threading
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask
app = Flask(__name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
    static_url_path='/static'
)

# Configure app
app.config.update(
    SECRET_KEY='privacy-pac-2025',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    SEND_FILE_MAX_AGE_DEFAULT=0,
    DEBUG=True
)

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading'
)

# Database configuration
DATABASE = os.path.join(BASE_DIR, "database/quiz_data.db")

# Event queues
class SafeQueue:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()

    def append(self, item):
        with self.lock:
            self.queue.append(item)

    def get(self):
        with self.lock:
            return self.queue.pop(0) if self.queue else None

gpio_events = SafeQueue()
nfc_events = SafeQueue()

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    return render_template('Welcome-Home.html')

@app.route('/conditions')
def conditions():
    return render_template('conditions.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/insert_card')
def insert_card():
    return render_template('insert-card.html')

@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/fetch_questions')
def fetch_questions():
    """Fetch quiz questions"""
    try:
        set_id = request.args.get("set_id", "1")
        logger.info(f"Fetching questions for set_id: {set_id}")
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, question, left_choice, right_choice 
            FROM questions 
            WHERE set_id = ? 
            ORDER BY id ASC
            LIMIT 5
        """, (set_id,))
        
        questions = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Found {len(questions)} questions for set {set_id}")
        return jsonify(questions)
    except Exception as e:
        logger.error(f"Error fetching questions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/submit_response', methods=['POST'])
def submit_response():
    """Submit quiz response"""
    try:
        data = request.get_json()
        logger.info(f"Submitting response: {data}")
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO responses (session_id, question_id, choice)
            VALUES (?, ?, ?)
        """, (data['session_id'], data['question_id'], data['choice']))
        
        db.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Error submitting response: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/gpio-events')
def gpio_events_stream():
    """SSE endpoint for GPIO events"""
    def generate():
        while True:
            try:
                event = gpio_events.get()
                if event:
                    yield f"data: {{\"choice\": \"{event}\"}}\n\n"
                else:
                    yield "data: {\"type\": \"heartbeat\"}\n\n"
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"GPIO stream error: {e}")
                time.sleep(1)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

@app.route('/gpio-button-press', methods=['POST'])
def gpio_button_press():
    """Handle GPIO button press"""
    try:
        data = request.get_json()
        if not data or 'choice' not in data:
            return jsonify({'error': 'Missing choice'}), 400
        
        choice = data['choice']
        if choice not in ['left', 'right']:
            return jsonify({'error': 'Invalid choice'}), 400

        gpio_events.append(choice)
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"GPIO event error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/nfc-event', methods=['POST'])
def nfc_event():
    """Handle NFC card detection"""
    try:
        data = request.get_json()
        logger.info(f"NFC event received: {data}")
        nfc_events.append(data)
        socketio.emit('card_detected', data)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"NFC event error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/handle-navigation', methods=['POST'])
def handle_navigation():
    """Handle page navigation"""
    try:
        data = request.get_json()
        current_page = data.get('current_page', '').rstrip('.html')
        choice = data.get('choice')

        if not current_page or not choice:
            return jsonify({'error': 'Missing parameters'}), 400

        if current_page == '/quiz':
            return jsonify({'redirect': None})

        # Get navigation route from PAGE_ROUTES
        page_config = PAGE_ROUTES.get(current_page, {})
        next_route = page_config.get(choice)
        
        return jsonify({'redirect': next_route or '/'})
    except Exception as e:
        logger.error(f"Navigation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files"""
    try:
        return send_from_directory(app.static_folder, filename)
    except Exception as e:
        logger.error(f"Static file error: {e}")
        return str(e), 404

# Page navigation configuration
PAGE_ROUTES = {
    "/": {
        "template": "Welcome-Home.html",
        "left": None,
        "right": "/conditions"
    },
    "/conditions": {
        "template": "conditions.html",
        "right": "/terms",
        "left": None
    },
    "/terms": {
        "template": "terms.html",
        "left": None,
        "right": "/insert_card"
    },
    "/insert_card": {
        "template": "insert-card.html",
        "left": None,
        "right": "/loading"
    },
    "/loading": {
        "template": "loading.html"
    },
    "/quiz": {
        "template": "quiz.html"
    }
}

if __name__ == "__main__":
    try:
        # Create required directories
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        os.makedirs(app.template_folder, exist_ok=True)
        os.makedirs(app.static_folder, exist_ok=True)

        # Log startup info
        logger.info(f"Starting Privacy-Pac application (UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})")
        logger.info(f"Current user: recker1103")
        logger.info(f"Template directory: {app.template_folder}")
        logger.info(f"Static directory: {app.static_folder}")

        # Start server
        socketio.run(
            app,
            host="0.0.0.0",
            port=5004,
            debug=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Startup error: {e}")