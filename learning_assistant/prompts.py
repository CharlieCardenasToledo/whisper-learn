# Prompts for English Learning Assistant

SUMMARY_PROMPT = """
You are an expert English teacher. Analyze the following transcription of an English class.
Provide a concise summary of the key topics covered, main grammar points explanations, and the general CEFR level (A1-C2) of the content.

Transcription:
{text}

Output format (JSON):
{{
    "summary": "...",
    "topics": ["topic1", "topic2"],
    "level": "B1"
}}
"""

VOCABULARY_PROMPT = """
You are an English teacher. Identify important, useful, or difficult vocabulary from the class transcription.
Focus on:
1. Phrasal verbs
2. Idioms/Collocations
3. Academic or specific terms
4. Words that seem to be the focus of the lesson

Ignore common basic words unless they are used in a novel way.

Transcription:
{text}

Output format (JSON list of max 15 items):
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

QUESTION_PROMPT = """
You are an English teacher creating a quiz for your students based on the class transcription.
Generate {count} questions to test comprehension and grammar concepts discussed.

Requirements:
- Mix of multiple choice (main) and true/false.
- Questions should focus on what was explicitly taught or discussed.
- Ensure only one correct answer per question.

Transcription:
{text}

Output format (JSON list):
[
    {{
        "question": "What is the main difference between present perfect and past simple mentioned?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option B",
        "explanation": "The teacher explained that...",
        "type": "multiple_choice"
    }},
    ...
]
"""

FLASHCARD_PROMPT = """
Target: Create flashcards for spaced repetition based on this class.
Focus on vocabulary, grammar rules, or key concepts explained.

Transcription:
{text}

Output format (JSON list of max 10 items):
[
    {{
        "front": "What is the past participle of 'go'?",
        "back": "Gone"
    }},
    {{
        "front": "Explanation of 'used to'",
        "back": "Used for past habits that are not true anymore."
    }}
]
"""
