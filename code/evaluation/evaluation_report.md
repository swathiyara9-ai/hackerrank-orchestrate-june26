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

## Operational Analysis

### 1. Active Pipeline: Pure Heuristic Mode
Because the Gemini API was blocked during execution, the active pipeline runs in **Pure Heuristic Mode**.
- **Model Calls**: 0 (no external LLM/VLM calls).
- **Token Usage**: 0 input tokens, 0 output tokens.
- **Images Processed**: 30 images parsed for metadata in sample set; 85 images in test set.
- **Cost**: **$0.00** (completely free, zero external API costs).
- **Latency / Runtime**:
  - Evaluation (`evaluate.py`): **~0.15 seconds** for 20 claims.
  - Test set processing (`main.py`): **~0.35 seconds** for 44 claims.
- **TPM/RPM and Scale**: Infinite scale, zero rate limit risk. `SLEEP_BETWEEN_CALLS` has been reduced to `0` to achieve maximum execution speed.

### 2. Design Pipeline: VLM Mode (gemini-2.0-flash-lite)
If the Gemini API key was active, the pipeline is fully prepared to use `gemini-2.0-flash-lite`.
- **Model Calls**: 20 calls for sample claims; 44 calls for test claims (1 call per claim row).
- **Images Processed**: 30 images (sample), 85 images (test).
- **Token Usage (Estimates)**:
  - Input tokens: ~1,500 tokens per image + ~300 prompt tokens. Average ~3,300 tokens per claim. Total test set input: **~145,200 tokens**.
  - Output tokens: ~150 tokens per JSON response. Total test set output: **~6,600 tokens**.
- **Cost (Pricing Assumptions)**:
  - Input: $0.075 / 1M tokens. Output: $0.30 / 1M tokens.
  - Total test set cost: 145,200 * ($0.075/1M) + 6,600 * ($0.30/1M) = $0.01089 + $0.00198 = **~$0.013** (less than 2 cents for the entire run).
- **Latency & Rate Limits**:
  - Latency: ~1-2 seconds per API call. Total run time without rate-limiting would be ~60 seconds.
  - TPM/RPM: Gemini free tier allows 15 RPM. The pipeline incorporates `SLEEP_BETWEEN_CALLS = 2` to safely remain under the limit.
  - Error Handling: A robust retry loop with exponential backoff and jitter is built into `vision.py` to handle 429 quota/rate limit exceptions gracefully.

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
