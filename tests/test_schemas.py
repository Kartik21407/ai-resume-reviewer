"""
Unit tests for Pydantic schema validation.

Tests cover:
- Valid data parsing
- Missing required fields
- Score range validation (clamping)
- FullAnalysisReport serialization
- Edge cases
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.schemas import FullAnalysisReport, ResumeAnalysis, ScoreBreakdown


# ─── Helpers ───────────────────────────────────────────


def _valid_analysis_data() -> dict:
    """Return a complete, valid ResumeAnalysis data dict."""
    return {
        "matched_skills": ["Python", "SQL", "Machine Learning"],
        "missing_skills": ["Docker", "Kubernetes"],
        "matched_keywords": ["REST API", "Data Analysis"],
        "missing_keywords": ["CI/CD", "AWS"],
        "experience_match": "3 years of relevant experience vs 2+ required.",
        "education_match": "B.S. Computer Science matches requirement.",
        "project_relevance": "ML project directly relevant to job.",
        "strengths": ["Strong Python skills", "ML experience", "Data analysis"],
        "weaknesses": ["No containerization experience", "No cloud platform exposure"],
        "suggested_improvements": ["Add quantified project metrics"],
        "suggested_keywords_to_emphasize": ["Python", "Machine Learning"],
        "suggested_keywords_to_learn": ["Docker", "AWS"],
        "interview_topics": ["Python OOP", "SQL joins", "ML basics"],
        "skill_match_score": 75,
        "keyword_match_score": 60,
        "experience_match_score": 80,
        "education_match_score": 90,
        "project_match_score": 70,
    }


def _valid_breakdown_data() -> dict:
    """Return a complete, valid ScoreBreakdown data dict."""
    return {
        "skill_match_raw": 75.0,
        "skill_match_weighted": 30.0,
        "keyword_match_raw": 60.0,
        "keyword_match_weighted": 12.0,
        "experience_match_raw": 80.0,
        "experience_match_weighted": 16.0,
        "education_match_raw": 90.0,
        "education_match_weighted": 9.0,
        "project_match_raw": 70.0,
        "project_match_weighted": 7.0,
        "overall_score": 74.0,
        "match_level": "Moderate Match",
    }


# ─── ResumeAnalysis Validation ─────────────────────────


class TestResumeAnalysis:
    """Tests for ResumeAnalysis schema."""

    def test_valid_data(self):
        """Valid data should parse successfully."""
        data = _valid_analysis_data()
        analysis = ResumeAnalysis(**data)

        assert analysis.skill_match_score == 75
        assert len(analysis.matched_skills) == 3
        assert "Python" in analysis.matched_skills

    def test_missing_required_field(self):
        """Missing required fields should raise ValidationError."""
        data = _valid_analysis_data()
        del data["matched_skills"]

        with pytest.raises(ValidationError):
            ResumeAnalysis(**data)

    def test_missing_score_field(self):
        """Missing score fields should raise ValidationError."""
        data = _valid_analysis_data()
        del data["skill_match_score"]

        with pytest.raises(ValidationError):
            ResumeAnalysis(**data)

    def test_score_clamping_above_100(self):
        """Scores above 100 should be clamped to 100."""
        data = _valid_analysis_data()
        data["skill_match_score"] = 150

        analysis = ResumeAnalysis(**data)
        assert analysis.skill_match_score == 100

    def test_score_clamping_below_0(self):
        """Scores below 0 should be clamped to 0."""
        data = _valid_analysis_data()
        data["keyword_match_score"] = -20

        analysis = ResumeAnalysis(**data)
        assert analysis.keyword_match_score == 0

    def test_all_scores_clamped(self):
        """All score fields should be clamped."""
        data = _valid_analysis_data()
        data["skill_match_score"] = 200
        data["keyword_match_score"] = -50
        data["experience_match_score"] = 999
        data["education_match_score"] = -1
        data["project_match_score"] = 101

        analysis = ResumeAnalysis(**data)
        assert analysis.skill_match_score == 100
        assert analysis.keyword_match_score == 0
        assert analysis.experience_match_score == 100
        assert analysis.education_match_score == 0
        assert analysis.project_match_score == 100

    def test_empty_lists_are_valid(self):
        """Empty lists should be accepted."""
        data = _valid_analysis_data()
        data["matched_skills"] = []
        data["missing_skills"] = []

        analysis = ResumeAnalysis(**data)
        assert analysis.matched_skills == []
        assert analysis.missing_skills == []

    def test_float_scores_converted_to_int(self):
        """Float scores should be converted to int."""
        data = _valid_analysis_data()
        data["skill_match_score"] = 75.8

        analysis = ResumeAnalysis(**data)
        assert analysis.skill_match_score == 75
        assert isinstance(analysis.skill_match_score, int)

    def test_boundary_score_0(self):
        """Score of exactly 0 should be valid."""
        data = _valid_analysis_data()
        data["skill_match_score"] = 0

        analysis = ResumeAnalysis(**data)
        assert analysis.skill_match_score == 0

    def test_boundary_score_100(self):
        """Score of exactly 100 should be valid."""
        data = _valid_analysis_data()
        data["skill_match_score"] = 100

        analysis = ResumeAnalysis(**data)
        assert analysis.skill_match_score == 100


# ─── ScoreBreakdown Validation ─────────────────────────


class TestScoreBreakdown:
    """Tests for ScoreBreakdown schema."""

    def test_valid_data(self):
        """Valid data should parse successfully."""
        data = _valid_breakdown_data()
        breakdown = ScoreBreakdown(**data)

        assert breakdown.overall_score == 74.0
        assert breakdown.match_level == "Moderate Match"

    def test_missing_field_raises(self):
        """Missing fields should raise ValidationError."""
        data = _valid_breakdown_data()
        del data["overall_score"]

        with pytest.raises(ValidationError):
            ScoreBreakdown(**data)


# ─── FullAnalysisReport Serialization ──────────────────


class TestFullAnalysisReport:
    """Tests for FullAnalysisReport serialization."""

    def test_full_report_creation(self):
        """Full report should combine analysis and breakdown."""
        analysis = ResumeAnalysis(**_valid_analysis_data())
        breakdown = ScoreBreakdown(**_valid_breakdown_data())

        report = FullAnalysisReport(
            resume_analysis=analysis,
            score_breakdown=breakdown,
            resume_filename="test_resume.pdf",
        )

        assert report.resume_filename == "test_resume.pdf"
        assert report.resume_analysis.skill_match_score == 75
        assert report.score_breakdown.overall_score == 74.0

    def test_json_serialization(self):
        """Full report should serialize to valid JSON."""
        analysis = ResumeAnalysis(**_valid_analysis_data())
        breakdown = ScoreBreakdown(**_valid_breakdown_data())

        report = FullAnalysisReport(
            resume_analysis=analysis,
            score_breakdown=breakdown,
            resume_filename="test.pdf",
        )

        json_str = json.dumps(report.model_dump(), indent=2)
        parsed = json.loads(json_str)

        assert parsed["resume_filename"] == "test.pdf"
        assert parsed["resume_analysis"]["skill_match_score"] == 75
        assert parsed["score_breakdown"]["overall_score"] == 74.0

    def test_timestamp_auto_generated(self):
        """Timestamp should be auto-generated if not provided."""
        analysis = ResumeAnalysis(**_valid_analysis_data())
        breakdown = ScoreBreakdown(**_valid_breakdown_data())

        report = FullAnalysisReport(
            resume_analysis=analysis,
            score_breakdown=breakdown,
        )

        # Should be a valid ISO timestamp
        timestamp = datetime.fromisoformat(report.analysis_timestamp)
        assert isinstance(timestamp, datetime)

    def test_default_filename(self):
        """Default filename should be 'unknown.pdf'."""
        analysis = ResumeAnalysis(**_valid_analysis_data())
        breakdown = ScoreBreakdown(**_valid_breakdown_data())

        report = FullAnalysisReport(
            resume_analysis=analysis,
            score_breakdown=breakdown,
        )

        assert report.resume_filename == "unknown.pdf"


# ─── Entry Point ──────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
