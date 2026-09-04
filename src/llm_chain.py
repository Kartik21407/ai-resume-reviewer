"""
LangChain LCEL chain for resume analysis.

Builds the prompt | llm | parser pipeline and provides
invocation with retry/fallback logic.
Supports Google Gemini via langchain-google-genai.
"""

import logging
from typing import Optional

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from src.prompts import get_analysis_prompt
from src.schemas import ResumeAnalysis

logger = logging.getLogger(__name__)


class LLMChainError(Exception):
    """Custom exception for LLM chain errors."""
    pass


def create_parser() -> PydanticOutputParser:
    """Create the PydanticOutputParser for ResumeAnalysis.

    Returns:
        Configured PydanticOutputParser instance.
    """
    return PydanticOutputParser(pydantic_object=ResumeAnalysis)


def create_llm(
    api_key: str,
    model_name: str = "gemini-3.1-flash-lite",
    temperature: float = 0.2,
) -> ChatGoogleGenerativeAI:
    """Create the ChatGoogleGenerativeAI LLM instance.

    Args:
        api_key: Google API key.
        model_name: Gemini model identifier.
        temperature: Sampling temperature (0.0-1.0).

    Returns:
        Configured ChatGoogleGenerativeAI instance.
    """
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        max_retries=2,
        timeout=120,
    )


def create_analysis_chain(
    api_key: str,
    model_name: str = "gemini-3.1-flash-lite",
    temperature: float = 0.2,
):
    """Build the LCEL chain: prompt | llm | parser.

    Args:
        api_key: Google API key.
        model_name: Gemini model identifier.
        temperature: Sampling temperature.

    Returns:
        A RunnableSequence chain (prompt | llm | parser).
    """
    if not api_key or not api_key.strip():
        raise LLMChainError("Google API key is required.")

    prompt = get_analysis_prompt()
    llm = create_llm(api_key, model_name, temperature)
    parser = create_parser()

    # LCEL chain: prompt | llm | parser
    chain = prompt | llm | parser

    return chain, parser


def run_analysis(
    chain,
    parser: PydanticOutputParser,
    resume_text: str,
    job_description: str,
    max_retries: int = 2,
) -> ResumeAnalysis:
    """Run the analysis chain with retry logic.

    Invokes the LCEL chain and handles parsing failures with
    retries. On the retry, the raw LLM output is fed back with
    repair instructions.

    Args:
        chain: The LCEL chain (prompt | llm | parser).
        parser: The PydanticOutputParser instance.
        resume_text: Cleaned resume text.
        job_description: Job description text.
        max_retries: Maximum number of retry attempts.

    Returns:
        Validated ResumeAnalysis instance.

    Raises:
        LLMChainError: If analysis fails after all retries.
    """
    format_instructions = parser.get_format_instructions()

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Analysis attempt {attempt}/{max_retries}")

            result = chain.invoke(
                {
                    "resume_text": resume_text,
                    "job_description": job_description,
                    "format_instructions": format_instructions,
                }
            )

            # Result should already be a ResumeAnalysis if parser succeeded
            if isinstance(result, ResumeAnalysis):
                logger.info("Analysis completed successfully.")
                return result

            # If somehow we got a non-parsed result, try parsing it
            if isinstance(result, str):
                return parser.parse(result)

            raise LLMChainError(
                f"Unexpected result type: {type(result).__name__}"
            )

        except OutputParserException as e:
            last_error = e
            logger.warning(
                f"Attempt {attempt} failed with parsing error: {str(e)[:200]}"
            )
            if attempt < max_retries:
                logger.info("Retrying with adjusted parameters...")
                continue

        except Exception as e:
            last_error = e
            error_msg = str(e).lower()

            if "api key" in error_msg or "authentication" in error_msg or "api_key" in error_msg:
                raise LLMChainError(
                    "Invalid Google API key. Please check your API key and try again."
                ) from e

            if "rate limit" in error_msg or "rate_limit" in error_msg or "quota" in error_msg:
                raise LLMChainError(
                    "API rate limit / quota reached. Please wait a moment and try again."
                ) from e

            if "timeout" in error_msg:
                raise LLMChainError(
                    "Request timed out. The resume may be too long, or the API "
                    "is experiencing high load. Please try again."
                ) from e

            if "connection" in error_msg or "network" in error_msg:
                raise LLMChainError(
                    "Network error. Please check your internet connection and try again."
                ) from e

            logger.error(f"Attempt {attempt} failed: {str(e)[:200]}")
            if attempt < max_retries:
                continue

    # All retries exhausted
    raise LLMChainError(
        f"Analysis failed after {max_retries} attempts. "
        f"Last error: {str(last_error)[:300]}. "
        "Please try again or use a different model."
    )
