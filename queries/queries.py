from db.mongo import db
import math

satellites   = db["satellites"]
tle_history  = db["tle_history"]
constellations = db["constellations"]

# ── Orbital mechanics constants ───────────────────────────────────────────────
MU    = 3.986004418e14  # Earth's gravitational parameter (m^3/s^2)
R_E   = 6371.0          # Earth's mean radius (km)


def mean_motion_to_altitude_km(mean_motion_rev_per_day):
    """Convert TLE mean motion (rev/day) to orbital altitude (km)."""
    n    = mean_motion_rev_per_day * 2 * math.pi / 86400  # rad/s
    a    = (MU / (n ** 2)) ** (1/3)                        # semi-major axis (m)
    return (a / 1000) - R_E                                # altitude (km)


# ── Query 1: Satellite count per constellation (descending) ───────────────────
def q1_satellite_count_per_constellation():
    """
    Equivalent SQL:
    SELECT constellation, COUNT(*) as count
    FROM satellites
    GROUP BY constellation
    ORDER BY count DESC
    """
    print("\n=== Q1: Satellite Count per Constellation ===")
    pipeline = [
        {"$group": {
            "_id":   "$constellation",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$project": {
            "_id":           0,
            "constellation": "$_id",
            "count":         1
        }}
    ]
    results = list(satellites.aggregate(pipeline))
    for r in results:
        print(f"  {r['constellation']:<25} {r['count']:>6} satellites")
    return results


# ── Query 2: Enrich satellites with constellation metadata ($lookup join) ─────
def q2_satellites_with_metadata():
    """
    Equivalent SQL:
    SELECT s.OBJECT_NAME, s.constellation, c.full_name, c.operator,
           c.country, c.purpose, c.orbit_type
    FROM satellites s
    JOIN constellations c ON s.constellation = c.constellation_id
    LIMIT 10
    """
    print("\n=== Q2: Satellites Enriched with Constellation Metadata ($lookup) ===")
    pipeline = [
        {"$lookup": {
            "from":         "constellations",
            "localField":   "constellation",
            "foreignField": "constellation_id",
            "as":           "meta"
        }},
        {"$unwind": "$meta"},
        {"$project": {
            "_id":          0,
            "OBJECT_NAME":  1,
            "constellation": 1,
            "full_name":    "$meta.full_name",
            "operator":     "$meta.operator",
            "country":      "$meta.country",
            "purpose":      "$meta.purpose",
            "orbit_type":   "$meta.orbit_type",
        }},
        {"$limit": 10}
    ]
    results = list(satellites.aggregate(pipeline))
    for r in results:
        print(f"  {r['OBJECT_NAME']:<30} | {r['full_name']:<35} | {r['country']}")
    return results


# ── Query 3: Altitude distribution bucketed by orbit regime ───────────────────
def q3_altitude_distribution():
    """
    Derives altitude from MEAN_MOTION using Kepler's third law,
    then buckets satellites into LEO / MEO / GEO / HEO.

    Equivalent SQL:
    SELECT
      CASE
        WHEN altitude < 2000  THEN 'LEO'
        WHEN altitude < 35786 THEN 'MEO'
        WHEN altitude < 36786 THEN 'GEO'
        ELSE 'HEO'
      END as regime,
      COUNT(*) as count, AVG(altitude) as avg_altitude
    FROM satellites
    GROUP BY regime
    """
    print("\n=== Q3: Altitude Distribution by Orbit Regime ===")

    # Pull mean motion for all satellites
    docs = list(satellites.find({}, {"_id": 0, "MEAN_MOTION": 1}))

    buckets = {"LEO (0–2,000 km)": [], "MEO (2,000–35,786 km)": [],
               "GEO (~35,786 km)": [], "HEO (>36,786 km)": []}

    for doc in docs:
        mm = doc.get("MEAN_MOTION")
        if not mm:
            continue
        alt = mean_motion_to_altitude_km(mm)
        if alt < 2000:
            buckets["LEO (0–2,000 km)"].append(alt)
        elif alt < 35786:
            buckets["MEO (2,000–35,786 km)"].append(alt)
        elif alt < 36786:
            buckets["GEO (~35,786 km)"].append(alt)
        else:
            buckets["HEO (>36,786 km)"].append(alt)

    results = []
    for label, alts in buckets.items():
        avg = sum(alts) / len(alts) if alts else 0
        print(f"  {label:<25} {len(alts):>6} satellites  |  avg alt: {avg:.0f} km")
        results.append({"regime": label, "count": len(alts), "avg_altitude_km": avg})

    return results


