"""
Unified Cleaning Pipeline
Reads the latest CSV from each source (Jobberman, MyJobMag, Remote OK),
standardizes columns, cleans values, and produces one unified dataset
saved to data/processed/jobs_unified_<timestamp>.csv
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import re

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


# ============= STEP 1: LOAD LATEST FILES =============

def get_latest_csv(source_prefix):
    """
    Find the most recent CSV for a given source.
    Example: source_prefix='jobberman' returns the newest jobberman_*.csv
    """
    matches = sorted(RAW_DIR.glob(f"{source_prefix}_*.csv"))
    if not matches:
        print(f"  WARNING: No {source_prefix} CSV found")
        return None
    latest = matches[-1]
    print(f"  Loading {source_prefix}: {latest.name}")
    return pd.read_csv(latest)


# ============= STEP 2: CLEAN SALARY =============

def clean_salary(value):
    """
    Standardize salary strings into a usable format.
    Returns a dict with currency, min, max, and is_disclosed flag.
    'Confidential' or NaN -> not disclosed.
    """
    if pd.isna(value) or not isinstance(value, str):
        return {"currency": None, "salary_min": None, "salary_max": None, "salary_disclosed": False}

    value = value.strip()
    if value.lower() in ["confidential", "negotiable", ""]:
        return {"currency": None, "salary_min": None, "salary_max": None, "salary_disclosed": False}

    # Detect currency
    currency = None
    if "USD" in value or "$" in value:
        currency = "USD"
    elif "NGN" in value or "₦" in value:
        currency = "NGN"

    # Extract numbers - removes commas and finds all numbers
    cleaned = value.replace(",", "")
    numbers = re.findall(r"\d+", cleaned)
    numbers = [int(n) for n in numbers if int(n) > 100]  # filter out small noise

    sal_min = numbers[0] if len(numbers) >= 1 else None
    sal_max = numbers[1] if len(numbers) >= 2 else sal_min

    return {
        "currency": currency,
        "salary_min": sal_min,
        "salary_max": sal_max,
        "salary_disclosed": sal_min is not None,
    }


# ============= STEP 3: CLEAN DATE =============

def clean_date(value, scraped_at):
    """
    Convert various date formats to a single posted_date (YYYY-MM-DD).
    Handles:
      - ISO timestamps from Remote OK
      - "2 days ago", "1mo", "3w" from Jobberman
      - "23 May", "1 June" from MyJobMag
    """
    if pd.isna(value):
        return None

    value = str(value).strip()
    scrape_date = pd.to_datetime(scraped_at).date() if scraped_at else datetime.now().date()

    # Case 1: ISO timestamp (Remote OK)
    try:
        return pd.to_datetime(value).date().isoformat()
    except (ValueError, TypeError):
        pass

    # Case 2: relative date "2 days ago", "1mo", "3w"
    relative_match = re.search(r"(\d+)\s*(day|week|month|year|d|w|mo|y)", value, re.IGNORECASE)
    if relative_match:
        num = int(relative_match.group(1))
        unit = relative_match.group(2).lower()
        if unit in ("day", "d"):
            delta = timedelta(days=num)
        elif unit in ("week", "w"):
            delta = timedelta(weeks=num)
        elif unit in ("month", "mo"):
            delta = timedelta(days=num * 30)
        elif unit in ("year", "y"):
            delta = timedelta(days=num * 365)
        else:
            delta = timedelta(days=0)
        return (scrape_date - delta).isoformat()

    # Case 3: "23 May" format - assume current year
    short_date_match = re.match(
        r"(\d{1,2})\s+(January|February|March|April|May|June|"
        r"July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)",
        value,
        re.IGNORECASE,
    )
    if short_date_match:
        try:
            # Build full date string with current year
            day = short_date_match.group(1)
            month = short_date_match.group(2)
            full_date_str = f"{day} {month} {scrape_date.year}"
            parsed = pd.to_datetime(full_date_str, dayfirst=True, errors="coerce")
            if pd.notna(parsed):
                # If the parsed date is in the future, it must be last year
                if parsed.date() > scrape_date:
                    parsed = parsed.replace(year=scrape_date.year - 1)
                return parsed.date().isoformat()
        except Exception:
            pass

    return None


# ============= STEP 4: CLEAN LOCATION =============

def clean_location(value):
    """Light location cleaning - strip whitespace, fix common variants."""
    if pd.isna(value) or not str(value).strip():
        return None
    value = str(value).strip()

    # Normalize remote variants
    if value.lower() in ["remote", "remote (work from home)", "worldwide", "anywhere"]:
        return "Remote"

    # Strip trailing commas
    value = value.rstrip(", ").strip()
    return value


# ============= STEP 5: PROCESS ONE DATAFRAME =============

def process_df(df):
    """Apply all cleaning steps to a single DataFrame."""
    if df is None or df.empty:
        return None

    # Clean salary - this returns a dict, so we expand it into 4 columns
    salary_cleaned = df["salary"].apply(clean_salary).apply(pd.Series)
    df = pd.concat([df, salary_cleaned], axis=1)

    # Clean date
    df["posted_date"] = df.apply(
        lambda row: clean_date(row.get("posted"), row.get("scraped_at")),
        axis=1
    )

    # Clean location
    df["location"] = df["location"].apply(clean_location)

    # Standardize title/company (strip whitespace, handle case)
    df["title"] = df["title"].astype(str).str.strip()
    df["company"] = df["company"].astype(str).str.strip().replace("nan", None)

    return df


# ============= STEP 6: MAIN =============

def main():
    print("Loading latest CSVs from each source...")
    df_jobberman = get_latest_csv("jobberman")
    df_myjobmag = get_latest_csv("myjobmag")
    df_remoteok = get_latest_csv("remoteok")

    dfs = [process_df(df_jobberman), process_df(df_myjobmag), process_df(df_remoteok)]
    dfs = [df for df in dfs if df is not None]

    if not dfs:
        print("ERROR: No data to process.")
        return

    # Combine - pandas aligns columns by name automatically
    combined = pd.concat(dfs, ignore_index=True, sort=False)

    # Select final columns in a sensible order
    final_columns = [
        "title", "company", "location", "job_type",
        "salary_min", "salary_max", "currency", "salary_disclosed",
        "posted_date", "url", "source", "scraped_at"
    ]
    combined = combined.reindex(columns=final_columns)

    # Drop duplicates based on title + company + source (sometimes same job appears twice)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["title", "company", "source"])
    after = len(combined)
    print(f"  Removed {before - after} duplicate rows")

    # Save
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = PROCESSED_DIR / f"jobs_unified_{timestamp}.csv"
    combined.to_csv(output_path, index=False)

    # Report
    print(f"\n{'='*60}")
    print(f"SUCCESS: {len(combined)} unified rows saved to {output_path}")
    print(f"{'='*60}")
    print(f"\nJobs per source:")
    print(combined["source"].value_counts())
    print(f"\nMissing values per column:")
    print(combined.isnull().sum())
    print(f"\nSalary disclosure rate:")
    print(combined["salary_disclosed"].value_counts(normalize=True).map("{:.1%}".format))
    print(f"\nSample rows (one per source):")
    for src in combined["source"].unique():
        sample = combined[combined["source"] == src].head(1)
        print(f"\n--- {src} ---")
        print(sample[["title", "company", "location", "salary_min", "currency", "posted_date"]].to_string(index=False))


if __name__ == "__main__":
    main()