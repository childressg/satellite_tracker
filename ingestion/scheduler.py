from apscheduler.schedulers.blocking import BlockingScheduler
from ingestion.ingest import ingest_group, Group

# Create a blocking scheduler (runs in the main thread)
scheduler = BlockingScheduler()

# List of satellite groups to ingest
# NOTE: Limiting active groups helps avoid MongoDB rate limits
Groups = [
    Group.STATIONS, # ~ 30 entries
    # Group.VISUAL, # ~ 148 entries
    # Group.ANALYST, # ~ 515 entries
    # Group.FENGYUN_1C_DEBRIS, # ~ 1,872 entries
    # Group.IRIDIUM_33_DEBRIS, # ~ 108 entries
    # Group.COSMOS_2251_DEBRIS, # ~ 582 entries
    Group.WEATHER, # ~ 70 entries
    # Group.RESOURCE, # ~ 162 entries
    Group.SARSAT, # ~ 84 entries
    Group.DMC, # ~ 9 entries
    Group.TDRSS, # ~ 26 entries
    Group.ARGOS, # ~ 30 entries
    # Group.PLANET, # ~ 137 entries
    Group.SPIRE, # ~ 76 entries
    # Group.GEO, # ~ 873 entries
    Group.INTELSAT, # ~ 56 entries
    Group.SES, # ~ 70 entries
    Group.EUTELSAT, # ~ 30 entries
    Group.TELESAT, # ~ 18 entries
    # Group.STARLINK, # ~ 10,146 entries
    # Group.ONEWEB, # ~ 651 entries
    # Group.QIANFAN, # ~ 126 entries
    # Group.HULIANWANG, # ~ 159 entries
    # Group.KUIPER, # ~ 238 entries
    Group.IRIDIUM_NEXT, # ~ 80 entries
    Group.ORBCOMM, # ~ 15 entries
    Group.GLOBALSTAR, # ~ 28 entries
    Group.AMATEUR, # ~ 97 entries
    # Group.SATNOGS, # ~ 686 entries
    Group.X_COMM, # ~ 19 entries
    Group.OTHER_COMM, # ~ 28 entries
    # Group.GNSS, # ~ 173 entries
    Group.GPS_OPS, # ~ 32 entries
    Group.GLO_OPS, # ~ 28 entries
    Group.GALILEO, # ~ 33 entries
    Group.BEIDOU, # ~ 54 entries
    Group.SBAS, # ~ 21 entries
    Group.SCIENCE, # ~ 48 entries
    Group.GEODETIC, # ~ 10 entries
    Group.ENGINEERING, # ~ 37 entries
    Group.EDUCATION, # ~ 6 entries
    Group.MILITARY, # ~ 22 entries
    Group.RADAR, # ~ 10 entries
    Group.CUBESAT # ~ 87 entries
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