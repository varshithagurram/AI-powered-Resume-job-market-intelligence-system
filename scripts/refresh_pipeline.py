"""
refresh_pipeline.py

Orchestrates an in-app, automatic daily data refresh: fetch -> clean -> load,
all in one Python call, using the SAME functions as the manual CLI scripts
(fetch_adzuna_jobs.py, clean_data.py, load_to_sql.py) so behavior stays
identical whether triggered manually or automatically.

Used by streamlit_app/app.py to keep a deployed app's data current without
any manual intervention: on each page load, the app checks whether today's
data already exists (via the `scraped_date` column already stored on every
job -- see clean_data.py) and only re-fetches if it's stale or missing.
"""

import json
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from fetch_adzuna_jobs import fetch_role, DEFAULT_ROLES
from clean_data import clean_record
from load_to_sql import init_db, load_csv

DB_PATH = Path("data/job_market.db")
RAW_DIR = Path("data/raw")
PROCESSED_PATH = Path("data/processed/cleaned_job_postings.csv")


def is_data_stale(db_path: Path = DB_PATH) -> bool:
    """Checks the ACTUAL persisted database (not just an in-memory cache),
    so staleness is correctly detected even after an app restart/redeploy.
    Returns True if the database doesn't exist yet, or its most recent
    `scraped_date` isn't today.
    """
    db_path = Path(db_path)  # tolerate a plain string being passed in
    if not db_path.exists():
        return True

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT MAX(scraped_date) FROM jobs").fetchone()
    except sqlite3.OperationalError:
        return True  # table doesn't exist yet
    finally:
        conn.close()

    if not row or not row[0]:
        return True

    return row[0] != date.today().isoformat()


def run_full_refresh(
    app_id: str,
    app_key: str,
    roles: list[str] | None = None,
    country: str = "in",
    results_per_page: int = 20,
    max_pages: int = 2,
) -> dict:
    """Fetches live postings for all roles, cleans them, and loads them into
    the database -- the same three steps as running fetch_adzuna_jobs.py,
    clean_data.py, and load_to_sql.py manually, done in-process in one call.
    """
    roles = roles or DEFAULT_ROLES
    run_date = date.today().isoformat()

    # 1. Fetch
    all_jobs = []
    for role in roles:
        jobs = fetch_role(app_id, app_key, role, country, results_per_page, max_pages)
        for job in jobs:
            job["scraped_date"] = run_date
        all_jobs.extend(jobs)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"adzuna_jobs_{run_date}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False)

    # 2. Clean
    cleaned = [clean_record(r, run_date) for r in all_jobs]
    df = pd.DataFrame(cleaned)
    df = df[df["title"].notna()]
    df["skills_str"] = df["skills"].apply(lambda s: ", ".join(s))

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["skills"]).to_csv(PROCESSED_PATH, index=False)

    # 3. Load
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    loaded_count = load_csv(conn, PROCESSED_PATH)
    conn.close()

    return {
        "run_date": run_date,
        "postings_fetched": len(all_jobs),
        "postings_loaded": loaded_count,
        "roles_requested": len(roles),
    }


def ensure_fresh_data(app_id: str | None, app_key: str | None) -> dict:
    """Called by the Streamlit app on load. Refreshes data only if it's
    stale AND credentials are available; otherwise leaves existing data
    untouched and reports why.
    """
    if not is_data_stale():
        return {"status": "up_to_date"}

    if not app_id or not app_key:
        return {
            "status": "stale_no_credentials",
            "reason": "Data is stale but no Adzuna API credentials are configured.",
        }

    try:
        result = run_full_refresh(app_id, app_key)
        return {"status": "refreshed", **result}
    except Exception as e:
        return {"status": "error", "reason": str(e)}
