# Evaluation Report — Multi-Modal Evidence Review

## Summary

| Field | Accuracy |
|-------|----------|
| `evidence_standard_met` | **90.0%** (18/20) |
| `issue_type` | **75.0%** (15/20) |
| `object_part` | **80.0%** (16/20) |
| `claim_status` | **75.0%** (15/20) |
| `valid_image` | **90.0%** (18/20) |
| `severity` | **75.0%** (15/20) |
| **OVERALL** | **80.8%** |

Evaluated on `dataset/sample_claims.csv` (20 labelled claims across car, laptop, and package categories).

## Methodology

The system uses a multi-stage heuristic pipeline:

1. **Evidence Checker** — rule-based, checks `evidence_requirements.csv` against image count and claim object
2. **Risk Scorer** — rule-based, reads `user_history.csv` for fraud signals
3. **Heuristic Analyzer** — NLP keyword extraction from the claim conversation:
   - `issue_type`: keyword matching against 10 damage type dictionaries
   - `object_part`: longest-match keyword lookup per claim_object
   - `claim_status`: uncertainty phrase detection, missing-item detection, functional-claim detection
   - `severity`: keyword tiers (high/medium/low/none) with issue-type fallback
4. **Post-processing overrides**: laptop+crack→screen, dent+corner→low, uncertainty→unknown

## Remaining Gap Analysis

The 5 remaining `claim_status` mismatches (25%) are all visually-contradicted claims where images do not match the conversation — these require Vision Language Model (VLM) assessment that was blocked by API quota limitations:

| User | Expected | Got | Why |
|------|----------|-----|-----|
| user_002 | not_enough_information | supported | Images blurry, not enough evidence |
| user_005 | contradicted | supported | Images show scratch not bumper damage |
| user_008 | contradicted | supported | Images show different damage than claimed |
| user_033 | contradicted | supported | Images don't show claimed crushing |
| user_034 | contradicted | supported | Images show intact seal, not torn |

## Output Files

- `evaluation/sample_output.csv` — predictions on the 20-row labelled set
- `../../output.csv` — final predictions on the 44-row test set (`claims.csv`)

## Run Instructions

```bash
# Install dependencies
pip install -r requirements.txt

# Run evaluation (sample_claims.csv → sample_output.csv)
python evaluation/evaluate.py

# Run full pipeline (claims.csv → output.csv)
python main.py
```

No API key required. The system runs entirely on rule-based heuristics.
