"""
Ishchilar Nazorati Moduli
- Yuz tanish (face recognition)
- Kirdi/chiqdi qayd etish
"""

import cv2
import os
import numpy as np
from datetime import datetime

YUZLAR_PAPKA = os.path.join(os.path.dirname(__file__), "..", "..", "models", "yuzlar")
os.makedirs(YUZLAR_PAPKA, exist_ok=True)

try:
    import face_recognition
    FACE_REC_MAVJUD = True
except ImportError:
    FACE_REC_MAVJUD = False
    print("[Ishchi] face_recognition topilmadi - demo rejimda ishlaydi")

# Yuzlar cache (xotiraga yuklangan ma'lum ishchilar)
_yuzlar_cache = {}   # {ism: encoding}


def yuzlarni_yuklash():
    """models/yuzlar/ papkasidan ishchi yuzlarini yuklash"""
    global _yuzlar_cache
    _yuzlar_cache = {}

    if not FACE_REC_MAVJUD:
        return

    for fayl in os.listdir(YUZLAR_PAPKA):
        if fayl.lower().endswith(('.jpg', '.jpeg', '.png')):
            ism = os.path.splitext(fayl)[0]
            yol = os.path.join(YUZLAR_PAPKA, fayl)
            try:
                rasm = face_recognition.load_image_file(yol)
                enc = face_recognition.face_encodings(rasm)
                if enc:
                    _yuzlar_cache[ism] = enc[0]
                    print(f"[Ishchi] Yuklandi: {ism}")
            except Exception as e:
                print(f"[Ishchi] {fayl} yuklanmadi: {e}")

    print(f"[Ishchi] Jami {len(_yuzlar_cache)} ishchi yuzi yuklandi")


def yuz_tanish(frame: np.ndarray) -> list:
    """
    Kadrdan yuzlarni tanish
    Qaytaradi: [{ism, joylashuv, ishonch}, ...]
    """
    natijalar = []

    if not FACE_REC_MAVJUD:
        # Demo rejim
        import random
        demo_ismlar = ["Ali Valiyev", "Sardor Toshmatov", "Bobur Rahimov", "Noma'lum"]
        ism = random.choice(demo_ismlar)
        natijalar.append({
            "ism": ism,
            "yuz_id": ism.replace(" ", "_").lower(),
            "joylashuv": (50, 200, 200, 50),
            "ishonch": round(random.uniform(0.75, 0.99), 2)
        })
        return natijalar

    if not _yuzlar_cache:
        yuzlarni_yuklash()

    try:
        # Kadrni kichraytirish (tezlik uchun)
        kichik = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb = cv2.cvtColor(kichik, cv2.COLOR_BGR2RGB)

        joylashuvlar = face_recognition.face_locations(rgb)
        kodlar = face_recognition.face_encodings(rgb, joylashuvlar)

        for kodlash, joy in zip(kodlar, joylashuvlar):
            ism = "Noma'lum"
            ishonch = 0.0

            if _yuzlar_cache:
                nomlar = list(_yuzlar_cache.keys())
                enc_list = list(_yuzlar_cache.values())
                masofalar = face_recognition.face_distance(enc_list, kodlash)
                min_idx = np.argmin(masofalar)

                if masofalar[min_idx] < 0.6:
                    ism = nomlar[min_idx]
                    ishonch = round(1 - masofalar[min_idx], 2)

            # Joylashuvni asl o'lchamga qaytarish
            yuqori, ong, quyi, chap = [v * 2 for v in joy]
            natijalar.append({
                "ism": ism,
                "yuz_id": ism.replace(" ", "_").lower(),
                "joylashuv": (yuqori, ong, quyi, chap),
                "ishonch": ishonch
            })

    except Exception as e:
        print(f"[Ishchi] Yuz tanishda xatolik: {e}")

    return natijalar


def ishchi_royxatga_olish(ism: str, rasm_yoli: str):
    """
    Yangi ishchini tizimga qo'shish
    Rasmni models/yuzlar/ ga ko'chiradi
    """
    try:
        import shutil
        maqsad = os.path.join(YUZLAR_PAPKA, f"{ism}.jpg")
        shutil.copy(rasm_yoli, maqsad)
        yuzlarni_yuklash()  # Keshni yangilash
        return True
    except Exception as e:
        print(f"[Ishchi] Ro'yxatga olishda xatolik: {e}")
        return False
