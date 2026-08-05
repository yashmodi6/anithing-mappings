import os
import json

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
MAPPING_EDITS_PATH = os.path.join(ASSETS_DIR, "mapping-edits.json")

def update_mapping_edits_json(data: dict) -> None:
    """Atomically append or update a verified anime in the mapping-edits.json file."""
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # Load existing file
    existing: list = []
    if os.path.exists(MAPPING_EDITS_PATH):
        with open(MAPPING_EDITS_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if not isinstance(existing, list):
            raise ValueError(f"Expected a list in {MAPPING_EDITS_PATH}, but got {type(existing)}")

    # Replace or append entry for this anilist_id
    anilist_id = data["anilist_id"]
    
    # If the format is MOVIE, set episodes to null, otherwise use the full mappings
    is_movie = "MOVIE" in str(data.get("format", "")).upper()
    episodes_data = None if is_movie else data.get("episode_mappings", {})

    entry = {
        "anilist_id": anilist_id,
        "mal_id": data.get("mal_id"),
        "tmdb_show_id": data.get("tmdb_show_id"),
        "tmdb_movie_id": data.get("tmdb_movie_id"),
        "tvdb_show_id": data.get("tvdb_show_id"),
        "tvdb_movie_id": data.get("tvdb_movie_id"),
        "episodes": episodes_data
    }
    
    # Remove existing entry for this anime to avoid duplicates on re-verification
    existing = [e for e in existing if e.get("anilist_id") != anilist_id]
    existing.append(entry)

    # Write to a temporary file first, then atomically replace to prevent data corruption
    tmp_path = MAPPING_EDITS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, MAPPING_EDITS_PATH)

def remove_mapping_edits_json(anilist_id: int) -> None:
    """Remove a verified anime from the mapping-edits.json file."""
    if not os.path.exists(MAPPING_EDITS_PATH):
        return

    try:
        with open(MAPPING_EDITS_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if not isinstance(existing, list):
            return
    except Exception:
        return

    filtered = [e for e in existing if e.get("anilist_id") != anilist_id]
    if len(filtered) == len(existing):
        return

    tmp_path = MAPPING_EDITS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, MAPPING_EDITS_PATH)

