# Step 2 Presentation & CLI Entrypoint for AniBridge Mappings Engine

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from downloader import AniBridgeDownloader


def handle_progress(event_type: str, data: dict) -> None:
    if event_type == "download_progress":
        print(f"DOWNLOAD_PROGRESS:{data['percentage']}% ({data['downloaded']}/{data['total']} bytes)", flush=True)
    elif event_type == "mapping_progress":
        print(f"MAPPING_PROGRESS:{data['processed']}/{data['total']} ({data['percentage']}%)", flush=True)
    elif event_type == "mapping_done":
        print(f"MAPPING_DONE: Inserted {data['total_mapped']:,} cross-provider entries into anibridge.db", flush=True)
    elif event_type == "info":
        print(f"[Info] {data['message']}", flush=True)
    elif event_type == "error":
        print(f"[Error] {data['message']}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="AniBridge Downloader & Mapping Engine Step 2")
    parser.add_argument("--clean", action="store_true", help="Force redownload of mappings and clean DB reinitialization")
    args = parser.parse_args()

    downloader = AniBridgeDownloader()
    downloader.run_pipeline(clean=args.clean, progress_callback=handle_progress)


if __name__ == "__main__":
    main()
