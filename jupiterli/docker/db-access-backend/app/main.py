import json
import logging

from fastapi import FastAPI
from pydantic import BaseModel

from .config import settings
from .db import get_client

logger = logging.getLogger(__name__)

app = FastAPI(title="db-access-server")

class Run(BaseModel):
    run_id: str
    run_label: str | None


class Series(BaseModel):
    series_id: str
    key: str

class StreamLatestId(BaseModel):
    latest_id: str


class LivePoint(BaseModel):
    stream_id: str
    run_serial_num: int
    timestamp: float
    value: float


class SeriesLive(BaseModel):
    next_after_id: str
    entries: list[LivePoint]


class SeriesHistory(BaseModel):
    timestamps: list[float]
    values: list[float]
    serials: list[int]

@app.get("/api/health")
def health() -> dict:
    get_client().query("SELECT 1")
    return {"ok": True}

@app.get("/api/runs", response_model=list[Run])
def list_runs() -> list[Run]:
    result = get_client().query(
        "SELECT run_id, run_label FROM runs_dets ORDER BY created_ts DESC"
    )
    return [Run(run_id=row[0], run_label=row[1]) for row in result.result_rows]

@app.get("/api/runs/{run_id}/series", response_model=list[Series])
def list_series(run_id: str) -> list[Series]:
    result = get_client().query(
        "SELECT series_id, key FROM series_dets WHERE run_id = %(run_id)s ORDER BY key",
        parameters={"run_id": run_id},
    )
    return [Series(series_id=row[0], key=row[1]) for row in result.result_rows]

@app.get("/api/series/{series_id}/history", response_model=SeriesHistory)
def series_history(series_id: str, max_serial: int | None = None) -> SeriesHistory:
    """One-shot ClickHouse backfill. With max_serial set, returns rows with
    run_serial_num < max_serial (the active-run path: everything older than
    the first live Redis observation). Without it, returns the full series —
    used as a fallback for runs that no longer produce live data."""
    if max_serial is None:
        result = get_client().query(
            """SELECT timestamp, value, run_serial_num
               FROM series
               WHERE series_id = %(series_id)s
               ORDER BY run_serial_num""",
            parameters={"series_id": series_id},
        )
    else:
        result = get_client().query(
            """SELECT timestamp, value, run_serial_num
               FROM series
               WHERE series_id = %(series_id)s AND run_serial_num < %(max_serial)s
               ORDER BY run_serial_num""",
            parameters={"series_id": series_id, "max_serial": max_serial},
        )
    return SeriesHistory(
        timestamps=[float(r[0]) for r in result.result_rows],
        values=[float(r[1]) for r in result.result_rows],
        serials=[int(r[2]) for r in result.result_rows],
    )

@app.post("/api/add-row", status_code = 201)
def add_row(rec: dict):
    print("add_row:", rec)
    rec_type = rec['type']

    if rec_type == 'run':
        table_name = 'runs'
    elif rec_type == 'series':
        table_name = 'series'
    else:
        raise Exception(f"unhandled rec_type {rec_type}")
    
    get_client().insert_rec(table_name, rec)
    return {"status": "OK"}
