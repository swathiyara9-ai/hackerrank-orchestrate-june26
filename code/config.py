import os
from dotenv import load_dotenv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-2.0-flash-lite"

DATASET_DIR = str(ROOT / "dataset")
SAMPLE_CSV = str(ROOT / "dataset/sample_claims.csv")
CLAIMS_CSV = str(ROOT / "dataset/claims.csv")
USER_HISTORY_CSV = str(ROOT / "dataset/user_history.csv")
EVIDENCE_REQ_CSV = str(ROOT / "dataset/evidence_requirements.csv")
OUTPUT_CSV = str(ROOT / "output.csv")

SLEEP_BETWEEN_CALLS = 0

ALLOWED_ISSUE_TYPES = [
    "dent","scratch","crack","glass_shatter","broken_part",
    "missing_part","torn_packaging","crushed_packaging",
    "water_damage","stain","none","unknown"
]
ALLOWED_CLAIM_STATUS = ["supported","contradicted","not_enough_information"]
ALLOWED_SEVERITY = ["none","low","medium","high","unknown"]
ALLOWED_RISK_FLAGS = [
    "none","blurry_image","cropped_or_obstructed","low_light_or_glare",
    "wrong_angle","wrong_object","wrong_object_part","damage_not_visible",
    "claim_mismatch","possible_manipulation","non_original_image",
    "text_instruction_present","user_history_risk","manual_review_required"
]
ALLOWED_OBJECT_PARTS = {
    "car": ["front_bumper","rear_bumper","door","hood","windshield",
            "side_mirror","headlight","taillight","fender","quarter_panel","body","unknown"],
    "laptop": ["screen","keyboard","trackpad","hinge","lid","corner",
               "port","base","body","unknown"],
    "package": ["box","package_corner","package_side","seal","label",
                "contents","item","unknown"]
}
OUTPUT_COLUMNS = [
    "user_id","image_paths","user_claim","claim_object",
    "evidence_standard_met","evidence_standard_met_reason",
    "risk_flags","issue_type","object_part","claim_status",
    "claim_status_justification","supporting_image_ids",
    "valid_image","severity"
]
