import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from pipeline import run_pipeline
from evidence_checker import load_evidence_requirements
from risk_scorer import load_user_history
from config import (
    CLAIMS_CSV, USER_HISTORY_CSV, EVIDENCE_REQ_CSV,
    OUTPUT_CSV, DATASET_DIR, GEMINI_API_KEY
)

def main():
    if not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not set. Running in pure heuristic mode.")

    print("=== Multi-Modal Evidence Review Pipeline ===")
    print(f"Input:  {CLAIMS_CSV}")
    print(f"Output: {OUTPUT_CSV}")

    requirements_df = load_evidence_requirements(EVIDENCE_REQ_CSV)
    history_df = load_user_history(USER_HISTORY_CSV)

    run_pipeline(
        input_csv=CLAIMS_CSV,
        output_csv=OUTPUT_CSV,
        requirements_df=requirements_df,
        history_df=history_df,
        base_dir=DATASET_DIR,
        resume=False
    )

if __name__ == "__main__":
    main()
