"""
streamlit_app/app.py

Interactive front end for the Resume-Job Market Intelligence System.

User flow:
  1. Upload a resume (PDF or DOCX)
  2. Pick a target role
  3. See: overall match score, strong skills, missing skills, most
     in-demand skills in current listings, recommended next skill, and
     match % across all available roles

Run with:
    streamlit run streamlit_app/app.py
(run from the project root so the relative imports/db path resolve)
"""

import sys
import tempfile
from pathlib import Path

import streamlit as st

# Allow importing sibling scripts (parse_resume, match_engine, multi_role_match)
sys.path.append(str(Path(__file__).resolve().parent.parent / "scripts"))

from parse_resume import parse_resume  # noqa: E402
from match_engine import DB_PATH, get_role_profile  # noqa: E402
from multi_role_match import get_all_roles, match_all_roles  # noqa: E402

st.set_page_config(page_title="Resume-Job Market Intelligence", layout="wide")

st.title("📊 Resume-Job Market Intelligence System")
st.caption(
    "Upload your resume, pick a target role, and see how you match against "
    "current job market demand."
)

with st.sidebar:
    st.header("Settings")
    backend = st.radio(
        "Matching method",
        options=["tfidf", "embeddings"],
        index=0,
        help=(
            "tfidf: fast, works offline. "
            "embeddings: semantic matching via Sentence-BERT, needs internet "
            "access on first run to download the model."
        ),
    )
    st.markdown("---")
    st.caption(
        "Data source: SQLite database built from scraped/Kaggle job postings. "
        "Run the pipeline scripts (see README) to refresh it."
    )

uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

try:
    available_roles = get_all_roles(DB_PATH)
except Exception:
    available_roles = []

if not available_roles:
    st.warning(
        "No roles found in the database. Run the data pipeline first "
        "(scrape/clean/load — see README) before using this app."
    )
    st.stop()

target_role = st.selectbox("Target role", options=available_roles)

analyze_clicked = st.button("Analyze match", type="primary", disabled=uploaded_file is None)

if analyze_clicked and uploaded_file is not None:
    with st.spinner("Parsing resume and computing match..."):
        # parse_resume() expects a file path, so write the upload to a temp file
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = Path(tmp.name)

        try:
            resume = parse_resume(tmp_path)
        except Exception as e:
            st.error(f"Could not parse resume: {e}")
            st.stop()
        finally:
            tmp_path.unlink(missing_ok=True)

        try:
            result = match_all_roles(resume, DB_PATH, backend=backend)
        except Exception as e:
            st.error(f"Matching failed: {e}")
            st.stop()

    st.success(f"Analysis complete for **{resume.get('name') or 'candidate'}**")

    # --- Primary match score for the selected target role ---
    target_result = next(
        (r for r in result["ranked_matches"] if r["role"] == target_role), None
    )

    if target_result:
        col1, col2, col3 = st.columns(3)
        col1.metric("Match score", f"{target_result['match_score_pct']}%")
        col2.metric("Strong skills", len(target_result["strong_skills"]))
        col3.metric("Missing skills", len(target_result["missing_skills"]))

        st.subheader(f"Skill breakdown for: {target_role}")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("**✅ Strong skills**")
            if target_result["strong_skills"]:
                for skill in target_result["strong_skills"]:
                    st.markdown(f"- {skill}")
            else:
                st.markdown("_None matched_")
        with sc2:
            st.markdown("**⚠️ Missing / weak skills**")
            if target_result["missing_skills"]:
                for skill in target_result["missing_skills"]:
                    st.markdown(f"- {skill}")
            else:
                st.markdown("_No gaps — fully matched!_")
    else:
        st.warning(f"No data available for role '{target_role}'.")

    # --- Recommended next skill ---
    if result["recommended_next_skill"]:
        rec = result["recommended_next_skill"]
        st.info(
            f"**Recommended next skill: {rec['recommended_skill']}** — "
            f"would help with {rec['would_help_n_roles']} of your top-matching roles."
        )
    else:
        st.info("No skill gaps found across your top-matching roles — nice work!")

    # --- Match % across all roles ---
    st.subheader("Match % across all roles")
    chart_data = {
        r["role"]: r["match_score_pct"] for r in result["ranked_matches"]
    }
    st.bar_chart(chart_data)

    with st.expander("See full ranked match details"):
        st.json(result["ranked_matches"])

elif uploaded_file is None:
    st.info("Upload a resume to get started.")
