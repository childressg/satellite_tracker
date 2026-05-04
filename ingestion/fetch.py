import requests
from enum import Enum

# Base URL for CelesTrak GP (General Perturbations) TLE data
BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"

# Enum representing available satellite groups on CelesTrak
class Group(Enum):
    STATIONS          = "stations"
    VISUAL            = "visual"
    ANALYST           = "analyst"
    FENGYUN_1C_DEBRIS = "fengyun-1c-debris"
    IRIDIUM_33_DEBRIS = "iridium-33-debris"
    COSMOS_2251_DEBRIS= "cosmos-2251-debris"
    WEATHER           = "weather"
    RESOURCE          = "resource"
    SARSAT            = "sarsat"
    DMC               = "dmc"
    TDRSS             = "tdrss"
    ARGOS             = "argos"
    PLANET            = "planet"
    SPIRE             = "spire"
    GEO               = "geo"
    INTELSAT          = "intelsat"
    SES               = "ses"
    EUTELSAT          = "eutelsat"
    TELESAT           = "telesat"
    STARLINK          = "starlink"
    ONEWEB            = "oneweb"
    QIANFAN           = "qianfan"
    HULIANWANG        = "hulianwang"
    KUIPER            = "kuiper"
    IRIDIUM_NEXT      = "iridium-NEXT"
    ORBCOMM           = "orbcomm"
    GLOBALSTAR        = "globalstar"
    AMATEUR           = "amateur"
    SATNOGS           = "satnogs"
    X_COMM            = "x-comm"
    OTHER_COMM        = "other-comm"
    GNSS              = "gnss"
    GPS_OPS           = "gps-ops"
    GLO_OPS           = "glo-ops"
    GALILEO           = "galileo"
    BEIDOU            = "beidou"
    SBAS              = "sbas"
    SCIENCE           = "science"
    GEODETIC          = "geodetic"
    ENGINEERING       = "engineering"
    EDUCATION         = "education"
    MILITARY          = "military"
    RADAR             = "radar"
    CUBESAT           = "cubesat"


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
        response = requests.get(url, timeout=100)
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