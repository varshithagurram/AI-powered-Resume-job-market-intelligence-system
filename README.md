# AI-Powered Resume-Job Market Intelligence System

## Problem Statement
Job seekers often don't know how well their resume actually matches the roles
they're applying for, which skills are most in-demand for a target role, or
what to learn next to become a stronger candidate. This project analyzes real
job postings to answer those questions directly, and scores a candidate's
resume against live market demand.

## What It Does
Given a resume and a target role (e.g. "Data Analyst"), the system returns:
- An overall **match score** (e.g. 78%)
- **Strong skills** already present in the resume that match the role
- **Missing/weak skills** preventing a stronger match
- **Most in-demand skills** in current job listings, ranked
- A **recommended next skill** to learn
- **Match % across multiple related roles** (e.g. Data Analyst, BI Analyst,
  Business Analyst, Data Scientist)

Stretch goal: continuously scrape new postings and generate a weekly
skill-demand report showing how the market is shifting over time.

## Tech Stack
- **Python** — scraping, resume parsing, NLP/embeddings-based matching
- **SQL** (PostgreSQL/SQLite) — stores job postings, skills, and salary data;
  powers demand and trend queries
- **Power BI** — market trend dashboard (skill demand, trends over time,
  salary by role/location)
- **Streamlit** — interactive app for resume upload and live match results

## Project Structure
```
resume-job-market-intelligence/
├── data/
│   ├── raw/              # Raw scraped/downloaded job posting data
│   └── processed/        # Cleaned, structured data
├── scripts/               # Scraping, cleaning, parsing, matching scripts
├── sql/                   # Schema and analysis queries
├── streamlit_app/          # Streamlit application
├── notebooks/              # Exploration / prototyping notebooks
├── requirements.txt
└── README.md
```

## Data Collection

Two data sources are supported, producing the same normalized schema
(`title`, `company`, `location`, `experience`, `skills`, `job_url`,
`description`):

1. **`scripts/scrape_naukri.py`** — scrapes live Naukri.com listings.
   Run locally (not from a restricted/cloud sandbox — job boards block
   many datacenter IPs):
   ```bash
   python scripts/scrape_naukri.py --role "data analyst" --pages 5
   ```
   Naukri's HTML structure changes periodically — if it returns 0 results,
   inspect the page and update the CSS selectors in `parse_job_cards()`.

2. **`scripts/load_kaggle_dataset.py`** — fallback/supplement using a public
   Kaggle job-postings dataset. Requires a Kaggle API token
   (`~/.kaggle/kaggle.json`):
   ```bash
   pip install kaggle
   python scripts/load_kaggle_dataset.py
   ```

`data/raw/sample_job_postings.json` is a small hand-written sample (5 jobs)
used to test the cleaning/matching pipeline end-to-end before real scraped
data is available.

## Data Cleaning & Skill Extraction

`scripts/clean_data.py` takes any raw JSON postings file (scraped, Kaggle,
or the sample data) and:
- Extracts skills from the job title + description using a regex-based
  skill taxonomy (`SKILL_TAXONOMY` in the script — extend this list as new
  skills show up in real data)
- Merges detected skills with any structured `skills` field already present
- Stamps each record with a `scraped_date` (preserves it if already set) —
  this is what will let future weekly batches be compared over time
- Outputs a clean CSV to `data/processed/`

```bash
python scripts/clean_data.py --input data/raw/sample_job_postings.json
```

## Database

`sql/schema.sql` defines a normalized SQLite schema:
- `jobs` — one row per posting, includes `scraped_date` for trend tracking
- `skills` — distinct skill names
- `job_skills` — many-to-many link between jobs and skills

`scripts/load_to_sql.py` creates the database (if needed) and loads a
cleaned CSV into it:

```bash
python scripts/load_to_sql.py --input data/processed/cleaned_job_postings.csv
```

This produces `data/job_market.db`, which SQL analysis queries (Day 5) and
Power BI (Day 10) will both read from.

## Analysis Queries

`sql/analysis_queries.sql` contains the SQL that powers the core insights:
- Most in-demand skills overall and per target role
- Skill demand trend over time (grouped by `scraped_date`)
- Skill co-occurrence (which skills commonly appear together in the same posting)
- Salary ranges by role/location (template query — activates once real
  scraped data includes salary fields)
- Which roles most value a given skill

Run these directly against `data/job_market.db` with any SQLite client, or
via Python (`sqlite3` / `pandas.read_sql`). These same queries will back
the Power BI dashboard (Day 10).

## Resume Parsing

`scripts/parse_resume.py` extracts structured data from a candidate's
resume (PDF or DOCX):
- Candidate name (via spaCy PERSON entity recognition)
- Years of experience (regex pattern matching)
- Skills — uses the **same skill taxonomy** as `clean_data.py`, so resume
  skills and job posting skills are extracted identically and can be
  directly compared in the matching engine (Day 7)

```bash
python scripts/parse_resume.py --input path/to/resume.pdf
python scripts/parse_resume.py --input path/to/resume.docx --out data/sample_resumes/parsed.json
```

`data/sample_resumes/sample_resume.docx` is a hand-written test resume used
to verify the parser end-to-end.

## Matching Engine

`scripts/match_engine.py` compares a parsed resume against a target role's
aggregated skill profile (built from all postings collected under that
`search_role` in the database) and returns:
- An overall **match score** (0-100%), blending semantic text similarity
  with the skills-overlap ratio
- **Strong skills** — present in both resume and role
- **Missing skills** — required by the role, absent from the resume

Two similarity backends:
- `embeddings` (default) — Sentence-BERT (`all-MiniLM-L6-v2`) cosine
  similarity. Captures semantic matches beyond exact keyword overlap.
  Requires internet access to download the model on first run — run
  locally, not from a restricted sandbox.
- `tfidf` — scikit-learn TF-IDF + cosine similarity. Fully offline, used
  as a fast baseline/comparison.

```bash
python scripts/match_engine.py --resume data/sample_resumes/parsed_sample_resume.json --role "data analyst" --backend embeddings
python scripts/match_engine.py --resume data/sample_resumes/parsed_sample_resume.json --role "data analyst" --backend tfidf
```

**Note on sample data:** with only a handful of sample postings per role,
per-role match scores can look skewed (e.g. a role with just 1 posting
can hit 100% skill overlap by chance). This is a small-sample artifact,
not a bug in the matching logic — it self-corrects once real scraped/Kaggle
data with many postings per role is loaded.

## Status
🚧 In progress — building incrementally. See commit history for day-by-day
progress.

## Roadmap
- [x] Data collection (job postings scraper)
- [x] Data cleaning and skill extraction
- [x] SQL database design and loading
- [x] SQL trend/demand queries
- [x] Resume parser
- [x] Matching engine (embeddings-based)
- [ ] Multi-role matching and recommendations
- [ ] Streamlit app
- [ ] Power BI dashboard
- [ ] Final polish and deployment
