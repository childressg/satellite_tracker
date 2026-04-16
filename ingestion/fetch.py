import requests
from enum import Enum

BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"

class Group(Enum):
    SPACE_STATIONS = "stations"
    STARLINK       = "starlink"
    GPS            = "gps-ops"
    WEATHER        = "weather"
    GALILEO        = "galileo"
    GLONASS        = "glo-ops"
    BEIDOU         = "beidou"
    ONEWEB         = "oneweb"
    IRIDIUM_NEXT   = "iridium-NEXT"
    CUBESATS       = "cubesat"
    FENGYUN        = "fengyun-1c-debris"

def parse_tle_text(text: str) -> list[dict]:
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    records = []

    for i in range(0, len(lines) - 2, 3):
        name   = lines[i]
        line1  = lines[i + 1]
        line2  = lines[i + 2]

        records.append({
            "OBJECT_NAME":  name,
            "NORAD_CAT_ID": int(line1[2:7]),
            "TLE_LINE1":    line1,
            "TLE_LINE2":    line2,
        })

    return records

def pull_data(group: Group) -> list[dict]:
    url = f"{BASE_URL}?GROUP={group.value}&FORMAT=tle"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        records = parse_tle_text(response.text)
        print(f"Fetched {len(records)} objects for group: {group.value}")
        return records

    except requests.exceptions.Timeout:
        print(f"Request timed out for group: {group.value}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error for group {group.value}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for group {group.value}: {e}")

    return []