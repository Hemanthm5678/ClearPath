"""
ClearPath LLM Gateway.

HARD RULE: This is the ONLY file in the entire repository that may import the `groq` package.
All LLM requests must pass through `ask(prompt_name, context_dict)`.

Flow:
1. Check exact match in SQLite cache.
2. If rate limited or groq throws error, fetch from `data/explanations.json` (offline bank) based on concept ID.
3. Try `llama-3.1-8b-instant`. If rate limit, fallback to `llama-3.3-70b-versatile`.
4. Save to cache and return.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# HARD RULE: gateway.py is the ONLY file that imports `groq`.
try:
    from groq import Groq, RateLimitError
except ImportError:
    Groq = None  # type: ignore
    RateLimitError = None  # type: ignore

from backend.app.config import settings
from backend.app.database import (
    get_cached_llm,
    get_stats,
    increment_stat,
    set_cached_llm,
)
from backend.app.llm.prompts import (
    TUTOR_SYSTEM_PROMPT,
    build_prompt_payload,
)

logger = logging.getLogger("clearpath.gateway")

# In-memory rate limiting throttle
_request_timestamps: List[float] = []
_offline_bank: Dict[str, Any] = {}

DEFAULT_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]
PRIMARY_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODEL = "openai/gpt-oss-120b"


def _resolve_explanations_file() -> Path:
    """Finds explanations.json across data/ and backend/data/ directories."""
    candidates = [
        settings.DATA_DIR / "explanations.json",
        settings.ROOT_DIR / "data" / "explanations.json",
        settings.BACKEND_DIR / "data" / "explanations.json",
        Path("data/explanations.json"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def load_offline_bank() -> Dict[str, Any]:
    """Loads and caches the offline bank from data/explanations.json."""
    global _offline_bank
    if not _offline_bank:
        bank_path = _resolve_explanations_file()
        if bank_path.exists():
            try:
                with open(bank_path, "r", encoding="utf-8") as f:
                    _offline_bank = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load offline bank from {bank_path}: {e}")
    return _offline_bank


def _normalize_concept_id(concept_raw: Any) -> str:
    """Maps concept input (ID or name) to verified concept ID in offline bank."""
    if not concept_raw:
        return "c3_fraction_as_division"

    raw = str(concept_raw).strip()
    bank = load_offline_bank()
    if raw in bank:
        return raw

    # Mapping table for human-friendly names or partial identifiers
    name_map = {
        "c1": "c1_fraction_basics",
        "fraction basics": "c1_fraction_basics",
        "c2": "c2_equal_parts",
        "equal parts": "c2_equal_parts",
        "equal part partitioning": "c2_equal_parts",
        "c3": "c3_fraction_as_division",
        "fraction as division": "c3_fraction_as_division",
        "fractions as division": "c3_fraction_as_division",
        "c4": "c4_equivalent_fractions",
        "equivalent fractions": "c4_equivalent_fractions",
        "c5": "c5_comparing_fractions",
        "comparing fractions": "c5_comparing_fractions",
        "c6": "c6_adding_fractions",
        "adding fractions": "c6_adding_fractions",
        "c7": "c7_python_tracing",
        "python": "c7_python_tracing",
        "coding": "c7_python_tracing",
        "tracing": "c7_python_tracing",
        "c8": "c8_quadratic_algebra",
        "quadratic": "c8_quadratic_algebra",
        "quadratics": "c8_quadratic_algebra",
        "algebra": "c8_quadratic_algebra",
        "deep algebra": "c8_quadratic_algebra",
    }
    lowered = raw.lower()
    for key, cid in name_map.items():
        if key in lowered:
            return cid

    return "c3_fraction_as_division"


def get_offline_explanation(
    concept_id: str,
    style: str = "visual",
    level: Union[int, str] = 1,
    question_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves guaranteed offline explanation from data/explanations.json based on question ID or concept ID.
    Ensures output JSON schema: {explanation, check_question, visual_description}.
    """
    bank = load_offline_bank()
    concept_entry = None

    # Prioritize exact question entry in bank if available
    if question_id and question_id in bank:
        concept_entry = bank[question_id]

    if not concept_entry:
        cid = _normalize_concept_id(concept_id)
        concept_entry = bank.get(cid) or bank.get("c3_fraction_as_division", {})

    # Map style
    style_norm = str(style).lower()
    if "worked" in style_norm or "step" in style_norm:
        style_key = "worked" if "worked" in concept_entry else "step_by_step"
    elif "analogy" in style_norm:
        style_key = "analogy"
    elif "simple" in style_norm:
        style_key = "simple_language"
    else:
        style_key = "visual"

    style_entry = concept_entry.get(style_key) or concept_entry.get("visual", {})

    # Map level
    level_val = str(level).lower()
    if level_val in ("3", "detailed", "deep"):
        lvl_key = "level_3"
    elif level_val in ("2", "normal", "medium"):
        lvl_key = "level_2"
    else:
        lvl_key = "level_1"

    data = style_entry.get(lvl_key) or style_entry.get("level_1") or {}

    explanation = data.get(
        "explanation",
        "Let's break this down step-by-step: focus on how many total equal parts make the whole, and how many parts are being considered."
    )
    check_question = data.get(
        "check_question",
        "What is the total number of equal parts in this problem?"
    )
    visual_description = data.get(
        "visual_description",
        "Draw the whole shape divided into equal sections, and shade the target portions."
    )

    return {
        "explanation": explanation,
        "check_question": check_question,
        "visual_description": visual_description,
        "source": "offline_bank",
    }


