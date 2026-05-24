"""
Remote OK API Integration
Fetches remote job listings from RemoteOK's public API.
Unlike scrapers, this consumes structured JSON directly.
"""

import requests
import pandas as pd
from datetime import datetime
import os

# ---------------- CONFIG ----------------
API_URL = "https://remoteok.com/api"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
OUTPUT_DIR = "data/raw"
# ----------------------------------------


def fetch_jobs():
    """
    Hit Remote OK's API endpoint, get back a list of job dicts.
    The first item in the response is metadata (a 'legal notice'),
    so we skip it.
    """
    print(f"Fetching: {API_URL}")
    response = requests.get(API_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    data = response.json()
    # First element is metadata, real jobs start at index 1
    jobs_raw = data[1:] if len(data) > 1 else []
    print(f"  Found {len(jobs_raw)} jobs in API response")
    return jobs_raw


def format_salary(job):
    """
    Remote OK provides salary_min and salary_max as numbers (annual USD).
    Format them into a readable string matching our schema.
    """
    sal_min = job.get("salary_min")
    sal_max = job.get("salary_max")

    if sal_min and sal_max:
        return f"USD {sal_min:,} - {sal_max:,}"
    elif sal_min:
        return f"USD {sal_min:,}+"
    elif sal_max:
        return f"Up to USD {sal_max:,}"
    return None


def parse_job(job):
    """
    Map Remote OK's JSON fields to our standardized schema.
    """
    return {
        "title": job.get("position"),
        "company": job.get("company"),
        "location": job.get("location") or "Remote",
        "job_type": "Remote",  # All Remote OK jobs are remote by definition
        "salary": format_salary(job),
        "posted": job.get("date"),
        "url": job.get("url") or job.get("apply_url"),
        "source": "remoteok",
    }


def main():
    try:
        jobs_raw = fetch_jobs()
    except Exception as e:
        print(f"Error fetching API: {e}")
        return

    if not jobs_raw:
        print("No jobs returned by API.")
        return

    # Map each raw job to our standardized schema
    jobs = [parse_job(job) for job in jobs_raw]
    # Filter out any without title (defensive)
    jobs = [j for j in jobs if j["title"]]

    # Save to CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/remoteok_{timestamp}.csv"

    df = pd.DataFrame(jobs)
    df["scraped_at"] = datetime.now().isoformat()
    df.to_csv(filename, index=False)

    print(f"\n{'='*60}")
    print(f"SUCCESS: Saved {len(df)} jobs to {filename}")
    print(f"{'='*60}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df[["title", "company", "location", "salary"]].head(3).to_string())
    print(f"\nMissing values per column:")
    print(df.isnull().sum())


if __name__ == "__main__":
    main()