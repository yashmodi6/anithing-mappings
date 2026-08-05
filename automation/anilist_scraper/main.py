# Step 1 Presentation & CLI Entrypoint

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import AniListScraper


# Progress callback to output CLI & TUI formatted status events
def handle_progress(event_type: str, data: dict) -> None:
    if event_type == "rate_limit":
        print(f"[429 Rate Limit] Retrying in {data['seconds_remaining']} seconds...", flush=True)
    elif event_type == "page_done":
        print(
            f"CHUNK:[{data['start_id']}..{data['end_id']}] Page {data['chunk_page']}/{data['last_page']} | {data['items_count']} items",
            flush=True
        )
    elif event_type == "chunk_done":
        print(
            f"CHUNK_DONE:[{data['start_id']}..{data['end_id']}] Saved {data['chunk_saved']} anime entries",
            flush=True
        )
    elif event_type == "incremental_page_done":
        print(
            f"INCREMENTAL: Page {data['page']}/{data['last_page']} | {data['items_count']} updated items",
            flush=True
        )
    elif event_type == "incremental_done":
        print(
            f"INCREMENTAL_DONE: Synced {data['total_saved']} updated anime entries",
            flush=True
        )
    elif event_type == "info":
        print(f"[Info] {data['message']}", flush=True)
    elif event_type == "gap_filler":
        print(f"GAP_FILLER: {data['message']}", flush=True)
    elif event_type == "error":
        print(f"[Error] Attempt {data['attempt']} failed: {data['message']}. Retrying in 3s...", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="AniList Scraper Step 1 Pipeline")
    parser.add_argument("--clean", action="store_true", help="Force a clean full scrape instead of incremental sync")
    parser.add_argument("--clean-graveyard", action="store_true", help="Wipe the dead IDs graveyard")
    args = parser.parse_args()
    
    if args.clean_graveyard:
        graveyard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "dead_ids.json")
        if os.path.exists(graveyard_path):
            try:
                os.remove(graveyard_path)
            except Exception: pass
        print("[Info] Graveyard wiped! Gap filler will re-verify all missing IDs.", flush=True)

    scraper = AniListScraper()
    est_time = scraper.estimate_duration(clean=args.clean)
    mode_name = "Clean Full Scrape" if args.clean else "Fast Incremental Sync"
    print(f"[Info] Mode: {mode_name} (Estimated time: {est_time})", flush=True)

    if args.clean:
        scraper.run_full_scrape(progress_callback=handle_progress)
    else:
        scraper.run_incremental_sync(progress_callback=handle_progress)




if __name__ == "__main__":
    main()

