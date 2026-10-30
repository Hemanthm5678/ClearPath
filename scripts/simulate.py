"""
Simulator entrypoint in scripts/simulate.py.
Delegates to backend/scripts/simulate.py.
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.scripts.simulate import run_simulation, simulate_dataset

if __name__ == "__main__":
    run_simulation()

