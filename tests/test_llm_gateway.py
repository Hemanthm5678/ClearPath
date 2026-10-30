"""
Unit tests for ClearPath LLM Gateway, Prompts, and Offline Bank Builder (Section 6).
"""

import ast
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.app.config import settings
from backend.app.database import init_db, get_cached_llm, set_cached_llm, get_stats, get_connection
from backend.app.llm.prompts import (
    EXPLAIN_CONCEPT_SCHEMA,
    CHAT_REPLY_SCHEMA,
    get_response_format,
    render_explain_prompt,
    render_chat_prompt,
    build_prompt_payload,
)
from backend.app.llm.gateway import (
    ask,
    get_offline_explanation,
    get_offline_chat_reply,
    PRIMARY_MODEL,
    FALLBACK_MODEL,
)
from scripts.build_bank import build_bank, validate_bank, OFFLINE_BANK_DATA


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM llm_cache")
        conn.commit()


# =============================================================================
# 1. Architecture Constraints Verification
# =============================================================================

class TestArchitectureConstraints:
    def test_only_gateway_imports_groq(self):
        """Verify that backend/app/llm/gateway.py is the ONLY file that imports groq."""
        root_dir = settings.ROOT_DIR
        violators = []

        for py_path in root_dir.rglob("*.py"):
            # Skip virtual environments if any
            if any(part in py_path.parts for part in (".venv", "venv", ".pytest_cache")):
                continue
            
            # gateway.py is the allowed importer
            if py_path.resolve() == (root_dir / "backend" / "app" / "llm" / "gateway.py").resolve():
                continue

            try:
                tree = ast.parse(py_path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == "groq" or alias.name.startswith("groq."):
                                violators.append(str(py_path))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and (node.module == "groq" or node.module.startswith("groq.")):
                            violators.append(str(py_path))
            except Exception:
                pass

        assert violators == [], f"Files improperly importing groq: {violators}"


# =============================================================================
# 2. Strict JSON Schemas & Prompts (prompts.py)
# =============================================================================

class TestPromptsAndSchemas:
    def test_explain_concept_schema_structure(self):
        """Test Prompt 1 schema strictness for Groq SDK."""
        assert EXPLAIN_CONCEPT_SCHEMA["type"] == "object"
        assert EXPLAIN_CONCEPT_SCHEMA["additionalProperties"] is False
        assert set(EXPLAIN_CONCEPT_SCHEMA["required"]) == {"explanation", "check_question", "visual_description"}
        assert "explanation" in EXPLAIN_CONCEPT_SCHEMA["properties"]
        assert "check_question" in EXPLAIN_CONCEPT_SCHEMA["properties"]
        assert "visual_description" in EXPLAIN_CONCEPT_SCHEMA["properties"]

    def test_chat_reply_schema_structure(self):
        """Test Prompt 2 schema strictness for Groq SDK."""
        assert CHAT_REPLY_SCHEMA["type"] == "object"
        assert CHAT_REPLY_SCHEMA["additionalProperties"] is False
        assert set(CHAT_REPLY_SCHEMA["required"]) == {"reply"}
        assert "reply" in CHAT_REPLY_SCHEMA["properties"]

    def test_get_response_format_groq_sdk(self):
        """Test response format structure for Groq structured outputs."""
        fmt_explain = get_response_format("explain_concept")
        assert fmt_explain["type"] == "json_schema"
        assert fmt_explain["json_schema"]["strict"] is True
        assert fmt_explain["json_schema"]["name"] == "explain_concept"
        assert fmt_explain["json_schema"]["schema"] == EXPLAIN_CONCEPT_SCHEMA

        fmt_chat = get_response_format("chat_reply")
        assert fmt_chat["type"] == "json_schema"
        assert fmt_chat["json_schema"]["strict"] is True
        assert fmt_chat["json_schema"]["name"] == "chat_reply"
        assert fmt_chat["json_schema"]["schema"] == CHAT_REPLY_SCHEMA

    def test_render_explain_prompt_inputs(self):
        """Test Prompt 1 inputs: concept_name, student_age, confusion_reasons, style, level."""
        prompt = render_explain_prompt(
            concept_name="Fraction as Division",
            student_age=11,
            confusion_reasons=["Hesitation on option switch", "Long dwell time"],
            style="worked",
            level=2,
        )
        assert "Fraction as Division" in prompt
        assert "11 years old" in prompt
        assert "Hesitation on option switch" in prompt
        assert "worked" in prompt.lower()
        assert "2" in prompt
        assert "explanation" in prompt

    def test_render_chat_prompt_inputs(self):
        """Test Prompt 2 inputs: chat_history, concept, student_message."""
        history = [
            {"role": "student", "content": "Why is 3/4 equal to 3 divided by 4?"},
            {"role": "assistant", "content": "Imagine sharing 3 pizzas among 4 friends."},
        ]
        prompt = render_chat_prompt(
            chat_history=history,
            concept="Fractions as Division",
            student_message="Does each person get less than 1 whole pizza?",
        )
        assert "Fractions as Division" in prompt
        assert "Does each person get less than 1 whole pizza?" in prompt
        assert "Student: Why is 3/4" in prompt


# =============================================================================
# 3. LLM Gateway & Offline Fallback Bank (gateway.py)
# =============================================================================

class TestLLMGateway:
    def test_offline_explanation_guarantee(self):
        """Test fetching from data/explanations.json based on concept ID."""
        for cid in ["c1_fraction_basics", "c2_equal_parts", "c3_fraction_as_division", "c4_equivalent_fractions", "c5_comparing_fractions", "c6_adding_fractions"]:
            res = get_offline_explanation(cid, style="analogy", level=1)
            assert res["source"] == "offline_bank"
            assert isinstance(res["explanation"], str) and len(res["explanation"]) > 10
            assert isinstance(res["check_question"], str) and len(res["check_question"]) > 5
            assert isinstance(res["visual_description"], str) and len(res["visual_description"]) > 10

    def test_offline_chat_reply_guarantee(self):
        """Test offline chat reply fallback."""
        res = get_offline_chat_reply("Why do we need equal parts?", concept_id="c2_equal_parts")
        assert res["source"] == "offline_bank"
        assert "reply" in res
        assert len(res["reply"]) > 10

    def test_ask_offline_bank_fallback_and_caching(self):
        """
        Test ask() flow:
        - Groq unconfigured/throws error -> fetches from offline bank based on concept ID.
        - Saves to cache.
        - Second identical call returns exact match from SQLite cache.
        """
        initial_stats = get_stats()
        initial_cache_hits = initial_stats.get("cache_hits", 0)

        # Call ask with unique parameters
        ctx = {
            "concept_id": "c4_equivalent_fractions",
            "concept_name": "Equivalent Fractions",
            "student_age": 10,
            "confusion_reasons": ["Multiple revisions"],
            "style": "visual",
            "level": 2,
            "nonce": "test_cache_run_1"
        }

        # First call: fallback to offline bank & save to cache
        res1 = ask("explain_concept", ctx)
        assert res1["source"] == "offline_bank"
        assert "explanation" in res1
        assert "check_question" in res1
        assert "visual_description" in res1

        # Second call: must hit cache
        res2 = ask("explain_concept", ctx)
        assert res2["source"] == "cache"
        assert res2["explanation"] == res1["explanation"]
        assert res2["check_question"] == res1["check_question"]
        assert res2["visual_description"] == res1["visual_description"]

        updated_stats = get_stats()
        assert updated_stats.get("cache_hits", 0) > initial_cache_hits

    def test_ask_model_chain_with_rate_limit_fallback(self):
        """
        Test Step 3:
        Try llama-3.1-8b-instant. If rate limit, fallback to llama-3.3-70b-versatile.
        """
        mock_client = MagicMock()

        # Simulate: llama-3.1-8b-instant raises rate limit error; llama-3.3-70b-versatile succeeds
        def fake_create(model, messages, response_format, **kwargs):
            if model == PRIMARY_MODEL:
                raise Exception("Rate limit reached on llama-3.1-8b-instant (HTTP 429)")
            elif model == FALLBACK_MODEL:
                mock_choice = MagicMock()
                mock_choice.message.content = json.dumps({
                    "explanation": "Success from 70b versatile fallback!",
                    "check_question": "Did 70b work?",
                    "visual_description": "Diagram of fallback model path."
                })
                mock_resp = MagicMock()
                mock_resp.choices = [mock_choice]
                return mock_resp
            raise ValueError(f"Unexpected model: {model}")

        mock_client.chat.completions.create.side_effect = fake_create

        with patch("backend.app.llm.gateway.get_groq_client", return_value=mock_client), \
             patch("backend.app.llm.gateway._is_rate_limited", return_value=False):

            ctx = {
                "concept_id": "c1_fraction_basics",
                "concept_name": "Fraction Basics",
                "student_age": 10,
                "confusion_reasons": ["Hesitation"],
                "style": "worked",
                "level": 1,
                "nonce": "test_model_fallback_run"
            }
            res = ask("explain_concept", ctx)
            assert res["source"] == "groq"
            assert res["explanation"] == "Success from 70b versatile fallback!"

            # Verify both models were invoked in sequence
            calls = mock_client.chat.completions.create.call_args_list
            assert len(calls) == 2
            assert calls[0].kwargs["model"] == PRIMARY_MODEL
            assert calls[1].kwargs["model"] == FALLBACK_MODEL


# =============================================================================
# 4. Offline Bank Builder (build_bank.py)
# =============================================================================

class TestBuildBank:
    def test_build_and_validate_bank(self):
        """Test build_bank writes valid JSON with all required concepts, styles, and levels."""
        bank = build_bank()
        concepts_file = settings.BACKEND_DIR / "data" / "concepts.json"
        errors = validate_bank(bank, concepts_file)
        assert errors == [], f"Validation errors found: {errors}"

        # Check file outputs
        backend_bank_file = settings.BACKEND_DIR / "data" / "explanations.json"
        root_bank_file = settings.ROOT_DIR / "data" / "explanations.json"
        assert backend_bank_file.exists()
        assert root_bank_file.exists()
