import os
from pathlib import Path
from typing import Any, Dict, List
import yaml
from dotenv import load_dotenv

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"

# Load .env from root or backend
env_path = ROOT_DIR / ".env"
if not env_path.exists():
    env_path = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Load config.yaml
config_path = ROOT_DIR / "config.yaml"
if not config_path.exists():
    config_path = BACKEND_DIR / "config.yaml"

raw_config: Dict[str, Any] = {}
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f) or {}

class Settings:
    # Environment variables
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEMO_MODE: str = os.getenv("DEMO_MODE", "live")  # live | replay
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # SQLite
    DB_PATH: Path = BACKEND_DIR / "clearpath.db"

    # LLM Settings from config.yaml
    llm_cfg = raw_config.get("llm", {})
    MODELS: List[str] = llm_cfg.get("models", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
    MAX_TOKENS: int = llm_cfg.get("max_tokens", 500)
    TEMPERATURE: float = llm_cfg.get("temperature", 0.2)
    TIMEOUT_SECONDS: float = float(llm_cfg.get("timeout_seconds", 4.0))
    RATE_LIMIT_RPM: int = int(llm_cfg.get("rate_limit_rpm", 30))
    CACHE_TTL_SECONDS: int = int(llm_cfg.get("cache_ttl_seconds", 86400))

    # Detector settings
    det_cfg = raw_config.get("detector", {})
    THRESHOLD_CONFUSED: float = float(det_cfg.get("threshold_confused", 0.70))
    THRESHOLD_HESITANT: float = float(det_cfg.get("threshold_hesitant", 0.40))
    RULES: Dict[str, Any] = det_cfg.get("rules", {
        "dwell_time_trigger_ms": 25000,
        "pause_trigger_ms": 15000,
        "edit_count_trigger": 4,
        "option_switch_trigger": 3,
        "lost_click_trigger": 1,
        "hint_click_trigger": 1,
    })

    # BKT defaults
    bkt_cfg = raw_config.get("bkt", {})
    BKT_P_L0: float = float(bkt_cfg.get("p_l0", 0.20))
    BKT_P_T: float = float(bkt_cfg.get("p_t", 0.15))
    BKT_P_G: float = float(bkt_cfg.get("p_g", 0.20))
    BKT_P_S: float = float(bkt_cfg.get("p_s", 0.10))
    BKT_MASTERY_THRESHOLD: float = float(bkt_cfg.get("mastery_threshold", 0.85))

    # Data files
    CONCEPTS_FILE: Path = DATA_DIR / "concepts.json"
    QUESTIONS_FILE: Path = DATA_DIR / "questions.json"
    EXPLANATIONS_FILE: Path = DATA_DIR / "explanations.json"
    MODEL_DIR: Path = BACKEND_DIR / "models"

settings = Settings()
