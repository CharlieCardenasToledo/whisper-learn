import ollama
import json
import logging
from .prompts import (
    SUBJECT_CONFIGS, DEFAULT_SUBJECT,
    get_system_role, get_summary_prompt, get_vocabulary_prompt,
    get_question_prompt, get_flashcard_prompt, get_grammar_prompt,
    get_roleplay_prompt
)

MODEL_NAME = "llama3.1:8b"

class LearningAgent:
    def __init__(self, model_name=MODEL_NAME):
        self.model = model_name
        self.logger = logging.getLogger(__name__)

    def ensure_connection(self, status_callback=None):
        """Check if Ollama is running, if not, try to start it with UI feedback."""
        try:
            ollama.list()
            return True
        except Exception:
            if status_callback:
                status_callback("Ollama está apagado. Iniciando servidor...")
            self.logger.info("Ollama not running. Attempting to start...")
            
            try:
                import subprocess
                # Start Ollama in background
                subprocess.Popen(["ollama", "serve"], 
                               creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
                
                # Wait for it to initialize (up to 8s)
                import time
                for i in range(8):
                    if status_callback:
                        status_callback(f"Iniciando motor IA... ({i+1}/8s)")
                    time.sleep(1)
                    try:
                        ollama.list()
                        self.logger.info("Ollama started successfully.")
                        return True
                    except:
                        pass
                return False
            except Exception as e:
                self.logger.error(f"Failed to auto-start Ollama: {e}")
                return False

    def _generate_json(self, prompt, context_text, subject=DEFAULT_SUBJECT, progress_callback=None):
        """Generic method to generate JSON output with retries and robust validation."""
        full_prompt = prompt.replace("{text}", context_text)
        system_role = get_system_role(subject)
        
        retries = 2
        for attempt in range(retries + 1):
            try:
                # Lower temperature on retries to be more deterministic
                temp = 0.2 if attempt == 0 else 0.1
                
                # Add a nudge on retries
                current_system_content = f'{system_role} You output strictly Valid JSON.'
                if attempt > 0:
                     current_system_content += " IMPORTANT: Previous attempt was empty. You MUST generate content."

                self.logger.debug(f"Sending prompt to LLM (Subject: {subject}, Attempt: {attempt+1})")
                
                # Use streaming to provide real-time progress
                content = ""
                last_update_len = 0
                
                stream = ollama.chat(
                    model=self.model, 
                    messages=[
                        {'role': 'system', 'content': current_system_content},
                        {'role': 'user', 'content': full_prompt}
                    ], 
                    format='json', 
                    options={'temperature': temp, 'num_ctx': 24576},
                    stream=True
                )
                
                print(f"[DEBUG] Starting LLM stream for subject={subject}")
                
                for chunk in stream:
                    content += chunk['message']['content']
                    
                    # Notify UI every ~50 chars for responsive feedback  
                    if progress_callback and len(content) - last_update_len > 50:
                        print(f"[DEBUG] Streaming update: {len(content)} chars")
                        progress_callback(f"Generando... ({len(content)} chars)")
                        last_update_len = len(content)
                
                self.logger.debug(f"Raw LLM Response: {content[:100]}...") # Log start to avoid spam
                
                parsed = json.loads(content)
                
                # VALIDATION: Check if empty
                is_empty = False
                if not parsed: is_empty = True
                elif isinstance(parsed, dict) and not parsed: is_empty = True # Empty dict {}
                elif isinstance(parsed, list) and not parsed: is_empty = True # Empty list []
                elif isinstance(parsed, dict):
                    # Check if it effectively represents "no content"
                    # Logic: It is empty if it has NO scalars AND (NO containers OR all containers are empty).
                    scalars = [v for v in parsed.values() if isinstance(v, (str, int, float, bool)) and v]
                    containers = [v for v in parsed.values() if isinstance(v, (list, dict))]
                    
                    has_valid_scalars = len(scalars) > 0
                    has_valid_containers = any(v for v in containers) # at least one non-empty container
                    
                    if not has_valid_scalars and not has_valid_containers:
                        is_empty = True

                if is_empty:
                    self.logger.warning(f"Attempt {attempt+1} returned empty JSON. Retrying...")
                    continue
                
                self.logger.info(f"Successfully parsed non-empty JSON. Type: {type(parsed)}")
                return parsed
                
            except Exception as e:
                self.logger.error(f"Error generating/parsing JSON (Attempt {attempt+1}): {e}")
                if attempt == retries:
                    return None
        
        return None

    def generate_summary(self, text, subject=DEFAULT_SUBJECT, progress_callback=None):
        """Generate class summary (and level for English)."""
        prompt = get_summary_prompt(subject)
        return self._generate_json(prompt, text, subject, progress_callback)

    def _chunk_text(self, text, chunk_size=8000, overlap=500):
        """Split text into overlapping chunks to manage context window."""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunk = text[start:]
                chunks.append(chunk)
                break
            
            # Try to find a sentence break to avoid cutting in middle
            last_period = text.rfind('.', start, end)
            if last_period != -1 and last_period > start + chunk_size * 0.8:
                end = last_period + 1
            
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            
        return chunks

    def _normalize_to_list(self, result, expected_keys=None):
        """Convert LLM response to list format (handles dict/list inconsistency)."""
        if result is None:
            return []
        
        if isinstance(result, list):
            return result
        
        if isinstance(result, dict):
            # Case 1: Dict with wrapper key like {"vocabulary": [...]} or {"flashcards": [...]}
            common_keys = ['vocabulary', 'words', 'terms', 'items', 'questions', 'flashcards', 'cards', 'list', 'results']
            if expected_keys:
                common_keys = expected_keys + common_keys
            
            for key in common_keys:
                if key in result and isinstance(result[key], list):
                    return result[key]
            
            # Case 2: Single item dict like {"word": "REST API", "definition": "..."}
            # Check if it looks like a single vocab/question/flashcard item
            if 'word' in result or 'question' in result or 'front' in result:
                return [result]
            
            # Case 3: Try to find any list value
            for val in result.values():
                if isinstance(val, list) and len(val) > 0:
                    return val
        
        return []

    def extract_vocabulary(self, text, subject=DEFAULT_SUBJECT, progress_callback=None, partial_callback=None):
        """Extract vocabulary - always notifies via partial_callback for reactivity."""
        if len(text) > 20000:
            self.logger.info(f"Text too long ({len(text)} chars). Using Chunking/Map-Reduce.")
            chunks = self._chunk_text(text)
            all_vocab = []
            seen_words = set()
            
            for i, chunk in enumerate(chunks):
                msg = f"Chunk {i+1}/{len(chunks)}"
                self.logger.info(f"Analyzing vocabulary: {msg}")
                if progress_callback: progress_callback(msg)
                
                prompt = get_vocabulary_prompt(subject)
                chunk_result = self._generate_json(prompt, chunk, subject, progress_callback)
                
                # Normalize to list (handles dict responses from LLM)
                items = self._normalize_to_list(chunk_result, ['vocabulary', 'words', 'terms'])
                
                new_items = []
                for item in items:
                    if isinstance(item, dict):
                        word = item.get('word', '').lower().strip()
                        if word and word not in seen_words:
                            seen_words.add(word)
                            all_vocab.append(item)
                            new_items.append(item)
                
                # Yield partial results immediately
                if partial_callback and new_items:
                    self.logger.info(f"Sending {len(new_items)} vocab items to partial_callback")
                    partial_callback(new_items)
            
            return all_vocab[:20] 
        else:
            prompt = get_vocabulary_prompt(subject)
            result = self._generate_json(prompt, text, subject, progress_callback)
            
            # Normalize to list
            items = self._normalize_to_list(result, ['vocabulary', 'words', 'terms'])
            
            # ALWAYS notify partial_callback
            if items and partial_callback:
                self.logger.info(f"Sending {len(items)} vocab items to partial_callback")
                partial_callback(items)
            return items

    def generate_questions(self, text, subject=DEFAULT_SUBJECT, count=5, progress_callback=None, partial_callback=None):
        """Generate quiz questions - always notifies via partial_callback for reactivity."""
        if len(text) > 20000:
            self.logger.info(f"Text too long ({len(text)} chars). Using Chunking/Map-Reduce for Quiz.")
            chunks = self._chunk_text(text)
            all_questions = []
            questions_per_chunk = max(1, count // len(chunks)) + 1
            
            for i, chunk in enumerate(chunks):
                msg = f"Chunk {i+1}/{len(chunks)}"
                self.logger.info(f"Generating questions: {msg}")
                if progress_callback: progress_callback(msg)
                
                prompt = get_question_prompt(subject, questions_per_chunk)
                chunk_result = self._generate_json(prompt, chunk, subject, progress_callback)
                
                # Normalize to list (handles dict responses from LLM)
                items = self._normalize_to_list(chunk_result, ['questions', 'quiz'])
                
                if items:
                    all_questions.extend(items)
                    # Yield partial results immediately
                    if partial_callback:
                        self.logger.info(f"Sending {len(items)} questions to partial_callback")
                        partial_callback(items)
            
            import random
            random.shuffle(all_questions)
            return all_questions[:count]
        else:
            prompt = get_question_prompt(subject, count)
            result = self._generate_json(prompt, text, subject, progress_callback)
            
            # Normalize to list
            items = self._normalize_to_list(result, ['questions', 'quiz'])
            
            # ALWAYS notify partial_callback
            if items and partial_callback:
                self.logger.info(f"Sending {len(items)} questions to partial_callback")
                partial_callback(items)
            return items

    def create_flashcards(self, text, subject=DEFAULT_SUBJECT, progress_callback=None, partial_callback=None):
        """Generate flashcards - always notifies via partial_callback for reactivity."""
        if len(text) > 20000:
            chunks = self._chunk_text(text)
            all_cards = []
            
            for i, chunk in enumerate(chunks):
                msg = f"Chunk {i+1}/{len(chunks)}"
                if progress_callback: progress_callback(msg)
                
                prompt = get_flashcard_prompt(subject)
                chunk_result = self._generate_json(prompt, chunk, subject, progress_callback)
                
                # Normalize to list (handles dict responses from LLM)
                items = self._normalize_to_list(chunk_result, ['flashcards', 'cards'])
                
                if items:
                    all_cards.extend(items)
                    # Yield partial results immediately
                    if partial_callback:
                        self.logger.info(f"Sending {len(items)} flashcards to partial_callback")
                        partial_callback(items)
            
            return all_cards[:15]
        else:
            prompt = get_flashcard_prompt(subject)
            result = self._generate_json(prompt, text, subject, progress_callback)
            
            # Normalize to list
            items = self._normalize_to_list(result, ['flashcards', 'cards'])
            
            # ALWAYS notify partial_callback
            if items and partial_callback:
                self.logger.info(f"Sending {len(items)} flashcards to partial_callback")
                partial_callback(items)
            return items

    def analyze_grammar(self, text, subject=DEFAULT_SUBJECT):
        """Analyze grammar and pragmatics (English only)."""
        prompt = get_grammar_prompt(subject)
        
        # Grammar analysis only available for English
        if prompt is None:
            self.logger.info(f"Grammar analysis skipped for subject: {subject}")
            return []
        
        result = self._generate_json(prompt, text, subject)
        
        # Robust parsing
        if isinstance(result, list):
             return result
        elif isinstance(result, dict):
             # Wrapper check
             if "grammar_points" in result: return result["grammar_points"]
             if "points" in result: return result["points"]
             if "analysis" in result: return result["analysis"]
             if "concepts" in result: return result["concepts"]
             
             # Single item check
             if "concept" in result and "explanation" in result:
                 return [result]
        return []

    def chat(self, text, user_question, subject=DEFAULT_SUBJECT, history=None):
        """Chat with the context of the class (Roleplay Mode)."""
        system_prompt = get_roleplay_prompt(subject)
        system_msg = system_prompt.replace("{text}", text)
        
        messages = [
            {'role': 'system', 'content': system_msg}
        ]
        if history:
            messages.extend(history)
        
        messages.append({'role': 'user', 'content': user_question})
        
        response = ollama.chat(model=self.model, messages=messages)
        return response['message']['content']

if __name__ == "__main__":
    # Test
    agent = LearningAgent()
    print("Agent initialized. Model:", agent.model)
    print("Available subjects:", list(SUBJECT_CONFIGS.keys()))
