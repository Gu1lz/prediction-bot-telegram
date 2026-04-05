import requests
from datetime import datetime, timezone, timedelta

SEARCH_URL = "https://gamma-api.polymarket.com/events"

def fetch_search(tag_slug="weather", limit=300):
    params = {
        "active": "true",
        "closed": "false",
        "tag_slug": tag_slug,
        "limit": limit
    }
    results = []
    r = requests.get(SEARCH_URL, params=params)
    r.raise_for_status()
    return r.json()
