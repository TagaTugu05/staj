import sqlite3
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path(__file__).parent / "staj.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            found_at TEXT NOT NULL,
            deadline TEXT
        )
    """)
    # Eski veritabanlarında deadline kolonu yoksa ekle (geriye dönük uyumluluk)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(listings)").fetchall()]
    if "deadline" not in cols:
        conn.execute("ALTER TABLE listings ADD COLUMN deadline TEXT")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ran_at TEXT NOT NULL,
            new_count INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_listing(company, source, title, url, deadline=None):
    """Yeni ilan ise True döner, zaten varsa False."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO listings (company, source, title, url, found_at, deadline) VALUES (?,?,?,?,?,?)",
            (company, source, title, url, datetime.utcnow().isoformat(), deadline),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # aynı url zaten kayıtlı
    finally:
        conn.close()


def remove_expired_listings():
    """deadline'ı bugünden önce olan ilanları siler. Kaç tane silindiğini döner."""
    today = date.today().isoformat()
    conn = get_conn()
    cur = conn.execute(
        "DELETE FROM listings WHERE deadline IS NOT NULL AND deadline < ?",
        (today,),
    )
    conn.commit()
    removed = cur.rowcount
    conn.close()
    return removed


def log_scan(new_count):
    conn = get_conn()
    conn.execute(
        "INSERT INTO scan_log (ran_at, new_count) VALUES (?,?)",
        (datetime.utcnow().isoformat(), new_count),
    )
    conn.commit()
    conn.close()


def get_all_listings():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM listings ORDER BY found_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_last_scan():
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM scan_log ORDER BY ran_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None
