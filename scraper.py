"""
Şirket başına, her kaynak (linkedin/instagram/kariyer.net) için
DuckDuckGo'nun herkese açık HTML arama sonuçlarını çeker.
Login gerektirmez, hiçbir platformun API/ToS kuralını ihlal etmez.
"""
import time
import requests
from bs4 import BeautifulSoup

from companies import COMPANIES, SOURCES
from db import save_listing, log_scan, init_db

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}
SEARCH_URL = "https://html.duckduckgo.com/html/"


def search(query):
    """Tek bir DuckDuckGo araması yapar, (başlık, url) listesi döner."""
    try:
        resp = requests.post(SEARCH_URL, data={"q": query}, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[HATA] arama başarısız: {query} -> {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for a in soup.select("a.result__a"):
        title = a.get_text(strip=True)
        url = a.get("href")
        if title and url:
            results.append((title, url))
    return results


def run_scan():
    init_db()
    new_count = 0
    for company in COMPANIES:
        for source in SOURCES:
            query = f'"{company}" staj site:{source}'
            for title, url in search(query):
                if save_listing(company, source, title, url):
                    new_count += 1
            time.sleep(2)  # DDG'yi yormamak için nazik bekleme
    log_scan(new_count)
    print(f"Tarama bitti. {new_count} yeni ilan bulundu.")
    return new_count


if __name__ == "__main__":
    run_scan()
