# SQLite Database Layer for Step 3 Verified Database & Queue Management

import os
import re
import json
import sqlite3
from typing import List, Dict, Any, Optional
from core.config import AUTOMATION_ROOT

OUTPUT_DIR = os.path.join(AUTOMATION_ROOT, "output", "step3_verified")
VERIFIED_DB_PATH = os.path.join(OUTPUT_DIR, "verified.db")
STEP1_DB_PATH = os.path.join(AUTOMATION_ROOT, "output", "step1_anilist", "anime.db")
STEP2_DB_PATH = os.path.join(AUTOMATION_ROOT, "output", "step2_anibridge", "anibridge.db")


class VerifiedDB:

    def __init__(self, db_path: str = VERIFIED_DB_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS verified_anime (
                anilist_id INTEGER PRIMARY KEY,
                mappings TEXT,
                episode_types TEXT,
                manual_checked BOOLEAN DEFAULT 1, 
                verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS skipped_anime (
                anilist_id INTEGER PRIMARY KEY,
                reason TEXT,
                skipped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            import glob
            mapping_files = glob.glob(os.path.join(AUTOMATION_ROOT, "..", "assets", "mapping-*.json"))
            for json_path in mapping_files:
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, list):
                            for entry in data:
                                conn.execute("""
                                INSERT OR IGNORE INTO verified_anime (
                                    anilist_id, mappings, episode_types, manual_checked
                                ) VALUES (?, ?, ?, 1)
                                """, (
                                    entry.get("anilist_id"),
                                    json.dumps(entry.get("mappings", [])),
                                    json.dumps(entry.get("episode_types", {}))
                                ))
                    except Exception as e:
                        import sys
                        print(f"[VerifiedDB] Sync error on {json_path}: {e}", file=sys.stderr)
                    
            skip_json_path = os.path.join(AUTOMATION_ROOT, "..", "assets", "skipped-anime.json")
            if os.path.exists(skip_json_path):
                try:
                    with open(skip_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for entry in data:
                            conn.execute("INSERT OR REPLACE INTO skipped_anime (anilist_id, reason) VALUES (?, ?)", 
                                (entry.get("anilist_id"), entry.get("reason")))
                except Exception as e:
                    pass

    def ensure_step1_indexes(self) -> None:
        if os.path.exists(STEP1_DB_PATH):
            try:
                with sqlite3.connect(STEP1_DB_PATH) as conn:
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_anime_status ON anime(status)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_anime_format ON anime(format)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_anime_id ON anime(anilist_id)")
            except Exception:
                pass

    def reset_db(self) -> None:
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass
        self.init_db()

    def get_verified_ids(self) -> set:
        if not os.path.exists(self.db_path):
            return set()
        with sqlite3.connect(self.db_path) as conn:
            return {row[0] for row in conn.execute("SELECT anilist_id FROM verified_anime WHERE manual_checked = 1").fetchall()}

    def get_skipped_ids(self) -> set:
        if not os.path.exists(self.db_path):
            return set()
        with sqlite3.connect(self.db_path) as conn:
            try:
                return {row[0] for row in conn.execute("SELECT anilist_id FROM skipped_anime").fetchall()}
            except Exception:
                return set()

    def get_unverified_queue(self, status_filter: str = "ALL", verification_filter: str = "UNVERIFIED", format_filter: str = "ALL", offset: int = 0, limit: Optional[int] = 30, search_query: Optional[str] = None, sort_by: str = "POPULARITY_DESC") -> Dict[str, Any]:
        if not os.path.exists(STEP1_DB_PATH):
            return {"queue": [], "total_matched": 0, "has_more": False}

        try:
            with sqlite3.connect(STEP1_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                verified_attached = False
                if os.path.exists(self.db_path):
                    conn.execute(f"ATTACH DATABASE '{self.db_path}' AS verified_db")
                    verified_attached = True

                conditions, params = [], []
                ver = verification_filter.upper()
                if verified_attached:
                    if ver == "UNVERIFIED":
                        conditions.append("a.anilist_id NOT IN (SELECT anilist_id FROM verified_db.verified_anime WHERE manual_checked = 1)")
                        conditions.append("a.anilist_id NOT IN (SELECT anilist_id FROM verified_db.skipped_anime)")
                    elif ver == "VERIFIED":
                        conditions.append("a.anilist_id IN (SELECT anilist_id FROM verified_db.verified_anime WHERE manual_checked = 1)")
                    elif ver == "SKIPPED":
                        conditions.append("a.anilist_id IN (SELECT anilist_id FROM verified_db.skipped_anime)")
                elif ver == "VERIFIED":
                    return {"queue": [], "total_matched": 0, "has_more": False}

                s = status_filter.upper()
                if s != "ALL":
                    conditions.append("a.status = ?")
                    params.append(s)

                f = format_filter.upper()
                if f == "MOVIE":
                    conditions.append("a.format LIKE '%MOVIE%'")
                elif f == "TV":
                    conditions.append("a.format IN ('TV', 'TV_SHORT')")
                elif f == "SPECIAL":
                    conditions.append("a.format IN ('OVA', 'ONA', 'SPECIAL')")

                if search_query and search_query.strip():
                    q = f"%{search_query.strip().lower()}%"
                    conditions.append("(LOWER(COALESCE(a.title_english, '')) LIKE ? OR LOWER(COALESCE(a.title_romaji, '')) LIKE ?)")
                    params.extend([q, q])

                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                total_matched = conn.execute(f"SELECT COUNT(*) FROM anime a {where_clause}", params).fetchone()[0]

                order_clause = "ORDER BY a.popularity DESC, a.anilist_id DESC" if sort_by == "POPULARITY_DESC" else "ORDER BY a.anilist_id DESC"
                
                data_sql = f"""
                    SELECT a.anilist_id, COALESCE(a.title_english, a.title_romaji, 'Anime #' || a.anilist_id) AS title,
                           a.format, a.status, a.episodes
                    FROM anime a {where_clause} {order_clause} LIMIT ? OFFSET ?
                """
                rows = conn.execute(data_sql, params + [limit if limit is not None else -1, offset]).fetchall()
                verified_ids = self.get_verified_ids()
                skipped_ids = self.get_skipped_ids()

                queue = [{
                    "anilist_id": r["anilist_id"], "title": r["title"], "format": r["format"] or "TV",
                    "status": r["status"] or "FINISHED", "episodes": r["episodes"] or 0,
                    "is_verified": r["anilist_id"] in verified_ids,
                    "is_skipped": r["anilist_id"] in skipped_ids
                } for r in rows]

                return {"queue": queue, "total_matched": total_matched, "has_more": (offset + len(queue)) < total_matched}
        except Exception as e:
            import sys
            print(f"[get_unverified_queue error] {e}", file=sys.stderr)
            return {"queue": [], "total_matched": 0, "has_more": False}

    def get_stats(self) -> Dict[str, Any]:
        verified_count = len(self.get_verified_ids())
        total_count = 0
        if os.path.exists(STEP1_DB_PATH):
            with sqlite3.connect(STEP1_DB_PATH) as conn:
                total_count = conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
        return {
            "verified_count": verified_count, "total_count": total_count,
            "percentage": round((verified_count / total_count * 100), 1) if total_count > 0 else 0
        }

    def get_anime_details(self, anilist_id: int) -> Dict[str, Any]:
        details = {
            "anilist_id": anilist_id, "title_romaji": None, "title_english": None, 
            "format": None, "status": None, "episodes": None, "raw_metadata": {}, 
            "is_verified": False, "mappings": [], "episode_types": {}
        }

        if os.path.exists(STEP1_DB_PATH):
            with sqlite3.connect(STEP1_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT title_romaji, title_english, format, status, episodes, released_episodes, raw_metadata FROM anime WHERE anilist_id = ?", (anilist_id,)).fetchone()
                if row:
                    details.update(dict(row))
                    if row["raw_metadata"]:
                        try:
                            details["raw_metadata"] = json.loads(row["raw_metadata"])
                        except Exception:
                            pass

        verified_row = None
        if os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                verified_row = conn.execute("SELECT mappings, episode_types FROM verified_anime WHERE anilist_id = ?", (anilist_id,)).fetchone()

        if verified_row:
            try:
                details["mappings"] = json.loads(verified_row["mappings"]) if verified_row["mappings"] else []
                ep_types = json.loads(verified_row["episode_types"]) if verified_row["episode_types"] else {}
                from core.transformers import decompress_episode_types
                details["episode_types"] = decompress_episode_types(ep_types)
            except Exception:
                pass
            details["is_verified"] = True
        elif os.path.exists(STEP2_DB_PATH):
            with sqlite3.connect(STEP2_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                row2 = conn.execute("SELECT mal_id, anidb_id, tmdb_show_id, tmdb_movie_id, tvdb_show_id, tvdb_movie_id, imdb_id, episode_mappings FROM mappings WHERE anilist_id = ?", (anilist_id,)).fetchone()
                if row2:
                    r2_dict = dict(row2)
                    fmt = (details.get("format") or "").lower()
                    is_movie = "movie" in fmt
                    from core.transformers import build_anibridge_mappings
                    details["mappings"].extend(build_anibridge_mappings(r2_dict, is_movie))

        rel_eps = details.get("released_episodes") or details.get("episodes")
        if not rel_eps or rel_eps <= 0:
            raw = details.get("raw_metadata") or {}
            next_airing = raw.get("nextAiringEpisode")
            if next_airing and isinstance(next_airing, dict):
                rel_eps = max(0, next_airing.get("episode", 1) - 1)

        details["released_episodes"] = rel_eps if rel_eps else 0
        return details

    def save_verified_anime(self, data: Dict[str, Any]) -> None:
        clean_mappings = []
        for m in data.get("mappings", []):
            cleaned = {k: v for k, v in m.items() if k != "_preview" and k != "globalIndex"}
            if cleaned.get("provider") == "mal":
                cleaned = {"provider": "mal", "id": cleaned.get("id")}
            clean_mappings.append(cleaned)
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            INSERT INTO verified_anime (
                anilist_id, mappings, episode_types, manual_checked
            ) VALUES (?, ?, ?, 1)
            ON CONFLICT(anilist_id) DO UPDATE SET
                mappings=excluded.mappings,
                episode_types=excluded.episode_types,
                manual_checked=1,
                verified_at=CURRENT_TIMESTAMP
            """, (
                data["anilist_id"],
                json.dumps(clean_mappings, ensure_ascii=False),
                json.dumps(data.get("episode_types", {}), ensure_ascii=False)
            ))

    def remove_verified_anime(self, anilist_id: int) -> None:
        if not os.path.exists(self.db_path):
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM verified_anime WHERE anilist_id = ?", (anilist_id,))

    def skip_anime(self, anilist_id: int, reason: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO skipped_anime (anilist_id, reason) VALUES (?, ?)", (anilist_id, reason))
