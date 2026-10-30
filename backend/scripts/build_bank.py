"""
ClearPath Offline Explanation Bank Builder entrypoint.
Delegates to scripts.build_bank.

NOTE: Per architecture specifications, this file MUST NOT import the `groq` package.
Only backend/app/llm/gateway.py may import `groq`.
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.build_bank import build_bank, validate_bank, OFFLINE_BANK_DATA

if __name__ == "__main__":
    build_bank()
