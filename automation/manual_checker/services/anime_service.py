from typing import Dict, Any, List, Set, Optional


def parse_seasons_from_mappings(episode_mappings: Optional[Dict[str, Any]], provider_key: str) -> List[int]:
    seasons: Set[int] = set()
    if not episode_mappings:
        return list(seasons)
    for ep_num_str, mapped_data in episode_mappings.items():
        if not isinstance(mapped_data, dict):
            continue
        p_data = mapped_data.get(provider_key, {})
        if p_data and p_data.get("s"):
            try:
                seasons.add(int(p_data["s"]))
            except ValueError:
                pass
    return sorted(list(seasons))


def align_episodes(provider: str, total_eps: int, mappings: dict, provider_eps: list) -> list:
    """Mirror of original _align_episodes in server.py."""
    lookup = {f"{e.get('season')}-{e.get('episode_in_season')}": e for e in provider_eps}
    aligned = []
    curr_s, curr_e = 1, 1

    for i in range(1, total_eps + 1):
        map_str = str(i)
        is_filler = False
        if map_str in mappings:
            m_t = mappings[map_str].get(provider, {})
            if m_t:
                try:
                    curr_s = int(m_t.get("s", m_t.get("season", curr_s)))
                    curr_e = int(m_t.get("e", m_t.get("episode", curr_e)))
                except (ValueError, TypeError):
                    pass
            is_filler = bool(mappings[map_str].get("is_filler"))

        ep_data = lookup.get(f"{curr_s}-{curr_e}", {}) if not is_filler else {}
        item = {
            "anilist_ep": i,
            "season": curr_s if not is_filler else None,
            "episode": curr_e if not is_filler else None,
            "thumbnail": ep_data.get("thumbnail"),
            "rollover_applied": curr_s > 1
        }
        if provider == "tmdb":
            item["title"] = ep_data.get("name")
        else:
            raw_name = ep_data.get("name") or ""
            item["names"] = [n.strip() for n in raw_name.split(" / ") if n.strip()] if raw_name else []

        aligned.append(item)
        if not is_filler:
            curr_e += 1

    return aligned

def fetch_anime_with_previews(anilist_id: int, db) -> Optional[Dict[str, Any]]:
    from concurrent.futures import ThreadPoolExecutor
    from providers import anilist

    details = db.get_anime_details(anilist_id)
    if not details:
        return None

    def fetch_a():
        try:
            return anilist.fetch_cover_image(anilist_id)
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=1) as executor:
        t_ani = executor.submit(fetch_a)
        details["anilist_poster"] = t_ani.result()

    return details

