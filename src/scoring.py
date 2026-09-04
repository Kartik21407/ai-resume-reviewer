"""
Deterministic scoring system for resume analysis.

Takes the LLM's semantic sub-scores and applies weighted scoring
to produce a reproducible, explainable overall match score.
The LLM provides the semantic analysis; this module provides
the deterministic calculation.
"""

from src.schemas import ResumeAnalysis, ScoreBreakdown


# --- Scoring Weights (must sum to 100) ---
WEIGHTS = {
    "skill_match": 40,
    "keyword_match": 20,
    "experience_match": 20,
    "education_match": 10,
    "project_match": 10,
}

# --- Match Level Thresholds ---
STRONG_MATCH_THRESHOLD = 75
MODERATE_MATCH_THRESHOLD = 50


def _clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamp a value to the specified range.

    Args:
        value: The value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        Clamped value.
    """
    return max(min_val, min(max_val, float(value)))


def _get_match_level(score: float) -> str:
    """Determine the match level based on the overall score.

    Args:
        score: Overall score (0-100).

    Returns:
        Human-readable match level string.
    """
    if score >= STRONG_MATCH_THRESHOLD:
        return "Strong Match"
    elif score >= MODERATE_MATCH_THRESHOLD:
        return "Moderate Match"
    else:
        return "Weak Match"


def calculate_score(analysis: ResumeAnalysis) -> ScoreBreakdown:
    """Calculate the deterministic score breakdown from LLM sub-scores.

    The LLM provides 0-100 sub-scores for each category. This function
    applies the predefined weights to compute the final score.

    Formula:
        overall = (skill * 0.40) + (keyword * 0.20) + (experience * 0.20)
                + (education * 0.10) + (project * 0.10)

    Args:
        analysis: Validated ResumeAnalysis from the LLM.

    Returns:
        ScoreBreakdown with raw scores, weighted scores, and overall.
    """
    # Extract and clamp raw scores
    skill_raw = _clamp(analysis.skill_match_score)
    keyword_raw = _clamp(analysis.keyword_match_score)
    experience_raw = _clamp(analysis.experience_match_score)
    education_raw = _clamp(analysis.education_match_score)
    project_raw = _clamp(analysis.project_match_score)

    # Calculate weighted scores
    skill_weighted = round(skill_raw * WEIGHTS["skill_match"] / 100, 1)
    keyword_weighted = round(keyword_raw * WEIGHTS["keyword_match"] / 100, 1)
    experience_weighted = round(experience_raw * WEIGHTS["experience_match"] / 100, 1)
    education_weighted = round(education_raw * WEIGHTS["education_match"] / 100, 1)
    project_weighted = round(project_raw * WEIGHTS["project_match"] / 100, 1)

    # Calculate overall score
    overall = round(
        skill_weighted
        + keyword_weighted
        + experience_weighted
        + education_weighted
        + project_weighted,
        1,
    )
    overall = _clamp(overall)

    # Determine match level
    match_level = _get_match_level(overall)

    return ScoreBreakdown(
        skill_match_raw=skill_raw,
        skill_match_weighted=skill_weighted,
        keyword_match_raw=keyword_raw,
        keyword_match_weighted=keyword_weighted,
        experience_match_raw=experience_raw,
        experience_match_weighted=experience_weighted,
        education_match_raw=education_raw,
        education_match_weighted=education_weighted,
        project_match_raw=project_raw,
        project_match_weighted=project_weighted,
        overall_score=overall,
        match_level=match_level,
    )


def get_weight_description() -> list[dict]:
    """Get the scoring weights as a descriptive list for UI display.

    Returns:
        List of dicts with category, weight, and max_score.
    """
    return [
        {"category": "Skill Match", "weight": WEIGHTS["skill_match"], "max_score": WEIGHTS["skill_match"]},
        {"category": "Keyword Match", "weight": WEIGHTS["keyword_match"], "max_score": WEIGHTS["keyword_match"]},
        {"category": "Experience Match", "weight": WEIGHTS["experience_match"], "max_score": WEIGHTS["experience_match"]},
        {"category": "Education Match", "weight": WEIGHTS["education_match"], "max_score": WEIGHTS["education_match"]},
        {"category": "Project Match", "weight": WEIGHTS["project_match"], "max_score": WEIGHTS["project_match"]},
    ]


def validate_weights() -> bool:
    """Verify that scoring weights sum to 100.

    Returns:
        True if weights sum to 100.

    Raises:
        ValueError: If weights do not sum to 100.
    """
    total = sum(WEIGHTS.values())
    if total != 100:
        raise ValueError(
            f"Scoring weights must sum to 100, but got {total}. "
            f"Current weights: {WEIGHTS}"
        )
    return True
