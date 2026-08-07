from typing import Optional, Dict, Any, List
from .base import safe_get_json
from core.config import TMDB_READ_ACCESS_TOKEN

def get_auth_kwargs() -> Dict[str, Any]:
    kwargs = {"headers": {"accept": "application/json"}}
    if not TMDB_READ_ACCESS_TOKEN or TMDB_READ_ACCESS_TOKEN.startswith("YOUR_"):
        return kwargs
    if len(TMDB_READ_ACCESS_TOKEN) > 50:
        kwargs["headers"]["Authorization"] = f"Bearer {TMDB_READ_ACCESS_TOKEN}"
    else:
        kwargs["params"] = {"api_key": TMDB_READ_ACCESS_TOKEN}
    return kwargs

def fetch_preview(tmdb_id: int, is_movie: bool = False) -> Optional[Dict[str, str]]:
    if not tmdb_id or not TMDB_READ_ACCESS_TOKEN or TMDB_READ_ACCESS_TOKEN.startswith("YOUR_"):
        return None
    endpoint = "movie" if is_movie else "tv"
    url = f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}?language=en-US"
    data = safe_get_json(url, **get_auth_kwargs())
    if data:
        return {
            "poster": f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None,
            "title": data.get("title") if is_movie else data.get("name"),
            "date": data.get("release_date") if is_movie else data.get("first_air_date")
        }
    return None

def fetch_episodes_with_rollover(tmdb_id: Optional[int], target_episode_count: int, exact_seasons: List[int], start_season: int = 1) -> List[Dict[str, Any]]:
    episodes_list = []
    if not tmdb_id or not TMDB_READ_ACCESS_TOKEN or TMDB_READ_ACCESS_TOKEN.startswith("YOUR_"):
        return episodes_list

    auth_kwargs = get_auth_kwargs()
    seasons_to_fetch = exact_seasons + list(range(max(exact_seasons) + 1, max(exact_seasons) + 25)) if exact_seasons else list(range(start_season, start_season + 50))

    empty_seasons_count = 0
    for current_season in seasons_to_fetch:
        if len(episodes_list) >= target_episode_count:
            break

        url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{current_season}"
        season_data = safe_get_json(url, **auth_kwargs)
        season_episodes = season_data.get("episodes", []) if season_data else []

        if not season_episodes:
            empty_seasons_count += 1
            if empty_seasons_count >= 5:
                break
            continue

        empty_seasons_count = 0
        for ep in season_episodes:
            if len(episodes_list) >= target_episode_count:
                break
            still_path = ep.get("still_path")
            thumbnail_url = f"https://image.tmdb.org/t/p/w300{still_path}" if still_path else None
            episodes_list.append({
                "global_episode": len(episodes_list) + 1,
                "season": current_season,
                "episode_in_season": ep.get("episode_number"),
                "name": ep.get("name"),
                "thumbnail": thumbnail_url,
                "rollover_applied": current_season > start_season
            })

    return episodes_list
