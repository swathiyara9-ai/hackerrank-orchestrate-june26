import pandas as pd
import json
import time
import os
from heuristic_analyzer import analyze_claim_heuristic as analyze_claim
from evidence_checker import load_evidence_requirements, check_evidence_standard
from risk_scorer import load_user_history, get_risk_flags
from injection_detector import detect_injection
from utils import parse_image_paths, validate_value, validate_flags, merge_flags
from config import (
    SLEEP_BETWEEN_CALLS, OUTPUT_COLUMNS,
    ALLOWED_ISSUE_TYPES, ALLOWED_CLAIM_STATUS,
    ALLOWED_SEVERITY, ALLOWED_RISK_FLAGS, ALLOWED_OBJECT_PARTS
)

PROGRESS_FILE = "progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return []

def save_progress(results):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(results, f)

def process_claim(row, requirements_df, history_df, base_dir):
    user_id = str(row["user_id"]).strip()
    image_paths_str = str(row["image_paths"]).strip()
    user_claim = str(row["user_claim"]).strip()
    claim_object = str(row["claim_object"]).strip().lower()

    images = parse_image_paths(image_paths_str, base_dir=base_dir)
    image_count = len(images)

    print(f"    Analyzing {image_count} image(s) via heuristic analyzer...")
    vision = analyze_claim(images, user_claim, claim_object)

    issue_type = validate_value(vision.get("issue_type"), ALLOWED_ISSUE_TYPES, "unknown")
    object_part = validate_value(
        vision.get("object_part"),
        ALLOWED_OBJECT_PARTS.get(claim_object, ["unknown"]), "unknown"
    )
    claim_status = validate_value(vision.get("claim_status"), ALLOWED_CLAIM_STATUS, "not_enough_information")
    severity = validate_value(vision.get("severity"), ALLOWED_SEVERITY, "unknown")
    valid_image = str(vision.get("valid_image", True)).lower()
    justification = str(vision.get("claim_status_justification", "")).strip()
    supporting_ids = str(vision.get("supporting_image_ids", "none")).strip()

    evidence_met, evidence_reason = check_evidence_standard(
        claim_object, issue_type, image_count, images, requirements_df
    )

    # --- Prompt injection detection ---
    is_injection, injection_matches = detect_injection(user_claim)
    injection_flag = "text_instruction_present" if is_injection else ""

    # --- Risk flags ---
    image_flags = validate_flags(str(vision.get("image_quality_issues","none")), ALLOWED_RISK_FLAGS)
    history_flags = get_risk_flags(user_id, history_df)
    combined_flags = merge_flags(image_flags, history_flags)
    if injection_flag:
        combined_flags = merge_flags(combined_flags, injection_flag)
    risk_flags = validate_flags(combined_flags, ALLOWED_RISK_FLAGS)

    # =============================================
    # POST-PROCESSING: Logical consistency enforcement
    # =============================================

    # FIX 1: evidence_standard_met=False → MUST be not_enough_information
    if not evidence_met and claim_status == "supported":
        claim_status = "not_enough_information"
        justification = (
            f"Evidence standard not met: {evidence_reason}. "
            "Cannot confirm support without sufficient visual evidence."
        )
        supporting_ids = "none"

    # FIX 2: issue_type=unknown AND severity=unknown → not_enough_information
    # If we can't determine what damage is claimed, we can't confirm it's supported
    if issue_type == "unknown" and severity == "unknown" and claim_status == "supported":
        claim_status = "not_enough_information"
        justification = (
            "Cannot determine the specific damage type or severity from the "
            "claim description. Insufficient information to confirm support."
        )
        supporting_ids = "none"

    # FIX 3: Prompt injection → downgrade to not_enough_information if no clear damage signal
    if is_injection:
        if issue_type == "unknown" or severity == "unknown":
            claim_status = "not_enough_information"
            justification = (
                "Conversation contains instruction-like text that may attempt to "
                "influence the review decision. Manual review is required."
            )
            supporting_ids = "none"
        # Always add manual_review_required for injection cases
        if "manual_review_required" not in risk_flags:
            risk_flags = merge_flags(risk_flags, "manual_review_required")
            risk_flags = validate_flags(risk_flags, ALLOWED_RISK_FLAGS)

    # FIX 4: claim_status != supported → supporting_image_ids should be "none"
    if claim_status != "supported":
        supporting_ids = "none"

    # FIX 5: Improve justification with image IDs when supported
    if claim_status == "supported" and supporting_ids != "none":
        img_ids_list = supporting_ids.replace(";", ", ")
        justification = (
            f"Claimed {issue_type} on {object_part} is consistent with the "
            f"submitted evidence ({img_ids_list}). "
            f"Severity assessed as {severity}."
        )

    return {
        "user_id": user_id,
        "image_paths": image_paths_str,
        "user_claim": user_claim,
        "claim_object": claim_object,
        "evidence_standard_met": str(evidence_met).lower(),
        "evidence_standard_met_reason": evidence_reason,
        "risk_flags": risk_flags,
        "issue_type": issue_type,
        "object_part": object_part,
        "claim_status": claim_status,
        "claim_status_justification": justification,
        "supporting_image_ids": supporting_ids,
        "valid_image": valid_image,
        "severity": severity
    }

def run_pipeline(input_csv, output_csv, requirements_df, history_df, base_dir, resume=True):
    df = pd.read_csv(input_csv)
    total = len(df)

    results = load_progress() if resume else []
    start_from = len(results)

    if start_from > 0:
        print(f"Resuming from claim {start_from + 1}/{total}")

    for i, row in df.iterrows():
        if i < start_from:
            continue
        print(f"\nProcessing claim {i+1}/{total} — user: {row['user_id']} — object: {row['claim_object']}")
        try:
            result = process_claim(row, requirements_df, history_df, base_dir)
            results.append(result)
            save_progress(results)
            print(f"    Status: {result['claim_status']} | Severity: {result['severity']}")
        except Exception as e:
            print(f"    ERROR on claim {i+1}: {e}")
            results.append({
                "user_id": str(row.get("user_id","")),
                "image_paths": str(row.get("image_paths","")),
                "user_claim": str(row.get("user_claim","")),
                "claim_object": str(row.get("claim_object","")),
                "evidence_standard_met": "false",
                "evidence_standard_met_reason": f"Processing error: {str(e)}",
                "risk_flags": "none",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": f"Error during processing: {str(e)}",
                "supporting_image_ids": "none",
                "valid_image": "false",
                "severity": "unknown"
            })
            save_progress(results)
        time.sleep(SLEEP_BETWEEN_CALLS)

    out_df = pd.DataFrame(results)[OUTPUT_COLUMNS]
    out_df.to_csv(output_csv, index=False)
    print(f"\nDone! Output written to {output_csv}")
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    return results
