from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from db.mongo import satellites  # MongoDB collection for satellite data
from typing import Optional
import uvicorn
import os

# Get the base directory of the project (used for serving frontend files)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize FastAPI app with a title
app = FastAPI(title="Satellite Tracker API")

# Enable CORS (Cross-Origin Resource Sharing)
# Allows requests from any origin (useful for frontend-backend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains (not recommended for production)
    allow_methods=["GET"],  # Only allow GET requests
    allow_headers=["*"],  # Allow all headers
)

# Endpoint to fetch satellites
# Optional query parameter: constellation (filters satellites by constellation name)
@app.get("/satellites")
def get_satellites(constellation: Optional[str] = Query(None)):
    query = {}

    # If a constellation is provided, filter results
    if constellation:
        query["constellation"] = constellation

    # Define which fields to return (projection)
    fields = {
        "_id": 0,  # Exclude MongoDB internal ID
        "NORAD_CAT_ID": 1,
        "OBJECT_NAME": 1,
        "TLE_LINE1": 1,
        "TLE_LINE2": 1,
        "constellation": 1,
    }

    # Execute query and convert results to a list
    docs = list(satellites.find(query, fields))
    return docs

# Endpoint to get a list of all unique constellations
@app.get("/constellations")
def get_constellations():
    return satellites.distinct("constellation")

# Health check endpoint (useful for monitoring)
@app.get("/health")
def health():
    return {"status": "ok"}

# Serve static frontend files (e.g., HTML, CSS, JS)
# Mounts the frontend directory at the root URL "/"
app.mount(
    "/",
    StaticFiles(directory=os.path.join(BASE_DIR, "frontend"), html=True),
    name="frontend"
)

# Run the app using Uvicorn when executed directly
if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",  # Path to the FastAPI app
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,       # Port number
        reload=True      # Auto-reload on code changes (dev only)
    )