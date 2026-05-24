"""
Debug script v2 - find the actual structure of job cards.
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

url = "https://www.jobberman.com/jobs"
response = requests.get(url, headers=HEADERS, timeout=15)
soup = BeautifulSoup(response.text, "lxml")

print(f"Status: {response.status_code}\n")

# Find all <a> tags pointing to /listings/
listing_links = soup.find_all("a", href=lambda h: h and "/listings/" in h)
print(f"Total /listings/ links found: {len(listing_links)}\n")

if listing_links:
    print("=" * 70)
    print("INSPECTING THE FIRST LISTING LINK")
    print("=" * 70)
    first_link = listing_links[0]
    print(f"\nLink href: {first_link.get('href')}")
    print(f"Link text (first 100 chars): {first_link.get_text(strip=True)[:100]}")

    print("\n--- WALKING UP THE PARENT CHAIN ---")
    parent = first_link.parent
    depth = 1
    while parent and depth <= 6:
        tag = parent.name
        classes = parent.get("class", [])
        class_preview = " ".join(classes[:3]) if classes else "(no class)"
        print(f"Level {depth}: <{tag}> class='{class_preview}'")
        parent = parent.parent
        depth += 1

    print("\n--- FULL HTML OF THE LIKELY CARD (3rd parent up) ---")
    card = first_link.parent.parent.parent
    print(str(card)[:1500])
    print("\n... (truncated)")