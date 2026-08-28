"""
multi_role_match.py

Extends match_engine.py to run a resume against every role profile
available in the database (not just one), producing:
  - a ranked list of match % across roles (e.g. Data Analyst 82%,
    BI Analyst 76%, Business Analyst 68%, Data Scientist 43%)
  - a single "recommended next skill" -- the missing skill that would
    most improve the candidate's standing across their best-matching roles

Usage:
    python multi_role_match.py --resume data/sample_resumes/parsed_sample_resume.json \\
                                --backend tfidf
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from match_engine import DB_PATH, compute_match, get_role_profile
import sqlite3


def get_all_roles(db_path: Path) -> list[str]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT DISTINCT search_role FROM jobs WHERE search_role IS NOT NULL"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def recommend_next_skill(role_results: list[dict], top_n_roles: int = 3) -> dict | None:
    """Looks at missing skills across the candidate's top N best-matching
    roles and recommends the one that appears most often -- i.e. the
    single skill that would improve standing across the most roles at once.
    Ties are broken by which role it would help the most (highest match
    score among roles missing that skill).
    """
    top_roles = sorted(role_results, key=lambda r: r["match_score_pct"], reverse=True)[:top_n_roles]

    skill_counter = Counter()
    skill_best_role_score = {}
    for role_result in top_roles:
        for skill in role_result["missing_skills"]:
            skill_counter[skill] += 1
            skill_best_role_score[skill] = max(
                skill_best_role_score.get(skill, 0), role_result["match_score_pct"]
            )

    if not skill_counter:
        return None  # no missing skills across top roles -- candidate is well-matched

    # Sort by: appears in most roles, then by highest score it would help
    best_skill, count = max(
        skill_counter.items(),
        key=lambda item: (item[1], skill_best_role_score[item[0]]),
    )

    return {
        "recommended_skill": best_skill,
        "would_help_n_roles": count,
        "considered_top_roles": [r["role"] for r in top_roles],
    }


def match_all_roles(resume: dict, db_path: Path, backend: str = "tfidf") -> dict:
    roles = get_all_roles(db_path)
    if not roles:
        raise ValueError(f"No roles found in {db_path}")

    role_results = []
    for role in roles:
        try:
            profile = get_role_profile(db_path, role)
        except ValueError:
            continue
        result = compute_match(resume, profile, backend=backend)
        role_results.append(result)

    role_results.sort(key=lambda r: r["match_score_pct"], reverse=True)
    recommendation = recommend_next_skill(role_results)

    return {
        "candidate": resume.get("name"),
        "roles_evaluated": len(role_results),
        "ranked_matches": [
            {
                "role": r["role"],
                "match_score_pct": r["match_score_pct"],
                "strong_skills": r["strong_skills"],
                "missing_skills": r["missing_skills"],
            }
            for r in role_results
        ],
        "recommended_next_skill": recommendation,
    }


def main():
    parser = argparse.ArgumentParser(description="Match a resume against all available roles")
    parser.add_argument("--resume", required=True, help="Path to parsed resume JSON")
    parser.add_argument("--db", default=str(DB_PATH), help="Path to SQLite database")
    parser.add_argument(
        "--backend",
        default="tfidf",
        choices=["embeddings", "tfidf"],
        help="Similarity backend (see match_engine.py for details)",
    )
    args = parser.parse_args()

    with open(args.resume, "r", encoding="utf-8") as f:
        resume = json.load(f)

    result = match_all_roles(resume, Path(args.db), backend=args.backend)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
