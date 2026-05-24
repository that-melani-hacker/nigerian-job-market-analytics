"""
Jobberman Scraper
Scrapes job listings from Jobberman.com and saves to a timestamped CSV.

Strategy: find <a data-cy="listing-title-link"> elements (stable test attribute),
then walk up to the card container and extract fields by their position.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os

# ---------------- CONFIG ----------------
BASE_URL = "https://www.jobberman.com/jobs"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
OUTPUT_DIR = "data/raw"
PAGES_TO_SCRAPE = 5
DELAY_BETWEEN_REQUESTS = 2
# ----------------------------------------


def fetch_page(url):
    """Download HTML for a single page."""
    print(f"Fetching: {url}")
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_job_card(title_link):
    """
    Extract data from one job listing.
    title_link is the <a data-cy="listing-title-link"> tag.
    The card container is 4 levels up.
    """
    job = {
        "title": None,
        "company": None,
        "location": None,
        "job_type": None,
        "salary": None,
        "posted": None,
        "url": None,
        "source": "jobberman",
    }

    # URL and title from the link itself
    job["url"] = title_link.get("href")
    job["title"] = title_link.get("title") or title_link.get_text(strip=True)

    # Walk up to the card container (4 levels based on our debug output)
    try:
        card = title_link.parent.parent.parent.parent
    except AttributeError:
        return job

    # Company: it's the <p> right after the link's parent div
    # Looking at the HTML, company is in a <p class="text-sm text-blue-700">
    company_tag = card.find("p", class_=lambda c: c and "text-blue-700" in c and "text-sm" in c)
    if company_tag:
        job["company"] = company_tag.get_text(strip=True)

    # Location, job_type, salary are in <span> chips with bg-brand-secondary-100
    chips = card.find_all("span", class_=lambda c: c and "bg-brand-secondary-100" in c)
    chip_texts = [chip.get_text(strip=True) for chip in chips]

    if len(chip_texts) >= 1:
        job["location"] = chip_texts[0]
    if len(chip_texts) >= 2:
        job["job_type"] = chip_texts[1]
    if len(chip_texts) >= 3:
        # Salary chip contains "NGN 150,000 - 250,000" etc.
        job["salary"] = chip_texts[2]

    # Posted date: usually the last <p class="text-sm text-gray-500"> 
    # with content like "2 days ago" or "1mo"
    date_tags = card.find_all("p", class_=lambda c: c and "text-gray-500" in c and "text-sm" in c)
    if date_tags:
        # The last gray small text is usually the date
        last_text = date_tags[-1].get_text(strip=True)
        if last_text:
            job["posted"] = last_text

    return job


def scrape_page(page_number):
    """Scrape one page of Jobberman job listings."""
    url = BASE_URL if page_number == 1 else f"{BASE_URL}?page={page_number}"
    html = fetch_page(url)
    soup = BeautifulSoup(html, "lxml")

    # Find all job title links via the stable data-cy attribute
    title_links = soup.find_all("a", attrs={"data-cy": "listing-title-link"})
    print(f"  Found {len(title_links)} job listings on page {page_number}")

    jobs = [parse_job_card(link) for link in title_links]
    return jobs


def main():
    all_jobs = []

    for page in range(1, PAGES_TO_SCRAPE + 1):
        try:
            jobs = scrape_page(page)
            all_jobs.extend(jobs)
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            continue

    if not all_jobs:
        print("No jobs scraped.")
        return

    # Save to CSV with timestamp
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/jobberman_{timestamp}.csv"

    df = pd.DataFrame(all_jobs)
    df["scraped_at"] = datetime.now().isoformat()
    df.to_csv(filename, index=False)

    print(f"\n{'='*60}")
    print(f"SUCCESS: Saved {len(df)} jobs to {filename}")
    print(f"{'='*60}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df.head(3).to_string())
    print(f"\nMissing values per column:")
    print(df.isnull().sum())


if __name__ == "__main__":
    main()