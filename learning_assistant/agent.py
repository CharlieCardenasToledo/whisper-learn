import ollama
import json
import logging
from .prompts import SUMMARY_PROMPT, VOCABULARY_PROMPT, QUESTION_PROMPT, FLASHCARD_PROMPT

MODEL_NAME = "llama3.1:8b"

class LearningAgent:
    def __init__(self, model_name=MODEL_NAME):
        self.model = model_name
        self.logger = logging.getLogger(__name__)

    def _generate_json(self, prompt, context_text):
        """Generic method to generate JSON output from LLM"""
        full_prompt = prompt.replace("{text}", context_text)
        self.logger.debug(f"Sending prompt to LLM (Length: {len(full_prompt)})")
        
        try:
            response = ollama.chat(model=self.model, messages=[
                {
                    'role': 'system',
                    'content': 'You are a helpful AI English Tutor. You output strictly Valid JSON.'
                },
                {
                    'role': 'user',
                    'content': full_prompt
                }
            ], format='json', options={'temperature': 0.2})
            
            content = response['message']['content']
            self.logger.debug(f"Raw LLM Response: {content}")
            
            parsed = json.loads(content)
            self.logger.info(f"Successfully parsed JSON. Type: {type(parsed)}")
            return parsed
        except Exception as e:
            self.logger.error(f"Error generating/parsing JSON: {e}", exc_info=True)
            return None

    def generate_summary(self, text):
        """Generate class summary and level"""
        return self._generate_json(SUMMARY_PROMPT, text)

    def extract_vocabulary(self, text):
        """Extract vocabulary list"""
        result = self._generate_json(VOCABULARY_PROMPT, text)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            # Check if it's a wrapper
            if "vocabulary" in result: return result["vocabulary"]
            if "words" in result: return result["words"]
            if "items" in result: return result["items"]
            
            # Check if it's a SINGLE item (Llama 3 sometimes returns just one object)
            if "word" in result and "definition" in result:
                return [result]
                
        return []

    def generate_questions(self, text, count=5):
        """Generate quiz questions"""
        prompt = QUESTION_PROMPT.replace("{count}", str(count))
        result = self._generate_json(prompt, text)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
             if "questions" in result: return result["questions"]
             if "quiz" in result: return result["quiz"]
             # Single item check
             if "question" in result and "options" in result:
                 return [result]
        return []

    def create_flashcards(self, text):
        """Generate flashcards"""
        result = self._generate_json(FLASHCARD_PROMPT, text)
        if isinstance(result, list):
             return result
        elif isinstance(result, dict):
             if "flashcards" in result: return result["flashcards"]
             if "cards" in result: return result["cards"]
             # Single item check
             if "front" in result and "back" in result:
                 return [result]
        return []

    def analyze_grammar(self, text):
        """Analyze grammar and pragmatics (Phase 1)"""
        from .prompts import GRAMMAR_ANALYSIS_PROMPT
        result = self._generate_json(GRAMMAR_ANALYSIS_PROMPT, text)
        
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

    def chat(self, text, user_question, history=None):
        """Chat with the context of the class"""
        messages = [
            {'role': 'system', 'content': f"You are an English Tutor. Answer the student's question based strictly on this class transcript:\n\n{text}"}
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
