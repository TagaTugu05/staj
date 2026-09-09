from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import threading

from db import init_db, get_all_listings, get_last_scan
from scraper import run_scan
from companies import COMPANIES

app = Flask(__name__)
CORS(app)  # frontend farklı bir adresten çağıracağı için gerekli

init_db()

scan_lock = threading.Lock()


def run_scan_safely():
    # Aynı anda iki tarama birden başlamasın diye kilit
    if not scan_lock.acquire(blocking=False):
        print("Tarama zaten çalışıyor, yeni istek atlandı.")
        return
    try:
        run_scan()
    finally:
        scan_lock.release()


@app.get("/api/listings")
def listings():
    return jsonify(get_all_listings())


@app.get("/api/status")
def status():
    return jsonify({
        "company_count": len(COMPANIES),
        "last_scan": get_last_scan(),
    })


@app.post("/api/scan-now")
def scan_now():
    """Taramayı arka planda başlatır, isteği hemen bitirir (worker timeout'a takılmasın diye)."""
    if scan_lock.locked():
        return jsonify({"status": "already_running"}), 200
    threading.Thread(target=run_scan_safely, daemon=True).start()
    return jsonify({"status": "started"}), 202


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Her 3 saatte bir otomatik tarama -> 7/24 çalışan kısım burası
    scheduler.add_job(run_scan_safely, "interval", hours=3, id="staj_tarama")
    scheduler.start()


# Modül seviyesinde çağırıyoruz çünkü Render'da uygulamayı gunicorn başlatıyor,
# "if __name__ == '__main__'" bloğu gunicorn ile ÇALIŞMAZ. Scheduler'ın hem
# yerelde (python app.py) hem gunicorn'da başlaması için burada olması şart.
start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
