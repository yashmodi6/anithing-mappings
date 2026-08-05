from typing import Optional
from .base import safe_post_json
from core.config import ANILIST_GRAPHQL_URL

def fetch_cover_image(anilist_id: int) -> Optional[str]:
    query = """query ($id: Int) { Media(id: $id, type: ANIME) { coverImage { extraLarge large medium } } }"""
    data = safe_post_json(ANILIST_GRAPHQL_URL, {"query": query, "variables": {"id": anilist_id}})
    if data:
        media = data.get("data", {}).get("Media")
        if media and media.get("coverImage"):
            imgs = media["coverImage"]
            return imgs.get("extraLarge") or imgs.get("large") or imgs.get("medium")
    return None
