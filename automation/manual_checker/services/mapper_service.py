import requests
from typing import Dict, Any, Optional
from providers.base import safe_get_json
from providers.tmdb import get_auth_kwargs
from providers.tvdb import get_bearer_headers
from core.config import TMDB_READ_ACCESS_TOKEN

def auto_map(title: str, year: Optional[int] = None) -> Dict[str, Any]:
    """Simple auto mapper that uses TMDB and TVDB search API to find matching IDs."""
    result = {"tmdb": None, "tvdb": None}
    
    # 1. Search TMDB
    if TMDB_READ_ACCESS_TOKEN and not TMDB_READ_ACCESS_TOKEN.startswith("YOUR_"):
        auth_kwargs = get_auth_kwargs()
        tmdb_url = f"https://api.themoviedb.org/3/search/multi?query={requests.utils.quote(title)}"
        if year:
            tmdb_url += f"&primary_release_year={year}&first_air_date_year={year}"
        
        tmdb_data = safe_get_json(tmdb_url, **auth_kwargs)
        if tmdb_data and tmdb_data.get("results"):
            match = tmdb_data["results"][0]
            media_type = match.get("media_type")
            if media_type in ["tv", "movie"]:
                result["tmdb"] = {
                    "id": str(match.get("id")),
                    "type": "show" if media_type == "tv" else "movie"
                }
                
    # 2. Search TVDB
    headers = get_bearer_headers()
    if headers:
        tvdb_url = f"https://api4.thetvdb.com/v4/search?query={requests.utils.quote(title)}"
        if year:
            tvdb_url += f"&year={year}"
            
        tvdb_data = safe_get_json(tvdb_url, headers=headers)
        if tvdb_data and tvdb_data.get("data"):
            match = tvdb_data["data"][0]
            tvdb_type = match.get("type", "").lower()
            if tvdb_type in ["series", "movie"]:
                result["tvdb"] = {
                    "id": str(match.get("tvdb_id", match.get("id"))),
                    "type": "show" if tvdb_type == "series" else "movie"
                }
                
    return result
