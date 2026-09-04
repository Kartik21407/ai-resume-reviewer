"""
AI Resume Reviewer & Job Match Scorer — Streamlit Application.

Main entry point for the web application. Provides the UI for
resume upload, job description input, LLM analysis, and results
dashboard with deterministic scoring.
"""

import os
import sys

import streamlit as st
from dotenv import load_dotenv

# Ensure the project root is on sys.path for imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.llm_chain import LLMChainError, create_analysis_chain, run_analysis
from src.pdf_loader import PDFLoadError, load_pdf_from_upload
from src.scoring import calculate_score, get_weight_description
from src.text_processing import get_text_stats, truncate_text
from src.utils import (
    create_full_report,
    generate_json_report,
    generate_text_report,
    get_match_level_emoji,
    get_score_color,
)

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Reviewer & Job Match Scorer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import Google Font ───────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global Styles ────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hero Header ──────────────────────────────── */
    .hero-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(48, 43, 99, 0.3);
    }
    .hero-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.5px;
    }
    .hero-header p {
        color: #a5b4fc;
        font-size: 1.05rem;
        margin: 0;
        font-weight: 400;
    }

    /* ── Section Cards ────────────────────────────── */
    .section-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s ease;
    }
    .section-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e1b4b;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Score Display ────────────────────────────── */
    .score-container {
        text-align: center;
        padding: 2rem;
    }
    .score-circle {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        font-weight: 800;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        position: relative;
    }
    .score-circle::after {
        content: '%';
        font-size: 1.2rem;
        font-weight: 600;
        position: absolute;
        bottom: 2.2rem;
        right: 1.8rem;
    }
    .match-badge {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.3px;
    }
    .match-strong {
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        color: #065f46;
    }
    .match-moderate {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        color: #92400e;
    }
    .match-weak {
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        color: #991b1b;
    }

    /* ── Skill Tags ───────────────────────────────── */
    .skill-tag {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.2rem;
        transition: transform 0.15s ease;
    }
    .skill-tag:hover {
        transform: translateY(-1px);
    }
    .skill-matched {
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        color: #065f46;
        border: 1px solid #6ee7b7;
    }
    .skill-missing {
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        color: #991b1b;
        border: 1px solid #fca5a5;
    }
    .skill-emphasize {
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        color: #1e40af;
        border: 1px solid #93c5fd;
    }
    .skill-learn {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        color: #92400e;
        border: 1px solid #fcd34d;
    }

    /* ── Score Breakdown Table ─────────────────────── */
    .breakdown-row {
        display: flex;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid #f3f4f6;
    }
    .breakdown-row:last-child {
        border-bottom: none;
    }
    .breakdown-label {
        flex: 0 0 180px;
        font-weight: 600;
        color: #374151;
        font-size: 0.95rem;
    }
    .breakdown-bar-bg {
        flex: 1;
        height: 10px;
        background: #f3f4f6;
        border-radius: 5px;
        overflow: hidden;
        margin: 0 1rem;
    }
    .breakdown-bar-fill {
        height: 100%;
        border-radius: 5px;
        transition: width 0.6s ease;
    }
    .breakdown-score {
        flex: 0 0 70px;
        text-align: right;
        font-weight: 700;
        color: #1f2937;
        font-size: 0.95rem;
    }

    /* ── Analysis Card ────────────────────────────── */
    .analysis-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        line-height: 1.7;
        color: #374151;
        font-size: 0.95rem;
    }

    /* ── Sidebar Styles ───────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1744 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e7ff !important;
    }
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label {
        color: #a5b4fc !important;
        font-weight: 500;
    }

    /* ── List Styles ──────────────────────────────── */
    .styled-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .styled-list li {
        padding: 0.5rem 0;
        border-bottom: 1px solid #f3f4f6;
        color: #374151;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .styled-list li:last-child {
        border-bottom: none;
    }

    /* ── Stacked metric override ──────────────────── */
    div[data-testid="stMetric"] {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1f2937 !important;
        font-weight: 700 !important;
    }

    /* ── Download buttons ─────────────────────────── */
    .stDownloadButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────
