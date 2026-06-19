import os

def parse_image_paths(image_paths_str, base_dir):
    paths = image_paths_str.strip().split(";")
    result = []
    for p in paths:
        p = p.strip()
        if not p:
            continue
        img_id = os.path.splitext(os.path.basename(p))[0]
        full_path = os.path.join(base_dir, p)
        result.append((img_id, full_path))
    return result

def validate_value(value, allowed_list, fallback="unknown"):
    if value and str(value).strip().lower() in allowed_list:
        return str(value).strip().lower()
    return fallback

def validate_flags(flags_str, allowed_flags):
    if not flags_str or str(flags_str).strip().lower() in ["","none","nan"]:
        return "none"
    flags = [f.strip().lower() for f in str(flags_str).split(";") if f.strip()]
    seen = set()
    deduped = []
    for f in flags:
        if f in allowed_flags and f not in seen:
            seen.add(f)
            deduped.append(f)
    return ";".join(deduped) if deduped else "none"

def merge_flags(*flag_strings):
    all_flags = []
    for fs in flag_strings:
        if fs and str(fs).strip().lower() not in ["none","","nan"]:
            for f in str(fs).split(";"):
                f = f.strip().lower()
                if f and f != "none" and f not in all_flags:
                    all_flags.append(f)
    return ";".join(all_flags) if all_flags else "none"
