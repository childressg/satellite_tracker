import requests
from enum import Enum

# Base URL for CelesTrak GP (General Perturbations) TLE data
BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"

# Enum representing available satellite groups on CelesTrak
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


# Parse raw TLE text into structured records
def parse_tle_text(text: str) -> list[dict]:
    # Split into non-empty, stripped lines
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    records = []

    # TLE format comes in groups of 3 lines:
    # [name, line1, line2]
    for i in range(0, len(lines) - 2, 3):
        name   = lines[i]
        line1  = lines[i + 1]
        line2  = lines[i + 2]

        # Extract NORAD ID from fixed position in line1
        # (columns 3–7 in TLE format)
        records.append({
            "OBJECT_NAME":  name,
            "NORAD_CAT_ID": int(line1[2:7]),
            "TLE_LINE1":    line1,
            "TLE_LINE2":    line2,
        })

    return records


# Fetch TLE data for a specific group from CelesTrak
def pull_data(group: Group) -> list[dict]:
    # Build request URL with group and TLE format
    url = f"{BASE_URL}?GROUP={group.value}&FORMAT=tle"

    try:
        # Send HTTP request with timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise error for bad HTTP status

        # Parse response text into structured records
        records = parse_tle_text(response.text)

        print(f"Fetched {len(records)} objects for group: {group.value}")
        return records

    # Handle request timeout
    except requests.exceptions.Timeout:
        print(f"Request timed out for group: {group.value}")

    # Handle HTTP errors (e.g., 404, 500)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error for group {group.value}: {e}")

    # Handle all other request-related errors
    except requests.exceptions.RequestException as e:
        print(f"Request failed for group {group.value}: {e}")

    # Return empty list on failure
    return []