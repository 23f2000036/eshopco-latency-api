
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import math
import os

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)

data_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "telemetry.json"
)

with open(data_path, encoding="utf-8") as f:
    records = json.load(f)


@app.post("/")
@app.post("/api")
async def get_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))

    result = []

    for region in regions:
        rows = [
            r for r in records
            if r["region"].lower() == region.lower()
        ]

        latencies = sorted(
            float(r["latency_ms"]) for r in rows
        )
        uptimes = [
            float(r["uptime_pct"]) for r in rows
        ]

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = latencies[
                math.ceil(0.95 * len(latencies)) - 1
            ]
            avg_uptime = sum(uptimes) / len(uptimes)
            breaches = sum(x > threshold for x in latencies)
        else:
            avg_latency = 0
            p95_latency = 0
            avg_uptime = 0
            breaches = 0

        result.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        })

    return {"regions": result}
