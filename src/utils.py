"""
Utility functions for report generation and UI helpers.

Provides JSON and text report generation, color coding,
and other shared utilities.
"""

import json
from datetime import datetime

from src.schemas import FullAnalysisReport, ResumeAnalysis, ScoreBreakdown


def create_full_report(
    analysis: ResumeAnalysis,
    score_breakdown: ScoreBreakdown,
    resume_filename: str = "unknown.pdf",
) -> FullAnalysisReport:
    """Create a complete analysis report.

    Args:
        analysis: Validated LLM analysis output.
        score_breakdown: Deterministic score breakdown.
        resume_filename: Original filename of the resume.

    Returns:
        FullAnalysisReport combining all data.
    """
    return FullAnalysisReport(
        resume_analysis=analysis,
        score_breakdown=score_breakdown,
        resume_filename=resume_filename,
        analysis_timestamp=datetime.now().isoformat(),
    )


def generate_json_report(report: FullAnalysisReport) -> str:
    """Serialize the full report to pretty-printed JSON.

    Args:
        report: The complete analysis report.

    Returns:
        JSON string.
    """
    return json.dumps(report.model_dump(), indent=2, ensure_ascii=False)


def generate_text_report(report: FullAnalysisReport) -> str:
    """Generate a human-readable text report.

    Args:
        report: The complete analysis report.

    Returns:
        Formatted text string.
    """
    a = report.resume_analysis
    s = report.score_breakdown

    lines = [
        "=" * 60,
        "  AI RESUME REVIEWER — ANALYSIS REPORT",
        "=" * 60,
        f"  Resume: {report.resume_filename}",
        f"  Date:   {report.analysis_timestamp}",
        "=" * 60,
        "",
        "─" * 40,
        f"  OVERALL MATCH SCORE: {s.overall_score:.0f}/100  ({s.match_level})",
        "─" * 40,
        "",
        "  SCORE BREAKDOWN",
        "  ───────────────────────────────────",
        f"  Skill Match:       {s.skill_match_weighted:.1f}/{40}  (raw: {s.skill_match_raw:.0f}/100)",
        f"  Keyword Match:     {s.keyword_match_weighted:.1f}/{20}  (raw: {s.keyword_match_raw:.0f}/100)",
        f"  Experience Match:  {s.experience_match_weighted:.1f}/{20}  (raw: {s.experience_match_raw:.0f}/100)",
        f"  Education Match:   {s.education_match_weighted:.1f}/{10}  (raw: {s.education_match_raw:.0f}/100)",
        f"  Project Match:     {s.project_match_weighted:.1f}/{10}  (raw: {s.project_match_raw:.0f}/100)",
        "  ───────────────────────────────────",
        f"  TOTAL:             {s.overall_score:.1f}/100",
        "",
        "─" * 40,
        "  MATCHED SKILLS",
        "─" * 40,
    ]
    for skill in a.matched_skills:
        lines.append(f"  ✓ {skill}")

    lines.extend([
        "",
        "─" * 40,
        "  MISSING SKILLS",
        "─" * 40,
    ])
    for skill in a.missing_skills:
        lines.append(f"  ✗ {skill}")

    lines.extend([
        "",
        "─" * 40,
        "  MATCHED KEYWORDS",
        "─" * 40,
    ])
    for kw in a.matched_keywords:
        lines.append(f"  ✓ {kw}")

    lines.extend([
        "",
        "─" * 40,
        "  MISSING KEYWORDS",
        "─" * 40,
    ])
    for kw in a.missing_keywords:
        lines.append(f"  ✗ {kw}")

    lines.extend([
        "",
        "─" * 40,
        "  EXPERIENCE ANALYSIS",
        "─" * 40,
        f"  {a.experience_match}",
        "",
        "─" * 40,
        "  EDUCATION ANALYSIS",
        "─" * 40,
        f"  {a.education_match}",
        "",
        "─" * 40,
        "  PROJECT RELEVANCE",
        "─" * 40,
        f"  {a.project_relevance}",
    ])

    lines.extend([
        "",
        "─" * 40,
        "  STRENGTHS",
        "─" * 40,
    ])
    for i, s_item in enumerate(a.strengths, 1):
        lines.append(f"  {i}. {s_item}")

    lines.extend([
        "",
        "─" * 40,
        "  WEAKNESSES / GAPS",
        "─" * 40,
    ])
    for i, w_item in enumerate(a.weaknesses, 1):
        lines.append(f"  {i}. {w_item}")

    lines.extend([
        "",
        "─" * 40,
        "  RESUME IMPROVEMENT SUGGESTIONS",
        "─" * 40,
    ])
    for i, imp in enumerate(a.suggested_improvements, 1):
        lines.append(f"  {i}. {imp}")

    lines.extend([
        "",
        "─" * 40,
        "  KEYWORDS TO EMPHASIZE (Safe to Add)",
        "─" * 40,
    ])
    for kw in a.suggested_keywords_to_emphasize:
        lines.append(f"  → {kw}")

    lines.extend([
        "",
        "─" * 40,
        "  KEYWORDS TO LEARN (Missing)",
        "─" * 40,
    ])
    for kw in a.suggested_keywords_to_learn:
        lines.append(f"  → {kw}")

    lines.extend([
        "",
        "─" * 40,
        "  INTERVIEW PREPARATION TOPICS",
        "─" * 40,
    ])
    for i, topic in enumerate(a.interview_topics, 1):
        lines.append(f"  {i}. {topic}")

    lines.extend(["", "=" * 60, "  End of Report", "=" * 60])

    return "\n".join(lines)


def get_score_color(score: float) -> str:
    """Get a hex color based on the score value.

    Args:
        score: Score value (0-100).

    Returns:
        Hex color string.
    """
    if score >= 75:
        return "#10B981"  # Emerald green
    elif score >= 50:
        return "#F59E0B"  # Amber
    else:
        return "#EF4444"  # Red


def get_match_level_emoji(match_level: str) -> str:
    """Get an emoji for the match level.

    Args:
        match_level: "Strong Match", "Moderate Match", or "Weak Match".

    Returns:
        Emoji string.
    """
    emoji_map = {
        "Strong Match": "🟢",
        "Moderate Match": "🟡",
        "Weak Match": "🔴",
    }
    return emoji_map.get(match_level, "⚪")
