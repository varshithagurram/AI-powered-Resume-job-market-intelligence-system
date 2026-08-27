"""
match_engine.py

Core matching engine: compares a parsed resume against a job/role profile
and produces:
  - an overall match score (0-100%)
  - strong skills (present in both resume and role)
  - missing/weak skills (required by the role, absent from the resume)

Two similarity backends are supported:
  - "embeddings" (default, recommended): Sentence-BERT (all-MiniLM-L6-v2)
    cosine similarity over resume text vs. role description text. Captures
    semantic matches (e.g. "5 years Python" ~ "senior Python developer")
    that keyword matching misses. Requires internet access to download the
    model from Hugging Face on first run -- run this locally, not from a
    network-restricted sandbox.
  - "tfidf": scikit-learn TF-IDF + cosine similarity. No model download
    required, works fully offline. Used as a fast baseline/comparison and
    as a fallback if the embeddings model can't be downloaded.

The skills gap (strong/missing) is always computed via simple set
comparison on the taxonomy-based skills lists (from clean_data.py /
parse_resume.py), independent of which similarity backend is used for the
score -- this keeps the skills list accurate and interpretable regardless
of backend.

Usage:
    python match_engine.py --resume data/sample_resumes/parsed_sample_resume.json \\
                            --role "data analyst" --backend embeddings

    python match_engine.py --resume data/sample_resumes/parsed_sample_resume.json \\
                            --role "data analyst" --backend tfidf
"""

import argparse
import json
import sqlite3
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = Path("data/job_market.db")


def get_role_profile(db_path: Path, role: str) -> dict:
    """Builds a 'role profile' from all postings collected under a given
    search_role: the combined skill set (required_skills) and a text blob
    (titles) used for embedding/TF-IDF similarity.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    postings = conn.execute(
        "SELECT job_id, title FROM jobs WHERE search_role = ?", (role,)
    ).fetchall()

    if not postings:
        conn.close()
        raise ValueError(f"No postings found for role '{role}' in {db_path}")

    job_ids = [p["job_id"] for p in postings]
    placeholders = ",".join("?" * len(job_ids))
    skill_rows = conn.execute(
        f"""
        SELECT DISTINCT s.skill_name
        FROM job_skills js
        JOIN skills s ON js.skill_id = s.skill_id
        WHERE js.job_id IN ({placeholders})
        """,
        job_ids,
    ).fetchall()

    conn.close()

    required_skills = sorted({row["skill_name"] for row in skill_rows})
    text_blob = " ".join(p["title"] for p in postings)

    return {
        "role": role,
        "required_skills": required_skills,
        "text_blob": text_blob,
        "postings_count": len(postings),
    }


def resume_text_blob(resume: dict) -> str:
    parts = [resume.get("name") or ""]
    parts += resume.get("skills", [])
    return " ".join(parts)


def similarity_tfidf(text_a: str, text_b: str) -> float:
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([text_a, text_b])
    score = cosine_similarity(tfidf[0], tfidf[1])[0][0]
    return float(score)


def similarity_embeddings(text_a: str, text_b: str) -> float:
    # Imported lazily so the tfidf backend works even without
    # sentence-transformers / internet access to download the model.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode([text_a, text_b])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(score)


def compute_match(resume: dict, role_profile: dict, backend: str = "embeddings") -> dict:
    resume_skills = set(resume.get("skills", []))
    required_skills = set(role_profile["required_skills"])

    strong_skills = sorted(resume_skills & required_skills)
    missing_skills = sorted(required_skills - resume_skills)

    text_a = resume_text_blob(resume)
    text_b = role_profile["text_blob"] + " " + " ".join(required_skills)

    if backend == "embeddings":
        similarity = similarity_embeddings(text_a, text_b)
    elif backend == "tfidf":
        similarity = similarity_tfidf(text_a, text_b)
    else:
        raise ValueError(f"Unknown backend: {backend}")

    # Blend semantic similarity with the skills-overlap ratio so the score
    # reflects both "does the language match" and "are the actual required
    # skills present" -- pure semantic similarity alone can be misleadingly
    # high even when key skills are missing.
    skill_overlap_ratio = (
        len(strong_skills) / len(required_skills) if required_skills else 0.0
    )
    blended_score = 0.5 * similarity + 0.5 * skill_overlap_ratio
    match_score_pct = round(blended_score * 100, 1)

    return {
        "role": role_profile["role"],
        "match_score_pct": match_score_pct,
        "similarity_backend": backend,
        "raw_similarity": round(similarity, 3),
        "skill_overlap_ratio": round(skill_overlap_ratio, 3),
        "strong_skills": strong_skills,
        "missing_skills": missing_skills,
        "required_skills_count": len(required_skills),
        "postings_analyzed": role_profile["postings_count"],
    }


def main():
    parser = argparse.ArgumentParser(description="Match a resume against a target role")
    parser.add_argument("--resume", required=True, help="Path to parsed resume JSON (from parse_resume.py)")
    parser.add_argument("--role", required=True, help="Target role, e.g. 'data analyst'")
    parser.add_argument("--db", default=str(DB_PATH), help="Path to SQLite database")
    parser.add_argument(
        "--backend",
        default="embeddings",
        choices=["embeddings", "tfidf"],
        help="Similarity backend. 'embeddings' needs internet access to download the "
             "model on first run; 'tfidf' works fully offline.",
    )
    args = parser.parse_args()

    with open(args.resume, "r", encoding="utf-8") as f:
        resume = json.load(f)

    role_profile = get_role_profile(Path(args.db), args.role)
    result = compute_match(resume, role_profile, backend=args.backend)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
