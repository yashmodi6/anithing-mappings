import os
import json
import sqlite3
from typing import Dict, Any, List

def init_db(output_dir: str, clean: bool = False) -> sqlite3.Connection:
    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(output_dir, "anime.db")
    if clean:
        for file_name in ["anime.db", "anime.db-wal", "anime.db-shm", "anime.db-journal", "stats.json"]:
            target_path = os.path.join(output_dir, file_name)
            if os.path.exists(target_path):
                try: os.remove(target_path)
                except Exception: pass

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime (
        anilist_id INTEGER PRIMARY KEY,
        mal_id INTEGER,
        title_romaji TEXT,
        title_english TEXT,
        title_native TEXT,
        format TEXT,
        status TEXT,
        episodes INTEGER,
        released_episodes INTEGER,
        popularity INTEGER,
        updated_at INTEGER,
        raw_metadata TEXT,
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Dead IDs have been moved to persistent assets/dead_ids.db to survive --clean runs
    for col, col_type in [("format", "TEXT"), ("status", "TEXT"), ("episodes", "INTEGER"), ("released_episodes", "INTEGER"), ("popularity", "INTEGER")]:
        try: cursor.execute(f"ALTER TABLE anime ADD COLUMN {col} {col_type}")
        except Exception: pass
    conn.commit()
    return conn

def get_last_updated_at(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(updated_at) FROM anime")
        row = cursor.fetchone()
        return row[0] if (row and row[0]) else 0
    except Exception: return 0

def get_max_local_id(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(anilist_id) FROM anime")
        row = cursor.fetchone()
        return row[0] if (row and row[0]) else 0
    except Exception: return 0

def get_local_timestamp_map(conn: sqlite3.Connection) -> Dict[int, int]:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT anilist_id, updated_at FROM anime")
        return {row[0]: (row[1] or 0) for row in cursor.fetchall()}
    except Exception: return {}

def save_anime_batch(conn: sqlite3.Connection, items: List[Dict[str, Any]]) -> None:
    if not items: return
    cursor = conn.cursor()
    rows = []
    for item in items:
        anilist_id = item["id"]
        mal_id = item.get("idMal")
        titles = item.get("title") or {}
        format_val = item.get("format")
        status_val = item.get("status")
        episodes_val = item.get("episodes")
        next_airing = item.get("nextAiringEpisode")
        if not episodes_val and next_airing and isinstance(next_airing, dict):
            released_val = max(0, next_airing.get("episode", 1) - 1)
        else:
            released_val = episodes_val

        updated_at = item.get("updatedAt") or 0
        popularity = item.get("popularity") or 0
        raw_metadata = json.dumps(item, ensure_ascii=False)
        title_english = titles.get("english") or titles.get("userPreferred")
        rows.append((anilist_id, mal_id, titles.get("romaji"), title_english, titles.get("native"), format_val, status_val, episodes_val, released_val, popularity, updated_at, raw_metadata))

    cursor.executemany("""
    INSERT INTO anime (anilist_id, mal_id, title_romaji, title_english, title_native, format, status, episodes, released_episodes, popularity, updated_at, raw_metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(anilist_id) DO UPDATE SET
        mal_id=excluded.mal_id,
        title_romaji=excluded.title_romaji,
        title_english=excluded.title_english,
        title_native=excluded.title_native,
        format=excluded.format,
        status=excluded.status,
        episodes=excluded.episodes,
        released_episodes=excluded.released_episodes,
        popularity=excluded.popularity,
        updated_at=excluded.updated_at,
        raw_metadata=excluded.raw_metadata,
        synced_at=CURRENT_TIMESTAMP
    """, rows)
    conn.commit()

def save_stats(conn: sqlite3.Connection, db_path: str, stats_path: str) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM anime")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM anime WHERE mal_id IS NOT NULL AND mal_id != '' AND mal_id != 0")
    mal_present = cursor.fetchone()[0]

    status_breakdown = {}
    try:
        cursor.execute("SELECT status, COUNT(*) FROM anime GROUP BY status ORDER BY COUNT(*) DESC")
        for row in cursor.fetchall():
            st = row[0] if row[0] else "UNKNOWN"
            status_breakdown[st] = row[1]
    except Exception: pass

    stats = {
        "step": "step1_anilist",
        "total_animes": total,
        "mal_ids_present": mal_present,
        "mal_ids_missing": total - mal_present,
        "mal_ids_present_percentage": f"{((mal_present / total) * 100):.2f}%" if total > 0 else "0%",
        "status_breakdown": status_breakdown,
        "database_path": db_path
    }
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    return stats

# Gap filler helpers
def get_local_ids_in_range(conn: sqlite3.Connection, start_id: int, end_id: int) -> List[int]:
    cursor = conn.cursor()
    cursor.execute("SELECT anilist_id FROM anime WHERE anilist_id >= ? AND anilist_id <= ?", (start_id, end_id))
    return [row[0] for row in cursor.fetchall()]

DEAD_IDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "dead_ids.json")

def load_dead_ids() -> set:
    if os.path.exists(DEAD_IDS_PATH):
        try:
            with open(DEAD_IDS_PATH, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception: pass
    return set()

def save_dead_ids(dead_set: set) -> None:
    os.makedirs(os.path.dirname(DEAD_IDS_PATH), exist_ok=True)
    with open(DEAD_IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(list(dead_set), f)

def get_dead_ids_in_range(conn: sqlite3.Connection, start_id: int, end_id: int) -> List[int]:
    dead = load_dead_ids()
    return [d for d in dead if start_id <= d <= end_id]

def mark_dead_ids(conn: sqlite3.Connection, dead_ids: List[int]) -> None:
    if not dead_ids: return
    dead = load_dead_ids()
    dead.update(dead_ids)
    save_dead_ids(dead)
