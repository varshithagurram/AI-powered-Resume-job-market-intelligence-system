import pandas as pd

df = pd.read_csv("data/processed/cleaned_job_postings.csv")
subset = df[df["search_role"] == "financial analyst"][["title", "company", "skills_str"]]

if subset.empty:
    print("No financial analyst rows found in cleaned_job_postings.csv")
else:
    print(subset.to_string())
