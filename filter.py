import re
from datetime import date

CURRENT_YEAR = date.today().year

# Bu kelimeler geçen başlıklar genelde "sonuç duyurusu" ya da "kapandı" anlamına gelir,
# açık ilan değildir -> ele.
NEGATIVE_SIGNALS = [
    "başvurdu", "başvuru aldık", "başvuru sayısı", "değerlendirmeye alındı",
    "tamamlandı", "sona erdi", "kapandı", "kapanmıştır", "doldu",
    "teşekkür ederiz", "rekor başvuru", "bin başvuru", "bin öğrenci",
]

YEAR_RE = re.compile(r"\b(20\d{2})\b")


def is_stale_or_closed(title):
    """Eski yıla ait ya da 'kapandı/sonuçlandı' türü duyuruysa True döner (ele)."""
    lower = title.lower()

    if any(sig in lower for sig in NEGATIVE_SIGNALS):
        return True

    years_found = [int(y) for y in YEAR_RE.findall(title)]
    # Başlıkta geçen yıl bu yıldan eskiyse (örn. 2023 Yaz Dönemi) -> eski ilan
    if years_found and max(years_found) < CURRENT_YEAR:
        return True

    return False
