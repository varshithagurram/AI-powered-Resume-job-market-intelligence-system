"""
streamlit_app/app.py

Interactive front end for the Resume-Job Market Intelligence System, with
automatic daily data refresh: on each load, the app checks whether today's
job posting data already exists (via the `scraped_date` stored on every
job) and automatically re-fetches from the Adzuna API if it's missing or
stale -- no manual script-running needed once deployed.

Run with:
    streamlit run streamlit_app/app.py
(run from the project root so relative imports and the database path resolve)

For deployment (e.g. Streamlit Community Cloud): set ADZUNA_APP_ID and
ADZUNA_APP_KEY in the app's Secrets (Settings -> Secrets), not as plain
environment variables -- st.secrets is how Streamlit Cloud injects them.
"""

import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent / "scripts"))

from parse_resume import parse_resume  # noqa: E402
from match_engine import DB_PATH  # noqa: E402
from multi_role_match import get_all_roles, match_all_roles  # noqa: E402
from refresh_pipeline import ensure_fresh_data  # noqa: E402

st.set_page_config(page_title="Resume-Job Market Intelligence", layout="wide")


def get_adzuna_credentials():
    """Checks Streamlit secrets first (for deployment), then falls back to
    environment variables (for local development)."""
    app_id = st.secrets.get("ADZUNA_APP_ID") if hasattr(st, "secrets") else None
    app_key = st.secrets.get("ADZUNA_APP_KEY") if hasattr(st, "secrets") else None
    app_id = app_id or os.environ.get("ADZUNA_APP_ID")
    app_key = app_key or os.environ.get("ADZUNA_APP_KEY")
    return app_id, app_key


# --- Automatic daily data refresh (runs once per day, shared across all
# users of a deployed instance -- see refresh_pipeline.is_data_stale, which
# checks the database's own scraped_date rather than relying on an
# in-memory cache that wouldn't survive an app restart) ---
app_id, app_key = get_adzuna_credentials()
with st.spinner("Checking for fresh job market data..."):
    refresh_result = ensure_fresh_data(app_id, app_key)

if refresh_result["status"] == "refreshed":
    st.toast(
        f"Refreshed job market data: {refresh_result['postings_loaded']} "
        f"postings loaded for today.",
        icon="✅",
    )
elif refresh_result["status"] == "stale_no_credentials":
    st.warning(
        "Job market data hasn't been refreshed today (no Adzuna API "
        "credentials configured), so results reflect the most recent "
        "available data instead of today's live postings."
    )
elif refresh_result["status"] == "error":
    st.warning(
        f"Couldn't refresh job market data today ({refresh_result['reason']}). "
        "Showing the most recent available data instead."
    )

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
        "Job posting data refreshes automatically once per day from the "
        "Adzuna API. No manual steps needed."
    )

uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

try:
    available_roles = get_all_roles(DB_PATH)
except Exception:
    available_roles = []

if not available_roles:
    st.warning(
        "No roles found in the database yet. If this is a fresh deployment, "
        "make sure ADZUNA_APP_ID and ADZUNA_APP_KEY are set in Secrets."
    )
    st.stop()

target_role = st.selectbox("Target role", options=available_roles)

analyze_clicked = st.button("Analyze match", type="primary", disabled=uploaded_file is None)

if analyze_clicked and uploaded_file is not None:
    with st.spinner("Parsing resume and computing match..."):
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

    if result["recommended_next_skill"]:
        rec = result["recommended_next_skill"]
        st.info(
            f"**Recommended next skill: {rec['recommended_skill']}** — "
            f"would help with {rec['would_help_n_roles']} of your top-matching roles."
        )
    else:
        st.info("No skill gaps found across your top-matching roles — nice work!")

    st.subheader("Match % across all roles")
    chart_data = {r["role"]: r["match_score_pct"] for r in result["ranked_matches"]}
    st.bar_chart(chart_data)

    with st.expander("See full ranked match details"):
        st.json(result["ranked_matches"])

elif uploaded_file is None:
    st.info("Upload a resume to get started.")
