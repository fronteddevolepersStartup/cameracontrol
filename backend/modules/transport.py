"""
Transport Moduli
- Mashina turini aniqlash (fura / yengil)
- Rangini aniqlash
- Rasmga olish
"""

import cv2
import os
import numpy as np
from datetime import datetime

RASM_PAPKA = os.path.join(os.path.dirname(__file__), "..", "data", "rasmlar")
os.makedirs(RASM_PAPKA, exist_ok=True)

# Rang diapazoni (HSV)
RANGLAR = {
    "Qizil":   [([0, 100, 100],   [10, 255, 255]),
                ([160, 100, 100], [180, 255, 255])],
    "Yashil":  [([35, 50, 50],    [85, 255, 255])],
    "Ko'k":    [([95, 50, 50],    [135, 255, 255])],
    "Sariq":   [([20, 100, 100],  [35, 255, 255])],
    "Oq":      [([0, 0, 180],     [180, 30, 255])],
    "Qora":    [([0, 0, 0],       [180, 255, 50])],
    "Kulrang": [([0, 0, 60],      [180, 30, 170])],
}


def rang_aniqlash(frame: np.ndarray) -> str:
    """Kadrdan asosiy rangni aniqlash"""
    try:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Markaziy qismni olish (36%x36%)
        h, w = hsv.shape[:2]
        roi = hsv[h//3: 2*h//3, w//4: 3*w//4]

        eng_katta = 0
        asosiy_rang = "Noma'lum"

        for rang_nomi, diapazonlar in RANGLAR.items():
            maska = None
            for (quyi, yuqori) in diapazonlar:
                m = cv2.inRange(roi,
                                np.array(quyi, dtype=np.uint8),
                                np.array(yuqori, dtype=np.uint8))
                maska = m if maska is None else cv2.bitwise_or(maska, m)

            son = cv2.countNonZero(maska)
            if son > eng_katta:
                eng_katta = son
                asosiy_rang = rang_nomi

        return asosiy_rang
    except Exception as e:
        print(f"[Rang] Xatolik: {e}")
        return "Noma'lum"


def mashina_turi_aniqlash(frame: np.ndarray) -> str:
    """
    Mashina turini aniqlash:
    Soddalashtirilgan versiya - balandlik/kenglik nisbatiga qarab
    To'liq versiyada YOLO v8 ishlatiladi
    """
    try:
        h, w = frame.shape[:2]
        nisbat = h / w

        # Furalar odatda balandroq va kattaroq bo'ladi
        # Bu yerda kamera kadrining umumiy maydoniga qarab hukm chiqariladi
        # Haqiqiy tizimda YOLO detection kerak
        if w * h > 80000:   # Katta ob'ekt
            return "Fura"
        else:
            return "Yengil"
    except:
        return "Noma'lum"


def rasm_saqlash(frame: np.ndarray, raqam: str, tur: str) -> str:
    """Mashinani rasmga olish va saqlash"""
    try:
        vaqt = datetime.now().strftime("%Y%m%d_%H%M%S")
        fayl_nomi = f"{tur}_{raqam}_{vaqt}.jpg"
        # Fayl nomidan noto'g'ri belgilarni olib tashlash
        fayl_nomi = "".join(c for c in fayl_nomi if c.isalnum() or c in ('_', '-', '.'))
        yol = os.path.join(RASM_PAPKA, fayl_nomi)
        cv2.imwrite(yol, frame)
        return yol
    except Exception as e:
        print(f"[Rasm] Saqlashda xatolik: {e}")
        return ""


def transport_qayta_ishlash(frame: np.ndarray, harakat: str = "kirdi") -> dict:
    """
    Asosiy funksiya: kadrni qayta ishlash
    Qaytaradi: barcha ma'lumotlar dict ko'rinishida
    """
    from .anpr import raqam_oqish

    anpr = raqam_oqish(frame)
    rang = rang_aniqlash(frame)
    tur = mashina_turi_aniqlash(frame)
    rasm_yol = rasm_saqlash(frame, anpr["raqam"], tur)

    return {
        "raqam":   anpr["raqam"],
        "tur":     tur,
        "rang":    rang,
        "davlat":  anpr["davlat"],
        "viloyat": anpr["viloyat"],
        "harakat": harakat,
        "ishonch": anpr["ishonch"],
        "rasm_yol": rasm_yol,
    }
