import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "classes.db")

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables with subject support."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Classes table (with subject column)
        c.execute('''CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            title TEXT,
            raw_text TEXT,
            summary TEXT,
            level TEXT,
            duration_sec INTEGER,
            subject TEXT DEFAULT 'english'
        )''')
        
        # Add subject column if it doesn't exist (migration)
        try:
            c.execute("ALTER TABLE classes ADD COLUMN subject TEXT DEFAULT 'english'")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        # Add source column if it doesn't exist (migration for history)
        try:
            c.execute("ALTER TABLE classes ADD COLUMN source TEXT")
        except sqlite3.OperationalError:
            pass
        
        # Vocabulary table
        c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            word TEXT,
            definition TEXT,
            example TEXT,
            type TEXT, -- idiom, phrasal_verb, word, concept
            level TEXT,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )''')
        
        # Questions table
        c.execute('''CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            question TEXT,
            options_json TEXT, -- JSON list of options
            correct_answer TEXT,
            explanation TEXT,
            type TEXT, -- multiple_choice, open
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )''')
        
        # Flashcards table (Spaced Repetition)
        c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            front TEXT,
            back TEXT,
            box INTEGER DEFAULT 1,
            next_review_ts TEXT,
            last_review_ts TEXT,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )''')

        # Grammar Analysis table (English only)
        c.execute('''CREATE TABLE IF NOT EXISTS grammar_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            concept TEXT,
            explanation TEXT,
            example_in_text TEXT,
            rule TEXT,
            tone_learning TEXT,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )''')
        
        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def save_class(self, title, raw_text, duration_sec=0, subject='english', source=None):
        """Save a new class with subject and source."""
        timestamp = datetime.now().isoformat()
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO classes (timestamp, title, raw_text, duration_sec, subject, source) VALUES (?, ?, ?, ?, ?, ?)",
                  (timestamp, title, raw_text, duration_sec, subject, source))
        class_id = c.lastrowid
        conn.commit()
        conn.close()
        return class_id
        
    def get_recent_classes(self, limit=20):
        """Get list of recent classes for history."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, title, timestamp, duration_sec, subject, source FROM classes ORDER BY id DESC LIMIT ?", (limit,))
        data = [dict(row) for row in c.fetchall()]
        conn.close()
        return data
    
    def update_class_summary(self, class_id, summary, level=None):
        """Update class summary and optionally level."""
        conn = self.get_connection()
        c = conn.cursor()
        if level:
            c.execute("UPDATE classes SET summary = ?, level = ? WHERE id = ?", (summary, level, class_id))
        else:
            c.execute("UPDATE classes SET summary = ? WHERE id = ?", (summary, class_id))
        conn.commit()
        conn.close()

    def save_vocabulary(self, class_id, vocab_list):
        """
        vocab_list: list of dicts {word, definition, example, type, level}
        """
        conn = self.get_connection()
        c = conn.cursor()
        for v in vocab_list:
            c.execute('''INSERT INTO vocabulary (class_id, word, definition, example, type, level) 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (class_id, v['word'], v['definition'], v.get('example', ''), v.get('type', 'concept'), v.get('level', '')))
        conn.commit()
        conn.close()

    def save_questions(self, class_id, questions_list):
        """
        questions_list: list of dicts {question, options, correct_answer, explanation, type}
        """
        conn = self.get_connection()
        c = conn.cursor()
        for q in questions_list:
            options_json = json.dumps(q.get('options', []))
            c.execute('''INSERT INTO questions (class_id, question, options_json, correct_answer, explanation, type) 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (class_id, q['question'], options_json, q['correct_answer'], q.get('explanation', ''), q.get('type', 'multiple_choice')))
        conn.commit()
        conn.close()

    def save_grammar_points(self, class_id, points_list):
        """
        points_list: list of dicts {concept, explanation, example_in_text, rule, tone_learning}
        """
        conn = self.get_connection()
        c = conn.cursor()
        for p in points_list:
            c.execute('''INSERT INTO grammar_points (class_id, concept, explanation, example_in_text, rule, tone_learning) 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (class_id, p.get('concept'), p.get('explanation'), p.get('example_in_text'), 
                       p.get('rule'), p.get('tone_learning', '')))
        conn.commit()
        conn.close()

    def get_grammar_points(self, class_id):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM grammar_points WHERE class_id = ?", (class_id,))
        rows = c.fetchall()
        
        conn.close()
        return [dict(r) for r in rows]

    def get_class(self, class_id):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_recent_classes(self, limit=10):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, timestamp, title, summary, subject FROM classes ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

if __name__ == "__main__":
    db = Database()
    print(f"Database initialized at {db.db_path}")
