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
                mal_id INTEGER, anidb_id INTEGER, tmdb_show_id INTEGER, tmdb_movie_id INTEGER,
                tvdb_show_id INTEGER, tvdb_movie_id INTEGER, imdb_id TEXT, episode_mappings TEXT,
                manual_checked BOOLEAN DEFAULT 1, verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            json_path = os.path.join(AUTOMATION_ROOT, "..", "assets", "mapping-edits.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for entry in data:
                            conn.execute("""
                            INSERT OR IGNORE INTO verified_anime (
                                anilist_id, mal_id, anidb_id, tmdb_show_id, tmdb_movie_id, tvdb_show_id, tvdb_movie_id, imdb_id, episode_mappings, manual_checked
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                            """, (
                                entry.get("anilist_id"), entry.get("mal_id"), entry.get("anidb_id"),
                                entry.get("tmdb_show_id"), entry.get("tmdb_movie_id"), entry.get("tvdb_show_id"),
                                entry.get("tvdb_movie_id"), entry.get("imdb_id"), json.dumps(entry.get("episode_overrides", {}))
                            ))
                except Exception as e:
                    import sys
                    print(f"[VerifiedDB] Sync error: {e}", file=sys.stderr)

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
                    elif ver == "VERIFIED":
                        conditions.append("a.anilist_id IN (SELECT anilist_id FROM verified_db.verified_anime WHERE manual_checked = 1)")
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

                queue = [{
                    "anilist_id": r["anilist_id"], "title": r["title"], "format": r["format"] or "TV",
                    "status": r["status"] or "FINISHED", "episodes": r["episodes"] or 0,
                    "is_verified": r["anilist_id"] in verified_ids
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
            "anilist_id": anilist_id, "mal_id": None, "anidb_id": None, "tmdb_show_id": None,
            "tmdb_movie_id": None, "tvdb_show_id": None, "tvdb_movie_id": None, "imdb_id": None,
            "episode_mappings": {}, "title_romaji": None, "title_english": None, "format": None,
            "status": None, "episodes": None, "raw_metadata": {}, "is_verified": False
        }

        if os.path.exists(STEP1_DB_PATH):
            with sqlite3.connect(STEP1_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT mal_id, title_romaji, title_english, format, status, episodes, released_episodes, raw_metadata FROM anime WHERE anilist_id = ?", (anilist_id,)).fetchone()
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
                verified_row = conn.execute("SELECT mal_id, anidb_id, tmdb_show_id, tmdb_movie_id, tvdb_show_id, tvdb_movie_id, imdb_id FROM verified_anime WHERE anilist_id = ?", (anilist_id,)).fetchone()

        if verified_row:
            details.update(dict(verified_row))
            details["is_verified"] = True
        elif os.path.exists(STEP2_DB_PATH):
            with sqlite3.connect(STEP2_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                row2 = conn.execute("SELECT mal_id, anidb_id, tmdb_show_id, tmdb_movie_id, tvdb_show_id, tvdb_movie_id, imdb_id, episode_mappings FROM mappings WHERE anilist_id = ?", (anilist_id,)).fetchone()
                if row2:
                    r2_dict = dict(row2)
                    ep_map_raw = r2_dict.pop("episode_mappings", None)
                    if not details["mal_id"]:
                        details["mal_id"] = r2_dict.get("mal_id")
                    for k in ("anidb_id", "tmdb_show_id", "tmdb_movie_id", "tvdb_show_id", "tvdb_movie_id", "imdb_id"):
                        details[k] = r2_dict.get(k)
                    if ep_map_raw:
                        try:
                            details["episode_mappings"] = json.loads(ep_map_raw)
                        except Exception:
                            pass

        rel_eps = details.get("released_episodes") or details.get("episodes")
        if not rel_eps or rel_eps <= 0:
            raw = details.get("raw_metadata") or {}
            next_airing = raw.get("nextAiringEpisode")
            if next_airing and isinstance(next_airing, dict):
                rel_eps = max(0, next_airing.get("episode", 1) - 1)

        if not rel_eps or rel_eps <= 0:
            mappings = details.get("episode_mappings")
            max_ep = 0
            if mappings and isinstance(mappings, dict):
                for outer_val in mappings.values():
                    if isinstance(outer_val, dict):
                        for sub_k, sub_v in outer_val.items():
                            for expr in (str(sub_k), str(sub_v)):
                                for n in re.findall(r"\b\d+\b", expr):
                                    max_ep = max(max_ep, int(n))
            rel_eps = max_ep if max_ep > 0 else 0

        details["released_episodes"] = rel_eps
        return details

    def save_verified_anime(self, data: Dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            INSERT INTO verified_anime (
                anilist_id, mal_id, anidb_id, tmdb_show_id, tmdb_movie_id, tvdb_show_id, tvdb_movie_id, imdb_id, episode_mappings, manual_checked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(anilist_id) DO UPDATE SET
                mal_id=excluded.mal_id, anidb_id=excluded.anidb_id, tmdb_show_id=excluded.tmdb_show_id,
                tmdb_movie_id=excluded.tmdb_movie_id, tvdb_show_id=excluded.tvdb_show_id, tvdb_movie_id=excluded.tvdb_movie_id,
                imdb_id=excluded.imdb_id, episode_mappings=excluded.episode_mappings, manual_checked=1, verified_at=CURRENT_TIMESTAMP
            """, (
                data["anilist_id"], data.get("mal_id"), data.get("anidb_id"), data.get("tmdb_show_id"),
                data.get("tmdb_movie_id"), data.get("tvdb_show_id"), data.get("tvdb_movie_id"), data.get("imdb_id"),
                json.dumps(data.get("episode_mappings", {}), ensure_ascii=False)
            ))

    def remove_verified_anime(self, anilist_id: int) -> None:
        if not os.path.exists(self.db_path):
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM verified_anime WHERE anilist_id = ?", (anilist_id,))
