"""
Heuristic claim analyzer — v2.
Extracts structured fields from conversation text using keyword rules
tuned against the 20 ground-truth sample_claims.csv rows.
Used as primary analyzer when Gemini API is unavailable.
"""

import re
from config import ALLOWED_ISSUE_TYPES, ALLOWED_CLAIM_STATUS, ALLOWED_SEVERITY, ALLOWED_OBJECT_PARTS


# ---------------------------------------------------------------------------
# Keyword maps
# ---------------------------------------------------------------------------

ISSUE_TYPE_KEYWORDS = {
    "crack": [
        "crack", "cracked", "cracking", "glass broke", "split",
        "fracture", "chipped", "stone hit", "chip",
        "shattered", "shattered screen", "screen shatter",
        "glass shatter",
        # Spanish
        "agrietado", "grieta", "rajado",
    ],
    "dent": [
        "dent", "dented", "denting", "depression",
        "indentation",
        # Spanish
        "abolladura", "abollado",
    ],
    "scratch": [
        "scratch", "scratched", "scrape", "scraped", "scraping",
        "scuff", "gouge", "mark across",
        # Spanish
        "raspado", "raspon", "raspadura",
    ],
    "stain": [
        "stain", "stained", "staining", "spill", "spilled", "sticky",
        "residue", "discolor"
    ],
    "water_damage": [
        "water damage", "water damaged", "wet stain", "moisture damage",
        "flood", "soaked", "wet-looking", "got wet", "became wet",
        "box wet", "package wet", "label wet"
    ],
    "broken_part": [
        "broken part", "snapped", "wobble", "wobbles",
        "not sitting", "clipped my car", "detached", "loose hinge",
        "hinge broke", "fell off", "hanging", "crumbled",
        "not opening smoothly", "no longer opens",
        "does not close", "will not shut", "piece came off",
        "mirror came off", "part detached",
        "broken", "broke",
        "is broken", "looks broken", "was broken",
        "appears broken", "seems broken", "got broken",
        "is damaged", "looks damaged",
        # Hindi/Hinglish
        "toot gaya", "toot", "tuta", "toota", "tuta hua",
        "toot gaya hai", "tut gaya",
        # Spanish
        "roto", "rota", "se rompio", "esta roto",
        "dano", "danado",
    ],
    "missing_part": [
        "missing key", "keycap", "keycaps came off", "key fell off",
        "keys missing", "part missing", "piece missing",
        "missing part", "came off", "fell out",
        # Spanish
        "faltan", "falta",
    ],
    "crushed_packaging": [
        "crushed", "caved in", "caved", "collapsed", "compressed",
        "squashed", "smashed", "corner was crushed", "crushed in",
        "crushing",
    ],
    "torn_packaging": [
        "torn", "tore", "ripped", "phati", "phata", "seal broken",
        "seal wali", "parcel khola", "seal area torn",
        "seal damage", "tape phati", "jaise parcel khola",
        "opened jaisa", "seal torn", "package seal",
    ],
    "none": [
        "stopped working", "not working", "no longer working",
        "doesn't work", "does not work", "not functioning",
        "stopped functioning", "no physical damage", "functional issue",
        "no visible damage"
    ],
}

# Claim-object-specific object_part keyword maps
OBJECT_PART_KEYWORDS = {
    "car": {
        "rear_bumper": [
            "rear bumper", "back bumper", "back of the car", "rear of the car",
            "tapped from behind", "hit from behind", "rear area", "back area",
            "bumper area",
        ],
        "front_bumper": [
            "front bumper", "front side", "front of the car",
            "front part", "front par", "bumper ke upar",
        ],
        "windshield": [
            "windshield", "front glass", "windscreen", "glass crack",
            "stone hit", "crack spreading"
        ],
        "side_mirror": [
            "side mirror", "mirror", "wing mirror"
        ],
        "door": [
            "door", "along the side", "car door",
            "side of my car", "body panel"
        ],
        "headlight": [
            "headlight", "head light"
        ],
        "taillight": [
            "taillight", "tail light", "rear light", "back light"
        ],
        "hood": [
            "hood", "bonnet", "top panel", "front hood"
        ],
        "fender": [
            "fender"
        ],
        "quarter_panel": [
            "quarter panel", "quarter-panel"
        ],
        "body": [
            "body", "side panel", "panels", "outer body"
        ],
    },
    "laptop": {
        "screen": [
            "screen", "display", "monitor", "lcd",
            "display glass", "visible crack", "screen has a",
            "screen shatter", "shattered screen", "screen damage",
            "display area", "screen is broken", "broken screen"
        ],
        "hinge": [
            "hinge", "opens smoothly", "opening", "lid",
            "no longer opens", "hinge area", "hinge broke"
        ],
        "keyboard": [
            "keyboard", "keys", "key", "typing area", "spill on"
        ],
        "corner": [
            "corner", "edge of the laptop", "corner of the laptop",
            "hit the floor", "hit the corner", "dent on corner"
        ],
        "trackpad": [
            "trackpad", "touchpad", "track pad", "touch pad"
        ],
        "lid": [
            "lid", "outer cover", "outer lid", "outer shell", "back of the screen"
        ],
        "port": [
            "port", "usb", "charging port", "hdmi", "jack"
        ],
        "base": [
            "base", "bottom panel", "underside", "bottom of the laptop"
        ],
        "body": [
            "body", "casing", "chassis", "body only", "outer body"
        ],
    },
    "package": {
        "package_corner": [
            "corner", "corner was crushed", "corner damage",
            "edge of package", "one corner"
        ],
        "seal": [
            "seal", "tape", "seal area", "phati hui",
            "seal damage", "seal wali", "seal torn"
        ],
        "package_side": [
            "package side", "outside of the package",
            "wet stain", "water stain", "water damage", "exterior"
        ],
        "box": [
            "box", "cardboard box", "cardboard"
        ],
        "label": [
            "label", "shipping label", "mailing label", "address label"
        ],
        "contents": [
            "not inside", "missing",
            "could not find the product", "could not find the item",
            "contents", "product inside",
            "wasn't there", "package empty",
            "nothing inside"
        ],
        "item": [
            "item", "product", "device"
        ],
    },
}

