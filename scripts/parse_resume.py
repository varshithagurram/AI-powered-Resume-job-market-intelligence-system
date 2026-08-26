"""
parse_resume.py

Extracts text and structured fields (name, skills, years of experience)
from a resume file (PDF or DOCX).

Uses the same skill taxonomy as scripts/clean_data.py for skill detection,
so a candidate's resume skills and job posting skills are directly
comparable in the matching engine (Day 7).

Usage:
    python parse_resume.py --input path/to/resume.pdf
    python parse_resume.py --input path/to/resume.docx
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber
import docx2txt
import spacy

# Reuse the same taxonomy as clean_data.py so resume skills and job posting
# skills are extracted the same way and can be directly compared.
SKILL_TAXONOMY = {
    "SQL": [r"\bsql\b"],
    "Python": [r"\bpython\b"],
    "Excel": [r"\bexcel\b"],
    "Tableau": [r"\btableau\b"],
    "Power BI": [r"\bpower\s*bi\b"],
    "Statistics": [r"\bstatistic(s)?\b", r"\bstats\b"],
    "A/B Testing": [r"\ba/?b\s*testing\b"],
    "Machine Learning": [r"\bmachine\s*learning\b", r"\bml\b"],
    "DAX": [r"\bdax\b"],
    "R": [r"\br programming\b", r"\br\b(?=.*(statist|analy))"],
    "Communication": [r"\bcommunication\b"],
    "Deep Learning": [r"\bdeep\s*learning\b"],
    "NLP": [r"\bnlp\b", r"\bnatural language processing\b"],
    "Spark": [r"\bspark\b"],
    "AWS": [r"\baws\b"],
    "Azure": [r"\bazure\b"],
}

_nlp = None  # lazy-loaded spaCy model


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    elif suffix == ".docx":
        return docx2txt.process(str(file_path))
    else:
        raise ValueError(f"Unsupported file type: {suffix} (use .pdf or .docx)")


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill, patterns in SKILL_TAXONOMY.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.append(skill)
                break
    return sorted(found)


def extract_name(text: str) -> str | None:
    """Best-effort candidate name extraction using spaCy PERSON entities.
    Looks only at the first ~300 characters, since resumes conventionally
    put the candidate's name at the very top.
    """
    nlp = get_nlp()
    doc = nlp(text[:300])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


def extract_years_experience(text: str) -> float | None:
    """Best-effort extraction of total years of experience via regex
    patterns like '3 years', '2+ years of experience'."""
    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s*years?", text.lower())
    if not matches:
        return None
    return max(float(m) for m in matches)


def parse_resume(file_path: Path) -> dict:
    text = extract_text(file_path)
    if not text.strip():
        raise ValueError(f"No extractable text found in {file_path}")

    return {
        "file_name": file_path.name,
        "name": extract_name(text),
        "years_experience": extract_years_experience(text),
        "skills": extract_skills(text),
        "raw_text_length": len(text),
    }


def main():
    parser = argparse.ArgumentParser(description="Parse a resume (PDF/DOCX) into structured data")
    parser.add_argument("--input", required=True, help="Path to resume file (.pdf or .docx)")
    parser.add_argument("--out", help="Optional path to save parsed result as JSON")
    args = parser.parse_args()

    file_path = Path(args.input)
    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = parse_resume(file_path)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
