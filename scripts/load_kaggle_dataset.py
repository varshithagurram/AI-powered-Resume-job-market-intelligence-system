"""
load_kaggle_dataset.py

Fallback data source: loads a public Kaggle job-postings dataset and
normalizes it into the same schema the Naukri scraper produces, so
downstream cleaning/matching code works regardless of data source.

Setup:
    1. pip install kaggle
    2. Place your kaggle.json API token in ~/.kaggle/kaggle.json
       (get it from https://www.kaggle.com/settings -> API -> Create New Token)
    3. Run: python load_kaggle_dataset.py

Recommended dataset (LinkedIn/Indeed-style job postings with skills):
    https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
(You can swap DATASET_SLUG below for any similar postings dataset.)
"""

import json
import subprocess
from pathlib import Path

import pandas as pd

DATASET_SLUG = "arshkon/linkedin-job-postings"
DOWNLOAD_DIR = Path("data/raw/kaggle_download")
OUTPUT_PATH = Path("data/raw/kaggle_job_postings.json")


def download_dataset():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {DATASET_SLUG} via Kaggle API...")
    subprocess.run(
        [
            "kaggle", "datasets", "download",
            "-d", DATASET_SLUG,
            "-p", str(DOWNLOAD_DIR),
            "--unzip",
        ],
        check=True,
    )
    print("Download complete.")


def normalize_to_schema(df: pd.DataFrame) -> list[dict]:
    """Map dataset columns to the common job-posting schema used across
    this project: title, company, location, experience, skills, job_url.

    NOTE: column names vary by dataset version — check df.columns after
    downloading and adjust the mapping below if needed.
    """
    records = []
    for _, row in df.iterrows():
        records.append({
            "title": row.get("title"),
            "company": row.get("company_name"),
            "location": row.get("location"),
            "experience": None,  # not always present in this dataset
            "skills": [],         # filled in during the Day 3 cleaning step
            "job_url": row.get("job_posting_url"),
            "description": row.get("description"),
            "search_role": None,
            "source": "kaggle",
        })
    return records


def main():
    if not DOWNLOAD_DIR.exists() or not any(DOWNLOAD_DIR.glob("*.csv")):
        download_dataset()

    csv_files = list(DOWNLOAD_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV found in {DOWNLOAD_DIR} after download.")

    # Use the largest CSV (main postings file) if multiple are bundled
    main_csv = max(csv_files, key=lambda p: p.stat().st_size)
    print(f"Loading {main_csv}...")
    df = pd.read_csv(main_csv)
    print(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    records = normalize_to_schema(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(records)} normalized job postings to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
