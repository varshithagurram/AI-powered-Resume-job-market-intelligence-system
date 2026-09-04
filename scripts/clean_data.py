"""
clean_data.py

Cleans raw job postings (from scraping, Kaggle, or the sample file),
extracts/standardizes skills from title + description text using a skill
taxonomy, and writes a structured table to data/processed/.

Also stamps each record with the date it was processed as `scraped_date`
(or preserves an existing one), so future runs can be compared over time
for weekly trend reporting.

Usage:
    python clean_data.py --input data/raw/sample_job_postings.json
    python clean_data.py --input data/raw/naukri_data_analyst.json
"""

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from skill_taxonomy import extract_skills


def clean_record(record: dict, run_date: str) -> dict:
    # Combine any existing structured skills list with skills detected in
    # the free-text description/title, then dedupe.
    text_blob = " ".join(
        str(record.get(field, "") or "")
        for field in ("title", "description")
    )
    detected_skills = extract_skills(text_blob)
    existing_skills = record.get("skills") or []

    all_skills = sorted(set(existing_skills) | set(detected_skills))

    return {
        "title": (record.get("title") or "").strip() or None,
        "company": (record.get("company") or "").strip() or None,
        "location": (record.get("location") or "").strip() or None,
        "experience": record.get("experience"),
        "skills": all_skills,
        "job_url": record.get("job_url"),
        "search_role": record.get("search_role"),
        "source": record.get("source", "scraped"),
        "scraped_date": record.get("scraped_date") or run_date,
    }


def main():
    parser = argparse.ArgumentParser(description="Clean and standardize job postings")
    parser.add_argument("--input", required=True, help="Path to raw JSON file")
    parser.add_argument(
        "--out",
        default="data/processed/cleaned_job_postings.csv",
        help="Output path for cleaned CSV",
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        raw_records = json.load(f)

    run_date = date.today().isoformat()
    cleaned = [clean_record(r, run_date) for r in raw_records]

    df = pd.DataFrame(cleaned)

    # Drop rows with no title at all — not usable
    before = len(df)
    df = df[df["title"].notna()]
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} record(s) with no title")

    # skills column: store as a comma-separated string for CSV portability
    # (job_skills table in SQL will normalize this into one row per skill)
    df["skills_str"] = df["skills"].apply(lambda s: ", ".join(s))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["skills"]).to_csv(out_path, index=False)

    print(f"Cleaned {len(df)} job postings -> {out_path}")
    print(f"\nSkill frequency in this batch:")
    skill_counts = pd.Series([s for skills in df["skills_str"] for s in skills.split(", ") if s]).value_counts()
    print(skill_counts.to_string())


if __name__ == "__main__":
    main()
