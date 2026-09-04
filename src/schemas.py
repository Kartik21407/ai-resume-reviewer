"""
Pydantic schemas for structured LLM output and scoring.

Defines the data models that enforce structured output from the LLM,
the deterministic scoring breakdown, and the full analysis report
used for downloads.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator


class ResumeAnalysis(BaseModel):
    """Structured output schema for the LLM resume analysis.

    The LLM must return data conforming to this schema. Sub-scores
    are 0-100 integers that feed into the deterministic scoring system.
    """

    # --- Skill Analysis ---
    matched_skills: List[str] = Field(
        description="List of skills found in the resume that match the job description."
    )
    missing_skills: List[str] = Field(
        description="List of skills required by the job description but not found in the resume."
    )

    # --- Keyword Analysis ---
    matched_keywords: List[str] = Field(
        description="List of important keywords from the job description found in the resume."
    )
    missing_keywords: List[str] = Field(
        description="List of important keywords from the job description NOT found in the resume."
    )

    # --- Qualitative Analysis ---
    experience_match: str = Field(
        description=(
            "Detailed analysis of how the candidate's experience aligns with "
            "the job requirements. Include required vs. actual experience."
        )
    )
    education_match: str = Field(
        description=(
            "Detailed analysis of how the candidate's education aligns with "
            "the job requirements."
        )
    )
    project_relevance: str = Field(
        description=(
            "Detailed analysis of how the candidate's projects relate to "
            "the job requirements. Mention specific projects and technologies."
        )
    )

    # --- Strengths & Weaknesses ---
    strengths: List[str] = Field(
        description="3 to 7 specific strengths of the candidate relative to this job."
    )
    weaknesses: List[str] = Field(
        description=(
            "Concrete, actionable gaps or weaknesses. Avoid vague statements. "
            "Each weakness should be specific and constructive."
        )
    )

    # --- Suggestions ---
    suggested_improvements: List[str] = Field(
        description=(
            "Specific, actionable resume improvement suggestions. "
            "Never recommend adding skills the candidate does not possess."
        )
    )
    suggested_keywords_to_emphasize: List[str] = Field(
        description=(
            "Keywords from the job description that the candidate appears to have "
            "evidence for and should emphasize more prominently."
        )
    )
    suggested_keywords_to_learn: List[str] = Field(
        description=(
            "Keywords from the job description that the candidate appears to lack. "
            "These are skills/technologies the candidate should learn."
        )
    )
    interview_topics: List[str] = Field(
        description=(
            "Suggested interview preparation topics based on the job requirements "
            "and the candidate's profile."
        )
    )

    # --- Numeric Sub-Scores (0-100) for Deterministic Scoring ---
    skill_match_score: int = Field(
        ge=0, le=100,
        description="Skill match score from 0 to 100."
    )
    keyword_match_score: int = Field(
        ge=0, le=100,
        description="Keyword match score from 0 to 100."
    )
    experience_match_score: int = Field(
        ge=0, le=100,
        description="Experience match score from 0 to 100."
    )
    education_match_score: int = Field(
        ge=0, le=100,
        description="Education match score from 0 to 100."
    )
    project_match_score: int = Field(
        ge=0, le=100,
        description="Project relevance match score from 0 to 100."
    )

    @field_validator(
        "skill_match_score",
        "keyword_match_score",
        "experience_match_score",
        "education_match_score",
        "project_match_score",
        mode="before",
    )
    @classmethod
    def clamp_score(cls, v: int) -> int:
        """Clamp scores to 0-100 range for safety."""
        if isinstance(v, (int, float)):
            return max(0, min(100, int(v)))
        return v


class ScoreBreakdown(BaseModel):
    """Deterministic scoring breakdown computed from LLM sub-scores."""

    skill_match_raw: float = Field(description="Raw skill match (0-100).")
    skill_match_weighted: float = Field(description="Weighted skill match (0-40).")

    keyword_match_raw: float = Field(description="Raw keyword match (0-100).")
    keyword_match_weighted: float = Field(description="Weighted keyword match (0-20).")

    experience_match_raw: float = Field(description="Raw experience match (0-100).")
    experience_match_weighted: float = Field(description="Weighted experience match (0-20).")

    education_match_raw: float = Field(description="Raw education match (0-100).")
    education_match_weighted: float = Field(description="Weighted education match (0-10).")

    project_match_raw: float = Field(description="Raw project match (0-100).")
    project_match_weighted: float = Field(description="Weighted project match (0-10).")

    overall_score: float = Field(description="Final weighted score (0-100).")
    match_level: str = Field(description="Strong Match / Moderate Match / Weak Match.")


class FullAnalysisReport(BaseModel):
    """Complete analysis report combining LLM output and deterministic scoring."""

    resume_analysis: ResumeAnalysis
    score_breakdown: ScoreBreakdown
    resume_filename: str = Field(default="unknown.pdf")
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
