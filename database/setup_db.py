import sqlite3
import os

DATABASE = "database/quiz_data.db"

def init_db():
    # Delete old database if it exists
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create questions table with set_id
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        left_choice TEXT NOT NULL,
        right_choice TEXT NOT NULL,
        set_id INTEGER NOT NULL CHECK(set_id IN (1,2))
    )
    """)

    # Create responses table (Includes timestamps for tracking multiple attempts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        question_id INTEGER NOT NULL,
        choice TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions (id)
    )
    """)

    # Insert updated sample questions for both sets
    sample_questions = [
        # Question Set 1: App Permissions & Security
        ("A flashlight app asks for camera and microphone access.", 
         "Accept—it probably needs them.", 
         "Deny and check if the permissions make sense.", 1),
        
        ("Your phone’s software update notification pops up.", 
         "Postpone it indefinitely.", 
         "Update to ensure security patches are applied.", 1),
        
        ("Your gaming app asks for location access, even though it’s not necessary.", 
         "Allow it to avoid app issues.", 
         "Check why it needs this access before allowing.", 1),
        
        ("A fitness app shares data with advertisers by default.", 
         "Accept because it’s common.", 
         "Review settings and disable unnecessary data sharing.", 1),
        
        ("Your app store suggests an unknown app with few reviews.", 
         "Download it and try it out.", 
         "Research reviews and developer credibility first.", 1),

        # Question Set 2: Social Media & Data Tracking
        ("You get a notification: 'Your friend just joined! Allow access to your contacts to connect.'", 
         "Allow access so you can find friends.", 
         "Deny access and add friends manually.", 2),
        
        ("An app asks for microphone permission while it’s not in use.", 
         "Accept; it’s probably harmless.", 
         "Deny and check app settings.", 2),
        
        ("You search for sneakers online. Later, all your ads are for shoes.", 
         "Accept it as normal and ignore it.", 
         "Review and limit app tracking in settings.", 2),
        
        ("A post goes viral offering 'Free concert tickets—just enter your details!'", 
         "Sign up quickly before it’s gone!", 
         "Verify the source before entering any data.", 2),
        
        ("A new social media app forces you to allow location access to sign up.", 
         "Allow it since you need the app.", 
         "Check if location sharing is necessary for app features.", 2),
    ]

    # Insert questions into the database
    cursor.executemany(
        "INSERT INTO questions (question, left_choice, right_choice, set_id) VALUES (?, ?, ?, ?)",
        sample_questions
    )

    # Check inserted questions
    cursor.execute("SELECT COUNT(*) FROM questions WHERE set_id = 1")
    set1_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM questions WHERE set_id = 2")
    set2_count = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    print(f"✅ Database initialized successfully!")
    print(f"✅ Set 1 Questions: {set1_count}/5")
    print(f"✅ Set 2 Questions: {set2_count}/5")

if __name__ == "__main__":
    init_db()
