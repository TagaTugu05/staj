"""
Şirket başına TEK sorgu ile Tavily arama API'sini kullanır
(linkedin.com + instagram.com + kariyer.net aynı anda taranır).
Tavily kendi altyapısını kullandığı için IP engeli / captcha sorunu olmaz.
"""
import os
import re
import time
from datetime import date
from urllib.parse import urlparse

from tavily import TavilyClient

from companies import COMPANIES, SOURCES
from db import save_listing, log_scan, init_db, remove_expired_listings, remove_stale_listings
from filters import is_stale_or_closed

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

TR_MONTHS = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5,
    "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11,
    "aralık": 12, "aralik": 12,
}

DATE_NUMERIC_RE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")
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


def detect_source(url):
    host = urlparse(url).netloc.lower()
    for source in SOURCES:
        if source in host:
            return source
    return "diğer"


def search_company(client, company):
    """Bir şirket için TEK Tavily sorgusu, 3 kaynağı birden kapsayacak şekilde."""
    try:
        resp = client.search(
            query=f'"{company}" staj başvuru',
            search_depth="basic",
            max_results=10,
            include_domains=SOURCES,
        )
        return resp.get("results", [])
    except Exception as e:
        print(f"[HATA] '{company}' için Tavily araması başarısız: {e}")
        return []


def run_scan():
    init_db()

    if not TAVILY_API_KEY:
        print("[HATA] TAVILY_API_KEY tanımlı değil. Render'da Environment sekmesinden ekleyin.")
        return 0

    client = TavilyClient(api_key=TAVILY_API_KEY)
    new_count = 0

    for company in COMPANIES:
        results = search_company(client, company)
        company_hits = 0
        for r in results:
            try:
                title = r.get("title", "")
                url = r.get("url", "")
                if not title or not url:
                    continue
                if is_stale_or_closed(title):
                    continue
                deadline = guess_deadline(title)
                if deadline and deadline < date.today().isoformat():
                    continue
                source = detect_source(url)
                if save_listing(company, source, title, url, deadline):
                    new_count += 1
                    company_hits += 1
            except Exception as e:
                print(f"[HATA] sonuç işlenirken hata ({company}): {e}")
        print(f"[TARAMA] {company}: {company_hits} yeni ilan bulundu.")
        time.sleep(1)  # Tavily'nin rate limitine karşı nazik bekleme

    removed_expired = remove_expired_listings()
    removed_stale = remove_stale_listings()
    log_scan(new_count)
    print(f"Tarama bitti. {new_count} yeni ilan, "
          f"{removed_expired} süresi geçmiş, {removed_stale} eski/kapanmış ilan kaldırıldı.")
    return new_count


if __name__ == "__main__":
    run_scan()
