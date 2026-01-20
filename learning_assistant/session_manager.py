import threading
import logging
from datetime import datetime
from .database import Database
from .agent import LearningAgent

class SessionManager:
    def __init__(self):
        self.db = Database()
        self.agent = None # Lazy load
        self.logger = logging.getLogger(__name__)

    def _get_agent(self):
        if not self.agent:
            self.agent = LearningAgent()
        return self.agent

    def _analyze_session(self, class_id, text, progress_callback=None):
        """Run full analysis pipeline with progress updates (msg, percent)"""
        agent = self._get_agent()
        total_steps = 4
        current_step = 0
        
        def report(msg):
            percent = (current_step / total_steps)
            print(f"[Analysis] {msg} ({int(percent*100)}%)")
            if progress_callback:
                progress_callback(msg, percent)
        
        report("Iniciando análisis inteligente...")
        
        # 1. Summary & Level (Estimated: 5-8s)
        try:
            report(f"Generando resumen estratégico...")
            summary_data = agent.generate_summary(text)
            if summary_data:
                self.db.update_class_summary(class_id, summary_data.get('summary'), summary_data.get('level'))
        except Exception as e:
            self.logger.error(f"Error in summary: {e}")
        
        current_step += 1

        # 2. Vocabulary (Estimated: 5-8s)
        try:
            report(f"Analizando vocabulario avanzado...")
            vocab = agent.extract_vocabulary(text)
            if vocab:
                self.db.save_vocabulary(class_id, vocab)
        except Exception as e:
            self.logger.error(f"Error in vocab: {e}")

        current_step += 1

        # 3. Questions (Quiz) (Estimated: 8-12s)
        try:
            report(f"Diseñando evaluación pedagógica...")
            questions = agent.generate_questions(text)
            if questions:
                self.db.save_questions(class_id, questions)
        except Exception as e:
            self.logger.error(f"Error in questions: {e}")

        current_step += 1

        # 4. Flashcards (Estimated: 5-8s)
        try:
            report(f"Creando material de repaso...")
            cards = agent.create_flashcards(text)
            if cards:
                conn = self.db.get_connection()
                c = conn.cursor()
                for card in cards:
                    c.execute("INSERT INTO flashcards (class_id, front, back) VALUES (?, ?, ?)",
                              (class_id, card['front'], card['back']))
                conn.commit()
                conn.close()
        except Exception as e:
            self.logger.error(f"Error in flashcards: {e}")
            
        current_step += 1
        report("¡Análisis completado! 🎉")

    def save_session(self, raw_text, title=None, duration=0, progress_callback=None):
        """Save raw session and start background analysis"""
        if not raw_text.strip():
            return None
        
        if not title:
            title = f"Class {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        class_id = self.db.save_class(title, raw_text, duration)
        
        # Start analysis in background
        thread = threading.Thread(target=self._analyze_session, args=(class_id, raw_text, progress_callback))
        thread.start()
        
        return class_id

    def get_class_data(self, class_id):
        """Retrieve all data for a class"""
        data = {}
        data['info'] = self.db.get_class(class_id)
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Vocab
        c.execute("SELECT * FROM vocabulary WHERE class_id = ?", (class_id,))
        data['vocabulary'] = [dict(r) for r in c.fetchall()]
        
        # Questions
        c.execute("SELECT * FROM questions WHERE class_id = ?", (class_id,))
        data['questions'] = [dict(r) for r in c.fetchall()]
        
        # Flashcards
        c.execute("SELECT * FROM flashcards WHERE class_id = ?", (class_id,))
        data['flashcards'] = [dict(r) for r in c.fetchall()]
        
        conn.close()
        return data

import sqlite3 # Import specifically for row factory usage
