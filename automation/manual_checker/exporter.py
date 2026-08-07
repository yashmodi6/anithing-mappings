import os
import json
import glob
from core.database import VerifiedDB

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
SKIPPED_ANIME_PATH = os.path.join(ASSETS_DIR, "skipped-anime.json")

def get_mapping_path(format_str: str) -> str:
    fmt = str(format_str).lower().replace("_", "-")
    if not fmt:
        fmt = "unknown"
    return os.path.join(ASSETS_DIR, f"mapping-{fmt}.json")

def update_skipped_anime_json(anilist_id: int, reason: str) -> None:
    """Atomically append or update a skipped anime in the skipped-anime.json file."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    existing: list = []
    if os.path.exists(SKIPPED_ANIME_PATH):
        with open(SKIPPED_ANIME_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if not isinstance(existing, list):
            existing = []

    existing = [e for e in existing if e.get("anilist_id") != anilist_id]
    existing.append({"anilist_id": anilist_id, "reason": reason})
    existing.sort(key=lambda x: x.get("anilist_id", 0))

    tmp_path = SKIPPED_ANIME_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp_path, SKIPPED_ANIME_PATH)

def update_mapping_edits_json(data: dict) -> None:
    """Atomically append or update a verified anime in its format-specific mapping JSON file."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    format_str = data.get("format", "UNKNOWN")
    path = get_mapping_path(format_str)

    existing: list = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
        except Exception:
            pass

    anilist_id = data["anilist_id"]
    from core.transformers import compress_episode_types, clean_mappings_for_export
    
    clean_mappings = clean_mappings_for_export(data.get("mappings", []))
    
    entry = {
        "anilist_id": anilist_id,
        "title": data.get("title") or data.get("title_english") or data.get("title_romaji"),
        "format": format_str,
        "status": data.get("status"),
        "total_episodes": data.get("total_episodes") or data.get("episodes"),
        "episode_types": compress_episode_types(data.get("episode_types", {})),
        "mappings": clean_mappings
    }
    
    existing = [e for e in existing if e.get("anilist_id") != anilist_id]
    existing.append(entry)
    existing.sort(key=lambda x: x.get("anilist_id", 0))

    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp_path, path)

def remove_mapping_edits_json(anilist_id: int) -> None:
    """Remove a verified anime from any mapping JSON file it might exist in."""
    for path in glob.glob(os.path.join(ASSETS_DIR, "mapping-*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                continue
            
            filtered = [e for e in existing if e.get("anilist_id") != anilist_id]
            if len(filtered) < len(existing):
                tmp_path = path + ".tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(filtered, f, ensure_ascii=False, indent=2, sort_keys=True)
                os.replace(tmp_path, path)
        except Exception:
            continue
