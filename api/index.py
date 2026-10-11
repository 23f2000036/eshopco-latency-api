
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import math
import os

app = FastAPI()

# Enable CORS for all origins, including POST and OPTIONS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry.json from the repository root.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "telemetry.json")

with open(DATA_PATH, "r", encoding="utf-8") as file:
    records = json.load(file)


def calculate_p95(values):
    """Calculate the nearest-rank 95th percentile."""
    if not values:
        return 0

    ordered = sorted(values)
    index = math.ceil(0.95 * len(ordered)) - 1
    return ordered[index]


@app.post("/api")
@app.post("/")
async def get_metrics(request: Request):
    body = await request.json()

    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))

    results = []

    for region in regions:
        region_records = [
            record for record in records
            if record.get("region", "").lower() == region.lower()
        ]

        latencies = [
            float(record["latency_ms"])
            for record in region_records
        ]

        uptimes = [
            float(record["uptime_pct"])
            for record in region_records
        ]

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = calculate_p95(latencies)
            avg_uptime = sum(uptimes) / len(uptimes)
            breaches = sum(
                latency > threshold for latency in latencies
            )
        else:
            avg_latency = 0
            p95_latency = 0
            avg_uptime = 0
            breaches = 0

        results.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        })

    return JSONResponse(
        content={"regions": results},
        headers={"Access-Control-Allow-Origin": "*"}
    )
