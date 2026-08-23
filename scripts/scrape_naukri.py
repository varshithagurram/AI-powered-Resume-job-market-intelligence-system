"""
scrape_naukri.py

Scrapes job postings from Naukri.com for target roles and saves raw results
as JSON. Run this on your local machine (not a restricted sandbox) since
job boards block many cloud/datacenter IPs.

Usage:
    python scrape_naukri.py --role "data analyst" --pages 5
"""

import argparse
import json
import time
import random
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

BASE_URL = "https://www.naukri.com/{role}-jobs-{page}"


def build_search_url(role: str, page: int) -> str:
    role_slug = role.strip().lower().replace(" ", "-")
    return BASE_URL.format(role=role_slug, page=page)


def parse_job_cards(html: str) -> list[dict]:
    """Parse job listing cards from a Naukri search results page.

    NOTE: Naukri's markup changes fairly often. If this returns an empty
    list, inspect the page HTML and update the selectors below.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for card in soup.select("div.srp-jobtuple-wrapper"):
        title_el = card.select_one("a.title")
        company_el = card.select_one("a.comp-name")
        location_el = card.select_one("span.locWdth")
        exp_el = card.select_one("span.expwdth")
        skills_els = card.select("ul.tags-gt li")

        jobs.append({
            "title": title_el.get_text(strip=True) if title_el else None,
            "company": company_el.get_text(strip=True) if company_el else None,
            "location": location_el.get_text(strip=True) if location_el else None,
            "experience": exp_el.get_text(strip=True) if exp_el else None,
            "skills": [s.get_text(strip=True) for s in skills_els],
            "job_url": title_el["href"] if title_el and title_el.has_attr("href") else None,
        })

    return jobs


def scrape_role(role: str, pages: int, delay_range=(2, 5)) -> list[dict]:
    all_jobs = []
    for page in range(1, pages + 1):
        url = build_search_url(role, page)
        print(f"Fetching: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Failed on page {page}: {e}")
            continue

        jobs = parse_job_cards(resp.text)
        print(f"  Found {len(jobs)} jobs")
        for job in jobs:
            job["search_role"] = role
        all_jobs.extend(jobs)

        time.sleep(random.uniform(*delay_range))  # be polite, avoid rate limits

    return all_jobs


def main():
    parser = argparse.ArgumentParser(description="Scrape Naukri job postings")
    parser.add_argument("--role", required=True, help="Job role to search, e.g. 'data analyst'")
    parser.add_argument("--pages", type=int, default=5, help="Number of result pages to scrape")
    parser.add_argument(
        "--out",
        default="data/raw",
        help="Output directory for raw JSON",
    )
    args = parser.parse_args()

    jobs = scrape_role(args.role, args.pages)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    role_slug = args.role.strip().lower().replace(" ", "_")
    out_path = out_dir / f"naukri_{role_slug}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(jobs)} job postings to {out_path}")


if __name__ == "__main__":
    main()
