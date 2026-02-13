# Configuration constants
INCLUDE_RESUME = "include_resume"
INCLUDE_TRANSCRIPT = "include_transcript"
INCLUDE_COVER_LETTER = "include_cover_letter"
USERNAME = "username"
PASSWORD = "password"
LOGIN_URL = "login_url"
SEARCH_URL = "search_url"
RESUME_PATH = "resume_path"
TRANSCRIPT_PATH = "transcript_path"
COVER_LETTER_PATH = "cover_letter_path"

# Job application constants
JOB_ID = "job_id"
JOB_TITLE = "job_title"
COMPANY_NAME = "company_name"
JOB_DESCRIPTION = "job_description"

# CSV constants
JOBS_CSV_FILE = "jobs.csv"
CSV_HEADER_JOB_ID = "Job ID"
CSV_HEADER_COMPANY = "Company"
CSV_HEADER_POSITION = "Position"
CSV_HEADER_RESUME = "Resume"
CSV_HEADER_TRANSCRIPT = "Transcript"
CSV_HEADER_COVER_LETTER = "Cover Letter"
CSV_HEADER_DATE = "Date"

# CV constants
TEMPERATURE = 0.7
MODEL_NAME = "gpt-4.1-nano"
COVER_LETTER_PROMPT = """
You are a professional career writer.

Task:
Generate a tailored cover letter using the provided CV and job posting.

Requirements:
1. Personalize the letter to the specific company and role.
2. Clearly connect the candidate's skills and achievements to the job requirements.
3. Use a warm, conversational, and confident tone.
4. Keep it concise (400-500 words for the body paragraphs).
5. Do NOT fabricate experience or skills.
6. Extract the candidate's full name, email, phone number, and location from the CV. Use them in the header and signature. NEVER use placeholder text like [Your Name] or [Your Address] — if info is not found, omit it.
7. Do NOT include the employer's address or company address.
8. Format the output as a complete cover letter ready to send (no extra commentary).
9. Return the cover letter formatted in **Markdown**. Use `**bold**` for the candidate's name, `---` for separators, and standard Markdown paragraphs.
10. Use this structure:
   - **Candidate's full name** (bold)
   - Contact info (email, phone, location) separated by " | "
   - Date (e.g. February 12, 2026)
   - Blank line
   - Dear Hiring Manager,
   - Body paragraphs (4-5 paragraphs)
   - Sincerely,
   - **Candidate's full name** (bold)
"""