def render_sidebar() -> dict:
    """Render the sidebar with configuration options.

    Returns:
        Dict with api_key, model_name, temperature.
    """
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        st.markdown("---")

        # API Key
        env_key = os.getenv("GOOGLE_API_KEY", "")
        api_key = st.text_input(
            "🔑 Google API Key",
            value=env_key,
            type="password",
            help="Enter your Google API key or set it in .env file.",
            placeholder="your-api-key...",
        )

        st.markdown("")

        # Model Selection
        env_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        model_options = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]
        default_idx = model_options.index(env_model) if env_model in model_options else 0
        model_name = st.selectbox(
            "🤖 Model",
            options=model_options,
            index=default_idx,
            help="Select the Gemini model to use for analysis.",
        )

        st.markdown("")

        # Temperature
        temperature = st.slider(
            "🌡️ Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.1,
            help="Lower = more deterministic, Higher = more creative.",
        )

        st.markdown("---")

        # Scoring Weights Info
        with st.expander("📊 Scoring Weights"):
            weights = get_weight_description()
            for w in weights:
                st.markdown(f"**{w['category']}**: {w['weight']}%")
            st.markdown("---")
            st.caption("Weights are applied deterministically to LLM sub-scores.")

        st.markdown("")

        # About Section
        with st.expander("ℹ️ About"):
            st.markdown("""
**AI Resume Reviewer** analyzes your resume against a job description using Generative AI.

**Key Features:**
- 📄 PDF resume parsing
- 🤖 LLM-powered semantic analysis
- 📊 Deterministic scoring system
- 🎯 Structured output via Pydantic
- 📥 Downloadable reports

**Tech Stack:**
- Streamlit • LangChain LCEL
- PydanticOutputParser
- PyPDFLoader • Google Gemini API

Built as a GenAI engineering portfolio project.
            """)

    return {
        "api_key": api_key,
        "model_name": model_name,
        "temperature": temperature,
    }


