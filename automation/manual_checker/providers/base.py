import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_resilient_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

session = create_resilient_session()

def safe_get_json(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
    try:
        res = session.get(url, headers=headers, params=params, timeout=timeout)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

def safe_post_json(url: str, json_data: Dict[str, Any], headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
    try:
        res = session.post(url, json=json_data, headers=headers, timeout=timeout)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None
