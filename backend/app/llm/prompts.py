"""
Structured Prompt Templates and Strict JSON Schemas for ClearPath LLM Tutor.

NOTE: Per architecture specifications, this file MUST NOT import the `groq` package.
Only backend/app/llm/gateway.py may import `groq`.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

TUTOR_SYSTEM_PROMPT = """You are ClearPath, an empathetic, confusion-aware adaptive math and computer science coding tutor.
Your goal is to guide students to genuine conceptual understanding without giving away the direct answer immediately.
Adapt your explanation based on the requested style (visual, analogy, worked/step_by_step, simple_language) and level (1=simple, 2=normal, 3=detailed).
Always provide your answer in valid JSON strictly matching the requested schema."""

# =============================================================================
# Strict JSON Schemas for Groq SDK Structured Outputs
# =============================================================================

EXPLAIN_CONCEPT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "explanation": {
            "type": "string",
            "description": "Clear, empathetic explanation tailored to the student age, style, and depth level."
        },
        "check_question": {
            "type": "string",
            "description": "A quick low-stakes check question to verify comprehension."
        },
        "visual_description": {
            "type": "string",
            "description": "A concrete mental picture or diagram description."
        }
    },
    "required": ["explanation", "check_question", "visual_description"],
    "additionalProperties": False
}

CHAT_REPLY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "reply": {
            "type": "string",
            "description": "Helpful, conversational, encouraging answer addressing student question."
        }
    },
    "required": ["reply"],
    "additionalProperties": False
}

ANALYZE_QUESTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "complexity_tier": {
            "type": "string",
            "enum": ["Easy", "Medium", "Hard"],
            "description": "Difficulty tier of the question based on cognitive load and multi-step reasoning."
        },
        "expected_time_sec": {
            "type": "integer",
            "description": "Expected response time in seconds (Easy: 20s, Medium: 45-55s, Hard: 65-75s)."
        },
        "complexity_weight": {
            "type": "number",
            "description": "Complexity multiplier (Easy: 1.0, Medium: 1.8, Hard: 2.5)."
        },
        "hint": {
            "type": "string",
            "description": "A pedagogical Socratic hint that nudges the student towards the first step without revealing the answer."
        },
        "step_by_step": {
            "type": "string",
            "description": "Clear step-by-step mathematical or code execution solution."
        },
        "visual_explanation": {
            "type": "string",
            "description": "Visual intuition, spatial layout, or coordinate/array diagram explaining the concept."
        },
        "visual_check_question": {
            "type": "string",
            "description": "Low-stakes check question verifying visual comprehension."
        },
        "analogy_explanation": {
            "type": "string",
            "description": "Real-world physical metaphor (e.g. scales, boxes, roads, food) explaining the logic."
        },
        "analogy_check_question": {
            "type": "string",
            "description": "Low-stakes check question verifying analogy comprehension."
        },
        "worked_explanation": {
            "type": "string",
            "description": "Step-by-step worked procedure with exact calculations and substitutions."
        },
        "worked_check_question": {
            "type": "string",
            "description": "Low-stakes check question verifying procedural understanding."
        },
        "simple_explanation": {
            "type": "string",
            "description": "Plain English ELI5 explanation or quick rule of thumb."
        },
        "simple_check_question": {
            "type": "string",
            "description": "Low-stakes check question verifying simple rule of thumb."
        }
    },
    "required": [
        "complexity_tier", "expected_time_sec", "complexity_weight",
        "hint", "step_by_step",
        "visual_explanation", "visual_check_question",
        "analogy_explanation", "analogy_check_question",
        "worked_explanation", "worked_check_question",
        "simple_explanation", "simple_check_question"
    ],
    "additionalProperties": False
}

# Aliases for backwards compatibility
EXPLAIN_JSON_SCHEMA = EXPLAIN_CONCEPT_SCHEMA
CHAT_JSON_SCHEMA = CHAT_REPLY_SCHEMA

PROMPT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "explain_concept": EXPLAIN_CONCEPT_SCHEMA,
    "chat_reply": CHAT_REPLY_SCHEMA,
    "analyze_question": ANALYZE_QUESTION_SCHEMA,
}


def get_response_format(prompt_name: str) -> Dict[str, Any]:
    """
    Returns strict JSON schema configuration for Groq SDK `response_format`.
    """
    schema = PROMPT_SCHEMAS.get(prompt_name)
    if schema:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": prompt_name,
                "strict": True,
                "schema": schema,
            }
        }
    return {"type": "json_object"}


# =============================================================================
# Prompt Builders
# =============================================================================

def render_explain_prompt(
    concept_name: str,
    student_age: Union[int, str] = 10,
    confusion_reasons: Optional[Union[List[str], str]] = None,
    style: str = "visual",
    level: Union[int, str] = 1,
    **kwargs
) -> str:
    """
    Prompt 1: explain_concept
    Inputs:
      - concept_name: str
      - student_age: int or str (e.g. 10)
      - confusion_reasons: list of str or str
      - style: str ('analogy', 'visual', 'worked')
      - level: int or str (1=simple, 2=normal, 3=detailed)
    """
    if isinstance(confusion_reasons, list):
        reasons_str = ", ".join(confusion_reasons) if confusion_reasons else "general hesitation"
    elif confusion_reasons:
        reasons_str = str(confusion_reasons)
    else:
        reasons_str = "general hesitation"

    # Normalize style
    style_norm = str(style).lower()
    if "worked" in style_norm or "step" in style_norm:
        style_desc = "worked (step-by-step procedure with worked example)"
    elif "analogy" in style_norm:
        style_desc = "analogy (relatable real-world metaphor)"
    elif "simple" in style_norm:
        style_desc = "simple_language (plain simple terms, elementary vocabulary, formulas or rules of thumb)"
    else:
        style_desc = "visual (concrete mental image and diagram layout)"

    # Normalize level
    level_val = str(level).lower()
    if level_val in ("1", "simple", "light"):
        level_desc = "1 (simple: intuitive nudge, everyday vocabulary, gentle reframing)"
    elif level_val in ("3", "detailed", "deep"):
        level_desc = "3 (detailed: deep foundational mechanics and rigorous step-by-step logic)"
    else:
        level_desc = "2 (normal: clear conceptual explanation with standard depth)"

    question_prompt = kwargs.get("question_prompt", "")
    q_line = f'Current problem being attempted: "{question_prompt}"\n' if question_prompt else ""

    prompt_focus = (
        f'CRITICAL INSTRUCTION: Your explanation, analogy, and visual diagram MUST specifically focus on the current problem: "{question_prompt}". Use the exact numbers and items from this problem. Do NOT use numbers, items, or examples from unrelated questions.\n'
        if question_prompt else ""
    )

    domain_label = "coding / computer science" if ("python" in concept_name.lower() or "code" in str(kwargs.get("question_id", "")).lower() or "def " in question_prompt) else "mathematics"
    audience_level = "high school / undergraduate computer science & math" if domain_label == "coding / computer science" or "algebra" in concept_name.lower() or "quadratic" in concept_name.lower() else f"{student_age} years old"

    return f"""The student is learning {domain_label} concept: "{concept_name}".
