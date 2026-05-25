# Nigerian Job Market Analytics

End-to-end data pipeline that scrapes, cleans, and analyzes job listings from multiple sources to map the Nigerian and international remote labor market.

## Status

In active development (Day 1)

## Data Sources

- [Jobberman](https://www.jobberman.com) — Nigerian market jobs (scraping)-Done
- [MyJobMag](https://www.myjobmag.com) — Nigerian market jobs (scraping) — Done
- [Remote OK](https://remoteok.com) — International remote jobs (API) — *coming soon*

## Tech Stack

- **Python** — pandas, requests, BeautifulSoup
- **Streamlit** — interactive web app
- **SQLite** — local storage
- **GitHub Actions** — scheduled data refresh

## Project Structure

\`\`\`
nigerian-job-market-analysis/
├── scrapers/        # Source-specific scrapers
├── data/
│   ├── raw/         # Raw scraped data (timestamped CSVs)
│   └── processed/   # Cleaned, unified data
├── notebooks/       # EDA notebooks
└── app/             # Streamlit application
\`\`\`

## Setup

\`\`\`bash
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
\`\`\`

## Day 1 Progress

- ✅ Jobberman scraper built (80 jobs / 5 pages)
- ✅ Data quality verified (zero missing values across all columns)
- ✅MyJobMag scraper (Day 2)
- ✅Remote OK API integration (Day 3)
- ✅Unified cleaning pipeline (Day 4-5)
- Streamlit app (Day 6-7)
