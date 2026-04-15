import requests
from enum import Enum

class Group(Enum):
    SPACE_STATIONS = "stations"
    STARLINK       = "starlink"
    GPS            = "gps-ops"
    WEATHER        = "weather"
    NOAA           = "noaa"
    GALILEO        = "galileo"
    GLONASS        = "glo-ops"
    BEIDOU         = "beidou"
    ONEWEB         = "oneweb"
    IRIDIUM_NEXT   = "iridium-NEXT"
    CUBESATS       = "cubesat"
    FENGYUN        = "fengyun-1c-debris"

BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"

def pull_data(group: Group) -> list[dict]:
    url = f"{BASE_URL}?GROUP={group.value}&FORMAT=json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Fetched {len(data)} objects for group: {group.value}")
        return data

    except requests.exceptions.Timeout:
        print(f"Request timed out for group: {group.value}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error for group {group.value}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for group {group.value}: {e}")

    return []