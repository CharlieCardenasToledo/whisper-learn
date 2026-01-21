import threading
import logging
import sqlite3
from datetime import datetime
from .database import Database
from .agent import LearningAgent
from .prompts import SUBJECT_CONFIGS, DEFAULT_SUBJECT

class SessionManager:
    def __init__(self):
        self.db = Database()
        self.agent = None  # Lazy load
        self.logger = logging.getLogger(__name__)

    def _get_agent(self):
        if not self.agent:
            self.agent = LearningAgent()
        return self.agent

    def _analyze_session(self, class_id, text, subject=DEFAULT_SUBJECT, progress_callback=None):
        """Run full analysis pipeline with progress updates (step, total, msg, percent)."""
        agent = self._get_agent()
        config = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
        
        # Determine number of steps based on subject features
        has_grammar = config.get("show_grammar", False)
        total_steps = 5 if has_grammar else 4
        current_step = 0
        
        # Step names for user feedback (Norman: clear system status)
        step_names = [
            "📝 Generando resumen",
            f"📖 Analizando {config.get('vocabulary_label', 'vocabulario').lower()}",
            "📝 Creando preguntas de quiz",
            "🧠 Generando flashcards"
        ]
        if has_grammar:
            step_names.append("🔍 Analizando gramática")
        
        def report(step_idx, custom_msg=None):
            percent = step_idx / total_steps
            step_name = step_names[step_idx] if step_idx < len(step_names) else "Finalizando"
            msg = custom_msg if custom_msg else f"Paso {step_idx + 1}/{total_steps}: {step_name}"
            print(f"[Analysis] {msg} ({int(percent*100)}%)")
            if progress_callback:
                progress_callback(msg, percent, step_idx + 1, total_steps)
        
        report(0, f"🚀 Iniciando análisis de {config['name']}...")
        
        if not agent.ensure_connection(lambda m: progress_callback(m, 0, 0, total_steps) if progress_callback else None):
            if progress_callback:
                progress_callback("Error: No se pudo iniciar Ollama 🔴", 0, 0, total_steps)
            self.logger.error("Ollama connection failed. Aborting analysis.")
            return

        # Define sub-task callback for streaming LLM progress
        def agent_callback(sub_msg):
            # sub_msg e.g. "Generando... (200 chars)" or "Chunk 1/4"
            if progress_callback:
                full_msg = f"Paso {current_step+1}/{total_steps}: {step_names[current_step]} | {sub_msg}"
                progress_callback(full_msg, current_step / total_steps, current_step + 1, total_steps)

        # Helper for incremental saving (Streaming)
        def save_incremental(dtype, items):
            if not items: return
            
            print(f"[DEBUG] save_incremental called: dtype={dtype}, items_count={len(items)}")
            
            if dtype == 'vocabulary':
                self.db.save_vocabulary(class_id, items)
            elif dtype == 'questions':
                self.db.save_questions(class_id, items)
            elif dtype == 'flashcards':
                conn = self.db.get_connection()
                c = conn.cursor()
                for card in items:
                    c.execute("INSERT INTO flashcards (class_id, front, back) VALUES (?, ?, ?)",
                              (class_id, card['front'], card['back']))
                conn.commit()
                conn.close()
            
            print(f"[DEBUG] save_incremental: Saved {len(items)} {dtype} items to DB")
            
            # Notify UI to unlock/refresh immediately
            if progress_callback:
                print(f"[DEBUG] save_incremental: Calling progress_callback with data_type={dtype}")
                progress_callback(f"{dtype.title()} listo ✅", current_step / total_steps, current_step, total_steps, data_type=dtype)

        # 1. Summary & Level
        try:
            report(0)
            summary_data = agent.generate_summary(text, subject, progress_callback=agent_callback)
            if summary_data:
                level = summary_data.get('level') if subject == 'english' else None
                self.db.update_class_summary(class_id, summary_data.get('summary'), level)
                # Notify UI that summary is ready
                if progress_callback:
                    progress_callback("Resumen listo ✅", 0.25, 1, total_steps, data_type='summary')
        except Exception as e:
            self.logger.error(f"Error in summary: {e}")
        
        current_step = 1

        # 2. Vocabulary / Technical Terms
        try:
            report(1)
            vocab_chunks_saved = False
            
            def vocab_partial(items):
                nonlocal vocab_chunks_saved
                vocab_chunks_saved = True
                save_incremental('vocabulary', items)

            vocab = agent.extract_vocabulary(text, subject, progress_callback=agent_callback, partial_callback=vocab_partial)
            
            # If partials weren't called (no chunks), save and notify now
            if vocab and not vocab_chunks_saved:
                self.db.save_vocabulary(class_id, vocab)
                if progress_callback:
                    progress_callback("Vocabulario listo ✅", 0.4, 2, total_steps, data_type='vocabulary')
        except Exception as e:
            self.logger.error(f"Error in vocab: {e}")

        current_step = 2

        # 3. Questions (Quiz)
        try:
            report(2)
            questions_chunks_saved = False
            def questions_partial(items):
                nonlocal questions_chunks_saved
                questions_chunks_saved = True
                save_incremental('questions', items)

            questions = agent.generate_questions(text, subject, count=5, progress_callback=agent_callback, partial_callback=questions_partial)
            
            # If partials weren't called (no chunks), save and notify now
            if questions and not questions_chunks_saved:
                self.db.save_questions(class_id, questions)
                if progress_callback:
                    progress_callback("Quiz listo ✅", 0.6, 3, total_steps, data_type='questions')
        except Exception as e:
            self.logger.error(f"Error in questions: {e}")

        current_step = 3

        # 4. Flashcards
        try:
            report(3)
            cards_chunks_saved = False
            def cards_partial(items):
                nonlocal cards_chunks_saved
                cards_chunks_saved = True
                save_incremental('flashcards', items)

            cards = agent.create_flashcards(text, subject, progress_callback=agent_callback, partial_callback=cards_partial)
            
            # If partials weren't called (no chunks), save and notify now
            if cards and not cards_chunks_saved:
                conn = self.db.get_connection()
                c = conn.cursor()
                for card in cards:
                    c.execute("INSERT INTO flashcards (class_id, front, back) VALUES (?, ?, ?)",
                              (class_id, card['front'], card['back']))
                conn.commit()
                conn.close()
                if progress_callback:
                    progress_callback("Flashcards listo ✅", 0.8, 4, total_steps, data_type='flashcards')
        except Exception as e:
            self.logger.error(f"Error in flashcards: {e}")
            
        current_step = 4

        # 5. Grammar & Context (English only)
        if has_grammar:
            try:
                report(4)
                grammar_points = agent.analyze_grammar(text, subject)
                if grammar_points:
                    self.db.save_grammar_points(class_id, grammar_points)
            except Exception as e:
                self.logger.error(f"Error in grammar analysis: {e}")

            current_step += 1
        
        report(total_steps, "¡Análisis completado! 🎉")

    def create_draft_session(self, raw_text, title=None, duration=0, subject=DEFAULT_SUBJECT, source=None):
        """Save a new session draft without analysis."""
        if not raw_text.strip(): return None
        
        if not title:
            config = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
            title = f"{config['icon']} {config['name']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        return self.db.save_class(title, raw_text, duration, subject, source)

    def start_analysis(self, class_id, progress_callback=None):
        """Resume analysis for an existing session."""
        info = self.db.get_class(class_id)
        if not info: return
        
        # Start analysis in background
        thread = threading.Thread(target=self._analyze_session, args=(class_id, info['raw_text'], info['subject'], progress_callback))
        thread.start()

    def save_session(self, raw_text, title=None, duration=0, subject=DEFAULT_SUBJECT, progress_callback=None, source=None):
        """Save raw session and start background analysis with subject."""
        class_id = self.create_draft_session(raw_text, title, duration, subject, source)
        if class_id:
            self.start_analysis(class_id, progress_callback)
        return class_id

    def get_class_data(self, class_id):
        """Retrieve all data for a class."""
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
        
        # Grammar (English)
        c.execute("SELECT * FROM grammar_points WHERE class_id = ?", (class_id,))
        data['grammar'] = [dict(r) for r in c.fetchall()]
        
        conn.close()
        return data

    def chat_with_class(self, class_id, user_message, history=None):
        """Chat with the persona of the class."""
        class_info = self.db.get_class(class_id)
        if not class_info:
            return "Error: Class not found."
            
        raw_text = class_info.get('raw_text', '')
        subject = class_info.get('subject', DEFAULT_SUBJECT)
        agent = self._get_agent()
        return agent.chat(raw_text, user_message, subject, history)
