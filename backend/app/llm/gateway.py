import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional

# HARD RULE 1: Only backend/app/llm/gateway.py may import the `groq` package.
try:
    from groq import Groq
except ImportError:
    Groq = None  # Graceful fallback if package is absent

from backend.app.config import settings
from backend.app.database import (
    get_cached_llm,
    get_stats,
    increment_stat,
    set_cached_llm,
)
from backend.app.llm.prompts import TUTOR_SYSTEM_PROMPT

logger = logging.getLogger("clearpath.gateway")

# In-memory throttle state
_request_timestamps = []
_offline_bank: Dict[str, Any] = {}

def load_offline_bank() -> Dict[str, Any]:
    global _offline_bank
    if not _offline_bank and settings.EXPLANATIONS_FILE.exists():
        try:
            with open(settings.EXPLANATIONS_FILE, "r", encoding="utf-8") as f:
                _offline_bank = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load offline bank: {e}")
    return _offline_bank

def get_offline_explanation(
    concept_id: str,
    style: str = "visual",
    level: int = 1
) -> Dict[str, Any]:
    """
    Guaranteed fallback response retrieved from precomputed data/explanations.json
    """
    bank = load_offline_bank()
    concept_entry = bank.get(concept_id) or bank.get("c3_fraction_as_division", {})
    style_entry = concept_entry.get(style) or concept_entry.get("visual", {})
    level_key = f"level_{level}"
    explanation_data = style_entry.get(level_key) or style_entry.get("level_1")

    if not explanation_data:
        # Universal fallback guarantee
        explanation_data = {
            "explanation": "Let's break this down step-by-step: focus on how many total equal parts make the whole, and how many parts are being considered.",
            "check_question": "What is the total number of parts in this problem?",
            "visual_description": "Draw the whole shape divided into equal sections, and shade the target portions."
        }

    return {
        "explanation": explanation_data["explanation"],
        "check_question": explanation_data["check_question"],
        "visual_description": explanation_data["visual_description"],
        "source": "offline_bank"
    }

def get_offline_chat_reply(message: str) -> Dict[str, Any]:
    """Guaranteed fallback for student follow-up queries."""
    return {
        "reply": f"Great question! When thinking about this, try visualizing the problem with smaller numbers or drawing equal slices. You're doing great—take another look at the numerator and denominator!",
        "source": "offline_bank"
    }

def _is_rate_limited() -> bool:
    global _request_timestamps
    now = time.time()
    # Filter timestamps within the last 60 seconds
    _request_timestamps = [t for t in _request_timestamps if now - t < 60.0]
    if len(_request_timestamps) >= settings.RATE_LIMIT_RPM:
        return True
    _request_timestamps.append(now)
    return False

def get_groq_client() -> Optional[Any]:
    if Groq is None or not settings.GROQ_API_KEY or settings.GROQ_API_KEY.strip() == "":
        return None
    try:
        return Groq(api_key=settings.GROQ_API_KEY.strip())
    except Exception as e:
        logger.warning(f"Error initializing Groq client: {e}")
        return None

def ask(
    prompt: str,
    system: str = TUTOR_SYSTEM_PROMPT,
    response_format: str = "json",
    fallback_concept_id: str = "c3_fraction_as_division",
    style: str = "visual",
    level: int = 1,
    is_chat: bool = False,
    chat_message: str = ""
) -> Dict[str, Any]:
    """
    Main LLM entrypoint:
    1. Checks local SQLite cache.
    2. Attempts Groq API across model chain with timeouts & throttling.
    3. Seamlessly falls back to local offline bank on ANY failure.
    """
    # 1. Check Cache
    cache_key = hashlib.md5(f"{prompt}:{system}:{style}:{level}:{is_chat}".encode("utf-8")).hexdigest()
    cached = get_cached_llm(cache_key)
    if cached:
        increment_stat("cache_hits")
        cached["source"] = "cache"
        return cached

    # 2. Check Groq Client Availability
    client = get_groq_client()
    if client is not None and not _is_rate_limited():
        for model in settings.MODELS:
            try:
                kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": settings.TEMPERATURE,
                    "max_tokens": settings.MAX_TOKENS,
                    "timeout": settings.TIMEOUT_SECONDS,
                }
                if response_format == "json":
                    kwargs["response_format"] = {"type": "json_object"}

                completion = client.chat.completions.create(**kwargs)
                raw_text = completion.choices[0].message.content or "{}"
                data = json.loads(raw_text)

                data["source"] = "groq"
                increment_stat("groq_calls")

                # Persist in cache
                set_cached_llm(cache_key, prompt, data)
                return data

            except Exception as e:
                logger.info(f"Groq model {model} attempt failed: {e}. Trying fallback...")
                continue

    # 3. Fallback to Offline Bank (Guaranteed Usable Response)
    increment_stat("offline_used")
    if is_chat:
        fallback = get_offline_chat_reply(chat_message)
    else:
        fallback = get_offline_explanation(fallback_concept_id, style, level)

    # Store in cache for rapid access
    set_cached_llm(cache_key, prompt, fallback)
    return fallback

def get_health_status() -> Dict[str, Any]:
    """Health check for badge and rehearsal."""
    stats = get_stats()
    groq_ok = False
    client = get_groq_client()
    if client is not None:
        try:
            # Minimal verification probe with quick timeout
            client.models.list()
            groq_ok = True
        except Exception:
            groq_ok = False

    return {
        "mode": settings.DEMO_MODE,
        "groq_ok": groq_ok,
        "models": settings.MODELS,
        "cache_hits": stats.get("cache_hits", 0),
        "offline_used": stats.get("offline_used", 0)
    }
