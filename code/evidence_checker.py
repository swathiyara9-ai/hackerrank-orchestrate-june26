import os
import pandas as pd

def load_evidence_requirements(path):
    return pd.read_csv(path)

def check_evidence_standard(claim_object, issue_type, image_count, image_paths_with_ids, requirements_df):
    if image_count == 0:
        return False, "No images submitted."

    missing = [img_id for img_id, path in image_paths_with_ids if not os.path.exists(path)]
    if len(missing) == image_count:
        return False, "All submitted images are missing or inaccessible."

    matches = requirements_df[requirements_df["claim_object"].isin([claim_object, "all"])]
    if matches.empty:
        return True, f"No specific requirement found; {image_count} image(s) submitted."

    # Package contents / missing-item claims need images showing interior —
    # exterior-only images are insufficient regardless of count.
    if claim_object == "package" and issue_type in ["missing_part", "unknown"]:
        return False, (
            f"Contents claim requires images showing the opened package interior; "
            f"exterior-only images are insufficient ({image_count} submitted)."
        )

    return True, f"Evidence standard met: {image_count} image(s) for {claim_object} claim."
