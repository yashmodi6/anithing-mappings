import json
import os
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify, send_file
from core.database import VerifiedDB
from core.config import MANUAL_CHECKER_ROOT, AUTOMATION_ROOT
from providers import tmdb, tvdb, anilist, mal
from services.mapper_service import auto_map
from services.anime_service import parse_seasons_from_mappings, align_episodes
from exporter import update_mapping_edits_json

api_bp = Blueprint("api", __name__)
db = VerifiedDB()




@api_bp.route("/api/stats", methods=["GET"])
def api_stats():
    return jsonify(db.get_stats())


@api_bp.route("/api/queue", methods=["GET"])
def api_queue():
    status = request.args.get("status", "ALL")
    filter_type = request.args.get("filter", "UNVERIFIED")
    format_type = request.args.get("format", "ALL")
    offset = int(request.args.get("offset", 0))
    sort_by = request.args.get("sort", "POPULARITY_DESC")
    limit = 30

    result = db.get_unverified_queue(
        status_filter=status,
        verification_filter=filter_type,
        format_filter=format_type,
        offset=offset,
        limit=limit,
        search_query=None,
        sort_by=sort_by
    )
    # Inject stats into response — matches original server.py
    result["stats"] = db.get_stats()
    return jsonify(result)


@api_bp.route("/api/anime/<int:anilist_id>", methods=["GET"])
def api_anime(anilist_id):
    details = db.get_anime_details(anilist_id)
    if not details:
        return jsonify({"error": "Anime not found"}), 404

    def fetch_p(provider):
        p_id = details.get(f"{provider}_show_id") or details.get(f"{provider}_movie_id")
        if p_id:
            try:
                is_movie = bool(details.get(f"{provider}_movie_id"))
                if provider == "tmdb":
                    return tmdb.fetch_preview(int(p_id), is_movie)
                else:
                    return tvdb.fetch_preview(int(p_id), is_movie)
            except Exception:
                pass
        return None

    def fetch_m():
        if details.get("mal_id"):
            try:
                return mal.fetch_preview(int(details["mal_id"]))
            except Exception:
                pass
        return None

    def fetch_a():
        try:
            return anilist.fetch_cover_image(anilist_id)
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=4) as executor:
        t_tmdb = executor.submit(fetch_p, "tmdb")
        t_tvdb = executor.submit(fetch_p, "tvdb")
        t_mal = executor.submit(fetch_m)
        t_ani = executor.submit(fetch_a)

        tmdb_prev = t_tmdb.result() or {}
        tvdb_prev = t_tvdb.result() or {}
        mal_prev = t_mal.result() or {}

        details["tmdb_poster"] = tmdb_prev.get("poster")
        details["tmdb_title"] = tmdb_prev.get("title")
        details["tmdb_date"] = tmdb_prev.get("date")

        details["tvdb_poster"] = tvdb_prev.get("poster")
        details["tvdb_title"] = tvdb_prev.get("title")
        details["tvdb_date"] = tvdb_prev.get("date")

        details["mal_poster"] = mal_prev.get("poster")
        details["mal_title"] = mal_prev.get("title")
        details["mal_date"] = mal_prev.get("date")

        details["anilist_poster"] = t_ani.result()

    return jsonify(details)


# Match original URL: /api/poster/<provider>/<id>?movie=0|1
@api_bp.route("/api/poster/<provider>/<int:provider_id>", methods=["GET"])
def api_poster(provider, provider_id):
    try:
        is_movie = request.args.get("movie", "0") == "1"
        if provider == "tmdb":
            prev = tmdb.fetch_preview(provider_id, is_movie)
        elif provider == "tvdb":
            prev = tvdb.fetch_preview(provider_id, is_movie)
        elif provider == "mal":
            prev = mal.fetch_preview(provider_id)
        else:
            return jsonify({"error": "Unknown provider"}), 400
        return jsonify(prev or {"poster": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/episodes/<provider>/<int:anilist_id>", methods=["GET", "POST"])
def api_episodes(provider, anilist_id):
    if provider not in ["tmdb", "tvdb"]:
        return jsonify({"error": "Invalid provider"}), 400

    details = db.get_anime_details(anilist_id)
    if not details:
        return jsonify({"error": "Anime not found"}), 404

    # Use released_episodes preferentially — matches original server.py
    rel_eps = details.get("released_episodes") or details.get("episodes") or 0
    mappings = details.get("episode_mappings") or {}

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
            try:
                p_id = int(p_id)
                exact_seasons = parse_seasons_from_mappings(mappings, provider)
                if provider == "tmdb":
                    eps = tmdb.fetch_episodes_with_rollover(p_id, rel_eps, exact_seasons)
                else:
                    eps = tvdb.fetch_episodes_with_rollover(p_id, rel_eps)
            except Exception:
                pass
        else:
            rel_eps = 0
    else:
        rel_eps = 0

    aligned = align_episodes(provider, rel_eps, mappings, eps)
    return jsonify({
        "anilist_id": anilist_id,
        "total_episodes": rel_eps,
        "episodes": aligned
    })


@api_bp.route("/api/verify", methods=["POST"])
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


@api_bp.route("/api/auto_map/<int:anilist_id>", methods=["POST"])
def api_auto_map(anilist_id):
    try:
        details = db.get_anime_details(anilist_id)
        result = auto_map(details)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/unverify/<int:anilist_id>", methods=["POST"])
def api_unverify(anilist_id):
    try:
        from exporter import remove_mapping_edits_json
        db.remove_verified_anime(anilist_id)
        remove_mapping_edits_json(anilist_id)
        return jsonify({"success": True, "stats": db.get_stats()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/api/skip/<int:anilist_id>", methods=["POST"])
def api_skip(anilist_id):
    try:
        req_data = request.json or {}
        reason = req_data.get("reason", "Other")
        
        from exporter import update_skipped_anime_json
        db.skip_anime(anilist_id, reason)
        update_skipped_anime_json(anilist_id, reason)
        
        return jsonify({"success": True, "stats": db.get_stats()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/mappings.json", methods=["GET"])
def api_mappings_json():
    from exporter import MAPPING_EDITS_PATH
    if os.path.exists(MAPPING_EDITS_PATH):
        return send_file(MAPPING_EDITS_PATH, mimetype="application/json")
    return jsonify([])

@api_bp.route("/api/skipped.json", methods=["GET"])
def api_skipped_json():
    from exporter import SKIPPED_ANIME_PATH
    if os.path.exists(SKIPPED_ANIME_PATH):
        return send_file(SKIPPED_ANIME_PATH, mimetype="application/json")
    return jsonify([])


@api_bp.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    from api.server import _shutdown_event
    _shutdown_event.set()
    return jsonify({"success": True, "message": "Session ended. You can close this tab."})
