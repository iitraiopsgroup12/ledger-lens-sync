import requests

BASE_URL = "https://www.nseindia.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


def create_nse_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    # NSE rejects API calls without cookies from a prior page visit.
    session.get(BASE_URL, timeout=10)
    return session