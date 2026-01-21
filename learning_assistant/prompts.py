# Prompts for Multi-Subject Learning Assistant
# UX Principles: Don Norman "Don't Make Me Think", Hick's Law, Fitts' Law
# Courses extracted from: https://material-docente.web.app/

# =============================================================================
# SUBJECT CONFIGURATIONS - UIDE Courses (Hick: Max 7 options)
# =============================================================================

SUBJECT_CONFIGS = {
    "simulacion": {
        "name": "Simulación",
        "icon": "🎲",
        "system_role": "You are an expert in simulation and Monte Carlo methods, specialized in random number generators, statistical tests, and complex system modeling.",
        "vocabulary_label": "Términos de Simulación",
        "vocabulary_focus": "random generators, probability distributions, goodness-of-fit tests, Monte Carlo techniques, simulation models",
        "quiz_style": "problem solving with probability, analysis of simulation outputs, statistical validation",
        "features": ["vocabulary", "quiz", "flashcards", "concepts"],
        "show_grammar": False,
        "show_level": False
    },
    "pmsbd": {
        "name": "PMSBD",
        "icon": "🔌",
        "system_role": "You are an expert in Middleware Programming and Database Security, specialized in REST APIs, Microservices, OAuth2, and secure backend development.",
        "vocabulary_label": "Términos de APIs/Middleware",
        "vocabulary_focus": "REST endpoints, HTTP methods, OAuth2 flows, JWT tokens, microservices patterns, API security",
        "quiz_style": "API design decisions, security scenarios, authentication/authorization flows",
        "features": ["vocabulary", "quiz", "flashcards", "concepts"],
        "show_grammar": False,
        "show_level": False
    },
    "hci": {
        "name": "HCI",
        "icon": "👤",
        "system_role": "You are an expert in Human-Computer Interaction, specialized in usability, user experience (UX), accessibility, and human-centered design principles.",
        "vocabulary_label": "Términos de UX/Usabilidad",
        "vocabulary_focus": "usability heuristics, UX patterns, accessibility guidelines (WCAG), user research methods, interaction design",
        "quiz_style": "usability evaluation, design critique, accessibility assessment",
        "features": ["vocabulary", "quiz", "flashcards", "concepts"],
        "show_grammar": False,
        "show_level": False
    },
    "estructuras": {
        "name": "Estructuras de Datos",
        "icon": "🌳",
        "system_role": "You are an expert in Data Structures and Algorithms, specialized in stacks, queues, trees, graphs, and complexity analysis.",
        "vocabulary_label": "Estructuras y Algoritmos",
        "vocabulary_focus": "data structures (stacks, queues, trees, graphs), algorithm complexity (Big O), sorting, searching, recursion",
        "quiz_style": "algorithm analysis, code tracing, complexity calculation, data structure selection",
        "features": ["vocabulary", "quiz", "flashcards", "concepts"],
        "show_grammar": False,
        "show_level": False
    },
    "sgbd": {
        "name": "SGBD",
        "icon": "🗄️",
        "system_role": "You are an expert in Database Management Systems, specialized in ACID transactions, concurrency control, logging, recovery, and SQL optimization.",
        "vocabulary_label": "Términos de BD",
        "vocabulary_focus": "ACID properties, transaction isolation levels, locking mechanisms, query optimization, database recovery",
        "quiz_style": "transaction analysis, concurrency scenarios, SQL query optimization",
        "features": ["vocabulary", "quiz", "flashcards", "concepts"],
        "show_grammar": False,
        "show_level": False
    },
    "ing_software": {
        "name": "Ing. Software",
        "icon": "⚙️",
        "system_role": "You are an expert in Software Engineering, specialized in software lifecycle, Agile methodologies (Scrum/XP), requirements engineering, and quality assurance.",
        "vocabulary_label": "Términos de Ing. Software",
        "vocabulary_focus": "software lifecycle phases, Scrum artifacts, user stories, testing types, code quality metrics",
        "quiz_style": "methodology selection, requirements analysis, QA scenarios",
        "features": ["vocabulary", "quiz", "flashcards", "concepts"],
        "show_grammar": False,
        "show_level": False
    },
    "aipti": {
        "name": "AIPTI",
        "icon": "☁️",
        "system_role": "You are an expert in IT Platform Architecture and Integration, specialized in cloud computing, virtualization, SOA, and distributed systems.",
        "vocabulary_label": "Términos de Arquitectura TI",
        "vocabulary_focus": "cloud models (IaaS/PaaS/SaaS), virtualization, containers, SOA, microservices, distributed systems",
        "quiz_style": "architecture decisions, cloud deployment scenarios, integration patterns",
        "features": ["vocabulary", "quiz", "flashcards", "concepts"],
        "show_grammar": False,
        "show_level": False
    },
    "english": {
        "name": "English",
        "icon": "🇬🇧",
        "system_role": "You are an expert English tutor specializing in language learning, grammar, and vocabulary acquisition.",
        "vocabulary_label": "Vocabulary",
        "vocabulary_focus": "phrasal verbs, idioms, collocations, academic terms",
        "quiz_style": "comprehension questions and grammar exercises",
        "features": ["vocabulary", "quiz", "flashcards", "grammar", "level"],
        "show_grammar": True,
        "show_level": True
    }
}

# Default subject for backward compatibility
DEFAULT_SUBJECT = "english"

# =============================================================================
# DYNAMIC PROMPT GENERATORS
# =============================================================================

def get_system_role(subject: str) -> str:
    """Get the system role for a subject."""
    config = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
    return config["system_role"]

