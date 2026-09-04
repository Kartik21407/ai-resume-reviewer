"""
PDF loading and text extraction using PyPDFLoader.

Handles file upload from Streamlit, temporary file management,
text extraction from all pages, and comprehensive error handling.
"""

import os
import tempfile
from typing import Tuple

from langchain_community.document_loaders import PyPDFLoader

from src.text_processing import clean_text, validate_text_content


class PDFLoadError(Exception):
    """Custom exception for PDF loading errors."""
    pass


def load_pdf_from_upload(uploaded_file) -> Tuple[str, int]:
    """Extract text from a Streamlit uploaded PDF file.

    Saves the uploaded file to a temporary location, uses PyPDFLoader
    to extract text from all pages, then cleans up.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        Tuple of (extracted_text, page_count).

    Raises:
        PDFLoadError: If the PDF cannot be loaded or contains no text.
    """
    if uploaded_file is None:
        raise PDFLoadError("No file was uploaded.")

    if not uploaded_file.name.lower().endswith(".pdf"):
        raise PDFLoadError(
            f"Invalid file type: '{uploaded_file.name}'. Please upload a PDF file."
        )

    # Check file size (limit to 10 MB)
    file_size = uploaded_file.size
    max_size = 10 * 1024 * 1024  # 10 MB
    if file_size > max_size:
        raise PDFLoadError(
            f"File is too large ({file_size / (1024*1024):.1f} MB). "
            f"Maximum allowed size is {max_size / (1024*1024):.0f} MB."
        )

    tmp_path = None
    try:
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix="resume_"
        ) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        # Load and extract text using PyPDFLoader
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()

        if not pages:
            raise PDFLoadError(
                "The PDF appears to be empty or could not be parsed. "
                "Please ensure the PDF contains readable text."
            )

        page_count = len(pages)

        # Combine text from all pages
        raw_text = "\n\n".join(
            page.page_content for page in pages if page.page_content
        )

        # Clean the extracted text
        cleaned_text = clean_text(raw_text)

        # Validate that meaningful text was extracted
        if not validate_text_content(cleaned_text):
            raise PDFLoadError(
                "Could not extract meaningful text from the PDF. "
                "This may be a scanned or image-only PDF. "
                "Please ensure your resume contains selectable text, not just images."
            )

        return cleaned_text, page_count

    except PDFLoadError:
        raise  # Re-raise our custom errors
    except Exception as e:
        raise PDFLoadError(
            f"Failed to process the PDF file: {str(e)}. "
            "Please ensure the file is a valid, non-corrupted PDF."
        ) from e
    finally:
        # Clean up temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # Best-effort cleanup
