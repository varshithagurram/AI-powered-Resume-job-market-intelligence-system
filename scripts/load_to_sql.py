"""
load_to_sql.py

Creates the SQLite database (if needed) from sql/schema.sql, then loads a
cleaned job postings CSV (from clean_data.py) into the normalized
jobs / skills / job_skills tables.

Usage:
    python load_to_sql.py --input data/processed/cleaned_job_postings.csv
"""

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/job_market.db")
SCHEMA_PATH = Path("sql/schema.sql")


def init_db(conn: sqlite3.Connection):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def get_or_create_skill_id(conn: sqlite3.Connection, skill_name: str) -> int:
    cur = conn.execute("SELECT skill_id FROM skills WHERE skill_name = ?", (skill_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO skills (skill_name) VALUES (?)", (skill_name,))
    return cur.lastrowid


def load_csv(conn: sqlite3.Connection, csv_path: Path):
    df = pd.read_csv(csv_path)
    inserted_jobs = 0

    for _, row in df.iterrows():
        cur = conn.execute(
            """
            INSERT INTO jobs (title, company, location, experience, job_url,
                               search_role, source, scraped_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("title"),
                row.get("company"),
                row.get("location"),
                row.get("experience"),
                row.get("job_url"),
                row.get("search_role"),
                row.get("source"),
                row.get("scraped_date"),
            ),
        )
        job_id = cur.lastrowid
        inserted_jobs += 1

        skills_str = row.get("skills_str")
        if isinstance(skills_str, str) and skills_str.strip():
            for skill_name in [s.strip() for s in skills_str.split(",") if s.strip()]:
                skill_id = get_or_create_skill_id(conn, skill_name)
                conn.execute(
                    "INSERT OR IGNORE INTO job_skills (job_id, skill_id) VALUES (?, ?)",
                    (job_id, skill_id),
                )

    conn.commit()
    return inserted_jobs


def main():
    parser = argparse.ArgumentParser(description="Load cleaned job postings CSV into SQLite")
    parser.add_argument("--input", required=True, help="Path to cleaned CSV from clean_data.py")
    parser.add_argument("--db", default=str(DB_PATH), help="Path to SQLite database file")
    args = parser.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    init_db(conn)

    count = load_csv(conn, Path(args.input))
    print(f"Loaded {count} job postings into {db_path}")

    # quick sanity check
    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    total_skills = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    print(f"Database now has {total_jobs} jobs and {total_skills} distinct skills")

    conn.close()


if __name__ == "__main__":
    main()
