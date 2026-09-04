"""
fetch_adzuna_jobs.py

Fetches live job postings from the Adzuna API (https://developer.adzuna.com/)
for a list of target roles. This is the PRIMARY data source -- more
reliable than scraping since it's a legitimate API that won't randomly
block you the way Naukri/Indeed's anti-bot protection does.

Setup (one-time, free):
    1. Sign up at https://developer.adzuna.com/
    2. Get your app_id and app_key from the dashboard
    3. Set them as environment variables (recommended, keeps keys out of
       git) or pass via --app-id / --app-key:

       Windows PowerShell:
           $env:ADZUNA_APP_ID="your_id"
           $env:ADZUNA_APP_KEY="your_key"
       Mac/Linux:
           export ADZUNA_APP_ID="your_id"
           export ADZUNA_APP_KEY="your_key"

Usage:
    python fetch_adzuna_jobs.py --roles "data analyst" "business analyst" "data scientist" "bi analyst" "data engineer"
    python fetch_adzuna_jobs.py --roles "data analyst" --country in --results 50
"""

import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

import requests

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

# Default role coverage: data/analytics roles (the project's core focus)
# plus general tech and cross-functional business roles, for broad market
# coverage. Extendable via --roles.
DEFAULT_ROLES = [
    # Data & analytics roles
    "data analyst",
    "business analyst",
    "bi analyst",
    "data scientist",
    "data engineer",
    "business intelligence developer",
    "product analyst",
    "marketing analyst",
    "financial analyst",
    "reporting analyst",
    "machine learning engineer",
    "analytics consultant",
    # General tech roles
    "software engineer",
    "full stack developer",
    "backend developer",
    "frontend developer",
    "product manager",
    "devops engineer",
    "qa engineer",
    "ui ux designer",
    "mobile app developer",
    "network engineer",
    "cybersecurity analyst",
    "it support specialist",
    # Marketing & sales
    "digital marketing manager",
    "seo specialist",
    "sales executive",
    "content marketing manager",
    # HR
    "hr manager",
    "talent acquisition specialist",
    # Operations & project management
    "operations manager",
    "supply chain analyst",
    "project manager",
    "customer success manager",
]


def fetch_role(app_id: str, app_key: str, role: str, country: str, results_per_page: int, max_pages: int = 2) -> list[dict]:
    all_jobs = []
    for page in range(1, max_pages + 1):
        url = ADZUNA_BASE_URL.format(country=country, page=page)
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": results_per_page,
            "what": role,
            "content-type": "application/json",
        }
        print(f"Fetching '{role}' page {page}...")
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Failed: {e}")
            break

        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        for job in results:
            all_jobs.append({
                "title": job.get("title"),
                "company": (job.get("company") or {}).get("display_name"),
                "location": (job.get("location") or {}).get("display_name"),
                "experience": None,  # Adzuna doesn't provide this directly
                "skills": [],         # filled in during clean_data.py's skill extraction
                "job_url": job.get("redirect_url"),
                "description": job.get("description"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "search_role": role,
                "source": "adzuna",
            })

        time.sleep(1)  # be polite to the API

    return all_jobs


def main():
    parser = argparse.ArgumentParser(description="Fetch live job postings from the Adzuna API")
    parser.add_argument("--roles", nargs="+", default=DEFAULT_ROLES, help="List of target roles to fetch")
    parser.add_argument("--country", default="in", help="Adzuna country code (in = India, us, gb, etc.)")
    parser.add_argument("--results", type=int, default=20, help="Results per page (max 50)")
    parser.add_argument("--app-id", default=os.environ.get("ADZUNA_APP_ID"), help="Adzuna app_id (or set ADZUNA_APP_ID env var)")
    parser.add_argument("--app-key", default=os.environ.get("ADZUNA_APP_KEY"), help="Adzuna app_key (or set ADZUNA_APP_KEY env var)")
    parser.add_argument("--out", default="data/raw", help="Output directory for raw JSON")
    args = parser.parse_args()

    if not args.app_id or not args.app_key:
        raise SystemExit(
            "Missing Adzuna credentials. Sign up free at https://developer.adzuna.com/, "
            "then set ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables, or pass "
            "--app-id / --app-key directly."
        )

    run_date = date.today().isoformat()
    all_jobs = []
    for role in args.roles:
        jobs = fetch_role(args.app_id, args.app_key, role, args.country, args.results)
        for job in jobs:
            job["scraped_date"] = run_date
        print(f"  Got {len(jobs)} postings for '{role}'")
        all_jobs.extend(jobs)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"adzuna_jobs_{run_date}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_jobs)} total job postings to {out_path}")


if __name__ == "__main__":
    main()
