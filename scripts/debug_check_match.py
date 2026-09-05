import json
import sqlite3
import sys

resume_path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_resumes/parsed_sample_resume.json"

with open(resume_path, "r", encoding="utf-8") as f:
    resume = json.load(f)

print("=== Resume ===")
print("Name:", resume.get("name"))
print("Skills detected:", resume.get("skills"))
print("Number of skills detected:", len(resume.get("skills", [])))
print("Raw text length:", resume.get("raw_text_length"))

conn = sqlite3.connect("data/job_market.db")

required = conn.execute(
    """
    SELECT DISTINCT s.skill_name
    FROM job_skills js
    JOIN skills s ON js.skill_id = s.skill_id
    JOIN jobs j ON js.job_id = j.job_id
    WHERE j.search_role = 'data analyst'
    """
).fetchall()
required_skills = sorted({r[0] for r in required})

print("\n=== Role: data analyst ===")
print("Number of required skills (aggregated across all postings):", len(required_skills))
print("Required skills:", required_skills)

resume_skills = set(resume.get("skills", []))
overlap = resume_skills & set(required_skills)
print("\n=== Overlap ===")
print("Matching:", sorted(overlap))
print("Missing:", sorted(set(required_skills) - resume_skills))

conn.close()
