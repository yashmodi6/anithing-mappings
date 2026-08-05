import os
import threading
from flask import Flask
from werkzeug.serving import make_server
from api.routes import api_bp
from core.config import MANUAL_CHECKER_ROOT

# Setup Flask
app = Flask(__name__, static_folder=os.path.join(MANUAL_CHECKER_ROOT, "web"), static_url_path="/")

app.register_blueprint(api_bp)

@app.route("/")
def serve_index():
    return app.send_static_file("index.html")

@app.errorhandler(404)
def not_found(e):
    return app.send_static_file("index.html")

_server = None
_server_thread = None
_shutdown_event = threading.Event()

def start_server(port=5000):
    global _server, _server_thread
    _server = make_server('0.0.0.0', port, app)
    
    def run():
        _server.serve_forever()
        
    _server_thread = threading.Thread(target=run, daemon=True)
    _server_thread.start()
    print(f"Manual Checker Flask API started on port {port}")
    
    # Wait until shutdown event is set
    try:
        _shutdown_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        _server.shutdown()
        _server_thread.join()
