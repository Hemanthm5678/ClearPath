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

PRIMARY_MODEL = "llama-3.1-8b-instant"
FALLBACK_MODEL = "llama-3.3-70b-versatile"


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
) -> Dict[str, Any]:
    """
    Retrieves guaranteed offline explanation from data/explanations.json based on concept ID.
    Ensures output JSON schema: {explanation, check_question, visual_description}.
    """
    bank = load_offline_bank()
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
        models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]

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
                    timeout=settings.TIMEOUT_SECONDS,
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

    # 2. If rate limited or groq throws error, fetch from data/explanations.json (offline bank) based on concept ID.
    increment_stat("offline_used")
    if prompt_name == "chat_reply":
        student_msg = str(context_dict.get("student_message") or context_dict.get("message") or "")
        result = get_offline_chat_reply(student_msg, concept_id=str(concept_id))
    else:
        style = str(context_dict.get("style", "visual"))
        level = context_dict.get("level", 1)
        result = get_offline_explanation(str(concept_id), style=style, level=level)

    result["source"] = "offline_bank"

    # 4. Save to cache and return
    set_cached_llm(cache_key, prompt_name, result)
    return result


def get_health_status() -> Dict[str, Any]:
    """Health check for badge and rehearsal."""
    stats = get_stats()
    groq_ok = False
    client = get_groq_client()
    if client is not None:
        try:
            client.models.list()
            groq_ok = True
        except Exception:
            groq_ok = False

    return {
        "mode": settings.DEMO_MODE,
        "groq_ok": groq_ok,
        "models": [PRIMARY_MODEL, FALLBACK_MODEL],
        "cache_hits": stats.get("cache_hits", 0),
        "offline_used": stats.get("offline_used", 0),
    }
