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

## Status
🚧 In progress — building incrementally. See commit history for day-by-day
progress.

## Roadmap
- [ ] Data collection (job postings scraper)
- [ ] Data cleaning and skill extraction
- [ ] SQL database design and loading
- [ ] SQL trend/demand queries
- [ ] Resume parser
- [ ] Matching engine (embeddings-based)
- [ ] Multi-role matching and recommendations
- [ ] Streamlit app
- [ ] Power BI dashboard
- [ ] Final polish and deployment
