"""
Text processing utilities for resume text cleaning and normalization.

Handles whitespace normalization, character cleaning, content validation,
and safe truncation for LLM context limits.
"""

import re
from typing import Tuple


def clean_text(raw_text: str) -> str:
    """Clean and normalize extracted resume text.

    Args:
        raw_text: Raw text extracted from PDF.

    Returns:
        Cleaned, normalized text.
    """
    if not raw_text:
        return ""

    text = raw_text

    # Remove non-printable characters (keep newlines, tabs, standard chars)
    text = re.sub(r"[^\x20-\x7E\n\t\r]", " ", text)

    # Normalize various whitespace characters
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple spaces into one (preserve newlines)
    text = re.sub(r"[^\S\n]+", " ", text)

    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Strip overall leading/trailing whitespace
    text = text.strip()

    return text


def truncate_text(text: str, max_chars: int = 15000) -> Tuple[str, bool]:
    """Safely truncate text to fit within LLM context limits.

    Truncates at the nearest sentence or paragraph boundary
    before max_chars.

    Args:
        text: Text to truncate.
        max_chars: Maximum character count.

    Returns:
        Tuple of (truncated_text, was_truncated).
    """
    if len(text) <= max_chars:
        return text, False

    # Try to truncate at a paragraph boundary
    truncated = text[:max_chars]
    last_para = truncated.rfind("\n\n")
    if last_para > max_chars * 0.7:
        return truncated[:last_para].strip(), True

    # Fall back to sentence boundary
    last_period = truncated.rfind(". ")
    if last_period > max_chars * 0.7:
        return truncated[: last_period + 1].strip(), True

    # Hard truncate as last resort
    return truncated.strip() + "\n\n[... text truncated ...]", True


def validate_text_content(text: str, min_meaningful_chars: int = 50) -> bool:
    """Check if extracted text has meaningful content.

    Detects cases where PDF extraction yielded very little or no
    useful text (e.g., scanned/image-only PDFs).

    Args:
        text: Cleaned text to validate.
        min_meaningful_chars: Minimum character threshold.

    Returns:
        True if the text appears to contain meaningful content.
    """
    if not text:
        return False

    # Remove whitespace and check remaining content length
    stripped = re.sub(r"\s+", "", text)
    if len(stripped) < min_meaningful_chars:
        return False

    # Check for a minimum number of alphabetic characters
    alpha_chars = sum(1 for c in stripped if c.isalpha())
    if alpha_chars < min_meaningful_chars * 0.5:
        return False

    return True


def get_text_stats(text: str) -> dict:
    """Get basic statistics about the text.

    Args:
        text: Text to analyze.

    Returns:
        Dictionary with word_count, char_count, line_count.
    """
    if not text:
        return {"word_count": 0, "char_count": 0, "line_count": 0}

    words = text.split()
    lines = text.split("\n")

    return {
        "word_count": len(words),
        "char_count": len(text),
        "line_count": len(lines),
    }
