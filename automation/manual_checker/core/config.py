import os
from typing import Dict

# core/config.py lives at manual_checker/core/config.py
# MANUAL_CHECKER_ROOT = manual_checker/
# AUTOMATION_ROOT = automation/ (parent, where output/ lives)
MANUAL_CHECKER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTOMATION_ROOT = os.path.dirname(MANUAL_CHECKER_ROOT)
ENV_FILE = os.path.join(AUTOMATION_ROOT, ".env")

def load_env() -> Dict[str, str]:
    env_vars = {}
    if not os.path.exists(ENV_FILE):
        return env_vars
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
    return env_vars

ENV = load_env()

TMDB_READ_ACCESS_TOKEN = ENV.get("TMDB_READ_ACCESS_TOKEN", "")
TVDB_API_KEY = ENV.get("TVDB_API_KEY", "")
MAL_CLIENT_ID = ENV.get("MAL_CLIENT_ID", "")
ANILIST_GRAPHQL_URL = "https://graphql.anilist.co"
