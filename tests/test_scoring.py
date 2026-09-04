"""
Unit tests for the deterministic scoring system.

Tests cover:
- 0% match (all scores zero)
- 50% match (midpoint scores)
- 100% match (perfect scores)
- Boundary conditions (clamping, edge cases)
- Weight validation
- Match level thresholds
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.schemas import ResumeAnalysis
from src.scoring import (
    MODERATE_MATCH_THRESHOLD,
    STRONG_MATCH_THRESHOLD,
    WEIGHTS,
    _clamp,
    _get_match_level,
    calculate_score,
    validate_weights,
)


# ─── Helpers ───────────────────────────────────────────


def _make_analysis(**overrides) -> ResumeAnalysis:
    """Create a ResumeAnalysis with defaults for testing."""
    defaults = {
        "matched_skills": ["Python"],
        "missing_skills": ["Docker"],
        "matched_keywords": ["API"],
        "missing_keywords": ["AWS"],
        "experience_match": "Meets requirements.",
        "education_match": "Meets requirements.",
        "project_relevance": "Relevant projects.",
        "strengths": ["Strong Python skills"],
        "weaknesses": ["No Docker experience"],
        "suggested_improvements": ["Add Docker"],
        "suggested_keywords_to_emphasize": ["Python"],
        "suggested_keywords_to_learn": ["Docker"],
        "interview_topics": ["Python OOP"],
        "skill_match_score": 50,
        "keyword_match_score": 50,
        "experience_match_score": 50,
        "education_match_score": 50,
        "project_match_score": 50,
    }
    defaults.update(overrides)
    return ResumeAnalysis(**defaults)


# ─── Weight Validation ─────────────────────────────────


class TestWeights:
    """Tests for scoring weight configuration."""

    def test_weights_sum_to_100(self):
        """Weights must sum to exactly 100."""
        assert sum(WEIGHTS.values()) == 100

    def test_validate_weights_passes(self):
        """validate_weights() should return True when weights are correct."""
        assert validate_weights() is True

    def test_all_weights_positive(self):
        """All weights must be positive."""
        for key, val in WEIGHTS.items():
            assert val > 0, f"Weight for '{key}' must be positive, got {val}"


# ─── Clamp Function ───────────────────────────────────


class TestClamp:
    """Tests for the _clamp helper."""

    def test_clamp_in_range(self):
        assert _clamp(50.0) == 50.0

    def test_clamp_below_min(self):
        assert _clamp(-10.0) == 0.0

    def test_clamp_above_max(self):
        assert _clamp(150.0) == 100.0

    def test_clamp_at_boundaries(self):
        assert _clamp(0.0) == 0.0
        assert _clamp(100.0) == 100.0


# ─── Match Level ──────────────────────────────────────


class TestMatchLevel:
    """Tests for match level classification."""

    def test_strong_match(self):
        assert _get_match_level(STRONG_MATCH_THRESHOLD) == "Strong Match"
        assert _get_match_level(100.0) == "Strong Match"

    def test_moderate_match(self):
        assert _get_match_level(MODERATE_MATCH_THRESHOLD) == "Moderate Match"
        assert _get_match_level(STRONG_MATCH_THRESHOLD - 0.1) == "Moderate Match"

    def test_weak_match(self):
        assert _get_match_level(0.0) == "Weak Match"
        assert _get_match_level(MODERATE_MATCH_THRESHOLD - 0.1) == "Weak Match"


# ─── Score Calculation ────────────────────────────────


class TestCalculateScore:
    """Tests for the main scoring function."""

    def test_zero_percent_match(self):
        """All scores at 0 should yield overall 0."""
        analysis = _make_analysis(
            skill_match_score=0,
            keyword_match_score=0,
            experience_match_score=0,
            education_match_score=0,
            project_match_score=0,
        )
        breakdown = calculate_score(analysis)

        assert breakdown.overall_score == 0.0
        assert breakdown.skill_match_weighted == 0.0
        assert breakdown.keyword_match_weighted == 0.0
        assert breakdown.experience_match_weighted == 0.0
        assert breakdown.education_match_weighted == 0.0
        assert breakdown.project_match_weighted == 0.0
        assert breakdown.match_level == "Weak Match"

    def test_fifty_percent_match(self):
        """All scores at 50 should yield overall 50."""
        analysis = _make_analysis(
            skill_match_score=50,
            keyword_match_score=50,
            experience_match_score=50,
            education_match_score=50,
            project_match_score=50,
        )
        breakdown = calculate_score(analysis)

        assert breakdown.overall_score == 50.0
        assert breakdown.skill_match_weighted == 20.0  # 50 * 40/100
        assert breakdown.keyword_match_weighted == 10.0  # 50 * 20/100
        assert breakdown.experience_match_weighted == 10.0  # 50 * 20/100
        assert breakdown.education_match_weighted == 5.0  # 50 * 10/100
        assert breakdown.project_match_weighted == 5.0  # 50 * 10/100
        assert breakdown.match_level == "Moderate Match"

    def test_hundred_percent_match(self):
        """All scores at 100 should yield overall 100."""
        analysis = _make_analysis(
            skill_match_score=100,
            keyword_match_score=100,
            experience_match_score=100,
            education_match_score=100,
            project_match_score=100,
        )
        breakdown = calculate_score(analysis)

        assert breakdown.overall_score == 100.0
        assert breakdown.skill_match_weighted == 40.0
        assert breakdown.keyword_match_weighted == 20.0
        assert breakdown.experience_match_weighted == 20.0
        assert breakdown.education_match_weighted == 10.0
        assert breakdown.project_match_weighted == 10.0
        assert breakdown.match_level == "Strong Match"

    def test_mixed_scores(self):
        """Mixed scores should yield correct weighted total."""
        analysis = _make_analysis(
            skill_match_score=85,
            keyword_match_score=80,
            experience_match_score=75,
            education_match_score=80,
            project_match_score=90,
        )
        breakdown = calculate_score(analysis)

        # Manual calculation:
        # 85 * 0.40 = 34.0
        # 80 * 0.20 = 16.0
        # 75 * 0.20 = 15.0
        # 80 * 0.10 = 8.0
        # 90 * 0.10 = 9.0
        # Total = 82.0
        assert breakdown.skill_match_weighted == 34.0
        assert breakdown.keyword_match_weighted == 16.0
        assert breakdown.experience_match_weighted == 15.0
        assert breakdown.education_match_weighted == 8.0
        assert breakdown.project_match_weighted == 9.0
        assert breakdown.overall_score == 82.0
        assert breakdown.match_level == "Strong Match"

    def test_raw_scores_preserved(self):
        """Raw scores should be preserved in breakdown."""
        analysis = _make_analysis(
            skill_match_score=73,
            keyword_match_score=62,
            experience_match_score=88,
            education_match_score=45,
            project_match_score=91,
        )
        breakdown = calculate_score(analysis)

        assert breakdown.skill_match_raw == 73.0
        assert breakdown.keyword_match_raw == 62.0
        assert breakdown.experience_match_raw == 88.0
        assert breakdown.education_match_raw == 45.0
        assert breakdown.project_match_raw == 91.0

    def test_threshold_boundary_strong(self):
        """Score exactly at strong threshold should be Strong Match."""
        analysis = _make_analysis(
            skill_match_score=75,
            keyword_match_score=75,
            experience_match_score=75,
            education_match_score=75,
            project_match_score=75,
        )
        breakdown = calculate_score(analysis)
        assert breakdown.overall_score == 75.0
        assert breakdown.match_level == "Strong Match"

    def test_threshold_boundary_moderate(self):
        """Score exactly at moderate threshold should be Moderate Match."""
        analysis = _make_analysis(
            skill_match_score=50,
            keyword_match_score=50,
            experience_match_score=50,
            education_match_score=50,
            project_match_score=50,
        )
        breakdown = calculate_score(analysis)
        assert breakdown.overall_score == 50.0
        assert breakdown.match_level == "Moderate Match"

    def test_just_below_strong_threshold(self):
        """Score just below strong threshold should be Moderate Match."""
        # We need overall to be just below 75
        # With all scores at 74: 74*0.4 + 74*0.2 + 74*0.2 + 74*0.1 + 74*0.1 = 74
        analysis = _make_analysis(
            skill_match_score=74,
            keyword_match_score=74,
            experience_match_score=74,
            education_match_score=74,
            project_match_score=74,
        )
        breakdown = calculate_score(analysis)
        assert breakdown.overall_score < STRONG_MATCH_THRESHOLD
        assert breakdown.match_level == "Moderate Match"


# ─── Entry Point ──────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
