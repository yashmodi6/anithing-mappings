# Step 3 Presentation & Entrypoint for Manual Verification GUI

import os
import sys
import time
import webbrowser
import threading
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.server import start_server, _shutdown_event
from core.database import VerifiedDB


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 3 Manual Verification Web GUI")
    parser.add_argument("--clean", action="store_true", help="Clean mode (no effect on GUI)")
    parser.add_argument("--force", action="store_true", help="Force reset verified.db database")
    args = parser.parse_args()

    port = 5000
    db = VerifiedDB()
    db.ensure_step1_indexes()

    if args.force:
        db.reset_db()

    stats = db.get_stats()
    print(f"VERIFIED_PROGRESS:{stats['verified_count']}/{stats['total_count']} ({stats['percentage']}%)", flush=True)
    print(f"[Info] Starting Step 3 Manual Verification Web GUI on http://localhost:{port}...", flush=True)

    flask_app = None # just to clarify it isn't returning
    
    # Open browser slightly after starting
    def open_browser():
        time.sleep(1)
        webbrowser.open(f"http://localhost:{port}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"[Info] Web GUI server is active at http://localhost:{port}", flush=True)
    print(f"[Info] Press Ctrl+C or click 'Complete For Now' in the browser when finished.", flush=True)
    
    try:
        start_server(port=port)
        print("\n[Info] Step 3 session completed. Server stopped.", flush=True)
    except KeyboardInterrupt:
        print("\n[Info] Step 3 Manual Verifier server stopped by user.", flush=True)

if __name__ == "__main__":
    main()

