from pymongo import MongoClient, ASCENDING, DESCENDING, GEOSPHERE
from pymongo.collection import Collection
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve MongoDB connection details from environment
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# Create MongoDB client and connect to database
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Define collections with type hints for better IDE support
satellites: Collection = db["satellites"]
tle_history: Collection = db["tle_history"]

def init_indexes():
    """
    Create indexes for collections to improve query performance
    and enforce constraints.
    """

    # ---- satellites collection indexes ----

    # Ensure each satellite (NORAD ID) is unique
    satellites.create_index("NORAD_CAT_ID", unique=True)

    # Compound index:
    # - constellation (ascending) for filtering
    # - EPOCH (descending) for getting most recent data quickly
    satellites.create_index([("constellation", ASCENDING), ("EPOCH", DESCENDING)])

    # ---- tle_history collection indexes ----

    # Index for querying history by satellite ID
    tle_history.create_index("NORAD_CAT_ID")

    # TTL (Time-To-Live) index:
    # Automatically deletes documents after 7 days
    tle_history.create_index(
        "ingested_at",
        expireAfterSeconds=60 * 60 * 24 * 7  # 7 days in seconds
    )

    print("Indexes created.")


# Run index initialization if this file is executed directly
if __name__ == "__main__":
    init_indexes()