def get_offline_chat_reply(
    student_message: str = "",
    concept_id: str = "c3_fraction_as_division",
) -> Dict[str, Any]:
    """Guaranteed offline chat reply for student follow-up queries."""
    cid = _normalize_concept_id(concept_id)
    bank = load_offline_bank()
    concept_name = cid.replace("c1_", "").replace("c2_", "").replace("c3_", "").replace("c4_", "").replace("c5_", "").replace("c6_", "").replace("_", " ").title()

    return {
        "reply": f"Great question about {concept_name}! When thinking through this, try visualizing the problem with smaller numbers or sketching equal slices. The top number counts parts you have, and the bottom number counts total parts in the whole. You're doing great—give it another try!",
        "source": "offline_bank",
    }


def _is_rate_limited() -> bool:
    """Client-side token bucket / sliding window rate limiter."""
    global _request_timestamps
    now = time.time()
    _request_timestamps = [t for t in _request_timestamps if now - t < 60.0]
    if len(_request_timestamps) >= settings.RATE_LIMIT_RPM:
        return True
    _request_timestamps.append(now)
    return False


def get_groq_client() -> Optional[Any]:
    """Instantiates Groq client safely if API key is present."""
    if Groq is None or not settings.GROQ_API_KEY or not settings.GROQ_API_KEY.strip():
        return None
    try:
        return Groq(api_key=settings.GROQ_API_KEY.strip())
    except Exception as e:
        logger.warning(f"Error initializing Groq client: {e}")
        return None


def _is_rate_limit_error(e: Exception) -> bool:
    """Detects Groq API rate limits (HTTP 429 or RateLimitError)."""
    if RateLimitError is not None and isinstance(e, RateLimitError):
        return True
    err_str = str(e).lower()
    if "rate_limit" in err_str or "rate limit" in err_str or "429" in err_str:
        return True
    if getattr(e, "status_code", None) == 429:
        return True
    return False


