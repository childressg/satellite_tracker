from pymongo import MongoClient, ASCENDING, DESCENDING, GEOSPHERE
from pymongo.collection import Collection
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

satellites: Collection = db["satellites"]
tle_history: Collection = db["tle_history"]

def init_indexes():
    # satellites collection
    satellites.create_index("NORAD_CAT_ID", unique=True)
    satellites.create_index([("constellation", ASCENDING), ("EPOCH", DESCENDING)])

    # tle_history collection
    tle_history.create_index("NORAD_CAT_ID")
    tle_history.create_index(
        "ingested_at",
        expireAfterSeconds = 60 * 60 * 24 * 90 # 90-day TTL
    )

    print("Indexes created.")


if __name__ == "__main__":
    init_indexes()