# ── Query 4: Expected vs actual satellite count per constellation ──────────────
def q4_expected_vs_actual():
    """
    Compares live satellite counts in the satellites collection
    against the expected_count stored in the constellations collection.

    Equivalent SQL:
    SELECT c.constellation_id, c.expected_count, COUNT(s.*) as actual_count,
           COUNT(s.*) - c.expected_count as delta
    FROM constellations c
    LEFT JOIN satellites s ON c.constellation_id = s.constellation
    GROUP BY c.constellation_id
    ORDER BY delta DESC
    """
    print("\n=== Q4: Expected vs Actual Satellite Count per Constellation ===")
    pipeline = [
        {"$lookup": {
            "from":         "satellites",
            "localField":   "constellation_id",
            "foreignField": "constellation",
            "as":           "sats"
        }},
        {"$project": {
            "_id":            0,
            "constellation":  "$constellation_id",
            "full_name":      1,
            "expected_count": 1,
            "actual_count":   {"$size": "$sats"},
            "delta":          {"$subtract": [{"$size": "$sats"}, "$expected_count"]}
        }},
        {"$sort": {"actual_count": -1}}
    ]
    results = list(constellations.aggregate(pipeline))
    for r in results:
        delta = r["delta"]
        flag  = "✓" if abs(delta) < 10 else ("▲" if delta > 0 else "▼")
        print(f"  {r['constellation']:<25} expected: {r['expected_count']:>6}  actual: {r['actual_count']:>6}  delta: {delta:>+6}  {flag}")
    return results


# ── Query 5: Average inclination by orbit type (via $lookup) ──────────────────
def q5_avg_inclination_by_orbit_type():
    """
    Joins satellites with constellation metadata to get orbit_type,
    then computes average inclination per orbit type.

    Equivalent SQL:
    SELECT c.orbit_type, AVG(s.INCLINATION) as avg_inclination,
           MIN(s.INCLINATION) as min_inc, MAX(s.INCLINATION) as max_inc
    FROM satellites s
    JOIN constellations c ON s.constellation = c.constellation_id
    GROUP BY c.orbit_type
    ORDER BY avg_inclination DESC
    """
    print("\n=== Q5: Average Inclination by Orbit Type ===")
    pipeline = [
        {"$lookup": {
            "from":         "constellations",
            "localField":   "constellation",
            "foreignField": "constellation_id",
            "as":           "meta"
        }},
        {"$unwind": "$meta"},
        {"$group": {
            "_id":           "$meta.orbit_type",
            "avg_inc":       {"$avg": "$INCLINATION"},
            "min_inc":       {"$min": "$INCLINATION"},
            "max_inc":       {"$max": "$INCLINATION"},
            "sat_count":     {"$sum": 1}
        }},
        {"$sort": {"avg_inc": -1}},
        {"$project": {
            "_id": 0,
            "orbit_type": "$_id",
            "avg_inc": 1,
            "min_inc": 1,
            "max_inc": 1,
            "sat_count": 1
        }}
    ]
    results = list(satellites.aggregate(pipeline))
    for r in results:
        avg = r["avg_inc"] or 0
        mn = r["min_inc"] or 0
        mx = r["max_inc"] or 0
        print(f"  {r['orbit_type']:<15} avg: {avg:>7.2f}°  "
              f"min: {mn:>7.2f}°  max: {mx:>7.2f}°  "
              f"({r['sat_count']} sats)")
    return results


# ── Query 6: TLE update frequency by constellation (last 7 days) ──────────────
def q6_tle_update_frequency():
    """
    Analyzes tle_history to show which constellations have the most
    orbital element set changes — a proxy for active maneuvering.

    Equivalent SQL:
    SELECT constellation, COUNT(*) as total_updates,
           COUNT(DISTINCT NORAD_CAT_ID) as unique_sats,
           COUNT(*) / COUNT(DISTINCT NORAD_CAT_ID) as updates_per_sat
    FROM tle_history
    GROUP BY constellation
    ORDER BY updates_per_sat DESC
    """
    print("\n=== Q6: TLE Update Frequency by Constellation (History) ===")
    pipeline = [
        {"$group": {
            "_id":          "$constellation",
            "total_updates": {"$sum": 1},
            "unique_sats":  {"$addToSet": "$NORAD_CAT_ID"}
        }},
        {"$project": {
            "_id":             0,
            "constellation":   "$_id",
            "total_updates":   1,
            "unique_sat_count": {"$size": "$unique_sats"},
            "updates_per_sat": {
                "$round": [
                    {"$divide": ["$total_updates", {"$size": "$unique_sats"}]},
                    2
                ]
            }
        }},
        {"$sort": {"updates_per_sat": -1}}
    ]
    results = list(tle_history.aggregate(pipeline))
    for r in results:
        print(f"  {r['constellation']:<25} total updates: {r['total_updates']:>5}  "
              f"unique sats: {r['unique_sat_count']:>5}  "
              f"updates/sat: {r['updates_per_sat']:>5}")
    return results


# ── Run all queries ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    q1_satellite_count_per_constellation()
    q2_satellites_with_metadata()
    q3_altitude_distribution()
    q4_expected_vs_actual()
    q5_avg_inclination_by_orbit_type()
    q6_tle_update_frequency()