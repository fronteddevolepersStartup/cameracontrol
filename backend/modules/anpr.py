"""
ANPR - Avtomatik Raqam Tanish Moduli
Hozircha: EasyOCR ishlatadi (GPU shart emas)
Keyinchalik: OpenALPR yoki Plate Recognizer API ga almashtiriladi
"""

import re
import cv2
import numpy as np

try:
    import easyocr
    READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    EASYOCR_MAVJUD = True
except ImportError:
    EASYOCR_MAVJUD = False
    print("[ANPR] EasyOCR topilmadi - demo rejimda ishlaydi")


# O'zbekiston viloyat kodlari
VILOYAT_KODLARI = {
    "01": "Toshkent shahar", "10": "Toshkent viloyat",
    "20": "Andijon",        "21": "Farg'ona",
    "22": "Namangan",       "30": "Samarqand",
    "31": "Buxoro",         "32": "Navoiy",
    "33": "Qashqadaryo",    "34": "Surxondaryo",
    "35": "Jizzax",         "36": "Sirdaryo",
    "37": "Xorazm",         "38": "Qoraqalpog'iston",
}

# Boshqa davlatlar prefikslari
DAVLAT_PREFIKSLARI = {
    "RU": "Rossiya", "KZ": "Qozog'iston", "KG": "Qirg'iziston",
    "TJ": "Tojikiston", "TM": "Turkmaniston", "UZ": "O'zbekiston",
    "CN": "Xitoy", "TR": "Turkiya",
}


def raqam_tozalash(matn: str) -> str:
    """OCR natijasini tozalash"""
    matn = matn.upper().strip()
    matn = re.sub(r'[^A-Z0-9]', '', matn)
    return matn


def davlat_viloyat_aniqlash(raqam: str):
    """
    Raqam belgisidan davlat va viloyatni aniqlash
    O'zbek format: 01 A 123 BC  yoki  01234ABC
    """
    davlat = "Noma'lum"
    viloyat = "Noma'lum"

    if not raqam:
        return davlat, viloyat

    # O'zbekiston formatini tekshirish (2 raqam bilan boshlanadi)
    kod = raqam[:2]
    if kod.isdigit() and kod in VILOYAT_KODLARI:
        davlat = "O'zbekiston"
        viloyat = VILOYAT_KODLARI[kod]
        return davlat, viloyat

    # Boshqa davlatlar (harf prefiksi)
    for prefiks, nom in DAVLAT_PREFIKSLARI.items():
        if raqam.startswith(prefiks):
            davlat = nom
            return davlat, viloyat

    return davlat, viloyat


def plaka_ajratish(frame: np.ndarray):
    """
    Kamera kadridan plaka qismini kesib olish
    Soddalashtirilgan versiya - to'liq versiyada YOLO ishlatiladi
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.018 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            nisbat = w / float(h)
            # Plaka nisbati: taxminan 3:1 dan 6:1 gacha
            if 2.5 < nisbat < 6.5 and w > 80:
                plaka = frame[y:y+h, x:x+w]
                return plaka, (x, y, w, h)

    return None, None


def raqam_oqish(frame: np.ndarray) -> dict:
    """
    Asosiy funksiya: kadrdan raqamni o'qish
    Qaytaradi: {raqam, davlat, viloyat, ishonch}
    """
    natija = {
        "raqam": "ANIQLANMADI",
        "davlat": "Noma'lum",
        "viloyat": "Noma'lum",
        "ishonch": 0.0
    }

    if not EASYOCR_MAVJUD:
        # Demo rejim - tasodifiy test raqami
        import random
        kodlar = list(VILOYAT_KODLARI.keys())
        kod = random.choice(kodlar)
        natija["raqam"] = f"{kod}A{random.randint(100,999)}BC"
        natija["davlat"] = "O'zbekiston"
        natija["viloyat"] = VILOYAT_KODLARI[kod]
        natija["ishonch"] = round(random.uniform(0.7, 0.95), 2)
        return natija

    # Plakani ajratib olish
    plaka, bbox = plaka_ajratish(frame)
    if plaka is None:
        # Butun kadrdan o'qishga urinish
        plaka = frame

    try:
        results = READER.readtext(plaka)
        if results:
            # Eng ishonchli natijani olish
            results.sort(key=lambda x: x[2], reverse=True)
            matn = raqam_tozalash(results[0][1])
            ishonch = results[0][2]

            if len(matn) >= 4:
                davlat, viloyat = davlat_viloyat_aniqlash(matn)
                natija.update({
                    "raqam": matn,
                    "davlat": davlat,
                    "viloyat": viloyat,
                    "ishonch": round(ishonch, 2)
                })
    except Exception as e:
        print(f"[ANPR] Xatolik: {e}")

    return natija
