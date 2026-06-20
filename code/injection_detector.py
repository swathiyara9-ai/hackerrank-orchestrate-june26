"""
Prompt injection detector for claim conversations.
Scans customer messages for instruction-like patterns that attempt
to influence automated review decisions.
"""

import re

# Patterns that indicate prompt injection attempts
# Each tuple: (compiled_regex, description)
INJECTION_PATTERNS = [
    # English direct instructions
    (re.compile(r"approve\s+(this|the|my|immediately|claim|it)", re.I),
     "Direct approval instruction"),
    (re.compile(r"skip\s+(manual\s+)?review", re.I),
     "Skip review instruction"),
    (re.compile(r"ignore\s+(all\s+)?(previous\s+)?instructions", re.I),
     "Ignore instructions attack"),
    (re.compile(r"mark\s+(this|as|it)\s+(as\s+)?(supported|approved|accepted)", re.I),
     "Mark-as-supported instruction"),
    (re.compile(r"(should|must|please)\s+approve", re.I),
     "Imperative approval"),
    (re.compile(r"accept\s+(this|the|my|it)\s+(claim|quickly|immediately)", re.I),
     "Accept claim instruction"),
    (re.compile(r"system\s+reading\s+this\s+should", re.I),
     "System-directed instruction"),
    (re.compile(r"do\s+not\s+(flag|reject|deny|review)", re.I),
     "Do-not-flag instruction"),

    # Hindi/Hinglish injection patterns
    (re.compile(r"claim\s+approve\s+kar", re.I),
     "Hindi approve instruction"),
    (re.compile(r"follow\s+kar(ke|na|o)", re.I),
     "Hindi follow instruction"),
    (re.compile(r"usko\s+follow", re.I),
     "Hindi follow-note instruction"),
    (re.compile(r"approve\s+kar\s+dena", re.I),
     "Hindi approve-do instruction"),

    # Spanish injection patterns
    (re.compile(r"aprueb(a|e|en)\s+(esto|el|la|mi)", re.I),
     "Spanish approve instruction"),

    # Embedded note references (images with text instructions)
    (re.compile(r"note\s+(in|on)\s+(the\s+)?(photo|image|picture)\s+.*?(approve|accept|support)", re.I),
     "Image-embedded instruction reference"),
    (re.compile(r"photo\s+mein\s+note", re.I),
     "Hindi image-note reference"),
]


def _extract_customer_messages(conversation):
    """Extract only customer-side messages from the conversation."""
    parts = conversation.split("|")
    customer_msgs = []
    for part in parts:
        part = part.strip()
        lower = part.lower()
        if lower.startswith("customer:") or lower.startswith("cliente:"):
            # Remove the speaker prefix
            msg = part.split(":", 1)[1].strip() if ":" in part else part
            customer_msgs.append(msg)
    return " ".join(customer_msgs)


def detect_injection(conversation):
    """
    Scan conversation for prompt injection attempts.

    Returns:
        tuple: (is_injection: bool, matched_patterns: list[str])
    """
    # Only scan customer messages, not support agent text
    customer_text = _extract_customer_messages(conversation)

    matched = []
    for pattern, description in INJECTION_PATTERNS:
        if pattern.search(customer_text):
            matched.append(description)

    return (len(matched) > 0, matched)
