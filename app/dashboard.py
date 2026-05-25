"""
Nigerian Job Market Dashboard
Interactive dashboard exploring 325 job listings across Jobberman, MyJobMag, and Remote OK.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Page configuration - this MUST be the first Streamlit command
st.set_page_config(
    page_title="Nigerian Job Market",
    page_icon="💼",
    layout="wide",  # Use full browser width instead of narrow centered column
    initial_sidebar_state="expanded"
)

# Title and intro
st.title("🇳🇬 Nigerian Job Market Analytics")
st.markdown("""
Interactive analysis of **325 job listings** scraped from three sources in May 2026.
Use the sidebar filters to explore the data.
""")
# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():
    """
    Load the latest unified jobs CSV from data/processed/.
    The @st.cache_data decorator means this function runs ONCE,
    then Streamlit serves cached data on subsequent calls.
    Without it, the CSV reloads from disk every interaction.
    """
    # Find the most recent unified CSV
    data_dir = Path(__file__).parent.parent / "data" / "processed"
    csv_files = sorted(data_dir.glob("jobs_unified_*.csv"))
    
    if not csv_files:
        st.error("No unified data file found in data/processed/. Run clean_and_unify.py first.")
        st.stop()
    
    latest_file = csv_files[-1]  # Sorted alphabetically = newest last
    df = pd.read_csv(latest_file)
    
    # Parse dates so filters work properly
    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")
    
    # Add salary midpoint for analysis (same as we did in the notebook)
    df["salary_midpoint"] = (df["salary_min"] + df["salary_max"]) / 2
    
    return df, latest_file.name

# Load the data
df, source_file = load_data()

# Show data source info in small text
st.caption(f"Data source: `{source_file}` • Loaded {len(df)} jobs")
# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔍 Filters")
st.sidebar.markdown("Filter the dataset to explore specific segments.")

# Filter 1: Source (multi-select)
all_sources = sorted(df["source"].unique())
selected_sources = st.sidebar.multiselect(
    "Source",
    options=all_sources,
    default=all_sources,
    help="Job boards to include"
)

# Filter 2: Region (we need to recreate the region column from the notebook)
def categorize_location(loc):
    """Same logic as the EDA notebook - groups raw locations into regions."""
    if pd.isna(loc):
        return "Unknown"
    loc_lower = str(loc).lower()
    nigerian_cities = ["lagos", "abuja", "ibadan", "kano", "ph", "port harcourt",
                       "benin", "kaduna", "enugu", "ogun", "oyo", "rivers", "anambra"]
    if any(city in loc_lower for city in nigerian_cities) or "nigeria" in loc_lower:
        return "Nigeria"
    if "remote" in loc_lower:
        return "Remote"
    if any(c in loc_lower for c in ["united states", "usa", "u.s."]):
        return "United States"
    if any(c in loc_lower for c in ["canada"]):
        return "Canada"
    if any(c in loc_lower for c in ["united kingdom", "uk"]):
        return "United Kingdom"
    if "india" in loc_lower:
        return "India"
    return "Other International"

df["region"] = df["location"].apply(categorize_location)

all_regions = sorted(df["region"].unique())
selected_regions = st.sidebar.multiselect(
    "Region",
    options=all_regions,
    default=all_regions,
    help="Geographic region"
)

# Filter 3: Salary disclosure
salary_filter = st.sidebar.radio(
    "Salary Information",
    options=["All jobs", "Only jobs with disclosed salary"],
    index=0,
    help="Some sources don't publish salary - filter to focus on those that do"
)

# Filter 4: Currency
all_currencies = ["All"] + sorted([c for c in df["currency"].dropna().unique()])
selected_currency = st.sidebar.selectbox(
    "Currency",
    options=all_currencies,
    index=0,
    help="Filter by salary currency"
)

# Apply all filters to create a filtered dataframe
filtered_df = df[
    (df["source"].isin(selected_sources)) &
    (df["region"].isin(selected_regions))
].copy()

if salary_filter == "Only jobs with disclosed salary":
    filtered_df = filtered_df[filtered_df["salary_disclosed"] == True]

if selected_currency != "All":
    filtered_df = filtered_df[filtered_df["currency"] == selected_currency]

# Show filter result count in sidebar
st.sidebar.divider()
st.sidebar.metric(
    "Jobs after filtering",
    f"{len(filtered_df):,}",
    delta=f"{len(filtered_df) - len(df)} from total"
)
# ============================================================
# KPI METRICS ROW
# ============================================================

st.markdown("### Key Metrics")

# Calculate the numbers we want to display
total_jobs = len(filtered_df)
total_sources = filtered_df["source"].nunique()
disclosed_pct = filtered_df["salary_disclosed"].mean() * 100 if len(filtered_df) > 0 else 0
remote_count = filtered_df["job_type"].str.contains("Remote", case=False, na=False).sum()

# Create 4 columns for the metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Jobs",
        value=f"{total_jobs:,}",
        help="Total unified job listings across all sources"
    )

with col2:
    st.metric(
        label="Data Sources",
        value=total_sources,
        help="Number of distinct job boards scraped"
    )

with col3:
    st.metric(
        label="Salary Disclosed",
        value=f"{disclosed_pct:.0f}%",
        help="Percentage of jobs publishing salary information"
    )

with col4:
    st.metric(
        label="Remote Roles",
        value=f"{remote_count}",
        help="Jobs explicitly tagged as remote"
    )

st.divider()
# ============================================================
# CHARTS
# ============================================================

st.markdown("### Market Composition")

# Handle empty filtered data gracefully
if len(filtered_df) == 0:
    st.warning("No jobs match the current filters. Try widening your selection.")
    st.stop()

# Two charts side by side
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Jobs by Source**")
    source_counts = filtered_df["source"].value_counts()
    st.bar_chart(source_counts, color="#2E75B6")

with chart_col2:
    st.markdown("**Jobs by Region**")
    region_counts = filtered_df["region"].value_counts()
    st.bar_chart(region_counts, color="#70AD47")
# ============================================================
# SALARY DISTRIBUTION
# ============================================================

st.markdown("### Salary Distribution")
st.markdown("Salaries split by currency since NGN and USD aren't directly comparable. Midpoint of disclosed ranges.")

# Get jobs with disclosed salary, split by currency
salary_df = filtered_df[filtered_df["salary_disclosed"] == True].copy()

if len(salary_df) == 0:
    st.info("No salary data in the current filter selection.")
else:
    ngn_salaries = salary_df[salary_df["currency"] == "NGN"]["salary_midpoint"].dropna()
    usd_salaries = salary_df[salary_df["currency"] == "USD"]["salary_midpoint"].dropna()

    sal_col1, sal_col2 = st.columns(2)

    with sal_col1:
        st.markdown(f"**Nigerian Salaries (NGN, n={len(ngn_salaries)})**")
        if len(ngn_salaries) > 0:
            # Create bins for histogram-style display
            ngn_in_thousands = ngn_salaries / 1000
            # Use pandas' cut to bin the data
            bins = pd.cut(ngn_in_thousands, bins=10).value_counts().sort_index()
            # Convert interval index to readable string labels
            bin_labels = [f"{int(interval.left)}-{int(interval.right)}k" for interval in bins.index]
            bin_df = pd.DataFrame({"Salary Range (NGN)": bin_labels, "Count": bins.values})
            st.bar_chart(bin_df.set_index("Salary Range (NGN)"), color="#2E75B6")
            
            # Quick stats
            st.metric("Median", f"₦{ngn_salaries.median():,.0f}")
        else:
            st.caption("No NGN salaries in current selection")

    with sal_col2:
        st.markdown(f"**Remote USD Salaries (n={len(usd_salaries)})**")
        if len(usd_salaries) > 0:
            usd_in_thousands = usd_salaries / 1000
            bins = pd.cut(usd_in_thousands, bins=10).value_counts().sort_index()
            bin_labels = [f"${int(interval.left)}-{int(interval.right)}k" for interval in bins.index]
            bin_df = pd.DataFrame({"Salary Range (USD)": bin_labels, "Count": bins.values})
            st.bar_chart(bin_df.set_index("Salary Range (USD)"), color="#70AD47")
            
            st.metric("Median", f"${usd_salaries.median():,.0f}")
        else:
            st.caption("No USD salaries in current selection")
            # ============================================================
# TOP HIRERS
# ============================================================

st.markdown("### Who's Hiring")

import html

def safe_unescape(value):
    """Decode HTML entities, handling NaN safely."""
    if pd.isna(value):
        return None
    return html.unescape(str(value)).strip()

# Clean company and title columns (same logic as the notebook)
filtered_df["company_clean"] = filtered_df["company"].apply(safe_unescape)
filtered_df["title_clean"] = filtered_df["title"].apply(safe_unescape)

EXCLUDE_COMPANIES = ["Anonymous Employer", "Confidential", "None"]
EXCLUDE_TITLES = ["Jobs", "Latest Jobs", "Job Openings", "None"]

hire_col1, hire_col2 = st.columns(2)

with hire_col1:
    st.markdown("**Top 10 Companies**")
    companies = filtered_df[~filtered_df["company_clean"].isin(EXCLUDE_COMPANIES)]
    top_companies = companies["company_clean"].value_counts().head(10)
    if len(top_companies) > 0:
        st.bar_chart(top_companies, color="#2E75B6", horizontal=True)
    else:
        st.caption("No company data in current selection")

with hire_col2:
    st.markdown("**Top 10 Job Titles**")
    titles = filtered_df[~filtered_df["title_clean"].isin(EXCLUDE_TITLES)]
    # Title-case for grouping
    titles["title_normalized"] = titles["title_clean"].str.title()
    top_titles = titles["title_normalized"].value_counts().head(10)
    if len(top_titles) > 0:
        st.bar_chart(top_titles, color="#70AD47", horizontal=True)
    else:
        st.caption("No title data in current selection")

st.divider()

# ============================================================
# JOB LISTINGS TABLE
# ============================================================

st.markdown("### Job Listings")
st.markdown(f"Showing **{len(filtered_df)} jobs** matching current filters. Click column headers to sort.")

# Search box for filtering by title/company
search_term = st.text_input(
    "🔎 Search title or company",
    placeholder="e.g. 'engineer', 'sales', 'remote'",
    help="Case-insensitive search across job title and company"
)

# Build the display dataframe
display_df = filtered_df.copy()

if search_term:
    search_lower = search_term.lower()
    mask = (
        display_df["title"].astype(str).str.lower().str.contains(search_lower, na=False) |
        display_df["company"].astype(str).str.lower().str.contains(search_lower, na=False)
    )
    display_df = display_df[mask]
    st.caption(f"Found {len(display_df)} jobs matching '{search_term}'")

# Select and rename columns for display
display_cols = display_df[[
    "title", "company", "location", "source", "job_type", 
    "salary_min", "salary_max", "currency", "url"
]].rename(columns={
    "title": "Job Title",
    "company": "Company",
    "location": "Location",
    "source": "Source",
    "job_type": "Type",
    "salary_min": "Min Salary",
    "salary_max": "Max Salary",
    "currency": "Currency",
    "url": "URL"
})

st.dataframe(
    display_cols,
    use_container_width=True,
    hide_index=True,
    column_config={
        "URL": st.column_config.LinkColumn("Apply Link", display_text="View →"),
        "Min Salary": st.column_config.NumberColumn(format="%.0f"),
        "Max Salary": st.column_config.NumberColumn(format="%.0f"),
    }
)