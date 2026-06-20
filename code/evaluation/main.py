import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = ROOT / "code"
sys.path.insert(0, str(CODE_DIR))
sys.path.insert(0, str(CODE_DIR / "evaluation"))

from evaluate import evaluate

if __name__ == "__main__":
    evaluate()
