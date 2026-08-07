import json
from collections import defaultdict
from typing import List, Dict, Any, Tuple
from providers import tmdb, tvdb

def _build_exact_lookup(ep_map_str: str) -> dict:
    """
    Parses a legacy episode_mapping JSON string into an exact lookup dictionary.
    Example Input: '{"s1": {"1-8": "1-8"}, "s0": {"542": "39"}}'
    Example Output: {(1, 1): 1, (1, 2): 2 ... (0, 39): 542}
    
    This allows the backend to precisely place episodes into their exact global slots.
    """
    lookup = {}
    if not ep_map_str:
        return lookup
    try:
        mapping = json.loads(ep_map_str)
        if not isinstance(mapping, dict):
            return lookup
            
        for season_key, ranges in mapping.items():
            if not season_key.startswith('s'): continue
            try:
                s_num = int(season_key.replace('s', ''))
            except ValueError:
                continue
                
            for global_range, local_range in ranges.items():
                try:
                    # Parse the global range (e.g. "1-8" -> start: 1, end: 8)
                    g_parts = str(global_range).split('-')
                    g_start = int(g_parts[0])
                    g_end = int(g_parts[1]) if len(g_parts) > 1 and g_parts[1] else g_start
                    
                    # Handle open-ended ranges (e.g. "1089-") by assigning an arbitrary large end point
                    if len(g_parts) > 1 and not g_parts[1]:
                        g_end = g_start + 2000 
                    
                    # Parse the local range (e.g. "1-8" -> start: 1)
                    l_parts = str(local_range).split('-')
                    l_start = int(l_parts[0])
                    
                    g_idx = g_start
                    l_idx = l_start
                    
                    # Iterate through the range and populate the lookup table
                    while g_idx <= g_end and (g_idx - g_start) < 2000:
                        lookup[(s_num, l_idx)] = g_idx
                        g_idx += 1
                        l_idx += 1
                except ValueError:
                    continue
    except Exception:
        pass
    return lookup

def sync_provider_episodes(mappings: List[Dict[str, Any]], rel_eps: int) -> Tuple[List[Any], List[Any]]:
    tmdb_eps = []
    tvdb_eps = []
    
    # We will process each mapping sequentially
    for m in mappings:
        provider = m.get("provider")
        p_id = m.get("id")
        ep_map_str = m.get("episode_mapping")
        scope = m.get("scope")
        
        if not p_id or provider not in ("tmdb", "tvdb"): 
            continue
            
        try:
            p_id = int(p_id)
        except ValueError:
            continue
            
        lookup = _build_exact_lookup(ep_map_str)
        
        exact_seasons = []
        if scope and str(scope).startswith('s'):
            try: exact_seasons.append(int(str(scope).replace('s', '')))
            except: pass
            
        for (s, _) in lookup.keys():
            exact_seasons.append(s)
            
        exact_seasons = sorted(list(set(exact_seasons))) if exact_seasons else None

        eps = []
        fetch_limit = max(rel_eps + 100, 2000)
        try:
            if provider == "tmdb":
                eps = tmdb.fetch_episodes_with_rollover(p_id, fetch_limit, exact_seasons)
            elif provider == "tvdb":
                eps = tvdb.fetch_episodes_with_rollover(p_id, fetch_limit, exact_seasons=exact_seasons)
        except Exception as e:
            print(f"Error fetching {provider} {p_id}: {e}")
            
        if lookup:
            # Reorder using exact mapping
            aligned_eps = []
            for ep in eps:
                s_num = ep.get('season')
                ep_num = ep.get('episode_in_season')
                if (s_num, ep_num) in lookup:
                    g_idx = lookup[(s_num, ep_num)]
                    ep_copy = dict(ep)
                    ep_copy['global_episode'] = g_idx
                    aligned_eps.append(ep_copy)
            aligned_eps.sort(key=lambda x: x['global_episode'])
            
            if provider == "tmdb":
                tmdb_eps.extend(aligned_eps)
            else:
                tvdb_eps.extend(aligned_eps)
        else:
            # Sequential append
            if provider == "tmdb":
                tmdb_eps.extend(eps)
            else:
                tvdb_eps.extend(eps)
                
    # Sort and pad
    tmdb_eps.sort(key=lambda x: x.get('global_episode', 9999))
    tvdb_eps.sort(key=lambda x: x.get('global_episode', 9999))
    
    # We need to construct exact arrays of size rel_eps
    final_tmdb = []
    final_tvdb = []
    
    for i in range(1, rel_eps + 1):
        # find ep in tmdb_eps
        t_ep = next((e for e in tmdb_eps if e.get('global_episode') == i), None)
        if t_ep:
            final_tmdb.append(t_ep)
        else:
            final_tmdb.append({
                "global_episode": i,
                "season": 1,
                "episode_in_season": i,
                "name": f"Episode {i} (Pending sync)",
                "thumbnail": None,
                "rollover_applied": True
            })
            
        v_ep = next((e for e in tvdb_eps if e.get('global_episode') == i), None)
        if v_ep:
            final_tvdb.append(v_ep)
        else:
            final_tvdb.append({
                "global_episode": i,
                "season": 1,
                "episode_in_season": i,
                "name": f"Episode {i} (Pending sync)",
                "thumbnail": None,
                "rollover_applied": True
            })

    return final_tmdb, final_tvdb
