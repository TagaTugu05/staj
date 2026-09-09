import sqlite3
from datetime import datetime
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
            found_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ran_at TEXT NOT NULL,
            new_count INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_listing(company, source, title, url):
    """Yeni ilan ise True döner, zaten varsa False."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO listings (company, source, title, url, found_at) VALUES (?,?,?,?,?)",
            (company, source, title, url, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # aynı url zaten kayıtlı
    finally:
        conn.close()


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
