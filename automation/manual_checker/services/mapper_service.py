import requests
from typing import Dict, Any, Optional, List
from providers.base import safe_get_json
from providers.tmdb import get_auth_kwargs
from providers.tvdb import get_bearer_headers
from core.config import TMDB_READ_ACCESS_TOKEN

def normalize_string(s: str) -> str:
    if not s: return ""
    return str(s).strip().lower()

def is_title_match(result_title: str, anilist_titles: List[str]) -> bool:
    rt = normalize_string(result_title)
    if not rt: return False
    for at in anilist_titles:
        if normalize_string(at) == rt:
            return True
    return False

def auto_map(details: Dict[str, Any]) -> Dict[str, Any]:
    """Advanced auto mapper that validates existing IDs, uses strict formats, and intelligently falls back through synonyms."""
    result = {"tmdb": None, "tvdb": None}
    
    # Extract AniList data
    raw = details.get("raw_metadata") or {}
    format_type = (details.get("format") or "").upper()
    is_movie = "MOVIE" in format_type
    
    year = None
    start_date = raw.get("startDate", {})
    if isinstance(start_date, dict) and start_date.get("year"):
        year = start_date.get("year")
        
    title_eng = details.get("title_english")
    title_rom = details.get("title_romaji")
    synonyms = raw.get("synonyms") or []
    
    # Build list of all valid AniList titles for comparison
    all_anilist_titles = [t for t in [title_eng, title_rom] + synonyms if t]
    
    # Build search query sequence
    search_queries = []
    if title_eng: search_queries.append(title_eng)
    if title_rom and title_rom not in search_queries: search_queries.append(title_rom)
    for syn in synonyms:
        if syn and syn not in search_queries:
            search_queries.append(syn)
            
    if not search_queries:
        return result

    # --- Phase 1: Validate Existing Mappings ---
    tmdb_auth = get_auth_kwargs() if (TMDB_READ_ACCESS_TOKEN and not TMDB_READ_ACCESS_TOKEN.startswith("YOUR_")) else None
    tvdb_headers = get_bearer_headers()
    
    existing_tmdb_id = details.get("tmdb_movie_id") if is_movie else details.get("tmdb_show_id")
    if existing_tmdb_id and tmdb_auth:
        endpoint = "movie" if is_movie else "tv"
        val_data = safe_get_json(f"https://api.themoviedb.org/3/{endpoint}/{existing_tmdb_id}", **tmdb_auth)
        if val_data and val_data.get("id"):
            result["tmdb"] = {"id": str(existing_tmdb_id), "type": "movie" if is_movie else "show"}

    existing_tvdb_id = details.get("tvdb_movie_id") if is_movie else details.get("tvdb_show_id")
    if existing_tvdb_id and tvdb_headers:
        endpoint = "movies" if is_movie else "series"
        val_data = safe_get_json(f"https://api4.thetvdb.com/v4/{endpoint}/{existing_tvdb_id}", headers=tvdb_headers)
        if val_data and val_data.get("data"):
            result["tvdb"] = {"id": str(existing_tvdb_id), "type": "movie" if is_movie else "show"}

    # --- Phase 2: Strict Searching ---
    
    # TMDB Search
    if result["tmdb"] is None and tmdb_auth:
        endpoint = "movie" if is_movie else "tv"
        year_param = f"&primary_release_year={year}" if is_movie else f"&first_air_date_year={year}"
        
        for query in search_queries:
            url = f"https://api.themoviedb.org/3/search/{endpoint}?query={requests.utils.quote(query)}"
            if year: url += year_param
            
            search_data = safe_get_json(url, **tmdb_auth)
            results = search_data.get("results", []) if search_data else []
            
            if results:
                best_match = results[0] # Default to first result of first successful query
                
                # Deep compare titles to find exact match
                for res in results:
                    res_title = res.get("title") if is_movie else res.get("name")
                    res_original = res.get("original_title") if is_movie else res.get("original_name")
                    if is_title_match(res_title, all_anilist_titles) or is_title_match(res_original, all_anilist_titles):
                        best_match = res
                        break
                        
                result["tmdb"] = {
                    "id": str(best_match.get("id")),
                    "type": "movie" if is_movie else "show"
                }
                break # Stop querying once we found results

    # TVDB Search
    if result["tvdb"] is None and tvdb_headers:
        tvdb_type = "movie" if is_movie else "series"
        
        for query in search_queries:
            url = f"https://api4.thetvdb.com/v4/search?type={tvdb_type}&query={requests.utils.quote(query)}"
            if year: url += f"&year={year}"
            
            search_data = safe_get_json(url, headers=tvdb_headers)
            results = search_data.get("data", []) if search_data else []
            
            if results:
                best_match = results[0]
                
                for res in results:
                    res_title = res.get("name")
                    # TVDB aliases are sometimes returned in search
                    aliases = res.get("aliases", [])
                    titles_to_check = [res_title] + (aliases if isinstance(aliases, list) else [])
                    
                    found_exact = False
                    for t in titles_to_check:
                        if is_title_match(t, all_anilist_titles):
                            best_match = res
                            found_exact = True
                            break
                    if found_exact:
                        break
                        
                result["tvdb"] = {
                    "id": str(best_match.get("tvdb_id", best_match.get("id"))),
                    "type": "movie" if is_movie else "show"
                }
                break # Stop querying once we found results

    return result