def ask(
    prompt_name: str,
    context_dict: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main LLM Tutor entrypoint:
    1. Check exact match in SQLite cache.
    2. If rate limited or groq throws error, fetch from data/explanations.json (offline bank) based on concept ID.
    3. Try llama-3.1-8b-instant. If rate limit, fallback to llama-3.3-70b-versatile.
    4. Save to cache and return.

    Accepts both:
      ask("explain_concept", {"concept_name": ..., "style": ..., "level": ...})
      ask("chat_reply", {"concept": ..., "student_message": ...})
    and legacy kwarg invocations for backwards compatibility.
    """
    # 0. Normalize inputs
    if prompt_name not in ("explain_concept", "chat_reply"):
        # Legacy positional invocation: prompt_name was raw prompt string
        if kwargs.get("is_chat"):
            actual_prompt = "chat_reply"
            ctx = {
                "student_message": kwargs.get("chat_message", ""),
                "concept": kwargs.get("fallback_concept_id", "c3_fraction_as_division"),
                "concept_id": kwargs.get("fallback_concept_id", "c3_fraction_as_division"),
                "chat_history": [],
            }
        else:
            actual_prompt = "explain_concept"
            ctx = {
                "concept_name": kwargs.get("concept_name", "Fractions"),
                "concept_id": kwargs.get("fallback_concept_id", "c3_fraction_as_division"),
                "student_age": kwargs.get("student_age", 10),
                "confusion_reasons": kwargs.get("reasons", []),
                "style": kwargs.get("style", "visual"),
                "level": kwargs.get("level", 1),
                "prompt": prompt_name,
            }
        prompt_name = actual_prompt
        context_dict = ctx
    else:
        context_dict = dict(context_dict or {})
        # Merge any additional kwargs into context_dict
        for k, v in kwargs.items():
            if k not in context_dict:
                context_dict[k] = v

    # 1. Check exact match in SQLite cache
    cache_payload = json.dumps({"name": prompt_name, "ctx": context_dict}, sort_keys=True)
    cache_key = hashlib.sha256(cache_payload.encode("utf-8")).hexdigest()

    cached = get_cached_llm(cache_key)
    if cached:
        increment_stat("cache_hits")
        cached["source"] = "cache"
        return cached

    # Determine concept ID for fallback
    concept_id = (
        context_dict.get("concept_id")
        or context_dict.get("concept")
        or context_dict.get("concept_name")
        or context_dict.get("fallback_concept_id")
        or "c3_fraction_as_division"
    )

    # 3. Try llama-3.1-8b-instant. If rate limit, fallback to llama-3.3-70b-versatile.
    client = get_groq_client()
    groq_success: Optional[Dict[str, Any]] = None

    if client is not None and not _is_rate_limited():
        system_prompt, user_prompt, response_format = build_prompt_payload(prompt_name, context_dict)
        models_to_try = DEFAULT_MODELS

        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=settings.TEMPERATURE,
                    max_tokens=settings.MAX_TOKENS,
                    timeout=min(6.0, settings.TIMEOUT_SECONDS),
                    response_format=response_format,
                )
                raw_text = completion.choices[0].message.content or "{}"
                parsed = json.loads(raw_text)

                # Validate expected keys based on prompt
                if prompt_name == "explain_concept":
                    if not all(k in parsed for k in ("explanation", "check_question", "visual_description")):
                        raise ValueError(f"Incomplete schema returned from Groq: {list(parsed.keys())}")
                elif prompt_name == "chat_reply":
                    if "reply" not in parsed:
                        raise ValueError(f"Missing reply key in Groq response: {list(parsed.keys())}")

                parsed["source"] = "groq"
                increment_stat("groq_calls")
                groq_success = parsed
                break

            except Exception as e:
                is_rl = _is_rate_limit_error(e)
                if is_rl:
                    logger.warning(f"Groq model {model} rate limited: {e}. Falling back to next model...")
                    continue
                else:
                    logger.warning(f"Groq model {model} failed: {e}. Falling back...")
                    continue

    if groq_success is not None:
        # 4. Save to cache and return
        set_cached_llm(cache_key, prompt_name, groq_success)
        return groq_success

    # 2. If rate limited or groq throws error, fetch from data/explanations.json (offline bank) based on question or concept ID.
    increment_stat("offline_used")
    if prompt_name == "chat_reply":
        student_msg = str(context_dict.get("student_message") or context_dict.get("message") or "")
        result = get_offline_chat_reply(student_msg, concept_id=str(concept_id))
    else:
        style = str(context_dict.get("style", "visual"))
        level = context_dict.get("level", 1)
        qid = context_dict.get("question_id")
        result = get_offline_explanation(str(concept_id), style=style, level=level, question_id=qid)

    result["source"] = "offline_bank"

    # 4. Save to cache and return
    set_cached_llm(cache_key, prompt_name, result)
    return result


def update_offline_bank(question_id: str, data: Dict[str, Any]) -> None:
    """Updates in-memory offline bank dynamically when teacher publishes a question."""
    global _offline_bank
    if _offline_bank is None:
        _offline_bank = {}
    _offline_bank[question_id] = data


def analyze_question_with_ai_tutor(
    prompt: str,
    options: List[str],
    correct_answer: str,
    concept_id: str,
    concept_name: str,
    user_difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    """
    AI Tutor auto-analysis for newly submitted teacher questions.
    Analyzes question complexity, timing, hints, and synthesizes all 4 multimodal scaffolding explanations.
    """
    clean_p = prompt.strip()
    clean_a = correct_answer.strip()
    norm_diff = (user_difficulty or "auto").capitalize()

    # 1. Try Groq LLM if client is active
    client = get_groq_client()
    if client is not None:
        system_prompt, user_prompt, response_format = build_prompt_payload(
            "analyze_question",
            {
                "concept_name": concept_name,
                "concept": concept_name,
                "prompt": clean_p,
                "options": options,
                "correct_answer": clean_a,
                "user_difficulty": user_difficulty,
            },
        )
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", DEFAULT_MODELS[0]]:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=1500,
                    timeout=8.0,
                    response_format=response_format,
                )
                raw_text = completion.choices[0].message.content or "{}"
                data = json.loads(raw_text)
                tier = data.get("complexity_tier", "Medium")
                if norm_diff in ("Easy", "Medium", "Hard"):
                    tier = norm_diff
                sec = int(data.get("expected_time_sec", 45 if tier == "Medium" else (20 if tier == "Easy" else 65)))
                weight = float(data.get("complexity_weight", 1.8 if tier == "Medium" else (1.0 if tier == "Easy" else 2.5)))

                increment_stat("groq_calls")
                return {
                    "complexity_tier": tier,
                    "expected_time_sec": sec,
                    "complexity_weight": weight,
                    "hint": data.get("hint", f"Think about how the core principles of {concept_name} apply to this problem."),
                    "step_by_step": data.get("step_by_step", f"Step 1: Parse the problem statement.\nStep 2: Apply the relevant theorem/rule.\nStep 3: Conclude that {clean_a} is the correct solution."),
                    "source": "groq",
                    "explanations": {
                        "visual": {
                            "explanation": data.get("visual_explanation", f"Visual model illustrating why {clean_a} is the solution for {concept_name}."),
                            "check_question": data.get("visual_check_question", f"What does the visual diagram represent in this {concept_name} problem?"),
                            "visual_description": f"Visual scaffolding diagram for {concept_name}",
                        },
                        "analogy": {
                            "explanation": data.get("analogy_explanation", f"Analogy explaining the mechanics of {concept_name} leading to {clean_a}."),
                            "check_question": data.get("analogy_check_question", f"How does the real-world metaphor map to the equation/code?"),
                            "visual_description": f"Real-world analogy for {concept_name}",
                        },
                        "step_by_step": {
                            "explanation": data.get("worked_explanation", f"Detailed breakdown solving for {clean_a} step by step."),
                            "check_question": data.get("worked_check_question", f"Which step transitions the initial setup to the answer?"),
                            "visual_description": f"Step-by-step logic breakdown for {concept_name}",
                        },
                        "simple_language": {
                            "explanation": data.get("simple_explanation", f"Simple intuition: In {concept_name}, remember this rule of thumb which gives {clean_a}."),
                            "check_question": data.get("simple_check_question", f"What is the simplest way to explain this rule?"),
                            "visual_description": f"Plain English rule of thumb for {concept_name}",
                        },
                    },
                }
            except Exception as e:
                logger.warning(f"Groq question analysis with {model} failed: {e}. Trying fallback...")

    # 2. Deterministic AI Pedagogical Fallback Synthesizer (Zero-Failure Guarantee)
    increment_stat("offline_used")
    is_code = (
        "c7" in concept_id.lower()
        or "python" in clean_p.lower()
        or "def " in clean_p
        or "print(" in clean_p
        or "return" in clean_p
        or "```python" in clean_p
    )
    is_quad = (
        "c8" in concept_id.lower()
        or "quadratic" in clean_p.lower()
        or "x²" in clean_p
        or "x^2" in clean_p
        or "root" in clean_p.lower()
        or "discriminant" in clean_p.lower()
    )

    if norm_diff in ("Easy", "Medium", "Hard"):
        tier = norm_diff
    else:
        tier = "Hard" if (is_quad and "k" in clean_p) or (is_code and ("^" in clean_p or "mystery" in clean_p)) else "Medium"

    if tier == "Easy":
        sec = 20
        weight = 1.0
    elif tier == "Hard":
        sec = 70 if is_quad else 65
        weight = 2.5
    else:
        sec = 50 if is_quad else 45
        weight = 1.8

    if is_code:
        hint = "Trace the program line by line. Pay close attention to how mutable containers or variables update in memory after each step."
        step_by_step = (
            f"Step 1: Inspect function arguments and variable definitions.\n"
            f"Step 2: Trace each statement sequentially in order of execution.\n"
            f"Step 3: Evaluate return expression or stdout print. Result matches: {clean_a}"
        )
        visual_exp = (
            f"Execution Memory Map: Visualize the call stack frame. As the code executes line by line, "
            f"variables and return buffers resolve sequentially until the output evaluates cleanly to {clean_a}."
        )
        visual_chk = "How does tracking memory state prevent off-by-one or mutability confusion?"
        analogy_exp = (
            f"Think of an assembly line or recipe checklist: each instruction modifies an item in an inbox. "
            f"The final printed result is whatever remains in the box at the conclusion of the script: {clean_a}."
        )
        analogy_chk = "In this analogy, what does each function call represent?"
        worked_exp = (
            f"Step-by-Step Execution Trace:\n"
            f"1. Setup environment and parse inputs.\n"
            f"2. Evaluate expressions and track side effects.\n"
            f"3. Produce final return value: {clean_a}."
        )
        worked_chk = "Which specific line of code determines the final output?"
        simple_exp = (
            f"Rule of Thumb: Code executes in strict top-to-bottom order. "
            f"Keep track of variables at each print or return point. The exact output is: {clean_a}."
        )
        simple_chk = "What is the most direct way to verify the output?"
    elif is_quad:
        hint = "Recall standard quadratic form ax² + bx + c = 0. Consider factoring, the quadratic formula x = [-b ± √(b² - 4ac)]/(2a), or root substitution."
        step_by_step = (
            f"Step 1: Write the equation in standard form ax² + bx + c = 0.\n"
            f"Step 2: Identify coefficients and factor or compute discriminant Δ = b² - 4ac.\n"
            f"Step 3: Solve for real roots. The confirmed solution is: {clean_a}"
        )
        visual_exp = (
            f"Parabola Intersection Model: Picture the curve y = f(x) graphed on coordinate axes. "
            f"The solutions correspond to the exact points where the parabola intersects the x-axis (y = 0): {clean_a}."
        )
        visual_chk = "What visual feature on the coordinate plane represents the roots?"
        analogy_exp = (
            f"Imagine a balanced seesaw: when you plug the root values back into the equation, "
            f"both sides balance out to exactly zero: 0 = 0. That confirms {clean_a} is the equilibrium point."
        )
        analogy_chk = "Why does substituting a valid root make the equation balance?"
        worked_exp = (
            f"Worked Quadratic Procedure:\n"
            f"1. Rearrange to standard form ax² + bx + c = 0.\n"
            f"2. Apply root relationships or discriminant.\n"
            f"3. Confirm roots: {clean_a}."
        )
        worked_chk = "What is the discriminant formula for ax² + bx + c = 0?"
        simple_exp = (
            f"Rule of Thumb: The roots are the values of x that make the equation equal 0. "
            f"You can always double-check by plugging the option directly into the problem to verify: {clean_a}!"
        )
        simple_chk = "How can you test if an answer choice is a true root in under 10 seconds?"
    else:
        hint = f"Focus on the fundamental definition of {concept_name}. Break the problem down into whole units and fractional components."
        step_by_step = (
            f"Step 1: Identify the given quantities in the problem.\n"
            f"Step 2: Apply the core principle of {concept_name}.\n"
            f"Step 3: Simplify to reach the final answer: {clean_a}"
        )
        visual_exp = (
            f"Spatial Mental Model: Visualize the whole divided into equal partitions or segments. "
            f"Shading the relevant units illustrates why {clean_a} is the exact mathematical result."
        )
        visual_chk = f"How many equal parts make up the complete unit in this problem?"
        analogy_exp = (
            f"Imagine sharing resources (like chocolate bars or pizzas) fairly among a group. "
            f"Fair division guarantees that each share matches: {clean_a}."
        )
        analogy_chk = "What does fair sharing tell us about equal partition sizes?"
        worked_exp = (
            f"Step-by-Step Procedure for {concept_name}:\n"
            f"1. State the relationship between numerator and denominator.\n"
            f"2. Perform division or conversion.\n"
            f"3. Verified result: {clean_a}."
        )
        worked_chk = "What is the first step in solving this question?"
        simple_exp = (
            f"Rule of Thumb for {concept_name}: The top number is what you have, "
            f"and the bottom number is what makes the whole. Result: {clean_a}."
        )
        simple_chk = "What does the bottom number of a fraction represent?"

    return {
        "complexity_tier": tier,
        "expected_time_sec": sec,
        "complexity_weight": weight,
        "hint": hint,
        "step_by_step": step_by_step,
        "source": "offline_bank",
        "explanations": {
            "visual": {
                "explanation": visual_exp,
                "check_question": visual_chk,
                "visual_description": f"Visual scaffolding diagram for {concept_name}",
            },
            "analogy": {
                "explanation": analogy_exp,
                "check_question": analogy_chk,
                "visual_description": f"Real-world analogy for {concept_name}",
            },
            "step_by_step": {
                "explanation": worked_exp,
                "check_question": worked_chk,
                "visual_description": f"Step-by-step logic breakdown for {concept_name}",
            },
            "simple_language": {
                "explanation": simple_exp,
                "check_question": simple_chk,
                "visual_description": f"Plain English rule of thumb for {concept_name}",
            },
        },
    }


def get_health_status() -> Dict[str, Any]:
    """Health check for badge and rehearsal."""
    stats = get_stats()
    groq_ok = False
    client = get_groq_client()
    if client is not None:
        try:
            client.models.list(timeout=2.0)
            groq_ok = True
        except Exception:
            groq_ok = False

    return {
        "mode": settings.DEMO_MODE,
        "groq_ok": groq_ok,
        "models": DEFAULT_MODELS[:2],
        "cache_hits": stats.get("cache_hits", 0),
        "offline_used": stats.get("offline_used", 0),
    }
