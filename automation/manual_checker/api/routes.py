import json
import os
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify, send_file
from core.database import VerifiedDB
from core.config import MANUAL_CHECKER_ROOT, AUTOMATION_ROOT
from providers import tmdb, tvdb, anilist, mal
from services.mapper_service import auto_map
from services.anime_service import parse_seasons_from_mappings, align_episodes, fetch_anime_with_previews
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
    search_query = request.args.get("search_query", None)
    limit = 30

    result = db.get_unverified_queue(
        status_filter=status,
        verification_filter=filter_type,
        format_filter=format_type,
        offset=offset,
        limit=limit,
        search_query=search_query,
        sort_by=sort_by
    )
    # Inject stats into response — matches original server.py
    result["stats"] = db.get_stats()
    return jsonify(result)


@api_bp.route("/api/anime/<int:anilist_id>", methods=["GET"])
def api_anime(anilist_id):
    details = fetch_anime_with_previews(anilist_id, db)
    if not details:
        return jsonify({"error": "Anime not found"}), 404
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


@api_bp.route("/api/episodes/sync/<int:anilist_id>", methods=["POST"])
def api_episodes_sync(anilist_id):
    details = db.get_anime_details(anilist_id)
    if not details:
        return jsonify({"error": "Anime not found"}), 404

    req_data = request.json or {}
    mappings = req_data.get("mappings", [])
    
    from services.episode_service import sync_provider_episodes
    from providers.mal import fetch_filler_episodes
    
    rel_eps = details.get("released_episodes") or details.get("episodes") or 0
    tmdb_eps, tvdb_eps = sync_provider_episodes(mappings, rel_eps)
    
    mal_fillers = {}
    for m in mappings:
        if m.get("provider") == "mal" and m.get("id"):
            try:
                mal_fillers = fetch_filler_episodes(int(m["id"]))
            except Exception:
                pass
            break
        
    return jsonify({
        "anilist_id": anilist_id,
        "total_episodes": rel_eps,
        "episodes": {
            "tmdb": tmdb_eps,
            "tvdb": tvdb_eps
        },
        "mal_fillers": mal_fillers
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


@api_bp.route("/api/mapping-<format>.json", methods=["GET"])
def api_mapping_format_json(format):
    from exporter import get_mapping_path
    path = get_mapping_path(format)
    if os.path.exists(path):
        return send_file(path, mimetype="application/json")
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
