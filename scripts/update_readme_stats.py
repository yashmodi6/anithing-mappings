import os
import sqlite3
import re
import urllib.parse
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
AUTOMATION_DIR = os.path.join(ROOT_DIR, "automation")
OUTPUT_DIR = os.path.join(AUTOMATION_DIR, "output")
STEP1_DB = os.path.join(OUTPUT_DIR, "step1_anilist", "anime.db")
STEP2_DB = os.path.join(OUTPUT_DIR, "step2_anibridge", "anibridge.db")
STEP3_DB = os.path.join(OUTPUT_DIR, "step3_verified", "verified.db")
README_PATH = os.path.join(ROOT_DIR, "README.md")
MAPPINGS_JSON = os.path.join(ROOT_DIR, "assets", "mapping-edits.json")

def get_stats():
    total_anilist = 0
    format_breakdown = {}
    verified_count = 0
    verified_format_breakdown = {}
    tmdb_valid = 0
    tvdb_valid = 0
    mal_valid = 0
    anibridge_corrections = 0

    if os.path.exists(STEP1_DB):
        try:
            with sqlite3.connect(STEP1_DB) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM anime")
                total_anilist = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(NULLIF(format, ''), 'UNKNOWN'), COUNT(*) FROM anime GROUP BY COALESCE(NULLIF(format, ''), 'UNKNOWN')")
                for r in cur.fetchall():
                    format_breakdown[r[0]] = r[1]
        except Exception:
            pass

    if os.path.exists(STEP3_DB):
        try:
            with sqlite3.connect(STEP3_DB) as conn:
                verified_count = conn.execute("SELECT COUNT(*) FROM verified_anime WHERE manual_checked = 1").fetchone()[0]
                
                # TMDB, TVDB, MAL valid counts for Quality Assurance
                tmdb_valid = conn.execute("SELECT COUNT(*) FROM verified_anime WHERE manual_checked = 1 AND (tmdb_show_id IS NOT NULL OR tmdb_movie_id IS NOT NULL)").fetchone()[0]
                tvdb_valid = conn.execute("SELECT COUNT(*) FROM verified_anime WHERE manual_checked = 1 AND (tvdb_show_id IS NOT NULL OR tvdb_movie_id IS NOT NULL)").fetchone()[0]
                mal_valid = conn.execute("SELECT COUNT(*) FROM verified_anime WHERE manual_checked = 1 AND mal_id IS NOT NULL").fetchone()[0]

                if os.path.exists(STEP1_DB):
                    conn.execute(f"ATTACH DATABASE '{STEP1_DB}' AS step1")
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT COALESCE(NULLIF(s1.format, ''), 'UNKNOWN'), COUNT(v.anilist_id)
                        FROM verified_anime v
                        JOIN step1.anime s1 ON v.anilist_id = s1.anilist_id
                        WHERE v.manual_checked = 1
                        GROUP BY COALESCE(NULLIF(s1.format, ''), 'UNKNOWN')
                    """)
                    for r in cur.fetchall():
                        verified_format_breakdown[r[0]] = r[1]
        except Exception:
            pass

    # Calculate Anibridge Corrections
    import glob
    mapping_files = glob.glob(os.path.join(ROOT_DIR, "assets", "mapping-*.json"))
    if os.path.exists(STEP2_DB) and mapping_files:
        try:
            edits = []
            for mf in mapping_files:
                try:
                    with open(mf, "r", encoding="utf-8") as f:
                        edits.extend(json.load(f))
                except Exception:
                    pass
            
            with sqlite3.connect(STEP2_DB) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                for edit in edits:
                    aid = edit["anilist_id"]
                    cursor.execute("SELECT * FROM mappings WHERE anilist_id = ?", (aid,))
                    row = cursor.fetchone()
                    
                    if not row:
                        anibridge_corrections += 1
                        continue
                        
                    is_changed = False
                    
                    edit_tmdb_id = ""
                    edit_tmdb_type = ""
                    edit_tvdb_id = ""
                    edit_tvdb_type = ""
                    edit_mal_id = ""
                    
                    for m in edit.get("mappings", []):
                        if m.get("provider") == "tmdb":
                            edit_tmdb_id = str(m.get("id", ""))
                            edit_tmdb_type = m.get("type", "")
                        elif m.get("provider") == "tvdb":
                            edit_tvdb_id = str(m.get("id", ""))
                            edit_tvdb_type = m.get("type", "")
                        elif m.get("provider") == "mal":
                            edit_mal_id = str(m.get("id", ""))

                    # Compare TMDB
                    orig_tmdb = str(row["tmdb_movie_id"]) if edit_tmdb_type == "movie" else str(row["tmdb_show_id"])
                    if orig_tmdb == "None": orig_tmdb = ""
                    
                    # Compare TVDB
                    orig_tvdb = str(row["tvdb_movie_id"]) if edit_tvdb_type == "movie" else str(row["tvdb_show_id"])
                    if orig_tvdb == "None": orig_tvdb = ""
                    
                    # Compare MAL
                    orig_mal = str(row["mal_id"])
                    if orig_mal == "None": orig_mal = ""
                    
                    if orig_tmdb != edit_tmdb_id or orig_tvdb != edit_tvdb_id or orig_mal != edit_mal_id:
                        is_changed = True
                        
                    if is_changed:
                        anibridge_corrections += 1
        except Exception as e:
            print("Error calculating anibridge corrections:", e)
            pass

    return {
        "total": total_anilist,
        "verified": verified_count,
        "format": format_breakdown,
        "v_format": verified_format_breakdown,
        "tmdb": tmdb_valid,
        "tvdb": tvdb_valid,
        "mal": mal_valid,
        "corrections": anibridge_corrections
    }

def format_markdown(stats):
    total = stats["total"]
    v_total = stats["verified"]
    pct = round((v_total / total * 100), 1) if total > 0 else 0
    
    tmdb_pct = round((stats['tmdb'] / v_total * 100), 1) if v_total > 0 else 0
    tvdb_pct = round((stats['tvdb'] / v_total * 100), 1) if v_total > 0 else 0
    mal_pct = round((stats['mal'] / v_total * 100), 1) if v_total > 0 else 0

    md = "## 📊 Database Coverage & Stats\n\n"
    md += f"- **Total Anime Tracked:** {total:,}\n"
    md += f"- **Total Verified:** {v_total:,} ({pct}%)\n"
    if stats['corrections'] > 0:
        md += f"- **Anibridge Corrections:** {stats['corrections']:,} mappings fixed!\n"
    
    skipped_md_path = os.path.join(ROOT_DIR, "SKIPPED.md")
    if os.path.exists(skipped_md_path):
        md += f"- **Skipped Anime:** [View Skipped Entries](SKIPPED.md)\n"
        
    md += "\n"
    
    # 2. Quality Assurance Table
    md += "### ✅ Verified Database Quality\n"
    md += "*(Indicates how complete the mapping is for anime that have been manually verified)*\n\n"
    md += "| Provider | Successfully Mapped | Missing / No Match |\n"
    md += "| :--- | --: | --: |\n"
    md += f"| **TMDB** | {stats['tmdb']:,} | {v_total - stats['tmdb']:,} |\n"
    md += f"| **TVDB** | {stats['tvdb']:,} | {v_total - stats['tvdb']:,} |\n"
    md += f"| **MAL** | {stats['mal']:,} | {v_total - stats['mal']:,} |\n\n"

    # 3. Format Breakdown Table
    md += "### 🎬 Format Breakdown\n"
    md += "*(Shows verification progress across different media types)*\n\n"
    md += "| Format | Total in AniList | Verified Here | Progress |\n"
    md += "| :--- | --: | --: | --: |\n"
    
    for fmt, f_total in sorted(stats["format"].items(), key=lambda x: x[1], reverse=True):
        f_ver = stats["v_format"].get(fmt, 0)
        f_pct = round((f_ver / f_total * 100), 1) if f_total > 0 else 0
        md += f"| **{fmt}** | {f_total:,} | {f_ver:,} | ![{f_pct}%](https://geps.dev/progress/{f_pct}) |\n"

    return md

def generate_skipped_md():
    skipped_json_path = os.path.join(ROOT_DIR, "assets", "skipped-anime.json")
    skipped_md_path = os.path.join(ROOT_DIR, "SKIPPED.md")
    if not os.path.exists(skipped_json_path):
        return
        
    try:
        with open(skipped_json_path, "r", encoding="utf-8") as f:
            skipped_data = json.load(f)
    except Exception:
        return
        
    if not skipped_data:
        return
        
    md = "# Skipped Anime\n\n"
    md += "This document lists anime that were manually reviewed but intentionally skipped during verification. These entries either had significant metadata issues (like wrong formatting or release dates) or were too ambiguous to map confidently.\n\n"
    md += "| AniList ID | Title | Format | Status | Skip Reason |\n"
    md += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    # Connect to STEP1_DB to fetch metadata
    metadata = {}
    if os.path.exists(STEP1_DB):
        try:
            with sqlite3.connect(STEP1_DB) as conn:
                conn.row_factory = sqlite3.Row
                ids = [str(entry.get("anilist_id")) for entry in skipped_data if entry.get("anilist_id")]
                if ids:
                    placeholders = ",".join("?" * len(ids))
                    cur = conn.cursor()
                    cur.execute(f"SELECT anilist_id, title_english, title_romaji, format, status FROM anime WHERE anilist_id IN ({placeholders})", ids)
                    for row in cur.fetchall():
                        metadata[row["anilist_id"]] = dict(row)
        except Exception:
            pass
            
    for entry in skipped_data:
        aid = entry.get("anilist_id")
        reason = entry.get("reason", "Other")
        info = metadata.get(aid, {})
        title = info.get("title_english") or info.get("title_romaji") or "Unknown"
        fmt = info.get("format") or "Unknown"
        status = info.get("status") or "Unknown"
        
        title_clean = title.replace("|", "\\|")
        
        md += f"| [{aid}](https://anilist.co/anime/{aid}) | {title_clean} | {fmt} | {status} | {reason} |\n"
        
    with open(skipped_md_path, "w", encoding="utf-8") as f:
        f.write(md)

def main():
    generate_skipped_md()
    
    if not os.path.exists(README_PATH):
        return
        
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        
    stats = get_stats()
    new_stats_md = format_markdown(stats)
    
    # Replace everything between markers
    marker_start = "<!-- STATS_START -->"
    marker_end = "<!-- STATS_END -->"
    
    pattern = re.compile(f"{marker_start}.*?{marker_end}", re.DOTALL)
    if pattern.search(content):
        new_content = pattern.sub(f"{marker_start}\n{new_stats_md}\n{marker_end}", content)
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)

if __name__ == "__main__":
    main()
