from typing import Optional
from .base import safe_get_json
from core.config import MAL_CLIENT_ID

def fetch_preview(mal_id: int) -> Optional[dict]:
    if not mal_id:
        return None
    if not MAL_CLIENT_ID or MAL_CLIENT_ID.startswith("YOUR_"):
        return None
    data = safe_get_json(
        f"https://api.myanimelist.net/v2/anime/{mal_id}?fields=id,title,alternative_titles,start_date,main_picture",
        headers={"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
    )
    if data:
        pic = data.get("main_picture", {})
        eng_title = data.get("alternative_titles", {}).get("en")
        return {
            "poster": pic.get("large") or pic.get("medium"),
            "title": eng_title if eng_title else data.get("title"),
            "date": data.get("start_date")
        }
    return None

def fetch_filler_episodes(mal_id: int) -> dict:
    import time
    import subprocess
    import json
    episode_types = {}
    if not mal_id:
        return episode_types
        
    page = 1
    while True:
        url = f"https://api.jikan.moe/v4/anime/{mal_id}/episodes?page={page}"
        try:
            res = subprocess.run(["curl", "-s", url], capture_output=True, text=True, timeout=10)
            data = json.loads(res.stdout)
        except Exception:
            break
            
        if not data or not data.get("data"):
            break
            
        for ep in data["data"]:
            ep_id = ep.get("mal_id")
            if not ep_id:
                continue
            
            is_filler = ep.get("filler", False)
            is_recap = ep.get("recap", False)
            
            if is_recap:
                episode_types[str(ep_id)] = "recap"
            elif is_filler:
                episode_types[str(ep_id)] = "filler"
            else:
                episode_types[str(ep_id)] = "canon"
                
        pagination = data.get("pagination", {})
        if not pagination.get("has_next_page"):
            break
            
        page += 1
        time.sleep(0.34)
        
    return episode_types
