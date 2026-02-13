# Handshake QuickApply Bot

IM PRETTY SURE HANDSHAKE DOESNT ALLOW BOTTING, SO USE AT YOUR OWN RISK!

Automated job application bot for Handshake that applies to multiple job postings based on your preferences.

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd HandShake-QuickApply-Bot
```

### 2. Install Dependencies

```bash
pip install -e .
```

This installs all required dependencies including `selenium`, `webdriver-manager`, `python-dotenv`, `fpdf2`, `markdown`, `PyPDF2`, `langchain`, and `chromadb`.

## Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your settings:

**Document Settings:**

- `INCLUDE_RESUME` - Set to `"True"` or `"False"` to control resume submission
- `INCLUDE_TRANSCRIPT` - Set to `"True"` or `"False"` to control transcript submission
- `INCLUDE_COVER_LETTER` - Set to `"True"` or `"False"` to control cover letter submission

**Document Paths:**

- `RESUME_PATH` - Path to your resume PDF file
- `TRANSCRIPT_PATH` - Path to your transcript PDF file
- `COVER_LETTER_PATH` - Directory where generated cover letters are saved

**Authentication:**

- `USERNAME` - Your university SSO username
- `PASSWORD` - Your university SSO password
- `OPENAI_API_KEY` - Your OpenAI API key (required for AI-generated cover letters)

**URLs:**

- `LOGIN_URL` - Your school's Handshake login URL (format: `https://<school>.joinhandshake.com/login?ref=app-domain`)
- `SEARCH_URL` - Full Handshake job search URL with filters applied

#### Finding Your URLs:

**LOGIN_URL:**

1. Go to your school's Handshake portal
2. Copy the login page URL
3. Format: `https://<your-school>.joinhandshake.com/login?ref=app-domain`

**SEARCH_URL:**

1. Navigate to Handshake job search
2. Apply desired filters (job type, location, keywords, etc.)
3. Copy the complete URL from your browser's address bar

### 3. Upload Documents

Add your resume, transcript, and cover letter PDFs to the `documents` folder. The resume is automatically uploaded to your Handshake profile. Update the paths in `.env` for transcript and cover letter if needed.

## Running the Bot

Execute the main script:

```bash
python main.py
```

**Process:**

1. Opens Chrome browser
2. Logs into Handshake via SSO
3. Waits for manual Duo authentication
4. Navigates through job search pages
5. Generates tailored cover letters using OpenAI (if enabled)
6. Applies to jobs matching your document preferences
7. Skips jobs requiring documents you've excluded
8. Skips external applications
9. Logs applications to `jobs.csv`

## Output

**jobs.csv** - Automatically generated CSV file tracking all submitted applications with:

- Job ID
- Company name
- Position title
- Documents submitted (Resume/Transcript/Cover Letter)
- Application date

The file is created on first run and updated with each application.
