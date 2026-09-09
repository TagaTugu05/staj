# Staj Radar — Kurulum

## 0) Tavily API anahtarı (ZORUNLU)
DuckDuckGo kazıma yöntemi Render gibi bulut sunuculardan engellendiği için sistem artık **Tavily** arama API'sini kullanıyor.

1. https://app.tavily.com adresinden ücretsiz hesap aç (ayda 1000 kredi ücretsiz).
2. Dashboard'dan API anahtarını kopyala (`tvly-...` ile başlar).
3. Render Dashboard → servisin → **Environment** sekmesi → **Add Environment Variable**:
   - Key: `TAVILY_API_KEY`
   - Value: kopyaladığın anahtar
4. Kaydet — Render otomatik olarak yeniden deploy eder.

Bu adım atlanırsa tarama çalışmaz, log'da `TAVILY_API_KEY tanımlı değil` uyarısı görürsün.

## 1) Yerelde test
```
cd backend
pip install -r requirements.txt
export TAVILY_API_KEY=tvly-xxxxxxxx   # Windows'ta: set TAVILY_API_KEY=tvly-xxxxxxxx
python app.py
```
Sonra `frontend/index.html` dosyasını tarayıcıda aç. (API_BASE zaten `http://localhost:5000`)

## 2) 7/24 çalışması için barındırma (hosting)
Bilgisayarınız kapalıyken de çalışması için backend'i bir sunucuya koymanız gerekir. Ücretsiz/ucuz seçenekler:

- **Render.com** (Free/Starter Web Service): `backend` klasörünü GitHub'a push edin, Render'da "New Web Service" ile bağlayın. Start command: `gunicorn app:app`
- **Railway.app**: Benzer şekilde, otomatik deploy.
- **Bir VPS (DigitalOcean, Hetzner)**: `gunicorn app:app` + `systemd` servisi olarak sürekli çalıştırılır.

> Not: Free planlarda sunucu boşta kalınca "uyuyabilir" — bu durumda zamanlanmış tarama da durur. Gerçek 7/24 için en az $5-7/ay bir plan (Render Starter, Railway hobby) veya ucuz bir VPS öneririm.

## 3) Frontend artık backend'in içinde
`backend/static/index.html` dosyası Flask tarafından otomatik servis edilir. Yani backend'i deploy ettiğiniz TEK link (örn. `https://staj-radar.onrender.com`) hem siteyi hem API'yi açar — ayrı bir Netlify/Vercel işlemi gerekmez.

Frontend'i yine de ayrı bir yerde host etmek isterseniz `frontend/index.html` içindeki `API_BASE` değişkenine backend adresinizi tam yazmanız gerekir.

## 3.5) GitHub'da güncelledim, hosting'de nasıl güncellenir?

**Render:**
1. Render Dashboard → ilgili servis → **Settings → Build & Deploy** kısmında "Auto-Deploy" **Yes** ise, GitHub'a her push attığınızda otomatik yeniden deploy olur (1-3 dk sürer). Üstteki **"Events"** sekmesinden ilerlemeyi izleyin.
2. Auto-Deploy kapalıysa: sağ üstteki **"Manual Deploy" → "Deploy latest commit"** butonuna basın.
3. Deploy bitince sayfayı **hard refresh** yapın (Ctrl+Shift+R / Cmd+Shift+R) — tarayıcı önbelleği eski sürümü gösterebilir.

**Railway:**
1. GitHub reponuz bağlıysa her push'ta otomatik deploy başlar; proje sayfasında **"Deployments"** sekmesinden durumu görürsünüz.
2. Otomatik değilse üç nokta menüsünden **"Redeploy"** seçin.

**404 kontrol listesi:**
- Ana link (`.../`) açılmıyorsa: `app.py` içinde `/` route'u olduğundan emin olun (bu güncellemede eklendi).
- `requirements.txt` içindeki paketlerin hepsi kurulu mu — deploy loglarında hata var mı bakın (Render/Railway "Logs" sekmesi).
- Start command doğru mu: `gunicorn app:app` (Flask app'in dosya adı `app.py` ise).
- `backend/static/index.html` dosyasının gerçekten repoya push edildiğinden emin olun (`git status`, `git add`, `git commit`, `git push`).

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
