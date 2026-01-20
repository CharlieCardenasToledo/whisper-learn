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
        """Initialize database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Classes table
        c.execute('''CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            title TEXT,
            raw_text TEXT,
            summary TEXT,
            level TEXT,
            duration_sec INTEGER
        )''')
        
        # Vocabulary table
        c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            word TEXT,
            definition TEXT,
            example TEXT,
            type TEXT, -- idiom, phrasal_verb, word
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

        # Grammar Analysis table (Phase 1)
        c.execute('''CREATE TABLE IF NOT EXISTS grammar_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            concept TEXT,
            explanation TEXT,
            example_in_text TEXT,
            rule TEXT,
            tone_learning TEXT, -- e.g. "Formal business tone detected"
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )''')
        
        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def save_class(self, title, raw_text, duration_sec=0):
        timestamp = datetime.now().isoformat()
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO classes (timestamp, title, raw_text, duration_sec) VALUES (?, ?, ?, ?)",
                  (timestamp, title, raw_text, duration_sec))
        class_id = c.lastrowid
        conn.commit()
        conn.close()
        return class_id
    
    def update_class_summary(self, class_id, summary, level):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("UPDATE classes SET summary = ?, level = ? WHERE id = ?", (summary, level, class_id))
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
                      (class_id, v['word'], v['definition'], v['example'], v.get('type', 'word'), v.get('level', '')))
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
        c.execute("SELECT id, timestamp, title, summary FROM classes ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

if __name__ == "__main__":
    db = Database()
    print(f"Database initialized at {db.db_path}")
