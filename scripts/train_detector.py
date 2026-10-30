"""
Training entrypoint in scripts/train_detector.py.
Delegates to backend/scripts/train_detector.py.
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.scripts.train_detector import train_and_evaluate

if __name__ == "__main__":
    train_and_evaluate()

