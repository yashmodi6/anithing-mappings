import json
import sqlite3
import os

with open("assets/mapping-edits.json", "r") as f:
    edits = json.load(f)

changed_count = 0
total_verified = len(edits)
unchanged_count = 0

db_path = "automation/output/step2_anibridge/anibridge.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

for edit in edits:
    aid = edit["anilist_id"]
    cursor.execute("SELECT * FROM mappings WHERE anilist_id = ?", (aid,))
    row = cursor.fetchone()
    
    if not row:
        changed_count += 1
        continue
        
    is_changed = False
    
    # Compare TMDB
    orig_tmdb = str(row["tmdb_movie_id"]) if edit.get("tmdb_type") == "movie" else str(row["tmdb_show_id"])
    if orig_tmdb == "None": orig_tmdb = ""
    new_tmdb = str(edit.get("tmdb_id", ""))
    
    # Compare TVDB
    orig_tvdb = str(row["tvdb_movie_id"]) if edit.get("tvdb_type") == "movie" else str(row["tvdb_show_id"])
    if orig_tvdb == "None": orig_tvdb = ""
    new_tvdb = str(edit.get("tvdb_id", ""))
    
    # Compare MAL
    orig_mal = str(row["mal_id"])
    if orig_mal == "None": orig_mal = ""
    new_mal = str(edit.get("mal_id", ""))
    
    if orig_tmdb != new_tmdb or orig_tvdb != new_tvdb or orig_mal != new_mal:
        is_changed = True
        
    if is_changed:
        changed_count += 1
    else:
        unchanged_count += 1

print(f"Total Verified: {total_verified}")
print(f"Changed from Anibridge: {changed_count}")
print(f"Unchanged (same as Anibridge): {unchanged_count}")
