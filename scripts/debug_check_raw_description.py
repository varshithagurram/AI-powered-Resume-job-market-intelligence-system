import json
import glob

# Find the most recent adzuna raw file automatically
files = sorted(glob.glob("data/raw/adzuna_jobs_*.json"))
if not files:
    print("No adzuna_jobs_*.json file found in data/raw/")
    exit()

latest_file = files[-1]
print(f"Reading: {latest_file}\n")

with open(latest_file, "r", encoding="utf-8") as f:
    jobs = json.load(f)

financial_jobs = [j for j in jobs if j.get("search_role") == "financial analyst"]
print(f"Found {len(financial_jobs)} financial analyst postings in raw data\n")

for job in financial_jobs[:5]:
    print("-" * 60)
    print("Title:", job.get("title"))
    desc = job.get("description")
    print("Description type:", type(desc))
    print("Description length:", len(desc) if desc else 0)
    print("Description text:", repr(desc)[:500])