# Severity keyword sets
SEVERITY_KEYWORDS = {
    "high": [
        "completely broken", "severely damaged", "major damage",
        "destroyed", "crushed completely", "collapsed entirely",
        "irreparable", "large crack spreading", "deep gash",
        "totally unusable", "beyond repair",
        "badly crushed", "badly damaged", "bad condition",
        "massive", "huge crack", "entire screen",
    ],
    "medium": [
        "crack", "broken", "hinge broke", "wobbles", "dent",
        "spilled water", "water damage", "stain", "visible damage",
        "clear damage", "mark visible", "scratch visible",
        "bumper damage", "crushed", "torn", "shattered"
    ],
    "low": [
        "minor scratch", "small scratch", "small dent", "small mark",
        "light scratch", "slight", "superficial",
        "barely visible", "cosmetic", "little mark", "hairline",
        "corner dent",
    ],
    "none": [
        "stopped working", "not working", "functional",
        "no physical", "no visible", "trackpad issue",
    ],
}

# Phrases that strongly suggest "not_enough_information" status
# Deliberately narrow to avoid false positives from claim-type uncertainty
NEI_PHRASES = [
    "not fully sure", "not certain", "cannot find",
    "could not find", "couldn't find", "wasn't there", "not inside",
    "not sure how to explain", "not sure what happened",
    "i am not fully sure", "could not see", "not visible",
    "couldn't see any",
]

# Phrases that suggest "contradicted" (functional claim, no physical damage)
CONTRADICTED_PHRASES = [
    "stopped working", "no longer works",
    "does not work", "not functioning", "functional issue",
    "no physical damage", "no visible damage",
]

# Missing item patterns → NEI + issue_type=unknown
MISSING_ITEM_PATTERNS = [
    "not inside the box", "not inside",
    "could not find the product", "could not find the item",
    "nothing inside", "item is not there",
    "package was empty", "product was missing",
    "contents are missing", "item went missing",
]


# ---------------------------------------------------------------------------
# Core extraction helpers
# ---------------------------------------------------------------------------

def _normalize(text):
    return text.lower().strip()


def _match_any(text, keywords):
    t = _normalize(text)
    return any(kw.lower() in t for kw in keywords)


def _is_missing_item_claim(text):
    """True if claim is about a missing item (not packaging damage)."""
    t = _normalize(text)
    return any(p in t for p in MISSING_ITEM_PATTERNS)


def extract_issue_type(conversation, claim_object):
    text = _normalize(conversation)

    # For non-package objects, use simpler ordering
    if claim_object == "package":
        ordered = [
            "water_damage",
            "torn_packaging",
            "crushed_packaging",
            "stain", "crack", "missing_part", "broken_part", "scratch", "dent", "none"
        ]
    else:
        ordered = [
            "water_damage", "stain", "crack", "scratch",
            "missing_part", "dent", "broken_part", "none"
        ]

    for issue in ordered:
        if _match_any(text, ISSUE_TYPE_KEYWORDS.get(issue, [])):
            if issue in ALLOWED_ISSUE_TYPES:
                return issue
    return "unknown"


def extract_object_part(conversation, claim_object):
    text = _normalize(conversation)
    parts = OBJECT_PART_KEYWORDS.get(claim_object, {})
    best_part = "unknown"
    best_len = 0
    for part, keywords in parts.items():
        for kw in keywords:
            if kw.lower() in text and len(kw) > best_len:
                best_len = len(kw)
                best_part = part
    return best_part


