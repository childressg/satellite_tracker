from datetime import datetime, timezone
from pymongo import UpdateOne
from db.mongo import satellites, tle_history
from ingestion.fetch import pull_data, Group

def ingest_group(group: Group):
    records = pull_data(group)
    if not records:
        return

    satellite_ops = []
    history_ops = []

    for record in records:
        norad_id = record["NORAD_CAT_ID"]
        now = datetime.now(timezone.utc)

        # satellites collection: upsert latest TLE
        satellite_ops.append(UpdateOne(
            {"NORAD_CAT_ID": norad_id},
            {"$set": {
                **record,
                "constellation": group.value,
                "ingested_at": now,
            }},
            upsert=True
        ))

        # tle_history: only insert if element set number changed
        last = satellites.find_one(
            {"NORAD_CAT_ID": norad_id},
            {"ELEMENT_SET_NO": 1}
        )
        if last is None or last.get("ELEMENT_SET_NO") != record.get("ELEMENT_SET_NO"):
            history_ops.append({
                **record,
                "constellation": group.value,
                "ingested_at": now,
            })

    if satellite_ops:
        result = satellites.bulk_write(satellite_ops)
        print(f"[{group.value}] upserted: {result.upserted_count} new, {result.modified_count} updated")

    if history_ops:
        tle_history.insert_many(history_ops)
        print(f"[{group.value}] history: {len(history_ops)} new element sets recorded")


if __name__ == "__main__":
    ingest_group(Group.SPACE_STATIONS)