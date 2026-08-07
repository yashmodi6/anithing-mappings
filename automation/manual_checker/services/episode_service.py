import json
from collections import defaultdict
from typing import List, Dict, Any, Tuple
from providers import tmdb, tvdb

def sync_provider_episodes(mappings: List[Dict[str, Any]], rel_eps: int) -> Tuple[List[Any], List[Any]]:
    """
    Groups mappings by provider ID, extracts scopes from episode_mapping,
    fetches episodes from providers, and returns padded episode lists.
    """
    tmdb_eps = []
    tvdb_eps = []
    
    grouped_mappings = defaultdict(list)
    for m in mappings:
        provider = m.get("provider")
        p_id = m.get("id")
        ep_map_str = m.get("episode_mapping")
        if not p_id or provider not in ("tmdb", "tvdb"): 
            continue
            
        try:
            p_id = int(p_id)
            if ep_map_str:
                try:
                    parsed_map = json.loads(ep_map_str)
                    if isinstance(parsed_map, dict):
                        for k in parsed_map.keys():
                            grouped_mappings[(provider, p_id)].append(k)
                except Exception:
                    pass
            # If no scopes found in episode_mapping, we still need to process the ID
            if not grouped_mappings[(provider, p_id)]:
                grouped_mappings[(provider, p_id)].append(None)
        except ValueError:
            pass

    for (provider, p_id), scopes in grouped_mappings.items():
        try:
            exact_seasons = []
            for sc in scopes:
                if sc and str(sc).startswith('s'):
                    try:
                        exact_seasons.append(int(str(sc).replace('s', '')))
                    except ValueError:
                        pass
            
            exact_seasons = sorted(list(set(exact_seasons))) if exact_seasons else None

            if provider == "tmdb":
                eps = tmdb.fetch_episodes_with_rollover(p_id, 1000, exact_seasons)
                tmdb_eps.extend(eps)
            elif provider == "tvdb":
                eps = tvdb.fetch_episodes_with_rollover(p_id, 1000, exact_seasons=exact_seasons)
                tvdb_eps.extend(eps)
        except Exception as e:
            print(f"Error fetching {provider} {p_id}: {e}")

    # We need to ensure we return exactly `total_episodes` length arrays
    if rel_eps > 0:
        tmdb_eps = tmdb_eps[:rel_eps]
        tvdb_eps = tvdb_eps[:rel_eps]
        
        # pad if necessary
        while len(tmdb_eps) < rel_eps: tmdb_eps.append({})
        while len(tvdb_eps) < rel_eps: tvdb_eps.append({})
        
    return tmdb_eps, tvdb_eps