Audience Level: {audience_level}.
{q_line}Detected confusion indicators: [{reasons_str}].

Pedagogical intervention parameters:
- Explanation Style: {style_desc}
- Depth Level: {level_desc}

{prompt_focus}Provide a targeted intervention strictly in JSON with keys:
- "explanation": clear explanation matching student level, style, and depth level
- "check_question": a quick low-stakes check question to verify comprehension
- "visual_description": a concrete mental picture or diagram description
"""


def render_chat_prompt(
    chat_history: Optional[Union[List[Dict[str, str]], str]] = None,
    concept: str = "Fractions",
    student_message: str = "",
    **kwargs
) -> str:
    """
    Prompt 2: chat_reply
    Inputs:
      - chat_history: list of messages or string
      - concept: str
      - student_message: str
    """
    history_lines: List[str] = []
    if isinstance(chat_history, list):
        for msg in chat_history:
            role = msg.get("role", "student")
            content = msg.get("content", "")
            history_lines.append(f"{role.capitalize()}: {content}")
    elif chat_history:
        history_lines.append(str(chat_history))

    history_block = ""
    if history_lines:
        history_block = "Recent Conversation History:\n" + "\n".join(history_lines) + "\n\n"

    question_prompt = kwargs.get("question_prompt", "")
    q_line = f'Current problem being attempted: "{question_prompt}"\n' if question_prompt else ""

    return f"""The student is learning about math concept: "{concept}".
{q_line}{history_block}Student asks: "{student_message}"

