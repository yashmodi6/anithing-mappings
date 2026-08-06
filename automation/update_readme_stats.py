import os
import sqlite3
import re
import urllib.parse

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(AUTOMATION_DIR, "output")
STEP1_DB = os.path.join(OUTPUT_DIR, "step1_anilist", "anime.db")
STEP3_DB = os.path.join(OUTPUT_DIR, "step3_verified", "verified.db")
README_PATH = os.path.join(AUTOMATION_DIR, "..", "README.md")

def get_stats():
    total_anilist = 0
    format_breakdown = {}
    verified_count = 0
    verified_format_breakdown = {}
    tmdb_valid = 0
    tvdb_valid = 0
    mal_valid = 0

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

    return {
        "total": total_anilist,
        "verified": verified_count,
        "format": format_breakdown,
        "v_format": verified_format_breakdown,
        "tmdb": tmdb_valid,
        "tvdb": tvdb_valid,
        "mal": mal_valid
    }

def create_shield(label, message, color):
    label_enc = urllib.parse.quote(label.replace("-", "--"))
    msg_enc = urllib.parse.quote(message.replace("-", "--"))
    return f"![{label}](https://img.shields.io/badge/{label_enc}-{msg_enc}-{color}?style=for-the-badge)"

def format_markdown(stats):
    total = stats["total"]
    v_total = stats["verified"]
    pct = round((v_total / total * 100), 1) if total > 0 else 0
    
    tmdb_pct = round((stats['tmdb'] / v_total * 100), 1) if v_total > 0 else 0
    tvdb_pct = round((stats['tvdb'] / v_total * 100), 1) if v_total > 0 else 0
    mal_pct = round((stats['mal'] / v_total * 100), 1) if v_total > 0 else 0

    md = "## 📊 Database Coverage & Stats\n\n"
    md += f"- **Total Anime Tracked:** {total:,}\n"
    md += f"- **Total Verified:** {v_total:,} ({pct}%)\n\n"
    
    # 1. At-a-glance badges
    md += f"<div align=\"center\">\n\n"
    md += f"</div>\n\n"

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

def main():
    if not os.path.exists(README_PATH):
        return
        
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        
    stats = get_stats()
    stats_md = format_markdown(stats)
    
    pattern = r'(<!-- STATS_START -->)(.*?)(<!-- STATS_END -->)'
    if re.search(pattern, content, flags=re.DOTALL):
        new_content = re.sub(pattern, f"\\1\n{stats_md}\n\\3", content, flags=re.DOTALL)
    else:
        new_content = content + "\n<!-- STATS_START -->\n" + stats_md + "\n<!-- STATS_END -->\n"
        
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == "__main__":
    main()