# ─────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────
def render_header():
    """Render the hero header."""
    st.markdown("""
    <div class="hero-header">
        <h1>📄 AI Resume Reviewer & Job Match Scorer</h1>
        <p>Analyze your resume against any job description using Generative AI</p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# Input Sections
# ─────────────────────────────────────────────────────────
def render_upload_section() -> tuple:
    """Render the resume upload section.

    Returns:
        Tuple of (resume_text, page_count, filename) or (None, 0, None).
    """
    st.markdown('<div class="section-title">📤 Upload Your Resume</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your resume as a PDF file",
        type=["pdf"],
        help="Max file size: 10 MB. The PDF must contain selectable text.",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        try:
            resume_text, page_count = load_pdf_from_upload(uploaded_file)
            stats = get_text_stats(resume_text)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 File", uploaded_file.name)
            with col2:
                st.metric("📑 Pages", page_count)
            with col3:
                st.metric("📝 Words", f"{stats['word_count']:,}")

            with st.expander("👁️ Preview Extracted Text", expanded=False):
                st.text(resume_text[:3000] + ("..." if len(resume_text) > 3000 else ""))

            return resume_text, page_count, uploaded_file.name

        except PDFLoadError as e:
            st.error(f"❌ {str(e)}")
            return None, 0, None

    return None, 0, None


def render_jd_section() -> str:
    """Render the job description input section.

    Returns:
        Job description text.
    """
    st.markdown('<div class="section-title">📋 Paste Job Description</div>', unsafe_allow_html=True)

    job_description = st.text_area(
        "Paste the full job description here",
        height=250,
        placeholder=(
            "Paste the complete job description here...\n\n"
            "Include: job title, required skills, qualifications, "
            "experience requirements, responsibilities, etc."
        ),
        label_visibility="collapsed",
    )

    if job_description:
        jd_stats = get_text_stats(job_description)
        st.caption(f"📊 {jd_stats['word_count']} words • {jd_stats['char_count']} characters")

    return job_description


# ─────────────────────────────────────────────────────────
# Results Dashboard
# ─────────────────────────────────────────────────────────
def render_overall_score(score_breakdown):
    """Render the overall match score with visual gauge."""
    score = score_breakdown.overall_score
    level = score_breakdown.match_level
    color = get_score_color(score)
    emoji = get_match_level_emoji(level)

    badge_class = {
        "Strong Match": "match-strong",
        "Moderate Match": "match-moderate",
        "Weak Match": "match-weak",
    }.get(level, "match-moderate")

    st.markdown(f"""
    <div class="score-container">
        <div class="score-circle" style="background: linear-gradient(135deg, {color}, {color}dd);">
            {score:.0f}
        </div>
        <br>
        <span class="match-badge {badge_class}">{emoji} {level}</span>
    </div>
    """, unsafe_allow_html=True)


def render_score_breakdown(score_breakdown):
    """Render the detailed score breakdown with progress bars."""
    st.markdown('<div class="section-title">📊 Score Breakdown</div>', unsafe_allow_html=True)

    categories = [
        ("Skill Match", score_breakdown.skill_match_weighted, 40, score_breakdown.skill_match_raw),
        ("Keyword Match", score_breakdown.keyword_match_weighted, 20, score_breakdown.keyword_match_raw),
        ("Experience Match", score_breakdown.experience_match_weighted, 20, score_breakdown.experience_match_raw),
        ("Education Match", score_breakdown.education_match_weighted, 10, score_breakdown.education_match_raw),
        ("Project Match", score_breakdown.project_match_weighted, 10, score_breakdown.project_match_raw),
    ]

    for label, weighted, max_score, raw in categories:
        pct = (weighted / max_score * 100) if max_score > 0 else 0
        color = get_score_color(raw)

        st.markdown(f"""
        <div class="breakdown-row">
            <div class="breakdown-label">{label}</div>
            <div class="breakdown-bar-bg">
                <div class="breakdown-bar-fill" style="width: {pct}%; background: {color};"></div>
            </div>
            <div class="breakdown-score">{weighted:.1f}/{max_score}</div>
        </div>
        """, unsafe_allow_html=True)

    # Total row
    st.markdown(f"""
    <div class="breakdown-row" style="border-top: 2px solid #1e1b4b; margin-top: 0.5rem; padding-top: 1rem;">
        <div class="breakdown-label" style="font-weight: 800; color: #1e1b4b;">TOTAL</div>
        <div style="flex:1;"></div>
        <div class="breakdown-score" style="font-size: 1.1rem; color: {get_score_color(score_breakdown.overall_score)};">
            {score_breakdown.overall_score:.1f}/100
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_skill_tags(skills: list, css_class: str, label: str):
    """Render a list of skills as styled tags."""
    if not skills:
        st.caption(f"No {label.lower()} found.")
        return

    tags_html = "".join(
        f'<span class="skill-tag {css_class}">{skill}</span>'
        for skill in skills
    )
    st.markdown(tags_html, unsafe_allow_html=True)


def render_analysis_text(title: str, content: str, icon: str = "📝"):
    """Render an analysis text block in a styled card."""
    st.markdown(f'<div class="section-title">{icon} {title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="analysis-card">{content}</div>', unsafe_allow_html=True)


def render_numbered_list(items: list, icon: str = "•"):
    """Render items as a styled numbered list."""
    if not items:
        st.caption("None identified.")
        return

    list_html = '<ul class="styled-list">'
    for i, item in enumerate(items, 1):
        list_html += f"<li>{icon} {item}</li>"
    list_html += "</ul>"
    st.markdown(list_html, unsafe_allow_html=True)


def render_results(analysis, score_breakdown, full_report):
    """Render the complete results dashboard."""

    st.markdown("---")
    st.markdown("## 📊 Analysis Results")

    # ── Overall Score ──
    render_overall_score(score_breakdown)

    st.markdown("---")

    # ── Score Breakdown ──
    render_score_breakdown(score_breakdown)

    st.markdown("---")

    # ── Skills Analysis (two columns) ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">✅ Matched Skills</div>', unsafe_allow_html=True)
        render_skill_tags(analysis.matched_skills, "skill-matched", "matched skills")

    with col2:
        st.markdown('<div class="section-title">❌ Missing Skills</div>', unsafe_allow_html=True)
        render_skill_tags(analysis.missing_skills, "skill-missing", "missing skills")

    st.markdown("---")

    # ── Keyword Analysis (two columns) ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">🔑 Matched Keywords</div>', unsafe_allow_html=True)
        render_skill_tags(analysis.matched_keywords, "skill-matched", "matched keywords")

    with col2:
        st.markdown('<div class="section-title">🔍 Missing Keywords</div>', unsafe_allow_html=True)
        render_skill_tags(analysis.missing_keywords, "skill-missing", "missing keywords")

    st.markdown("---")

    # ── Experience, Education, Projects ──
    render_analysis_text("Experience Analysis", analysis.experience_match, "💼")
    render_analysis_text("Education Analysis", analysis.education_match, "🎓")
    render_analysis_text("Project Relevance", analysis.project_relevance, "🚀")

    st.markdown("---")

    # ── Strengths & Weaknesses (two columns) ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">💪 Strengths</div>', unsafe_allow_html=True)
        render_numbered_list(analysis.strengths, "✅")

    with col2:
        st.markdown('<div class="section-title">⚠️ Weaknesses / Gaps</div>', unsafe_allow_html=True)
        render_numbered_list(analysis.weaknesses, "🔸")

    st.markdown("---")

    # ── Resume Improvements ──
    st.markdown('<div class="section-title">📝 Resume Improvement Suggestions</div>', unsafe_allow_html=True)
    render_numbered_list(analysis.suggested_improvements, "💡")

    st.markdown("---")

    # ── Suggested Keywords (two columns) ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">🟢 Safe to Emphasize</div>', unsafe_allow_html=True)
        render_skill_tags(analysis.suggested_keywords_to_emphasize, "skill-emphasize", "keywords to emphasize")

    with col2:
        st.markdown('<div class="section-title">📚 Should Learn</div>', unsafe_allow_html=True)
        render_skill_tags(analysis.suggested_keywords_to_learn, "skill-learn", "keywords to learn")

    st.markdown("---")

    # ── Interview Preparation ──
    st.markdown('<div class="section-title">🎯 Interview Preparation Topics</div>', unsafe_allow_html=True)
    render_numbered_list(analysis.interview_topics, "📌")

    st.markdown("---")

    # ── Download Section ──
    st.markdown('<div class="section-title">📥 Download Report</div>', unsafe_allow_html=True)

    col1, col2, _ = st.columns([1, 1, 2])

    json_report = generate_json_report(full_report)
    text_report = generate_text_report(full_report)

    with col1:
        st.download_button(
            label="📄 Download as JSON",
            data=json_report,
            file_name="resume_analysis.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        st.download_button(
            label="📝 Download as TXT",
            data=text_report,
            file_name="resume_analysis.txt",
            mime="text/plain",
            use_container_width=True,
        )


# ─────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────
def main():
    """Main application entry point."""

    # Render sidebar and get config
    config = render_sidebar()

    # Render header
    render_header()

    # ── Section 1: Upload Resume ──
    resume_text, page_count, filename = render_upload_section()

    st.markdown("")

    # ── Section 2: Job Description ──
    job_description = render_jd_section()

    st.markdown("")

    # ── Section 3: Analyze ──
    analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])

    with analyze_col2:
        analyze_clicked = st.button(
            "🔍 Analyze Resume",
            use_container_width=True,
            type="primary",
        )

    if analyze_clicked:
        # Validation
        if not config["api_key"]:
            st.error("❌ Please enter your OpenAI API key in the sidebar.")
            return

        if not resume_text:
            st.error("❌ Please upload a resume PDF first.")
            return

        if not job_description or not job_description.strip():
            st.error("❌ Please paste a job description.")
            return

        if len(job_description.strip()) < 50:
            st.warning("⚠️ The job description seems very short. For best results, paste the full JD.")

        # Truncate resume if too long
        processed_resume, was_truncated = truncate_text(resume_text)
        if was_truncated:
            st.info("ℹ️ Your resume was truncated to fit within the model's context window.")

        # Run analysis
        with st.spinner("🤖 Analyzing your resume... This may take 30-60 seconds."):
            try:
                # Create the LCEL chain
                chain, parser = create_analysis_chain(
                    api_key=config["api_key"],
                    model_name=config["model_name"],
                    temperature=config["temperature"],
                )

                # Run analysis with retry
                analysis = run_analysis(
                    chain=chain,
                    parser=parser,
                    resume_text=processed_resume,
                    job_description=job_description,
                )

                # Calculate deterministic score
                score_breakdown = calculate_score(analysis)

                # Create full report
                full_report = create_full_report(
                    analysis=analysis,
                    score_breakdown=score_breakdown,
                    resume_filename=filename or "unknown.pdf",
                )

                # Store in session state for persistence
                st.session_state["analysis"] = analysis
                st.session_state["score_breakdown"] = score_breakdown
                st.session_state["full_report"] = full_report

            except LLMChainError as e:
                st.error(f"❌ Analysis Error: {str(e)}")
                return
            except Exception as e:
                st.error(
                    "❌ An unexpected error occurred. Please try again. "
                    f"Error: {str(e)}"
                )
                return

    # ── Render Results (from session state) ──
    if "analysis" in st.session_state:
        render_results(
            st.session_state["analysis"],
            st.session_state["score_breakdown"],
            st.session_state["full_report"],
        )


if __name__ == "__main__":
    main()
