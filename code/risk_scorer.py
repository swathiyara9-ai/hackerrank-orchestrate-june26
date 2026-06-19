import pandas as pd

def load_user_history(path):
    return pd.read_csv(path)

def get_risk_flags(user_id, history_df):
    row = history_df[history_df["user_id"] == user_id]
    if row.empty:
        return "none"
    row = row.iloc[0]
    flags = []

    existing = str(row.get("history_flags","")).strip()
    if existing and existing.lower() not in ["none","","nan"]:
        for f in existing.split(";"):
            f = f.strip()
            if f and f.lower() != "none" and f not in flags:
                flags.append(f)

    total = int(row.get("past_claim_count", 0))
    rejected = int(row.get("rejected_claim", 0))
    if total > 0 and (rejected / total) > 0.3:
        if "user_history_risk" not in flags:
            flags.append("user_history_risk")

    recent = int(row.get("last_90_days_claim_count", 0))
    if recent >= 4:
        if "manual_review_required" not in flags:
            flags.append("manual_review_required")

    return ";".join(flags) if flags else "none"
