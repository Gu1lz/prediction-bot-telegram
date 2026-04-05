import re
from datetime import datetime

MONTH_DAY_RE = re.compile(
    r"on\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\?",
    re.I
)
NYC_COORDS = (40.7128, -74.0060)
TEMP_RE = re.compile(r"highest temperature", re.I)
UNIT_RE = re.compile(r"(C|F|celsius|fahrenheit)", re.I)

def parse_question(question: str, slug):
    q = question.lower()
    if "nyc" not in q:
        return None
    if TEMP_RE.search(q):
        unit_match = UNIT_RE.search(slug)
        unit = unit_match.group(1).lower() if unit_match else "c"
        unit_map = {"c": "celsius", "celsius": "celsius",
                    "f": "fahrenheit", "fahrenheit": "fahrenheit"}
        unit = unit_map.get(unit, "celsius")
        return {
            "type": "temperature",
            "metric": "max",
            "city": "NYC",
            "lat": NYC_COORDS[0],
            "lon": NYC_COORDS[1],
            "unit": unit
        }
    return None
