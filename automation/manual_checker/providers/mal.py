from typing import Optional
from .base import safe_get_json
from core.config import MAL_CLIENT_ID

def fetch_poster(mal_id: int) -> Optional[str]:
    if not mal_id:
        return None
    if not MAL_CLIENT_ID or MAL_CLIENT_ID.startswith("YOUR_"):
        return None
    data = safe_get_json(
        f"https://api.myanimelist.net/v2/anime/{mal_id}?fields=id,main_picture",
        headers={"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
    )
    if data and "main_picture" in data:
        pic = data["main_picture"]
        return pic.get("large") or pic.get("medium")
    return None
