# Local imports
from driver_handler import DriverHandler
import constants as const

# Standard imports
import os
import time

# External imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


from dotenv import load_dotenv

load_dotenv()

# Load configuration from environment variables
config = {
    const.INCLUDE_RESUME: bool(os.getenv("INCLUDE_RESUME") == "True"),
    const.INCLUDE_TRANSCRIPT: bool(os.getenv("INCLUDE_TRANSCRIPT") == "True"),
    const.INCLUDE_COVER_LETTER: bool(os.getenv("INCLUDE_COVER_LETTER") == "True"),
    const.USERNAME: os.getenv("USERNAME"),
    const.PASSWORD: os.getenv("PASSWORD"),
    const.LOGIN_URL: os.getenv("LOGIN_URL"),
    const.SEARCH_URL: os.getenv("SEARCH_URL"),
    const.TRANSCRIPT_PATH: os.getenv("TRANSCRIPT_PATH"),
    const.COVER_LETTER_PATH: os.getenv("COVER_LETTER_PATH"),
}


def main():
    """
    Main entry point for the program. Initializes the webdriver and mass applies to jobs
    """
    print("Starting Handshake Job Application Bot...")

    # This conveniently handles the annoying chrome driver logic for you
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # Initializes driver handler object, which wraps around the webdriver
    driver_handler = DriverHandler(driver, config)

    # Login
    try:
        driver_handler.login()
    except Exception as e:
        print(f"Error during login: {e}")
        driver.quit()
        return

    # Navigates to the job postings page
    driver_handler.get_driver().get(config[const.SEARCH_URL])

    # Get the total amount of pages to scrape
    total_pages = driver_handler.get_total_pages()

    # Iterate through all pages
    for page in range(total_pages):  # range(total_pages):
        print(f"Processing page {page + 1} of {total_pages}...")

        # Get all job posting URLs on the current page
        job_urls = driver_handler.get_job_postings()

        for job_url in job_urls:
            try:
                driver_handler.apply_to_job(job_url)
            except Exception as e:
                print(f"Error applying to job: {e}")
                continue

            time.sleep(
                5
            )  # Sleep for a few seconds to avoid overwhelming the server and to mimic human behavior

        # Navigate to the next page
        if page < total_pages - 1:
            driver_handler.go_to_next_page()

    print("Finished processing all pages. Closing the browser :)")


if __name__ == "__main__":
    main()
