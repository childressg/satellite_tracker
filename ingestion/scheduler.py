from apscheduler.schedulers.blocking import BlockingScheduler
from ingestion.ingest import ingest_group, Group

scheduler = BlockingScheduler()

TIER_1 = [
    Group.SPACE_STATIONS,
]

def run_all():
    for group in TIER_1:
        ingest_group(group)

if __name__ == "__main__":
    print("Starting scheduler - running initial ingest now...")
    run_all() # run immediately on startup, don't wait 90 min for first ingest

    scheduler.add_job(run_all, "interval", minutes=90)
    scheduler.start()