# ⚙️ Zavod Monitoring Tizimi

Kamera orqali zavod darvozasini avtomatik nazorat qilish tizimi.

## 🚀 Tez Ishga Tushirish

### Windows
```
start.bat  faylini ikki marta bosing
```

### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

### Qo'lda
```bash
cd backend
pip install -r ../requirements_minimal.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Brauzerda oching: **http://localhost:8000**

---

## 📁 Loyiha Tuzilmasi

```
zavod-monitoring/
├── backend/
│   ├── app.py              ← Asosiy server (FastAPI)
│   ├── kamera.py           ← Kamera boshqaruvi
│   ├── database.py         ← SQLite ma'lumotlar bazasi
│   ├── excel_eksport.py    ← Excel hisobotlar
│   ├── modules/
│   │   ├── anpr.py         ← Raqam o'qish (ANPR)
│   │   ├── transport.py    ← Mashina rang/tur aniqlash
│   │   └── ishchi.py       ← Yuz tanish
│   ├── data/
│   │   ├── zavod.db        ← Ma'lumotlar bazasi (avtomatik yaratiladi)
│   │   └── rasmlar/        ← Mashinalar rasmlari
│   └── exports/            ← Excel fayllar
├── frontend/
│   ├── templates/index.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── models/
│   └── yuzlar/             ← Ishchi yuz rasmlari (ism.jpg formatida)
├── requirements.txt        ← To'liq kutubxonalar
├── requirements_minimal.txt← Minimal (tez o'rnatish)
├── start.sh                ← Linux/macOS ishga tushirish
└── start.bat               ← Windows ishga tushirish
```

---

## 🎮 Foydalanish

### Transport qayd etish
1. Kamera oldiga mashina kelganda:
   - **▶ KIRDI** tugmasini bosing → raqam, rang, davlat, viloyat aniqlanadi + rasm olinadi
   - **◀ CHIQDI** tugmasini bosing

### Ishchi nazorat
1. **🔍 SKAN QILISH** tugmasi → kamera oldidagi yuzlar aniqlanadi

### Ishchi qo'shish (yuz tanish uchun)
`models/yuzlar/` papkasiga ishchi rasmini qo'ying:
```
models/yuzlar/Ali Valiyev.jpg
models/yuzlar/Sardor Toshmatov.jpg
```

### Excel hisobot
**📥 EXCEL YUKLAB OLISH** → davr tanlang → fayl yuklab olinadi

---

## 🔧 Sozlamalar

`backend/kamera.py` ichida:
```python
kamera = KameraManager(kamera_id=0)   # 0 = kompyuter kamerasi
                                        # 1,2... = boshqa kameralar
                                        # "rtsp://..." = IP kamera
```

---

## 📈 Keyingi Bosqichlar (Zavod uchun)

- [ ] IP kamera (RTSP) ulash
- [ ] Avtomatik harakat sensori (darvoza ochilganda)
- [ ] Telegram bot bildirishnomalar
- [ ] Ko'p kamera qo'llab-quvvatlash
- [ ] YOLO v8 bilan aniqroq mashina aniqlash
- [ ] OpenALPR bilan yaxshiroq raqam o'qish
