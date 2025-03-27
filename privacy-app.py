"""
Privacy-Pac Flask Application
Author: ngeorge4
Current Date: 2025-03-20 04:40:19 UTC
"""

import sqlite3
import os
import time
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory, g, Response, stream_with_context
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
DATABASE = "database/quiz_data.db"
gpio_events = []
gpio_lock = threading.Lock()

# Page navigation configuration
PAGE_ROUTES = {
    "/": {
        "template": "Welcome-Home.html",
        "left": None,
        "right": "/conditions"  # Fixed capitalization
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
    "/conditions": {
        "template": "conditions.html",
        "right": "/terms",  # Right button goes to terms
        "left": None  # No left button action
    },
    "/quiz": {
        "template": "quiz.html"
    },
    "/0": {
        "template": "0.html",
        "left": "/insert_card",
        "right": "/group01"
    },
    "/1": {
        "template": "1.html",
        "left": "/insert_card",
        "right": "/group01"
    },
    "/2": {
        "template": "2.html",
        "left": "/insert_card",
        "right": "/group01"
    },
    "/3": {
        "template": "3.html",
        "left": "/insert_card",
        "right": "/group01"
    },
    "/4": {
        "template": "4.html",
        "left": "/insert_card",
        "right": "/group01"
    },
    "/5": {
        "template": "5.html",
        "left": "/insert_card",
        "right": "/group01"
    },
    "/group01": {
        "template": "group01.html"
    }
}

def get_db():
    """Get database connection"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "utc_time": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }), 200

@app.route('/gpio-events')
def gpio_events_stream():
    """SSE endpoint for GPIO events"""
    def event_stream():
        while True:
            with gpio_lock:
                if gpio_events:
                    choice = gpio_events.pop(0)
                    yield f'data: {{"choice": "{choice}"}}\n\n'
                else:
                    yield 'data: {"type": "heartbeat"}\n\n'
            time.sleep(0.1)
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream'
    )

@app.route('/gpio-button-press', methods=['POST'])
def gpio_button_press():
    """Handle GPIO button press events"""
    try:
        data = request.json
        if not data or 'choice' not in data:
            return jsonify({'error': 'Missing choice parameter'}), 400
            
        choice = data['choice']
        if choice not in ['left', 'right']:
            return jsonify({'error': 'Invalid choice'}), 400

        with gpio_lock:
            gpio_events.append(choice)
            
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error handling GPIO button press: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/handle-navigation', methods=['POST'])
def handle_navigation():
    """Handle page navigation"""
    try:
        data = request.json
        current_page = data.get('current_page', '').rstrip('.html')
        choice = data.get('choice')

        if not current_page or not choice:
            return jsonify({'error': 'Missing parameters'}), 400

        # Skip navigation for quiz page
        if current_page == '/quiz':
            return jsonify({'redirect': None})

        # Get navigation route
        page_config = PAGE_ROUTES.get(current_page)
        if not page_config:
            return jsonify({'redirect': '/'})

        next_route = page_config.get(choice)
        return jsonify({'redirect': next_route or '/'})

    except Exception as e:
        logger.error(f"Navigation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route("/fetch_questions")
def fetch_questions():
    """Fetch quiz questions"""
    # set_id = request.args.get("set_id")
    set_id = request.args.get("set_id", "2")  # Default to set 2
    
    if not set_id:
        return jsonify({"error": "Missing set_id"}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """SELECT id, question, left_choice, right_choice 
               FROM questions WHERE set_id = ? 
               ORDER BY id ASC LIMIT 5""",
            (set_id,)
        )
        questions = [dict(row) for row in cursor.fetchall()]

        if len(questions) < 5:
            logger.warning(f"Only {len(questions)} questions found for set {set_id}")
        
        return jsonify(questions)
    except Exception as e:
        logger.error(f"Error fetching questions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/submit_response", methods=["POST"])
def submit_response():
    """Submit quiz response"""
    data = request.json
    logger.info(f"Incoming response: {data}")

    session_id = data.get("session_id") or str(uuid.uuid4())
    question_id = data.get("question_id")
    choice = data.get("choice")

    if not question_id or not choice:
        return jsonify({"error": "Missing question_id or choice"}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO responses (session_id, question_id, choice, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (session_id, question_id, choice))
        db.commit()
        
        return jsonify({"session_id": session_id})
    except Exception as e:
        logger.error(f"Error submitting response: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Dynamic route generation for all pages
for route, config in PAGE_ROUTES.items():
    def create_route_handler(template_name):
        def route_handler():
            return render_template(template_name)
        return route_handler

    # Strip leading slash for endpoint name
    endpoint = route.lstrip('/')
    if not endpoint:
        endpoint = 'home'

    # Register the route
    app.add_url_rule(
        route,
        endpoint=endpoint,
        view_func=create_route_handler(config['template'])
    )

    # Register .html version if needed
    if not route.endswith('.html') and route != '/':
        app.add_url_rule(
            f"{route}.html",
            endpoint=f"{endpoint}_html",
            view_func=create_route_handler(config['template'])
        )

@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(os.path.join(app.root_path, "static"), filename)

if __name__ == "__main__":
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    logger.info(f"Starting Privacy-Pac Flask application on port 5004 (UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})")
    app.run(host="0.0.0.0", port=5004, debug=True)