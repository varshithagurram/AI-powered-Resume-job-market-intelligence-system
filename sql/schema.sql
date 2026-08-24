-- schema.sql
-- Core schema for the Resume-Job Market Intelligence System.
--
-- Design notes:
-- - `jobs` and `skills` are normalized (many-to-many via `job_skills`)
--   so we can query "most in-demand skills" without string-parsing a
--   comma-separated column every time.
-- - `scraped_date` on `jobs` is what enables weekly trend comparisons
--   later (Day 5 queries, Power BI trend charts).
-- - Works as-is on SQLite; swap AUTOINCREMENT -> SERIAL/IDENTITY if
--   moving to PostgreSQL.

DROP TABLE IF EXISTS job_skills;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS skills;

CREATE TABLE jobs (
    job_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    company       TEXT,
    location      TEXT,
    experience    TEXT,
    job_url       TEXT,
    search_role   TEXT,       -- the role this posting was collected under (e.g. "data analyst")
    source        TEXT,       -- 'naukri', 'kaggle', 'sample'
    scraped_date  TEXT NOT NULL   -- ISO date (YYYY-MM-DD); enables weekly trend queries
);

CREATE TABLE skills (
    skill_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name    TEXT NOT NULL UNIQUE
);

CREATE TABLE job_skills (
    job_id        INTEGER NOT NULL,
    skill_id      INTEGER NOT NULL,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);

CREATE INDEX idx_jobs_scraped_date ON jobs(scraped_date);
CREATE INDEX idx_jobs_search_role ON jobs(search_role);
CREATE INDEX idx_job_skills_skill_id ON job_skills(skill_id);
