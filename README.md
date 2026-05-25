# Nigerian Job Market Analytics

Multi-source labor market intelligence pipeline analyzing 325 job listings from three Nigerian and international sources. Built to surface salary transparency patterns, regional demand, and the economic case for remote international work over local employment.

## Live Demo

🚀 [Try the interactive dashboard](https://nigerian-job-market-analytics.streamlit.app)

## Key Findings

- **Jobberman discloses salary in 81% of listings**, vs. only 3% on Remote OK — a Nigerian local board has dramatically higher transparency than a global tech board
- **Remote international roles pay roughly 5x more in real terms** than Nigerian local equivalents (USD median $52k vs NGN median ₦200k/month)
- **Nigerian local market skews toward sales, accounting, and admin** roles, not tech — international remote is where engineering demand concentrates

## Project Components

| Component | Description | File |
|-----------|-------------|------|
| Scrapers | Three independent data acquisition pipelines (2 HTML, 1 REST API) | `scrapers/*.py` |
| ETL | Unified schema across sources, deduplication, salary/date normalization | `scrapers/clean_and_unify.py` |
| EDA | Exploratory analysis notebook with 12 charts and written findings | `notebooks/01_eda.ipynb` |
| Dashboard | Interactive Streamlit app with filters, charts, and searchable table | `app/dashboard.py` |

## Tech Stack

- **Python 3.14** — core language
- **BeautifulSoup + lxml** — HTML parsing for Jobberman and MyJobMag
- **Requests** — REST API integration for Remote OK
- **Pandas** — data unification, transformation, analysis
- **Matplotlib + Seaborn** — notebook visualizations
- **Streamlit** — interactive dashboard

## Data Pipeline