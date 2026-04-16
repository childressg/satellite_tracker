from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from db.mongo import satellites
from typing import Optional
import uvicorn
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = FastAPI(title="Satellite Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/satellites")
def get_satellites(constellation: Optional[str] = Query(None)):
    query = {}
    if constellation:
        query["constellation"] = constellation

    fields = {
        "_id": 0,
        "NORAD_CAT_ID": 1,
        "OBJECT_NAME": 1,
        "TLE_LINE1": 1,
        "TLE_LINE2": 1,
        "constellation": 1,
    }

    docs = list(satellites.find(query, fields))
    return docs

@app.get("/constellations")
def get_constellations():
    return satellites.distinct("constellation")

@app.get("/health")
def health():
    return {"status": "ok"}

app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "frontend"), html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)