def extract_severity(conversation, issue_type):
    if issue_type == "none":
        return "none"
    if issue_type == "unknown":
        return "unknown"

    text = _normalize(conversation)

    # Check for explicit modifiers (order matters: high → low → default)
    if _match_any(text, SEVERITY_KEYWORDS["high"]):
        return "high"
    if _match_any(text, SEVERITY_KEYWORDS["none"]):
        return "none"
    if _match_any(text, SEVERITY_KEYWORDS["low"]):
        return "low"
    if _match_any(text, SEVERITY_KEYWORDS["medium"]):
        return "medium"

    # Fallback by issue type
    LOW_ISSUE = {"scratch"}
    HIGH_ISSUE = {"glass_shatter"}
    UNKNOWN_ISSUE = {"unknown"}
    NONE_ISSUE = {"none"}

    if issue_type in LOW_ISSUE:
        return "low"
    if issue_type in HIGH_ISSUE:
        return "high"
    if issue_type in UNKNOWN_ISSUE:
        return "unknown"
    if issue_type in NONE_ISSUE:
        return "none"
    return "medium"


def _detect_nei_reason(text):
    """Returns 'uncertainty' | 'missing_item' | None"""
    if _is_missing_item_claim(text):
        return "missing_item"
    if _match_any(text, NEI_PHRASES):
        return "uncertainty"
    return None


def extract_claim_status(conversation, issue_type, image_count):
    text = _normalize(conversation)

    nei_reason = _detect_nei_reason(text)

    if nei_reason == "missing_item":
        return ("not_enough_information",
                "Claim involves missing contents which cannot be verified from images.")

    if nei_reason == "uncertainty":
        return ("not_enough_information",
                "Claim description contains uncertainty about the nature or extent of damage.")

    # Functional issues with no physical damage claim → contradicted
    if issue_type == "none" or _match_any(text, CONTRADICTED_PHRASES):
        return ("contradicted",
                "Claim describes a functional issue; no physical damage is evident.")

    # Default: supported if images are present
    if image_count > 0:
        return ("supported",
                "Damage description is consistent and photographic evidence has been submitted.")
    return ("not_enough_information",
            "No images were provided to support the claim.")


def extract_supporting_ids(image_paths_with_ids, claim_status):
    if claim_status == "supported":
        ids = [img_id for img_id, _ in image_paths_with_ids]
        return ";".join(ids) if ids else "none"
    return "none"


# ---------------------------------------------------------------------------
# Main entry point (mirrors vision.analyze_claim signature)
# ---------------------------------------------------------------------------

def analyze_claim_heuristic(image_paths_with_ids, user_claim, claim_object):
    """
    Returns the same dict structure as vision.analyze_claim().
    No API calls — pure text heuristics.
    """
    image_count = len(image_paths_with_ids)
    conversation = user_claim
    text = _normalize(conversation)

    issue_type = extract_issue_type(conversation, claim_object)
    object_part = extract_object_part(conversation, claim_object)
    severity = extract_severity(conversation, issue_type)
    claim_status, justification = extract_claim_status(conversation, issue_type, image_count)
    supporting_ids = extract_supporting_ids(image_paths_with_ids, claim_status)

    # --- Post-processing overrides ---

    # 1. When claim_status is NEI due to genuine uncertainty → issue/severity unknown
    nei_reason = _detect_nei_reason(text)
    if claim_status == "not_enough_information" and nei_reason in ("uncertainty", "missing_item"):
        issue_type = "unknown"
        severity = "unknown"

    # 2. When package claim is about missing item → unknown issue/severity
    if claim_object == "package" and _is_missing_item_claim(text):
        issue_type = "unknown"
        severity = "unknown"
        claim_status = "not_enough_information"
        justification = "Claim involves missing contents which cannot be verified visually."

    # 3. Laptop + crack → object_part is screen fallback ONLY if unknown
    if claim_object == "laptop" and issue_type == "crack" and object_part == "unknown":
        object_part = "screen"

    # 3b. Screen/windshield + broken_part → crack (broken screens are cracks)
    if claim_object == "laptop" and object_part == "screen" and issue_type == "broken_part":
        issue_type = "crack"
    if claim_object == "car" and object_part == "windshield" and issue_type == "broken_part":
        issue_type = "crack"

    # 4. Dent + corner mention → low severity (corner dents are cosmetic)
    if issue_type == "dent" and "corner" in text:
        severity = "low"

    # 5. When issue_type is overridden to unknown → object_part=unknown too
    if issue_type == "unknown" and claim_status == "not_enough_information":
        object_part = "unknown"

    return {
        "issue_type": issue_type,
        "object_part": object_part,
        "claim_status": claim_status,
        "claim_status_justification": justification,
        "supporting_image_ids": supporting_ids,
        "valid_image": True,
        "severity": severity,
        "image_quality_issues": "none",
    }
