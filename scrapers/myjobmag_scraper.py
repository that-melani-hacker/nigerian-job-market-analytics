"""
MyJobMag Scraper
Scrapes job listings from MyJobMag.com and saves to a timestamped CSV.

Strategy: anchor on <li class="job-list-li"> (each represents one job).
Inside each, extract title+URL from <h2><a>, parse "Title at Company" pattern,
get description from <li class="job-desc">, get date from posted text.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
import re

# ---------------- CONFIG ----------------
BASE_URL = "https://www.myjobmag.com/jobs"
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


def split_title_company(full_title):
    """
    MyJobMag titles look like: 'Radiographer (Gwagwalada) at Crystal Thorpe'
    Split on the LAST ' at ' to separate role from company.
    """
    if not full_title or " at " not in full_title:
        return full_title, None

    parts = full_title.rsplit(" at ", 1)
    title = parts[0].strip()
    company = parts[1].strip() if len(parts) > 1 else None
    return title, company


def parse_job_card(card):
    """
    Extract data from one <li class="job-list-li"> element.
    """
    job = {
        "title": None,
        "company": None,
        "location": None,
        "job_type": None,
        "salary": None,
        "posted": None,
        "url": None,
        "source": "myjobmag",
    }

    # Title and URL from <h2><a>
    title_link = card.select_one("h2 a")
    if title_link:
        href = title_link.get("href", "")
        # Make absolute URL if it's relative
        if href.startswith("/"):
            job["url"] = "https://www.myjobmag.com" + href
        else:
            job["url"] = href

        full_title = title_link.get_text(strip=True)
        title, company = split_title_company(full_title)
        job["title"] = title
        job["company"] = company

   # Description from <li class="job-desc">
    desc = card.select_one("li.job-desc")
    if desc:
        job["job_type"] = desc.get_text(strip=True)[:500]  # cap to avoid huge text
    # Posted date - look for date pattern in the card text
    # MyJobMag shows dates like "23 May" near the bottom
    card_text = card.get_text(" ", strip=True)
    # Match patterns like "23 May", "1 June", etc.
    date_match = re.search(
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b",
        card_text,
        re.IGNORECASE,
    )
    if date_match:
        job["posted"] = date_match.group(0)

    return job


def scrape_page(page_number):
    """Scrape one page of MyJobMag job listings."""
    # MyJobMag pagination: /jobs/page/2, /jobs/page/3, etc.
    url = BASE_URL if page_number == 1 else f"{BASE_URL}/page/{page_number}"
    html = fetch_page(url)
    soup = BeautifulSoup(html, "lxml")

    cards = soup.find_all("li", class_="job-list-li")
    print(f"  Found {len(cards)} job listings on page {page_number}")

    jobs = [parse_job_card(card) for card in cards]
    # Filter out empty ones (sometimes job-list-li is used for ads/separators)
    jobs = [j for j in jobs if j["title"]]
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

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/myjobmag_{timestamp}.csv"

    df = pd.DataFrame(all_jobs)
    df["scraped_at"] = datetime.now().isoformat()
    df.to_csv(filename, index=False)

    print(f"\n{'='*60}")
    print(f"SUCCESS: Saved {len(df)} jobs to {filename}")
    print(f"{'='*60}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df[["title", "company", "posted", "url"]].head(3).to_string())
    print(f"\nMissing values per column:")
    print(df.isnull().sum())


if __name__ == "__main__":
    main()