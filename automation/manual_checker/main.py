# Step 3 Presentation & Entrypoint for Manual Verification GUI

import os
import sys
import time
import webbrowser
import threading
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.serving import make_server
from server import start_server, _shutdown_event
from db import VerifiedDB


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

    flask_app, shutdown_event = start_server(port=port)

    # Use make_server so we can call srv.shutdown() and cleanly release the port
    srv = make_server("127.0.0.1", port, flask_app)
    server_thread = threading.Thread(target=srv.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(0.5)
    webbrowser.open(f"http://localhost:{port}")

    print(f"[Info] Web GUI server is active at http://localhost:{port}", flush=True)
    print(f"[Info] Press Ctrl+C or click 'Complete For Now' in the browser when finished.", flush=True)

    try:
        while not shutdown_event.is_set():
            time.sleep(0.5)
        print("\n[Info] Step 3 session completed. Server stopped.", flush=True)
    except KeyboardInterrupt:
        print("\n[Info] Step 3 Manual Verifier server stopped by user.", flush=True)
    finally:
        srv.shutdown()   # cleanly releases the port so the next run doesn't hit "Address already in use"


if __name__ == "__main__":
    main()

