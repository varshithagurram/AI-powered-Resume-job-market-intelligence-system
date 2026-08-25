-- analysis_queries.sql
-- Reusable analysis queries for the Resume-Job Market Intelligence System.
-- Run against data/job_market.db (SQLite).
--
-- These are the queries that power:
--   - "most demanded skills" (README requirement #1)
--   - "skill combinations employers commonly request" (#3)
--   - "salary ranges by skill/role/location" (#4) -- needs a salary column
--     populated in `jobs`; currently NULL in sample data, query still works
--   - skill trend over time once multiple scraped_date batches exist (#2)


-- 1. Most in-demand skills overall
SELECT
    s.skill_name,
    COUNT(*) AS demand_count
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
GROUP BY s.skill_name
ORDER BY demand_count DESC;


-- 2. Most in-demand skills for a specific target role (e.g. 'data analyst')
SELECT
    s.skill_name,
    COUNT(*) AS demand_count
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
JOIN jobs j ON js.job_id = j.job_id
WHERE j.search_role = 'data analyst'
GROUP BY s.skill_name
ORDER BY demand_count DESC;


-- 3. Skill demand trend over time (per scraped_date batch)
-- Once multiple weekly batches exist, this shows week-over-week movement.
SELECT
    j.scraped_date,
    s.skill_name,
    COUNT(*) AS demand_count
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
JOIN jobs j ON js.job_id = j.job_id
GROUP BY j.scraped_date, s.skill_name
ORDER BY j.scraped_date, demand_count DESC;


-- 4. Skill co-occurrence: which skill pairs commonly appear together
-- (self-join job_skills on job_id, skill_id_a < skill_id_b to avoid duplicates/reversed pairs)
SELECT
    sa.skill_name AS skill_a,
    sb.skill_name AS skill_b,
    COUNT(*) AS co_occurrence_count
FROM job_skills a
JOIN job_skills b ON a.job_id = b.job_id AND a.skill_id < b.skill_id
JOIN skills sa ON a.skill_id = sa.skill_id
JOIN skills sb ON b.skill_id = sb.skill_id
GROUP BY sa.skill_name, sb.skill_name
ORDER BY co_occurrence_count DESC;


-- 5. Salary ranges by role / location
-- Requires a `salary_min` / `salary_max` column on `jobs` populated from
-- real scraped/Kaggle data (many sample postings won't have this).
-- Uncomment and adapt once salary data is available:
--
-- SELECT
--     j.search_role,
--     j.location,
--     AVG(j.salary_min) AS avg_salary_min,
--     AVG(j.salary_max) AS avg_salary_max,
--     COUNT(*) AS postings_count
-- FROM jobs j
-- WHERE j.salary_min IS NOT NULL
-- GROUP BY j.search_role, j.location
-- ORDER BY avg_salary_max DESC;


-- 6. Roles ranked by how many postings mention a given skill
-- (useful for "which roles most value skill X" insight)
SELECT
    j.search_role,
    COUNT(*) AS postings_mentioning_skill
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
JOIN jobs j ON js.job_id = j.job_id
WHERE s.skill_name = 'SQL'
GROUP BY j.search_role
ORDER BY postings_mentioning_skill DESC;
