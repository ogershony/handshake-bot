import os

from dotenv import load_dotenv
from PyPDF2 import PdfReader

import constants as const
from cover_letter_generator import generate_cover_letter

load_dotenv()

COVER_LETTER_DIR = "documents/cover_letters"


def test_generate_cover_letter_integration():
    """
    End-to-end test: reads the real resume, calls OpenAI, generates a cover letter PDF,
    and verifies the output file.
    """
    job_id = 99999
    job_desc = (
        "Software Engineer Intern at Acme Corp. "
        "Requirements: Python, REST APIs, teamwork. "
        "Location: San Francisco, CA."
    )
    config = {const.RESUME_PATH: os.getenv("RESUME_PATH", "documents/resume.pdf")}

    os.environ["COVER_LETTER_PATH"] = COVER_LETTER_DIR

    result = generate_cover_letter(job_desc, job_id, config)

    expected_path = os.path.join(COVER_LETTER_DIR, f"{job_id}.pdf")

    # Returns the correct path
    assert result == expected_path

    # File exists and is non-empty
    assert os.path.isfile(result)
    assert os.path.getsize(result) > 0

    # File is a valid PDF with content
    reader = PdfReader(result)
    assert len(reader.pages) >= 1
    text = reader.pages[0].extract_text()
    assert len(text) > 50, f"Cover letter text too short: {text}"

    print(f"\nGenerated cover letter ({len(text)} chars):\n{text[:500]}")


test_generate_cover_letter_integration()
