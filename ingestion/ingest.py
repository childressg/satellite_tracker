from datetime import datetime, timezone
from pymongo import UpdateOne
from db.mongo import satellites, tle_history
from ingestion.fetch import pull_data, Group

# Ingest TLE data for a specific satellite group
def ingest_group(group: Group):
    # Fetch latest TLE records from CelesTrak
    records = pull_data(group)
    if not records:
        return  # Exit early if no data retrieved

    satellite_ops = []  # Bulk operations for satellites collection
    history_ops = []    # Documents to insert into tle_history

    for record in records:
        norad_id = record["NORAD_CAT_ID"]
        now = datetime.now(timezone.utc)  # Current UTC timestamp

        # ── satellites collection ──────────────────────────────────────────────
        # Upsert (insert or update) the latest TLE for each satellite
        satellite_ops.append(UpdateOne(
            {"NORAD_CAT_ID": norad_id},  # Match by NORAD ID
            {"$set": {
                **record,
                "constellation": group.value,
                "ingested_at": now,
            }},
            upsert=True
        ))

        # ── tle_history collection ─────────────────────────────────────────────
        # Only store a new history record if the TLE has changed
        last = satellites.find_one(
            {"NORAD_CAT_ID": norad_id},
            {"ELEMENT_SET_NO": 1}  # (Note: not currently used below)
        )

        # Compare TLE_LINE1 to detect changes in orbital data
        if last is None or last.get("TLE_LINE1") != record.get("TLE_LINE1"):
            history_ops.append({
                **record,
                "constellation": group.value,
                "ingested_at": now,
            })

    # Execute bulk upserts for satellites collection
    if satellite_ops:
        result = satellites.bulk_write(satellite_ops)
        print(f"[{group.value}] upserted: {result.upserted_count} new, {result.modified_count} updated")

    # Insert new historical TLE records
    if history_ops:
        tle_history.insert_many(history_ops)
        print(f"[{group.value}] history: {len(history_ops)} new element sets recorded")


# Run ingestion for space stations if script is executed directly
if __name__ == "__main__":
    ingest_group(Group.SPACE_STATIONS)