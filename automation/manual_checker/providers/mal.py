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
