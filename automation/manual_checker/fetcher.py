# Metadata, Poster & Episode Fetcher with Season Rollover

import os
import requests
import time as _time
from typing import Dict, Any, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

AUTOMATION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(AUTOMATION_ROOT, ".env")


def load_env() -> Dict[str, str]:
    env_vars = {}
    if not os.path.exists(ENV_FILE):
        return env_vars
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
    return env_vars


ENV = load_env()
TMDB_READ_ACCESS_TOKEN = ENV.get("TMDB_READ_ACCESS_TOKEN", "")
TVDB_API_KEY = ENV.get("TVDB_API_KEY", "")
MAL_CLIENT_ID = ENV.get("MAL_CLIENT_ID", "")
ANILIST_GRAPHQL_URL = "https://graphql.anilist.co"


def _create_resilient_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_session = _create_resilient_session()

_TVDB_BEARER_TOKEN: Optional[str] = None
_TVDB_TOKEN_EXPIRY: float = 0.0
TVDB_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 25


def _safe_get_json(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
    try:
        res = _session.get(url, headers=headers, params=params, timeout=timeout)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


def _safe_post_json(url: str, json_data: Dict[str, Any], headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
    try:
        res = _session.post(url, json=json_data, headers=headers, timeout=timeout)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


def get_tvdb_bearer_headers() -> Optional[Dict[str, str]]:
    global _TVDB_BEARER_TOKEN, _TVDB_TOKEN_EXPIRY
    if not TVDB_API_KEY or TVDB_API_KEY.startswith("YOUR_"):
        return None
    if _TVDB_BEARER_TOKEN and _time.time() < _TVDB_TOKEN_EXPIRY:
        return {"Authorization": f"Bearer {_TVDB_BEARER_TOKEN}"}
    
    data = _safe_post_json("https://api4.thetvdb.com/v4/login", {"apikey": TVDB_API_KEY})
    if data:
        token = data.get("data", {}).get("token")
        if token:
            _TVDB_BEARER_TOKEN = token
            _TVDB_TOKEN_EXPIRY = _time.time() + TVDB_TOKEN_TTL_SECONDS
            return {"Authorization": f"Bearer {_TVDB_BEARER_TOKEN}"}
    return None


class ProviderFetcher:

    @staticmethod
    def get_tmdb_auth_kwargs() -> Dict[str, Any]:
        kwargs = {"headers": {"accept": "application/json"}}
        if not TMDB_READ_ACCESS_TOKEN or TMDB_READ_ACCESS_TOKEN.startswith("YOUR_"):
            return kwargs
        if len(TMDB_READ_ACCESS_TOKEN) > 50:
            kwargs["headers"]["Authorization"] = f"Bearer {TMDB_READ_ACCESS_TOKEN}"
        else:
            kwargs["params"] = {"api_key": TMDB_READ_ACCESS_TOKEN}
        return kwargs

    @staticmethod
    def fetch_anilist_cover_image(anilist_id: int) -> Optional[str]:
        query = """query ($id: Int) { Media(id: $id, type: ANIME) { coverImage { extraLarge large medium } } }"""
        data = _safe_post_json(ANILIST_GRAPHQL_URL, {"query": query, "variables": {"id": anilist_id}})
        if data:
            cover = data.get("data", {}).get("Media", {}).get("coverImage", {})
            return cover.get("extraLarge") or cover.get("large") or cover.get("medium")
        return None

    @staticmethod
    def fetch_mal_poster(mal_id: Optional[int]) -> Optional[str]:
        if not mal_id or not MAL_CLIENT_ID or MAL_CLIENT_ID.startswith("YOUR_"):
            return None

        data = _safe_get_json(f"https://api.myanimelist.net/v2/anime/{mal_id}?fields=id,main_picture", headers={"X-MAL-CLIENT-ID": MAL_CLIENT_ID})
        if data and "main_picture" in data:
            pic = data["main_picture"]
            return pic.get("large") or pic.get("medium")
        return None

    @staticmethod
    def fetch_tvdb_poster(tvdb_id: Optional[int], is_movie: bool = False) -> Optional[str]:
        if not tvdb_id:
            return None
        headers = get_tvdb_bearer_headers()
        if not headers:
            return None
        media_type = "movies" if is_movie else "series"
        data = _safe_get_json(f"https://api4.thetvdb.com/v4/{media_type}/{tvdb_id}", headers=headers)
        return data.get("data", {}).get("image") if data else None

    @staticmethod
    def fetch_tmdb_poster(tmdb_id: Optional[int], is_movie: bool = False) -> Optional[str]:
        if not tmdb_id or not TMDB_READ_ACCESS_TOKEN or TMDB_READ_ACCESS_TOKEN.startswith("YOUR_"):
            return None
        auth_kwargs = ProviderFetcher.get_tmdb_auth_kwargs()
        media_type = "movie" if is_movie else "tv"
        data = _safe_get_json(f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}", **auth_kwargs)
        path = data.get("poster_path") if data else None
        return f"https://image.tmdb.org/t/p/w500{path}" if path else None

    @staticmethod
    def parse_seasons_from_mappings(episode_mappings: Optional[Dict[str, Any]], provider_prefix: str) -> List[int]:
        seasons = set()
        if not episode_mappings or not isinstance(episode_mappings, dict):
            return []
        provider_key = "tmdb" if provider_prefix == "tmdb_show" else "tvdb"
        for val in episode_mappings.values():
            if isinstance(val, dict):
                p_data = val.get(provider_key, {})
                if p_data:
                    s_val = p_data.get("season") if p_data.get("season") is not None else p_data.get("s")
                    if s_val is not None:
                        seasons.add(int(s_val))
        return sorted(list(seasons))

    @staticmethod
    def fetch_tmdb_episodes_with_rollover(
        tmdb_id: Optional[int],
        target_episode_count: int,
        start_season: int = 1,
        episode_mappings: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        episodes_list = []
        if not tmdb_id or not TMDB_READ_ACCESS_TOKEN or TMDB_READ_ACCESS_TOKEN.startswith("YOUR_"):
            return episodes_list

        auth_kwargs = ProviderFetcher.get_tmdb_auth_kwargs()
        exact_seasons = ProviderFetcher.parse_seasons_from_mappings(episode_mappings, "tmdb_show")
        seasons_to_fetch = exact_seasons + list(range(max(exact_seasons) + 1, max(exact_seasons) + 25)) if exact_seasons else list(range(start_season, start_season + 50))

        empty_seasons_count = 0
        for current_season in seasons_to_fetch:
            if len(episodes_list) >= target_episode_count:
                break

            url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{current_season}"
            season_data = _safe_get_json(url, **auth_kwargs)
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

        while len(episodes_list) < target_episode_count:
            ep_num = len(episodes_list) + 1
            episodes_list.append({
                "global_episode": ep_num,
                "season": start_season,
                "episode_in_season": ep_num,
                "name": f"Episode {ep_num} (Pending TMDB sync or Error)",
                "thumbnail": None,
                "rollover_applied": True
            })

        return episodes_list

    @staticmethod
    def fetch_tvdb_episodes_with_rollover(
        tvdb_id: Optional[int],
        target_episode_count: int,
        start_season: int = 1
    ) -> List[Dict[str, Any]]:
        episodes_list = []
        headers = get_tvdb_bearer_headers()
        if not tvdb_id or not headers:
            return episodes_list

        try:
            page = 0
            all_eps = []
            while page < 20:
                data_eng = _safe_get_json(f"https://api4.thetvdb.com/v4/series/{tvdb_id}/episodes/official/eng?page={page}", headers=headers)
                if not data_eng:
                    break
                data_jpn = _safe_get_json(f"https://api4.thetvdb.com/v4/series/{tvdb_id}/episodes/official/jpn?page={page}", headers=headers)

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
