import sqlite3

conn = sqlite3.connect("data/job_market.db")

count = conn.execute(
    "SELECT COUNT(*) FROM jobs WHERE search_role = 'financial analyst'"
).fetchone()
print("Financial analyst postings in database:", count[0])

print("\nTitles found:")
for row in conn.execute(
    "SELECT title, company FROM jobs WHERE search_role = 'financial analyst'"
):
    print(" -", row)

conn.close()
