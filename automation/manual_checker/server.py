# Flask REST API & Static File Web Server for Step 3 Manual Verification Dashboard

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_from_directory, send_file

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import VerifiedDB
from fetcher import ProviderFetcher
from exporter import update_mapping_edits_json

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

db = VerifiedDB()
app = Flask(__name__, static_folder=WEB_DIR)
_shutdown_event = threading.Event()


# Helper: Unified episode alignment logic for TMDB and TVDB
def _align_episodes(provider: str, total_eps: int, mappings: dict, provider_eps: list) -> list:
    lookup = {f"{e.get('season')}-{e.get('episode_in_season')}": e for e in provider_eps}
    aligned = []
    curr_s, curr_e = 1, 1

    for i in range(1, total_eps + 1):
        map_str = str(i)
        is_filler = False
        if map_str in mappings:
            m_t = mappings[map_str].get(provider, {})
            curr_s = int(m_t.get("s", m_t.get("season", curr_s)))
            curr_e = int(m_t.get("e", m_t.get("episode", curr_e)))
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


# --- Static file routes ---
@app.route("/")
def serve_index():
    return send_from_directory(WEB_DIR, "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(WEB_DIR, filename)

@app.route("/api/mappings.json")
def serve_mappings():
    from exporter import MAPPING_EDITS_PATH
    import os
    if os.path.exists(MAPPING_EDITS_PATH):
        return send_file(MAPPING_EDITS_PATH, mimetype='application/json')
    return jsonify([])


# --- API: Stats & Queue ---
@app.route("/api/stats")
def api_stats():
    return jsonify(db.get_stats())

@app.route("/api/queue")
def api_queue():
    result = db.get_unverified_queue(
        status_filter=request.args.get("status", "ALL"),
        verification_filter=request.args.get("filter", "UNVERIFIED"),
        format_filter=request.args.get("format", "ALL"),
        offset=int(request.args.get("offset", 0)),
        limit=int(request.args.get("limit", 30)),
        search_query=request.args.get("q", None),
        sort_by=request.args.get("sort", "POPULARITY_DESC")
    )
    result["stats"] = db.get_stats()
    return jsonify(result)


# --- API: Anime details ---
@app.route("/api/anime/<int:anilist_id>")
def api_anime_details(anilist_id):
    try:
        details = db.get_anime_details(anilist_id)
        raw = details.get("raw_metadata") or {}
        cover_url = raw.get("coverImage", {}).get("extraLarge") or raw.get("coverImage", {}).get("large")
        
        format_val = (details.get("format") or "").upper()
        
        tmdb_movie_id = details.get("tmdb_movie_id")
        tmdb_show_id = details.get("tmdb_show_id")
        is_tmdb_movie = bool(tmdb_movie_id)
        tmdb_id = tmdb_movie_id or tmdb_show_id
        
        tvdb_movie_id = details.get("tvdb_movie_id")
        tvdb_show_id = details.get("tvdb_show_id")
        is_tvdb_movie = bool(tvdb_movie_id)
        tvdb_id = tvdb_movie_id or tvdb_show_id
        
        with ThreadPoolExecutor(max_workers=4) as pool:
            f_anilist = pool.submit(lambda: cover_url or ProviderFetcher.fetch_anilist_cover_image(anilist_id))
            f_mal = pool.submit(ProviderFetcher.fetch_mal_poster, details.get("mal_id"))
            f_tmdb = pool.submit(ProviderFetcher.fetch_tmdb_poster, tmdb_id, is_tmdb_movie)
            f_tvdb = pool.submit(ProviderFetcher.fetch_tvdb_poster, tvdb_id, is_tvdb_movie)

        details["anilist_poster"] = f_anilist.result()
        details["mal_poster"] = f_mal.result()
        details["tmdb_poster"] = f_tmdb.result()
        details["tvdb_poster"] = f_tvdb.result()
        return jsonify(details)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- API: Poster live preview ---
@app.route("/api/poster/<provider>/<int:provider_id>")
def api_poster(provider, provider_id):
    try:
        is_movie = request.args.get("movie", "0") == "1"
        if provider == "tmdb":
            url = ProviderFetcher.fetch_tmdb_poster(provider_id, is_movie=is_movie)
        elif provider == "tvdb":
            url = ProviderFetcher.fetch_tvdb_poster(provider_id, is_movie=is_movie)
        elif provider == "mal":
            url = ProviderFetcher.fetch_mal_poster(provider_id)
        else:
            return jsonify({"error": "Unknown provider"}), 400
        return jsonify({"poster": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- API: Episode alignment (TMDB & TVDB) ---
@app.route("/api/episodes/<provider>/<int:anilist_id>", methods=["GET", "POST"])
def api_episodes(provider, anilist_id):
    if provider not in ("tmdb", "tvdb"):
        return jsonify({"error": "Invalid provider"}), 400
    try:
        details = db.get_anime_details(anilist_id)
        rel_eps = details.get("released_episodes") or details.get("episodes") or 0
        is_movie = "MOVIE" in (details.get("format") or "").upper()
        mappings = details.get("episode_mappings", {})

        req_data = request.json if request.method == "POST" else {}
        if req_data.get("mappings"):
            mappings = req_data["mappings"]
            
        is_movie_flag = req_data.get("is_movie")
        if is_movie_flag is not None:
            is_movie = bool(is_movie_flag)
        else:
            is_movie = "MOVIE" in (details.get("format") or "").upper()

        eps = []
        if not is_movie:
            p_id = req_data.get(f"{provider}_id") or details.get(f"{provider}_show_id") or details.get(f"{provider}_movie_id")
            if p_id:
                if provider == "tmdb":
                    eps = ProviderFetcher.fetch_tmdb_episodes_with_rollover(p_id, rel_eps, episode_mappings=mappings)
                else:
                    eps = ProviderFetcher.fetch_tvdb_episodes_with_rollover(p_id, rel_eps)
        else:
            rel_eps = 0

        aligned = _align_episodes(provider, rel_eps, mappings, eps)
        return jsonify({"anilist_id": anilist_id, "total_episodes": rel_eps, "episodes": aligned})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- API: Verify, Shutdown ---
@app.route("/api/verify", methods=["POST"])
def api_verify():
    try:
        data = request.get_json(force=True)
        db.save_verified_anime(data)
        update_mapping_edits_json(data)

        next_result = db.get_unverified_queue(limit=1)
        queue_items = next_result.get("queue", [])
        return jsonify({
            "success": True,
            "verified_id": data["anilist_id"],
            "stats": db.get_stats(),
            "next_anime": queue_items[0] if queue_items else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/unverify/<int:anilist_id>", methods=["POST"])
def api_unverify(anilist_id):
    try:
        from exporter import remove_mapping_edits_json
        db.remove_verified_anime(anilist_id)
        remove_mapping_edits_json(anilist_id)
        return jsonify({"success": True, "stats": db.get_stats()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    _shutdown_event.set()
    return jsonify({"success": True, "message": "Session ended. You can close this tab."})


def start_server(port: int = 5000):
    return app, _shutdown_event
