import json
from typing import Dict, Any, List

def compress_episode_types(ep_types_dict: dict) -> dict:
    compressed = {}
    try:
        ep_nums = sorted([int(k) for k in ep_types_dict.keys() if str(k).isdigit()])
    except ValueError:
        return compressed
        
    for type_name in ["canon", "filler", "mixed"]:
        type_eps = sorted([ep for ep in ep_nums if ep_types_dict.get(str(ep)) == type_name])
        if not type_eps:
            continue
            
        ranges = []
        start = type_eps[0]
        end = start
        
        for i in range(1, len(type_eps)):
            if type_eps[i] == end + 1:
                end = type_eps[i]
            else:
                ranges.append(str(start) if start == end else f"{start}-{end}")
                start = type_eps[i]
                end = start
                
        ranges.append(str(start) if start == end else f"{start}-{end}")
        compressed[type_name] = ranges
        
    return compressed

def decompress_episode_types(ep_types: dict) -> dict:
    is_compressed = any(isinstance(v, list) for v in ep_types.values())
    if not is_compressed:
        return ep_types
        
    decompressed = {}
    for t, ranges in ep_types.items():
        if isinstance(ranges, list):
            for r in ranges:
                if "-" in str(r):
                    start, end = str(r).split("-")
                    for i in range(int(start), int(end) + 1):
                        decompressed[str(i)] = t
                else:
                    decompressed[str(r)] = t
    return decompressed

def build_anibridge_mappings(r2_dict: Dict[str, Any], is_movie: bool) -> List[Dict[str, Any]]:
    mappings = []
    ep_maps_raw = r2_dict.get("episode_mappings")
    ep_maps = {}
    if ep_maps_raw:
        try:
            ep_maps = json.loads(ep_maps_raw)
        except Exception:
            pass

    if r2_dict.get("mal_id"):
        mappings.append({"provider": "mal", "id": r2_dict["mal_id"]})
    
    for p in ("tmdb", "tvdb"):
        for t in ("show", "movie"):
            val = r2_dict.get(f"{p}_{t}_id")
            if val:
                val_str = str(val)
                b_id_str = val_str.split(":")[0] if ":" in val_str else val_str
                b_id = int(b_id_str) if b_id_str.isdigit() else b_id_str
                
                scopes_found = set()
                prefix = f"{p}_{t}:{b_id}:"
                merged_ep_map = {}
                for k in ep_maps.keys():
                    if k.startswith(prefix):
                        sc = k[len(prefix):]
                        if sc:
                            scopes_found.add(sc)
                            merged_ep_map[sc] = ep_maps[k]
                
                if scopes_found:
                    mappings.append({"provider": p, "type": t, "id": b_id, "episode_mapping": json.dumps(merged_ep_map)})
                else:
                    if ":" in val_str:
                        sc_str = val_str.split(":", 1)[1]
                        for sc in sc_str.split(","):
                            merged_ep_map[sc.strip()] = {}
                        mappings.append({"provider": p, "type": t, "id": b_id, "episode_mapping": json.dumps(merged_ep_map)})
                    else:
                        mappings.append({"provider": p, "type": t, "id": b_id})
                        
    return mappings

def clean_mappings_for_export(mappings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clean_mappings = []
    for m in mappings:
        cleaned = {k: v for k, v in m.items() if k not in ("_preview", "globalIndex", "_dirty")}
        if cleaned.get("provider") == "mal":
            cleaned = {"provider": "mal", "id": cleaned.get("id")}
        clean_mappings.append(cleaned)
    return clean_mappings
