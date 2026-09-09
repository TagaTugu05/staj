"""
Şirket başına, her kaynak (linkedin/instagram/kariyer.net) için
DuckDuckGo'nun herkese açık HTML arama sonuçlarını çeker.
Login gerektirmez, hiçbir platformun API/ToS kuralını ihlal etmez.
"""
import re
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from companies import COMPANIES, SOURCES
from db import save_listing, log_scan, init_db, remove_expired_listings, remove_stale_listings
from filters import is_stale_or_closed

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}
SEARCH_URL = "https://html.duckduckgo.com/html/"

TR_MONTHS = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5,
    "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11,
    "aralık": 12, "aralik": 12,
}

# "12.09.2026" / "12/09/2026" / "12-09-2026"
DATE_NUMERIC_RE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")
# "12 Eylül 2026" / "12 eylül"
DATE_TEXT_RE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(TR_MONTHS.keys()) + r")\s*(\d{4})?\b",
    re.IGNORECASE,
)


def guess_deadline(text):
    """Metinde bir tarih bulursa ISO formatında (YYYY-MM-DD) döner, yoksa None."""
    m = DATE_NUMERIC_RE.search(text)
    if m:
        day, month, year = map(int, m.groups())
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass

    m = DATE_TEXT_RE.search(text)
    if m:
        day = int(m.group(1))
        month = TR_MONTHS[m.group(2).lower()]
        year = int(m.group(3)) if m.group(3) else date.today().year
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass

    return None


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

    if not results:
        # Sonuç yoksa bunun "gerçekten sonuç yok" mu yoksa "engellendik" mi
        # olduğunu ayırt etmek için sayfa içeriğine bak.
        lower_body = resp.text.lower()
        if "anomaly" in lower_body or "unusual traffic" in lower_body or "captcha" in lower_body:
            print(f"[UYARI] '{query}' için DuckDuckGo bizi engellemiş olabilir (anomali/captcha sayfası döndü).")
        else:
            print(f"[BİLGİ] '{query}' için sonuç bulunamadı.")

    return results


def run_scan():
    init_db()
    new_count = 0
    for company in COMPANIES:
        company_hits = 0
        for source in SOURCES:
            query = f'"{company}" staj site:{source}'
            try:
                results = search(query)
            except Exception as e:
                print(f"[HATA] '{query}' sorgusunda beklenmedik hata: {e}")
                results = []

            for title, url in results:
                try:
                    if is_stale_or_closed(title):
                        continue
                    deadline = guess_deadline(title)
                    if deadline and deadline < date.today().isoformat():
                        continue
                    if save_listing(company, source, title, url, deadline):
                        new_count += 1
                        company_hits += 1
                except Exception as e:
                    print(f"[HATA] '{title}' işlenirken hata: {e}")
            time.sleep(2)  # DDG'yi yormamak için nazik bekleme

        print(f"[TARAMA] {company}: {company_hits} yeni ilan bulundu.")

    removed_expired = remove_expired_listings()
    removed_stale = remove_stale_listings()
    log_scan(new_count)
    print(f"Tarama bitti. {new_count} yeni ilan, "
          f"{removed_expired} süresi geçmiş, {removed_stale} eski/kapanmış ilan kaldırıldı.")
    return new_count


if __name__ == "__main__":
    run_scan()
