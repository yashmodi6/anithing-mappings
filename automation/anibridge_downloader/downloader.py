# Pure Business Logic for Step 2 AniBridge Mappings Downloader & DB Engine

import os
import json
import sqlite3
import requests
from typing import Callable, Optional, Dict, Any, List

AUTOMATION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(AUTOMATION_ROOT, "output", "step2_anibridge")
GITHUB_RELEASE_API = "https://api.github.com/repos/anibridge/anibridge-mappings/releases/latest"

PROV_KEYS = {
    "mal": "mal_id", "anidb": "anidb_id", "tmdb_show": "tmdb_show_id",
    "tmdb_movie": "tmdb_movie_id", "tvdb_show": "tvdb_show_id",
    "tvdb_movie": "tvdb_movie_id", "imdb_movie": "imdb_id"
}


class AniBridgeDownloader:

    def __init__(self, output_dir: str = OUTPUT_DIR) -> None:
        self.output_dir = output_dir
        self.db_path = os.path.join(self.output_dir, "anibridge.db")
        self.mappings_path = os.path.join(self.output_dir, "mappings.min.json")
        self.stats_path = os.path.join(self.output_dir, "stats.json")

    def init_db(self, clean: bool = False) -> sqlite3.Connection:
        os.makedirs(self.output_dir, exist_ok=True)
        if clean:
            for ext in ["", "-wal", "-shm", "-journal"]:
                path = self.db_path + ext
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mappings (
            anilist_id INTEGER PRIMARY KEY, mal_id INTEGER, anidb_id INTEGER,
            tmdb_show_id INTEGER, tmdb_movie_id INTEGER, tvdb_show_id INTEGER,
            tvdb_movie_id INTEGER, imdb_id TEXT, episode_mappings TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        return conn

    def fetch_latest_release_metadata(self) -> Dict[str, Any]:
        res = requests.get(GITHUB_RELEASE_API, headers={"User-Agent": "Anithing-API-Automation"}, timeout=15)
        res.raise_for_status()
        return res.json()

    def download_file(self, url: str, destination_path: str, progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None) -> None:
        tmp_path = destination_path + ".tmp"
        try:
            res = requests.get(url, headers={"User-Agent": "Anithing-API-Automation"}, stream=True, timeout=60)
            res.raise_for_status()
            total_size = int(res.headers.get("content-length", 0))
            downloaded = 0

            with open(tmp_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback("download_progress", {
                                "downloaded": downloaded, "total": total_size,
                                "percentage": round((downloaded / total_size) * 100, 1)
                            })

            if total_size > 0 and os.path.getsize(tmp_path) < int(total_size * 0.99):
                raise IOError(f"Download incomplete: received {downloaded}/{total_size} bytes")
            os.replace(tmp_path, destination_path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise

    def parse_and_store_mappings(self, conn: sqlite3.Connection, progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None) -> int:
        if not os.path.exists(self.mappings_path):
            raise FileNotFoundError(f"Mappings file {self.mappings_path} not found.")

        if progress_callback:
            progress_callback("info", {"message": "Reading mappings.min.json..."})

        with open(self.mappings_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        anilist_keys = [k for k in data.keys() if k.startswith("anilist:")]
        total_keys = len(anilist_keys)
        rows: List[tuple] = []

        if progress_callback:
            progress_callback("info", {"message": f"Extracting cross-provider IDs for {total_keys:,} AniList entries..."})

        for idx, k in enumerate(anilist_keys, 1):
            try:
                anilist_id = int(k.split(":")[1])
            except Exception:
                continue

            entry = data[k]
            ids = {v: None for v in PROV_KEYS.values()}

            for target_key in entry.keys():
                parts = target_key.split(":")
                p_type = parts[0]
                if p_type in PROV_KEYS:
                    try:
                        ids[PROV_KEYS[p_type]] = int(parts[1]) if p_type != "imdb_movie" else parts[1]
                    except Exception:
                        pass

            rows.append((
                anilist_id, ids["mal_id"], ids["anidb_id"], ids["tmdb_show_id"],
                ids["tmdb_movie_id"], ids["tvdb_show_id"], ids["tvdb_movie_id"],
                ids["imdb_id"], json.dumps(entry, ensure_ascii=False)
            ))

            if idx % 2000 == 0 and progress_callback:
                progress_callback("mapping_progress", {"processed": idx, "total": total_keys, "percentage": round((idx / total_keys) * 100, 1)})

        INSERT_SQL = """
        INSERT INTO mappings (anilist_id, mal_id, anidb_id, tmdb_show_id, tmdb_movie_id, tvdb_show_id, tvdb_movie_id, imdb_id, episode_mappings)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(anilist_id) DO UPDATE SET
            mal_id=excluded.mal_id, anidb_id=excluded.anidb_id, tmdb_show_id=excluded.tmdb_show_id,
            tmdb_movie_id=excluded.tmdb_movie_id, tvdb_show_id=excluded.tvdb_show_id, tvdb_movie_id=excluded.tvdb_movie_id,
            imdb_id=excluded.imdb_id, episode_mappings=excluded.episode_mappings, synced_at=CURRENT_TIMESTAMP
        """
        BATCH_SIZE = 5000
        for batch_start in range(0, len(rows), BATCH_SIZE):
            conn.executemany(INSERT_SQL, rows[batch_start:batch_start + BATCH_SIZE])
            conn.commit()

        return len(rows)

    def save_stats(self, conn: sqlite3.Connection, release_tag: str) -> Dict[str, Any]:
        row = conn.execute("""
            SELECT COUNT(*),
                   SUM(CASE WHEN mal_id IS NOT NULL AND mal_id != 0 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN anidb_id IS NOT NULL AND anidb_id != 0 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN tmdb_show_id IS NOT NULL OR tmdb_movie_id IS NOT NULL THEN 1 ELSE 0 END),
                   SUM(CASE WHEN tvdb_show_id IS NOT NULL OR tvdb_movie_id IS NOT NULL THEN 1 ELSE 0 END)
            FROM mappings
        """).fetchone()

        stats = {
            "step": "step2_anibridge", "release_tag": release_tag,
            "total_mapped_animes": row[0] or 0, "mal_mapped": row[1] or 0,
            "anidb_mapped": row[2] or 0, "tmdb_mapped": row[3] or 0,
            "tvdb_mapped": row[4] or 0, "database_path": self.db_path
        }
        with open(self.stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        return stats

    def run_pipeline(self, clean: bool = False, progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        conn = self.init_db(clean=clean)
        release_tag = "v3"

        if clean or not os.path.exists(self.mappings_path):
            if progress_callback:
                progress_callback("info", {"message": "Fetching latest AniBridge release metadata..."})
            release_info = self.fetch_latest_release_metadata()
            release_tag = release_info.get("tag_name", "v3")

            mappings_url = next((a["browser_download_url"] for a in release_info.get("assets", []) if a["name"] == "mappings.min.json"), None)
            if not mappings_url:
                raise RuntimeError("mappings.min.json asset not found in latest AniBridge release.")

            if progress_callback:
                progress_callback("info", {"message": f"Downloading release {release_tag} mappings.min.json..."})
            self.download_file(mappings_url, self.mappings_path, progress_callback)
        else:
            if progress_callback:
                progress_callback("info", {"message": "Using existing mappings.min.json file..."})

        total_mapped = self.parse_and_store_mappings(conn, progress_callback)
        stats = self.save_stats(conn, release_tag)
        conn.close()
        return stats