def get_summary_prompt(subject: str) -> str:
    """Generate summary prompt based on subject."""
    config = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
    
    if subject == "english":
        return """
You are an expert English teacher. 
Analyze the following transcription of an English class.

Transcription:
{text}

Instructions:
Provide a concise summary of the key topics covered, main grammar points explanations, and the general CEFR level (A1-C2) of the content.

Output format (JSON):
{{
    "summary": "...",
    "topics": ["topic1", "topic2"],
    "level": "B1"
}}
"""
    else:
        return f"""
You are {config['system_role']}. 
Analyze the following transcription of a class or lecture.

Transcription:
{{text}}

Instructions:
Provide a concise summary in Spanish of the key topics covered and main concepts explained.

Output format (JSON):
{{{{
    "summary": "A comprehensive summary of the content in Spanish...",
    "topics": ["topic1", "topic2", "topic3"],
    "key_concepts": ["concept1", "concept2"]
}}}}
"""

def get_vocabulary_prompt(subject: str) -> str:
    """Generate vocabulary extraction prompt based on subject."""
    config = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
    vocab_focus = config.get("vocabulary_focus", "important terms")
    
    if subject == "english":
        return """
You are an English teacher.

Transcription:
{text}

Instructions:
Identify important, useful, or difficult vocabulary from the class transcription above.
Focus on:
1. Phrasal verbs
2. Idioms/Collocations
3. Academic or specific terms
4. Words that seem to be the focus of the lesson
Ignore common basic words.

Output format (JSON List):
[
    {{
        "word": "look forward to",
        "definition": "To feel happy and excited about something that is going to happen",
        "example": "I look forward to hearing from you.",
        "type": "phrasal_verb",
        "level": "B1"
    }},
    ...
]
"""
    else:
        return f"""
You are {config['system_role']}.

Transcription:
{{text}}

Instructions:
Extract the most important technical terms, concepts, and code syntax from this transcription.
Focus on: {vocab_focus}, programming syntax, libraries, and reserved words.
Provide definitions in Spanish.
Ensure you extract at least 5 terms if possible.

Output format (JSON List):
[
    {{{{
        "word": "term/concept/syntax",
        "definition": "Clear definition in Spanish",
        "example": "Usage context",
        "code": "Optional code snippet (e.g. 'import pandas as pd', 'def func():') if applicable",
        "type": "concept/code"
    }}}},
    ...
]
"""

def get_question_prompt(subject: str, count: int = 5) -> str:
    """Generate quiz question prompt based on subject."""
    config = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
    quiz_style = config.get("quiz_style", "comprehension questions")
    
    lang_instruction = "in English" if subject == "english" else "in Spanish"
    
    return f"""
You are {config['system_role']}.

Transcript:
{{text}}

Instructions:
Generate {count} multiple-choice questions {lang_instruction} based on the transcript above to test understanding.
Focus on: {quiz_style}
Ensure questions cover different parts of the content.

Output Format (JSON List):
[
    {{{{
      "question": "Question text...",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "Option A",
      "explanation": "Why this is correct...",
      "type": "multiple_choice"
    }}}},
    ...
]
"""

def get_flashcard_prompt(subject: str) -> str:
    """Generate flashcard prompt based on subject."""
    config = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
    
    lang_instruction = "in English" if subject == "english" else "in Spanish"
    
    return f"""
You are {config['system_role']}.

Transcript:
{{text}}

Instructions:
Generate flashcards for spaced repetition {lang_instruction} based on the transcript above.
Create cards for all key concepts, definitions, or important facts found.
Generate at least 5-10 cards.

Output Format (JSON List):
[
    {{{{
      "front": "Concept or Question",
      "back": "Definition or Answer"
    }}}},
    ...
]
"""

def get_grammar_prompt(subject: str) -> str:
    """Generate grammar analysis prompt (English only)."""
    if subject != "english":
        return None
    
    return """
Act as an Applied Linguist. 
Analyze the transcript for grammar and pragmatics (usage in context).

Transcript:
{text}

Instructions:
Identify interesting grammar points, pragmatic uses, or nuances found in the text.
The number of points should depend on the complexity of the speech.

Output Format (JSON List):
[
    {
      "concept": "Name of the concept (e.g., 'Third Conditional', 'Irony')",
      "example_in_text": "The exact quote from text",
      "explanation": "Pedagogical explanation of WHY it was used here.",
      "rule": "The general rule",
      "tone_learning": "Comment on tone (e.g., Polite correction, Strong emphasis)" 
    },
    ...
]
"""

def get_roleplay_prompt(subject: str) -> str:
    """Generate roleplay system prompt based on subject."""
    config = SUBJECT_CONFIGS.get(subject, SUBJECT_CONFIGS[DEFAULT_SUBJECT])
    
    lang_instruction = "Respond in English." if subject == "english" else "Responde en español."
    
    return f"""
Act as the SPEAKER from the following transcript. You are {config['system_role']}.
Adopt their tone, vocabulary, and style. {lang_instruction}
The user is a student asking you follow-up questions about what you just said.

Instructions:
1. Stay in character (Persona).
2. Answer based strictly on the transcript info, but you can expand slightly using general knowledge if it fits the persona.
3. Be helpful, encouraging, and pedagogical (like a tutor).
4. If the user makes a mistake, politely correct them in a natural way.

Transcript Context:
{{text}}
"""

# =============================================================================
# LEGACY PROMPTS (for backward compatibility)
# =============================================================================

SUMMARY_PROMPT = get_summary_prompt("english")
VOCABULARY_PROMPT = get_vocabulary_prompt("english")
QUESTION_PROMPT = get_question_prompt("english")
FLASHCARD_PROMPT = get_flashcard_prompt("english")
GRAMMAR_ANALYSIS_PROMPT = get_grammar_prompt("english")
ROLEPLAY_SYSTEM_PROMPT = get_roleplay_prompt("english")
