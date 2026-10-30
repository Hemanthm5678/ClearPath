import json

TUTOR_SYSTEM_PROMPT = """You are ClearPath, an empathetic, confusion-aware adaptive math tutor.
Your goal is to guide students to genuine conceptual understanding without giving away the direct answer immediately unless needed.
Adapt your explanation based on the requested style (visual, analogy, step_by_step, simple_language) and level (1: gentle reframing, 2: deeper breakdown, 3: foundational prerequisite).
Always provide your answer in valid JSON strictly matching the requested schema."""

EXPLAIN_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "explanation": {"type": "string", "description": "Clear, friendly, empathetic explanation."},
        "check_question": {"type": "string", "description": "A quick low-stakes check question to verify comprehension."},
        "visual_description": {"type": "string", "description": "A concrete mental picture or diagram description."}
    },
    "required": ["explanation", "check_question", "visual_description"]
}

CHAT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string", "description": "Helpful, conversational, encouraging answer to student question."}
    },
    "required": ["reply"]
}

def build_explain_prompt(
    concept_name: str,
    question_prompt: str,
    style: str,
    level: int,
    reasons: list[str]
) -> str:
    reasons_str = ", ".join(reasons) if reasons else "general uncertainty"
    return f"""The student is working on the concept: "{concept_name}".
Current Question: "{question_prompt}"
Detected confusion signals: [{reasons_str}].

Generate a tutoring intervention with:
- Style: {style}
- Level: {level} (1 = light nudge, 2 = deep intuitive breakdown, 3 = step-by-step foundation)

Return valid JSON with:
{{
  "explanation": "...",
  "check_question": "...",
  "visual_description": "..."
}}
"""

def build_chat_prompt(
    concept_name: str,
    question_prompt: str,
    student_message: str
) -> str:
    return f"""The student is learning "{concept_name}".
Question being attempted: "{question_prompt}".
Student asks: "{student_message}".

Provide a concise, encouraging, and clear answer that addresses their specific confusion.
Return valid JSON:
{{
  "reply": "..."
}}
"""
