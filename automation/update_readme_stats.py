import os
import sqlite3
import re

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(AUTOMATION_DIR, "output")
STEP1_DB = os.path.join(OUTPUT_DIR, "step1_anilist", "anime.db")
STEP2_DB = os.path.join(OUTPUT_DIR, "step2_anibridge", "anibridge.db")
STEP3_DB = os.path.join(OUTPUT_DIR, "step3_verified", "verified.db")
README_PATH = os.path.join(AUTOMATION_DIR, "..", "README.md")

def get_stats():
    # Step 1 Stats
    total_anilist = 0
    status_breakdown = {}
    if os.path.exists(STEP1_DB):
        try:
            with sqlite3.connect(STEP1_DB) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM anime")
                total_anilist = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(NULLIF(status, ''), 'UNKNOWN'), COUNT(*) FROM anime GROUP BY COALESCE(NULLIF(status, ''), 'UNKNOWN')")
                for r in cur.fetchall():
                    status_breakdown[r[0]] = r[1]
        except Exception:
            pass

    # Step 2 Stats
    step2_data = {"total_mapped": 0, "mal": 0, "anidb": 0, "tvdb": 0, "tmdb": 0}
    if os.path.exists(STEP2_DB):
        try:
            with sqlite3.connect(STEP2_DB) as conn:
                cur = conn.cursor()
                step2_data["total_mapped"] = conn.execute("SELECT COUNT(*) FROM mappings").fetchone()[0]
                step2_data["mal"] = conn.execute("SELECT COUNT(*) FROM mappings WHERE mal_id IS NOT NULL AND mal_id != 0").fetchone()[0]
                step2_data["anidb"] = conn.execute("SELECT COUNT(*) FROM mappings WHERE anidb_id IS NOT NULL AND anidb_id != 0").fetchone()[0]
                step2_data["tvdb"] = conn.execute("SELECT COUNT(*) FROM mappings WHERE tvdb_show_id IS NOT NULL OR tvdb_movie_id IS NOT NULL").fetchone()[0]
                step2_data["tmdb"] = conn.execute("SELECT COUNT(*) FROM mappings WHERE tmdb_show_id IS NOT NULL OR tmdb_movie_id IS NOT NULL").fetchone()[0]
        except Exception:
            pass

    # Step 3 Stats
    verified_count = 0
    verified_status_breakdown = {}
    if os.path.exists(STEP3_DB):
        try:
            with sqlite3.connect(STEP3_DB) as conn:
                verified_count = conn.execute("SELECT COUNT(*) FROM verified_anime WHERE manual_checked = 1").fetchone()[0]
                if os.path.exists(STEP1_DB):
                    conn.execute(f"ATTACH DATABASE '{STEP1_DB}' AS step1")
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT COALESCE(NULLIF(s1.status, ''), 'UNKNOWN'), COUNT(v.anilist_id)
                        FROM verified_anime v
                        JOIN step1.anime s1 ON v.anilist_id = s1.anilist_id
                        WHERE v.manual_checked = 1
                        GROUP BY COALESCE(NULLIF(s1.status, ''), 'UNKNOWN')
                    """)
                    for r in cur.fetchall():
                        verified_status_breakdown[r[0]] = r[1]
        except Exception:
            pass

    base_total = max(total_anilist, step2_data.get("total_mapped", 0))
    return base_total, status_breakdown, step2_data, verified_count, verified_status_breakdown

def format_markdown(base_total, status_breakdown, step2_data, verified_count, verified_status_breakdown):
    md = "## Database Coverage & Stats\n\n"
    md += "### Provider Coverage\n"
    md += "| Provider Category | Total AniList | Mapped Count | Missing / Left |\n"
    md += "| :--- | --: | --: | --: |\n"
    
    providers = [
        ("MyAnimeList (MAL)", step2_data.get("mal", 0)),
        ("AniDB", step2_data.get("anidb", 0)),
        ("TVDB (Show/Movie)", step2_data.get("tvdb", 0)),
        ("TMDB (Show/Movie)", step2_data.get("tmdb", 0)),
        ("Step 3 Verified (Manual)", verified_count)
    ]
    
    for name, mapped in providers:
        missing = max(0, base_total - mapped)
        mapped_pct = f"({(mapped / base_total * 100):.1f}%)" if base_total > 0 else ""
        missing_pct = f"({(missing / base_total * 100):.1f}%)" if base_total > 0 else ""
        md += f"| {name} | {base_total:,} | {mapped:,} {mapped_pct} | {missing:,} {missing_pct} |\n"
    
    md += "\n### Anime Status Breakdown\n"
    md += "| Anime Status | Total Anime | Total Verified | Percentage |\n"
    md += "| :--- | --: | --: | --: |\n"
    
    for st_name, total_count in sorted(status_breakdown.items(), key=lambda x: x[1], reverse=True):
        v_count = verified_status_breakdown.get(st_name, 0)
        pct = f"{(v_count / total_count * 100):.1f}%" if total_count > 0 else "0%"
        md += f"| {st_name} | {total_count:,} | {v_count:,} | {pct} |\n"
        
    return md

def main():
    if not os.path.exists(README_PATH):
        return
        
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        
    stats = get_stats()
    stats_md = format_markdown(*stats)
    
    pattern = r'(<!-- STATS_START -->)(.*?)(<!-- STATS_END -->)'
    if re.search(pattern, content, flags=re.DOTALL):
        new_content = re.sub(pattern, f"\\1\n{stats_md}\n\\3", content, flags=re.DOTALL)
    else:
        new_content = content + "\n<!-- STATS_START -->\n" + stats_md + "\n<!-- STATS_END -->\n"
        
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == "__main__":
    main()
