from apscheduler.schedulers.blocking import BlockingScheduler
from ingestion.ingest import ingest_group, Group

# Create a blocking scheduler (runs in the main thread)
scheduler = BlockingScheduler()

# List of satellite groups to ingest
# NOTE: Limiting active groups helps avoid MongoDB rate limits
Groups = [
    Group.SPACE_STATIONS,
    # Group.STARLINK,
    Group.GPS,
    Group.WEATHER,
    # Group.GALILEO,
    # Group.GLONASS,
    # Group.BEIDOU,
    # Group.ONEWEB,
    # Group.IRIDIUM_NEXT,
    # Group.CUBESATS,
    # Group.FENGYUN,
]

# Run ingestion for all selected groups
def run_all():
    for group in Groups:
        ingest_group(group)

if __name__ == "__main__":
    print("Starting scheduler - running initial ingest now...")

    # Run immediately on startup (so we don't wait for first interval)
    run_all()

    # Schedule ingestion to run every 90 minutes
    scheduler.add_job(run_all, "interval", minutes=90)

    # Start the scheduler (blocks execution)
    scheduler.start()