Provide a friendly, conversational, and encouraging response that directly addresses their confusion in relation to their current problem without giving away final test answers immediately.
Return strictly valid JSON with key:
- "reply": helpful, conversational, encouraging explanation
"""


def render_analyze_question_prompt(
    concept_name: str,
    prompt: str,
    options: List[str],
    correct_answer: str,
    user_difficulty: Optional[str] = None,
) -> str:
    """
    Prompt 3: analyze_question
    Analyzes a newly submitted teacher question to automatically synthesize:
    - Complexity tier, timing thresholds, and weight
    - Socratic student hint
    - All 4 multimodal scaffolding explanations (Visual, Analogy, Step-by-Step, Simple)
    """
    options_text = "\n".join(f"- {opt}" for opt in options)
    diff_constraint = (
        f"The teacher preferred difficulty tier is: '{user_difficulty}'. Align with this tier if appropriate.\n"
        if user_difficulty and user_difficulty.lower() != "auto"
        else ""
    )

    return f"""A teacher has added a new multiple-choice question to the curriculum under concept: "{concept_name}".

QUESTION:
{prompt}

OPTIONS:
{options_text}

CORRECT ANSWER:
{correct_answer}

{diff_constraint}
TASK:
1. Determine the appropriate difficulty tier ("Easy", "Medium", or "Hard"), expected student response time in seconds (e.g. 20s for easy, 45-55s for medium, 65-75s for hard), and complexity multiplier (1.0 for Easy, 1.8 for Medium, 2.5 for Hard).
2. Generate a Socratic pedagogical hint that points the student in the right direction without giving away the direct answer.
3. Write a clear step-by-step mathematical or code tracing solution.
4. Synthesize all 4 multimodal pedagogical scaffolds with a comprehension check question for each:
   - Visual: spatial or visual mental model of why the answer is true.
   - Analogy: real-world concrete metaphor.
   - Worked: step-by-step procedure.
   - Simple Language: ELI5 plain English rule of thumb.

Return strictly valid JSON adhering to the required schema."""


def build_prompt_payload(
    prompt_name: str,
    context_dict: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Builds system prompt, user prompt, and Groq strict JSON schema response_format.
    """
    ctx = context_dict or {}
    response_format = get_response_format(prompt_name)

    if prompt_name == "explain_concept":
        user_prompt = render_explain_prompt(
            concept_name=ctx.get("concept_name") or ctx.get("concept") or "Fractions",
            student_age=ctx.get("student_age", 10),
            confusion_reasons=ctx.get("confusion_reasons") or ctx.get("reasons", []),
            style=ctx.get("style", "visual"),
            level=ctx.get("level", 1),
            question_prompt=ctx.get("question_prompt", "")
        )
    elif prompt_name == "chat_reply":
        user_prompt = render_chat_prompt(
            chat_history=ctx.get("chat_history", []),
            concept=ctx.get("concept") or ctx.get("concept_name") or "Fractions",
            student_message=ctx.get("student_message") or ctx.get("message", "")
        )
    elif prompt_name == "analyze_question":
        user_prompt = render_analyze_question_prompt(
            concept_name=ctx.get("concept_name") or ctx.get("concept") or "STEM Concept",
            prompt=ctx.get("prompt", ""),
            options=ctx.get("options", []),
            correct_answer=ctx.get("correct_answer", ""),
            user_difficulty=ctx.get("user_difficulty")
        )
    else:
        # Fallback generic prompt
        user_prompt = ctx.get("prompt") or str(ctx)

    return TUTOR_SYSTEM_PROMPT, user_prompt, response_format


# Backwards compatibility wrappers
def build_explain_prompt(
    concept_name: str,
    question_prompt: str,
    style: str,
    level: int,
    reasons: list[str]
) -> str:
    return render_explain_prompt(
        concept_name=concept_name,
        question_prompt=question_prompt,
        style=style,
        level=level,
        confusion_reasons=reasons
    )


def build_chat_prompt(
    concept_name: str,
    question_prompt: str,
    student_message: str
) -> str:
    return render_chat_prompt(
        concept=concept_name,
        student_message=student_message,
        question_prompt=question_prompt
    )
