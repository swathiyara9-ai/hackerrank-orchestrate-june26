import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import pandas as pd
from pipeline import run_pipeline
from evidence_checker import load_evidence_requirements
from risk_scorer import load_user_history
from config import (
    SAMPLE_CSV, USER_HISTORY_CSV, EVIDENCE_REQ_CSV,
    DATASET_DIR
)

EVAL_OUTPUT = str(ROOT / "code" / "evaluation" / "sample_output.csv")

SCORE_COLUMNS = [
    "evidence_standard_met", "issue_type", "object_part",
    "claim_status", "valid_image", "severity"
]

def evaluate():

    print("=== Evaluation on sample_claims.csv ===\n")

    requirements_df = load_evidence_requirements(EVIDENCE_REQ_CSV)
    history_df = load_user_history(USER_HISTORY_CSV)

    run_pipeline(
        input_csv=SAMPLE_CSV,
        output_csv=EVAL_OUTPUT,
        requirements_df=requirements_df,
        history_df=history_df,
        base_dir=DATASET_DIR,
        resume=False
    )

    pred_df = pd.read_csv(EVAL_OUTPUT)
    expected_df = pd.read_csv(SAMPLE_CSV)

    print("\n=== ACCURACY RESULTS ===\n")
    total = len(expected_df)
    scores = {}

    for col in SCORE_COLUMNS:
        if col not in expected_df.columns or col not in pred_df.columns:
            print(f"  {col}: skipped (not in both files)")
            continue
        exp = expected_df[col].astype(str).str.strip().str.lower()
        prd = pred_df[col].astype(str).str.strip().str.lower()
        matches = (exp == prd).sum()
        pct = 100 * matches / total
        scores[col] = pct
        print(f"  {col:35s}: {matches}/{total} ({pct:.1f}%)")

    if scores:
        avg = sum(scores.values()) / len(scores)
        print(f"\n  {'OVERALL':35s}: {avg:.1f}%")

    print("\n=== CLAIM_STATUS MISMATCHES ===")
    if "claim_status" in expected_df.columns and "claim_status" in pred_df.columns:
        exp = expected_df["claim_status"].astype(str).str.strip().str.lower()
        prd = pred_df["claim_status"].astype(str).str.strip().str.lower()
        for idx in expected_df.index[exp != prd]:
            uid = expected_df.loc[idx, "user_id"]
            e_val = expected_df.loc[idx, "claim_status"]
            p_val = pred_df.loc[idx, "claim_status"] if idx < len(pred_df) else "N/A"
            print(f"  {uid}: expected={e_val}, got={p_val}")

if __name__ == "__main__":
    evaluate()
