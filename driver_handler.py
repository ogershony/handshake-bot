# Imports
import csv
import os
import time
from datetime import datetime
import constants as const

# Selenium deps
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class DriverHandler:
    """
    Handles all interactions with the webdriver, such as logging in, navigating to pages, and extracting information.
    """

    def __init__(
        self, driver: webdriver.Chrome, config: dict, default_timeout: int = 10
    ) -> None:
        """
        Initializes the DriverHandler with a Selenium webdriver instance.
        """
        self.driver = driver
        self.config = config
        self.default_timeout = default_timeout

    def get_driver(self) -> webdriver.Chrome:
        """
        Returns the underlying Selenium webdriver instance.
        """
        return self.driver

    def login(self, user_timeout: int = 300) -> None:
        """
        Logs in to Handshake using the provided credentials and login URL. This method handles the entire authentication flow, including SSO and Duo authentication.
        """
        print("Authenticating to Handshake...")

        try:
            self.driver.get(self.config[const.LOGIN_URL])
        except Exception as e:
            print(f"Error navigating to login URL: {e}")
            raise

        # Find and click the SSO button
        sso_button = WebDriverWait(self.driver, self.default_timeout).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(@class, 'sso-button') and contains(@class, 'primary')]",
                )
            )
        )
        sso_button.click()

        # Wait for the UCSD SSO login page to load
        username_field = WebDriverWait(self.driver, self.default_timeout).until(
            EC.presence_of_element_located((By.ID, "ssousername"))
        )

        # Fill in username
        username_field.send_keys(self.config[const.USERNAME])

        # Fill in password
        password_field = self.driver.find_element(By.ID, "ssopassword")
        password_field.send_keys(self.config[const.PASSWORD])

        # Click the login button
        login_button = self.driver.find_element(By.NAME, "_eventId_proceed")
        login_button.click()

        # Wait for Duo authentication and successful login to Handshake
        # This waits until we're back on the Handshake domain after authentication
        print("Waiting for Duo authentication... Please complete it manually.")
        WebDriverWait(self.driver, user_timeout).until(
            EC.url_contains("joinhandshake.com")
        )

        print("Successfully logged in to Handshake!")

    def get_total_pages(self) -> int:
        """
        Assumes the driver is at the listing page. Returns the total number of pages of listings.
        """
        # Wait for the pagination element to load
        pagination = WebDriverWait(self.driver, self.default_timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//nav[@data-hook='job-search-pagination']")
            )
        )

        # Find the "last page" button and get its value attribute
        last_page_button = pagination.find_element(
            By.XPATH, ".//button[@data-page='last']"
        )
        total_pages = int(last_page_button.get_attribute("value"))

        print(f"Total number of pages: {total_pages}")

        return total_pages

    def get_job_postings(self) -> list:
        """
        Assumes the driver is at the job listings page. Returns a list of job URLs (as strings) on the current page.
        """
        # Wait for job cards to be present and visible
        WebDriverWait(self.driver, self.default_timeout).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div[data-hook^='job-result-card']")
            )
        )

        # Find all job links directly on the page
        # These are the clickable links inside job cards with aria-label="View [Job Title]"
        job_links = self.driver.find_elements(
            By.XPATH,
            "//div[contains(@data-hook, 'job-result-card')]//a[contains(@href, '/job-search/')]",
        )

        # Extract href attributes to get absolute URLs
        job_urls = []
        for job_link in job_links:
            try:
                url = job_link.get_attribute("href")
                if url:  # Only add non-empty URLs
                    job_urls.append(url)
            except Exception as e:
                print(f"Warning: Could not extract URL from job link: {e}")
                continue

        print(f"Found {len(job_urls)} job postings on this page")

        return job_urls

    def apply_to_job(self, job_url: str) -> (bool, str):
        """
        Given a job URL string, navigates to the job details page, and then clicks the "Apply" button if it's present.
        Return true if success, false if failure with failure message
        """
        # Navigate to the job details page using the URL
        self.driver.get(job_url)

        # Wait for the job details page to load by waiting for the presence of the "Share" button
        WebDriverWait(self.driver, self.default_timeout).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[text()='Share' or contains(text(), 'Share')]")
            )
        )

        job_details = self.parse_job_details()
        print(
            f"Applying to job: {job_details[const.JOB_TITLE]} at {job_details[const.COMPANY_NAME]} (ID: {job_details[const.JOB_ID]})"
        )

        apply_button = None
        # Try to find the Apply button. Deals with external application cases
        try:
            apply_button = self.driver.find_element(
                By.XPATH, "//button[@aria-label='Apply']"
            )

        except Exception as e:
            # Try to find external application button
            try:
                self.driver.find_element(
                    By.XPATH, "//button[@aria-label='Apply externally']"
                )

                print("External application detected. Skipping this job.")
                return False, "External application"

            except Exception as ex:
                print(
                    f"Error applying to job: {e}, Error finding external application button: {ex}"
                )
                return False, "Apply button not found"

        # Click the "Apply" button
        apply_button.click()

        # Wait for the application form to load by waiting for the "Submit Application" button
        submit_button = WebDriverWait(self.driver, self.default_timeout).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[text()='Submit Application']")
            )
        )

        valid_application = self.valid_application(
            job_details[const.JOB_ID]
        )  # returns (success, message)

        if not valid_application[0]:
            print(f"Invalid application: {valid_application[1]}. Skipping this job.")
            return False, valid_application[1]

        # Upload required documents
        try:
            self.add_documents()
        except FileNotFoundError as e:
            print(f"Critical error - required document missing: {e}")
            return False, f"Document not found: {e}"
        except Exception as e:
            print(f"Error uploading documents: {e}")
            # Log but don't fail - continue with submission

        submit_button.click()

        print("Applied to job successfully!")

        # Log the job application using config settings
        documents_used = {
            "resume": self.config[const.INCLUDE_RESUME],
            "transcript": self.config[const.INCLUDE_TRANSCRIPT],
            "cover_letter": self.config[const.INCLUDE_COVER_LETTER],
        }
        self.log_job(job_details, documents_used)

        return True, "Applied successfully"

    def add_documents(self) -> None:
        """
        Uploads documents (transcript, cover letter) to the application modal if required.
        Should be called after the application modal is open but before submission.
        """
        print("Checking for document upload requirements...")

        # Get current working directory for absolute paths
        cwd = os.getcwd()

        try:
            # Find the application modal
            modal = WebDriverWait(self.driver, self.default_timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@data-hook='apply-modal-content']")
                )
            )
        except Exception as e:
            print(f"Warning: Could not find application modal: {e}")
            return

        # Find all fieldsets in the modal (each represents a form field)
        try:
            fieldsets = modal.find_elements(By.TAG_NAME, "fieldset")
        except Exception as e:
            print(f"No fieldsets found in modal: {e}")
            return

        if not fieldsets:
            print("No document upload fields found in this application")
            return

        print(f"Found {len(fieldsets)} fieldset(s) in application modal")

        for fieldset in fieldsets:
            try:
                # Get the legend text to identify document type
                legend_text = fieldset.text.lower()

                # Determine document type and path based on legend text
                document_path = None
                document_type = None

                if "transcript" in legend_text:
                    if self.config[const.INCLUDE_TRANSCRIPT]:
                        document_path = self.config[const.TRANSCRIPT_PATH]
                        document_type = "Transcript"
                    else:
                        print("Skipping transcript upload (disabled in config)")
                        continue

                elif "cover letter" in legend_text:
                    if self.config[const.INCLUDE_COVER_LETTER]:
                        document_path = self.config[const.COVER_LETTER_PATH]
                        document_type = "Cover Letter"
                    else:
                        print("Skipping cover letter upload (disabled in config)")
                        continue
                else:
                    # Not a document we handle, skip this fieldset
                    continue

                # Convert to absolute path if needed
                if document_path and not os.path.isabs(document_path):
                    absolute_path = os.path.join(cwd, document_path)
                else:
                    absolute_path = document_path

                # Verify file exists
                if not os.path.isfile(absolute_path):
                    raise FileNotFoundError(
                        f"{document_type} file not found at: {absolute_path}"
                    )

                # Find the file input within this fieldset
                try:
                    file_input = fieldset.find_element(
                        By.XPATH, ".//input[@type='file']"
                    )
                except Exception as e:
                    print(f"Could not find file input in {document_type} fieldset: {e}")
                    continue

                print(f"Uploading {document_type}: {absolute_path}")

                # Upload the file using send_keys
                file_input.send_keys(absolute_path)

                # Wait for upload completion (SVG checkmark appears in fieldset)
                try:
                    WebDriverWait(self.driver, self.default_timeout).until(
                        EC.presence_of_element_located((By.XPATH, ".//svg"))
                    )
                    print(f"{document_type} uploaded successfully!")
                except Exception as e:
                    print(f"Warning: Could not confirm {document_type} upload: {e}")

            except FileNotFoundError as e:
                raise e
            except Exception as e:
                print(f"Error processing {document_type} fieldset: {e}")
                continue

        print("Document upload check complete")

    def go_to_next_page(self) -> None:
        """
        Navigates to the next page of job listings by clicking the "Next" button in the pagination.
        Assumes that the driver is currently on a job listings page.
        """
        next_button = WebDriverWait(self.driver, self.default_timeout).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//nav[@data-hook='job-search-pagination']//button[@aria-label='next page']",
                )
            )
        )
        next_button.click()

    def parse_job_details(self) -> dict:
        """
        Parses job details from the current job details page.
        Returns a dict with job_id, company_name, and job_title.
        """
        # Extract job ID from the current URL
        current_url = self.driver.current_url

        # Handle both /jobs/ and /job-search/ URL patterns
        if "/jobs/" in current_url:
            job_id = current_url.split("/jobs/")[1].split("?")[0]
        elif "/job-search/" in current_url:
            job_id = current_url.split("/job-search/")[1].split("?")[0]
        else:
            job_id = None

        # Extract company name - use aria-label from the employer link
        try:
            company_link = self.driver.find_element(
                By.XPATH,
                "//a[contains(@href, '/e/')][@aria-label][@data-size='xlarge']",
            )
            company_name = company_link.get_attribute("aria-label")
        except Exception as e:
            print(f"Error extracting company name: {e}")
            company_name = None

        # Extract job title - use h1 tag
        try:
            job_title_element = self.driver.find_element(
                By.XPATH, "//h1[contains(@class, 'sc-')]"
            )
            job_title = job_title_element.text
        except Exception as e:
            print(f"Error extracting job title: {e}")
            job_title = None

        return {
            const.JOB_ID: job_id,
            const.JOB_TITLE: job_title,
            const.COMPANY_NAME: company_name,
        }

    def job_already_applied(self, job_id: str) -> bool:
        """
        Checks if a job with the given job_id has already been applied to.

        Args:
            job_id: The job ID to check

        Returns:
            True if the job ID exists in jobs.csv, False otherwise
        """
        # If CSV doesn't exist, job hasn't been applied to
        if not os.path.isfile(const.JOBS_CSV_FILE):
            return False

        # Read CSV and check if job_id exists
        try:
            with open(const.JOBS_CSV_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get(const.CSV_HEADER_JOB_ID) == job_id:
                        return True
        except Exception as e:
            print(f"Warning: Error reading {const.JOBS_CSV_FILE}: {e}")
            return False

        return False

    def log_job(self, job_details: dict, documents_used: dict) -> None:
        """
        Logs a successfully applied job to jobs.csv in the current working directory.

        Args:
            job_details: Dict containing job_id, company_name, and job_title
            documents_used: Dict with keys 'resume', 'transcript', 'cover_letter' (True/False)
        """
        file_exists = os.path.isfile(const.JOBS_CSV_FILE)

        # Get current date as MM/DD
        current_date = datetime.now().strftime("%m/%d")

        # Prepare the row data
        row = [
            job_details.get(const.JOB_ID, "N/A"),
            job_details.get(const.COMPANY_NAME, "N/A"),
            job_details.get(const.JOB_TITLE, "N/A"),
            "Yes" if documents_used.get("resume", False) else "No",
            "Yes" if documents_used.get("transcript", False) else "No",
            "Yes" if documents_used.get("cover_letter", False) else "No",
            current_date,
        ]

        # Write to CSV
        with open(const.JOBS_CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header if file is new
            if not file_exists:
                writer.writerow(
                    [
                        const.CSV_HEADER_JOB_ID,
                        const.CSV_HEADER_COMPANY,
                        const.CSV_HEADER_POSITION,
                        const.CSV_HEADER_RESUME,
                        const.CSV_HEADER_TRANSCRIPT,
                        const.CSV_HEADER_COVER_LETTER,
                        const.CSV_HEADER_DATE,
                    ]
                )

            writer.writerow(row)

        print(f"Logged job application to {const.JOBS_CSV_FILE}")

    def valid_application(self, job_id: str) -> (bool, str):
        """
        Checks if the current application is valid based on the presence of required fields and the configuration settings.

        Args:
            job_id: The job ID to check for duplicates

        Returns (True, "") if valid, (False, "error message") if invalid.
        """

        # Check if we've already applied to this job
        if self.job_already_applied(job_id):
            return False, "Already applied to this job"

        # Get the entire modal content to search for required fields
        try:
            modal = self.driver.find_element(
                By.XPATH, "//div[@data-hook='apply-modal-content']"
            )
            modal_text = modal.text
        except Exception as e:
            print(f"Error finding application modal: {e}")
            return False, "Could not find application modal"

        # Check if job requires a resume and user doesn't want to provide one
        if not self.config[const.INCLUDE_RESUME]:
            if (
                "Attach your resume" in modal_text
                or "attach your resume" in modal_text.lower()
            ):
                return False, "Job requires resume but config excludes it"

        # Check if job requires a transcript and user doesn't want to provide one
        if not self.config[const.INCLUDE_TRANSCRIPT]:
            if (
                "Attach your transcript" in modal_text
                or "attach your transcript" in modal_text.lower()
            ):
                return False, "Job requires transcript but config excludes it"

        # Check if job requires a cover letter and user doesn't want to provide one
        if not self.config[const.INCLUDE_COVER_LETTER]:
            if (
                "Attach your cover letter" in modal_text
                or "attach your cover letter" in modal_text.lower()
            ):
                return False, "Job requires cover letter but config excludes it"

        return True, ""
