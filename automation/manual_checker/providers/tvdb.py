import time
from typing import Optional, Dict, Any, List
from .base import safe_get_json, safe_post_json
from core.config import TVDB_API_KEY

_TVDB_BEARER_TOKEN: Optional[str] = None
_TVDB_TOKEN_EXPIRY: float = 0.0
TVDB_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 25

def get_bearer_headers() -> Optional[Dict[str, str]]:
    global _TVDB_BEARER_TOKEN, _TVDB_TOKEN_EXPIRY
    if not TVDB_API_KEY or TVDB_API_KEY.startswith("YOUR_"):
        return None
    if _TVDB_BEARER_TOKEN and time.time() < _TVDB_TOKEN_EXPIRY:
        return {"Authorization": f"Bearer {_TVDB_BEARER_TOKEN}"}
    
    data = safe_post_json("https://api4.thetvdb.com/v4/login", {"apikey": TVDB_API_KEY})
    if data:
        token = data.get("data", {}).get("token")
        if token:
            _TVDB_BEARER_TOKEN = token
            _TVDB_TOKEN_EXPIRY = time.time() + TVDB_TOKEN_TTL_SECONDS
            return {"Authorization": f"Bearer {_TVDB_BEARER_TOKEN}"}
    return None

def fetch_preview(tvdb_id: int, is_movie: bool = False) -> Optional[Dict[str, str]]:
    if not tvdb_id:
        return None
    headers = get_bearer_headers()
    if not headers:
        return None
    media_type = "movies" if is_movie else "series"
    data = safe_get_json(f"https://api4.thetvdb.com/v4/{media_type}/{tvdb_id}", headers=headers)
    
    if data and "data" in data:
        d = data["data"]
        title = d.get("name")
        
        # Try to fetch English translation if available and not the native language
        if "eng" in d.get("nameTranslations", []) and d.get("originalLanguage") != "eng":
            eng_data = safe_get_json(f"https://api4.thetvdb.com/v4/{media_type}/{tvdb_id}/translations/eng", headers=headers)
            if eng_data and "data" in eng_data and eng_data["data"].get("name"):
                title = eng_data["data"]["name"]
                
        return {
            "poster": d.get("image"),
            "title": title,
            "date": d.get("firstAired") or d.get("year") or d.get("releaseDate")
        }
    return None

def fetch_episodes_with_rollover(tvdb_id: Optional[int], target_episode_count: int, start_season: int = 1) -> List[Dict[str, Any]]:
    episodes_list = []
    headers = get_bearer_headers()
    if not tvdb_id or not headers:
        return episodes_list

    try:
        page = 0
        all_eps = []
        while page < 20:
            data_eng = safe_get_json(f"https://api4.thetvdb.com/v4/series/{tvdb_id}/episodes/official/eng?page={page}", headers=headers)
            if not data_eng:
                break
            data_jpn = safe_get_json(f"https://api4.thetvdb.com/v4/series/{tvdb_id}/episodes/official/jpn?page={page}", headers=headers)

            page_data_eng = data_eng.get("data", {})
            eps_eng = page_data_eng.get("episodes", []) if isinstance(page_data_eng, dict) else (page_data_eng if isinstance(page_data_eng, list) else [])

            eps_jpn = []
            if data_jpn:
                page_data_jpn = data_jpn.get("data", {})
                eps_jpn = page_data_jpn.get("episodes", []) if isinstance(page_data_jpn, dict) else (page_data_jpn if isinstance(page_data_jpn, list) else [])

            if not eps_eng:
                break

            for i, ep in enumerate(eps_eng):
                name_eng = ep.get("name") or ""
                name_jpn = eps_jpn[i].get("name") or "" if i < len(eps_jpn) else ""
                combined_name = f"{name_eng} / {name_jpn}" if name_jpn and name_jpn != name_eng and name_eng else (name_eng or name_jpn)
                ep["name"] = combined_name

            all_eps.extend(eps_eng)
            if not data_eng.get("links", {}).get("next"):
                break
            page += 1

        if all_eps:
            season_filtered = [e for e in all_eps if e.get("seasonNumber", 0) >= start_season]
            season_filtered.sort(key=lambda e: (e.get("seasonNumber", 1), e.get("number", 1)))

            for ep in season_filtered:
                if len(episodes_list) >= target_episode_count:
                    break
                sn = ep.get("seasonNumber", start_season)
                img_url = ep.get("image")
                if img_url and img_url.startswith("/"):
                    img_url = f"https://artworks.thetvdb.com{img_url}"

                episodes_list.append({
                    "global_episode": len(episodes_list) + 1,
                    "season": sn,
                    "episode_in_season": ep.get("number"),
                    "name": ep.get("name"),
                    "thumbnail": img_url,
                    "rollover_applied": sn > start_season
                })
    except Exception:
        pass

    while len(episodes_list) < target_episode_count:
        ep_num = len(episodes_list) + 1
        episodes_list.append({
            "global_episode": ep_num,
            "season": start_season,
            "episode_in_season": ep_num,
            "name": f"Episode {ep_num} (Pending TVDB sync)",
            "thumbnail": None,
            "rollover_applied": True
        })

    return episodes_list
