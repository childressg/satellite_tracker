from db.mongo import db

# Reference to the constellations collection
constellations = db["constellations"]

# ── Constellation Metadata ────────────────────────────────────────────────────
# Each document corresponds to one CelesTrak satellite group.
# constellation_id matches the 'constellation' field in the satellites
# collection — this is the foreign key used by $lookup joins.
# expected_count reflects observed CelesTrak group sizes at time of writing.

CONSTELLATION_DATA = [
    # ── Special Interest ──────────────────────────────────────────────────────
    {
        "constellation_id":  "stations",
        "full_name":         "Space Stations",
        "operator":          "Multiple (NASA, Roscosmos, CNSA)",
        "country":           "International",
        "purpose":           "Human Spaceflight & Research",
        "orbit_type":        "LEO",
        "expected_count":    30,
        "operational_since": 1998,
        "website":           "https://www.nasa.gov/international-space-station"
    },
    # ... (rest of CONSTELLATION_DATA unchanged)
]


def seed_constellations():
    """
    Insert constellation metadata documents if the collection is empty.

    Creates a unique index on constellation_id before inserting to enforce
    referential integrity with the satellites collection. Safe to call
    multiple times — skips insertion if documents already exist.
    """
    existing = constellations.count_documents({})
    if existing > 0:
        print(f"Constellations collection already has {existing} documents — skipping seed.")
        return

    # Unique index on constellation_id enforces one document per group
    # and enables efficient $lookup joins from the satellites collection
    constellations.create_index("constellation_id", unique=True)

    result = constellations.insert_many(CONSTELLATION_DATA)
    print(f"Seeded {len(result.inserted_ids)} constellation documents.")


if __name__ == "__main__":
    seed_constellations()