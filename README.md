### 1. Introduction

#### 1.1 Purpose
Privacy-Pac is an interactive quiz system that combines physical card interactions (NFC) with button-based navigation to deliver privacy-related educational content.

#### 1.2 Project Structure
```plaintext
privacy-pac/
├── database/
│   └── quiz_data.db
├── static/
│   ├── fonts/
│   │   └── Pixeboy.ttf
│   ├── images/
│   │   ├── Welcome.png
│   │   ├── Conditions.png
│   │   ├── Bg-Terms.png
│   │   ├── insert-card.png
│   │   ├── bg-loading.png
│   │   ├── start-normal.png
│   │   ├── start-active.png
│   │   ├── cont-normal.png
│   │   └── cont-active.png
│   ├── b-style.css
│   ├── progress.css
│   ├── fullscreen.js
│   ├── page_handler.js
│   └── quiz_logic.js
├── templates/
│   ├── Welcome-Home.html
│   ├── conditions.html
│   ├── terms.html
│   ├── insert-card.html
│   ├── loading.html
│   ├── quiz.html
│   └── [0-5].html
└── privacy-app.py
├── button_press_handler.py
├── nfc_handler.py (Works independently not simultaneously with button press handler)

├── joystick_handler.py (Not integrated)

Caution: Event Stream Conflict
    The frontend uses EventSource (SSE) to listen for continuous GPIO events.
    The backend route /events may still attempt to send both GPIO and NFC events via a single SSE stream (from an older implementation).
    At the same time, NFC events are also being emitted via Socket.IO.
    This can lead to conflicts if the same event (e.g., NFC card detection) is delivered over both channels in different formats.
```
Notes:
Browsers block fullscreen unless triggered by a user action (e.g. click).
Attempts to force fullscreen on page load or with setTimeout will silently fail due to browser security policies.
Solution: Use a button or interaction to trigger requestFullscreen().

**some browser extensions or security settings block persistent fullscreen**

### 2. System Architecture

#### 2.1 Core Components
1.A **Flask Backend (`privacy-app.py`)**
   - Handles routing
   - Manages database operations
   - Processes NFC events
   - Handles GPIO button presses
   - Implements hybrid event system (SSE + Socket.IO)
   
**1.B NFC Handler (nfc_handler.py)**
  - Initializes NFC reader with py532lib for PN532 NFC Reader
  - Reads card UID and maps to quiz set
  - Sends event data to backend via UDP socket
  
**1.C GPIO Button Handler (button_press_handler.py)**
  - Monitors hardware GPIO pins
  - Detects left/right button presses
  - Sends press events to backend over HTTP

2. **Database (`quiz_data.db`)**
   - Tables:
     - questions (id, set_id, question, left_choice, right_choice)
     - responses (session_id, question_id, choice, timestamp)
     - scores (session_id, score, set_id)

3. **Frontend Pages**
   - Navigation Pages:
     - Welcome-Home
     - Conditions
     - Terms
   - Interactive Pages:
     - Insert Card
     - Loading
     - Quiz
   - Result Pages:
     - Score pages (0-5)

#### 2.2 Communication Systems
1. **GPIO Events (SSE)**
   - Uses Server-Sent Events
   - Handles physical button presses
   - Real-time button state updates
   - Lightweight, unidirectional

2. **NFC Events (Socket.IO)**
   - Uses WebSocket
   - Handles card detection
   - Bidirectional communication
   - Event-based card processing

### 3. Page Flow

```plaintext
Welcome → Conditions → Terms → Insert Card → Loading → Quiz → Score
```

#### 3.1 Navigation Logic
- Right button: Progress forward
- Left button: Return/cancel (where applicable)
- NFC card: Trigger quiz set selection

### 4. Technical Specifications

#### 4.1 Event Handling
1. **GPIO Events**
```javascript
const eventSource = new EventSource('/gpio-events');
eventSource.onmessage = (event) => {
    // Handle button presses
};
```

2. **NFC Events**
```javascript
const socket = io();
socket.on('card_detected', (data) => {
    // Handle card detection
});
```

#### 4.2 Database Schema
```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    set_id INTEGER,
    question TEXT,
    left_choice TEXT,
    right_choice TEXT
);

CREATE TABLE responses (
    session_id TEXT,
    question_id INTEGER,
    choice TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scores (
    session_id TEXT,
    score INTEGER,
    set_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5. User Interface Components

#### 5.1 Common Elements
- Background images
- Navigation buttons
- Error message container
- Progress indicators
- Fullscreen capability

#### 5.2 Quiz Interface
- Question display
- Left/Right choice buttons
- Progress bar
- Score tracking

### 6. Security Measures

#### 6.1 Data Protection
- SQLite database with proper access controls
- Session management for quiz attempts
- Input validation for all user interactions

#### 6.2 Error Handling
- Graceful error recovery
- User-friendly error messages
- Logging system for debugging

### 7. Integration Points

#### 7.1 Hardware Integration
1. **GPIO Buttons**
   - Left button input
   - Right button input
   - Debounce protection
   - Error handling

2. **NFC Reader**
   - Card detection
   - Set ID reading
   - Error recovery

#### 7.2 Software Integration
1. **Flask + Socket.IO**
   - Real-time events
   - Session management
   - Route handling

2. **Frontend + Backend**
   - AJAX calls
   - Event streams
   - WebSocket connections

### 8. Testing Requirements

#### 8.1 Test Cases
1. Navigation flow
2. Button functionality
3. NFC card detection
4. Quiz logic
5. Score calculation
6. Error handling
7. Session management

### 9. Deployment Requirements

#### 9.1 System Requirements
- Python 3.8+
- SQLite3
- Modern web browser
- GPIO hardware support
- NFC reader support 

#### 9.2 Dependencies
```plaintext
Flask==2.0.1
Flask-SocketIO==5.1.1
python-socketio==5.4.0
```

### 10. Maintenance

#### 10.1 Logging
- Event logging
- Error logging
- User interaction logging
- System status logging

#### 10.2 Monitoring
- GPIO status
- NFC reader status
- Database connections
- Event queue status

### 11. Future Enhancements
1. Multiple language support
2. Additional quiz sets
3. Analytics dashboard
4. User profiles
5. Achievement system
