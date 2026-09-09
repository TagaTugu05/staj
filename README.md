# Staj Radar — Kurulum

## 1) Yerelde test
```
cd backend
pip install -r requirements.txt
python app.py
```
Sonra `frontend/index.html` dosyasını tarayıcıda aç. (API_BASE zaten `http://localhost:5000`)

## 2) 7/24 çalışması için barındırma (hosting)
Bilgisayarınız kapalıyken de çalışması için backend'i bir sunucuya koymanız gerekir. Ücretsiz/ucuz seçenekler:

- **Render.com** (Free/Starter Web Service): `backend` klasörünü GitHub'a push edin, Render'da "New Web Service" ile bağlayın. Start command: `gunicorn app:app`
- **Railway.app**: Benzer şekilde, otomatik deploy.
- **Bir VPS (DigitalOcean, Hetzner)**: `gunicorn app:app` + `systemd` servisi olarak sürekli çalıştırılır.

> Not: Free planlarda sunucu boşta kalınca "uyuyabilir" — bu durumda zamanlanmış tarama da durur. Gerçek 7/24 için en az $5-7/ay bir plan (Render Starter, Railway hobby) veya ucuz bir VPS öneririm.

## 3) Frontend'i yayınlama
`frontend/index.html` içindeki `API_BASE` değişkenini backend'inizin gerçek adresiyle değiştirin (örn. `https://staj-radar.onrender.com`). Sonra bu dosyayı:
- Netlify / Vercel / GitHub Pages üzerine sürükle-bırak ile yükleyebilirsiniz (ücretsiz).

## 4) Tarama sıklığını değiştirme
`backend/app.py` içinde:
```python
scheduler.add_job(run_scan, "interval", hours=3, id="staj_tarama")
```
`hours=3` değerini istediğiniz sıklıkla değiştirin.

## 5) Şirket listesini güncelleme
`backend/companies.py` içindeki `COMPANIES` listesine ekleme/çıkarma yapabilirsiniz.

## Yasal not
Bu sistem Instagram/LinkedIn'e **giriş yapmaz**, sadece herkese açık arama motoru sonuçlarını okur. Bu yüzden hesap yasaklanma riski yoktur. Ancak arama motorları çok sık istek atan IP'leri geçici olarak sınırlayabilir — `scraper.py` içindeki `time.sleep(2)` bu yüzden var, düşürmeyin.
