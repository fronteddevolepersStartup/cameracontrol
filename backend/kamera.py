"""
Kamera Moduli
- Kompyuter kamerasi (webcam) yoki IP kamerani boshqarish
- Real-time kadrlarni qayta ishlash
- WebSocket orqali frontend ga yuborish
"""

import cv2
import base64
import threading
import time
import numpy as np
from datetime import datetime

from database import (
    transport_qoshish, ishchi_qoshish,
    transport_royxat, ishchi_royxat, init_db
)
from modules.transport import transport_qayta_ishlash
from modules.ishchi import yuz_tanish, yuzlarni_yuklash


class KameraManager:
    def __init__(self, kamera_id=0):
        self.kamera_id = kamera_id          # 0 = kompyuter kamerasi
        self.cap = None
        self.ishlayapti = False
        self.joriy_kadr = None              # Oxirgi kadr
        self.lock = threading.Lock()

        # Sozlamalar
        self.transport_rejim = True         # Transport aniqlash yoqilgan/o'chirilgan
        self.ishchi_rejim = True            # Ishchi nazorat yoqilgan/o'chirilgan
        self.qayta_ishlash_oraliq = 3       # Har necha sekundda bir qayta ishlash

        # So'nggi qayta ishlangan vaqt
        self._oxirgi_transport = 0
        self._oxirgi_ishchi = 0

    def boshlash(self):
        """Kamerani ishga tushirish - Windows/Linux/Mac uchun universal"""
        import platform

        # Windows da DirectShow orqali ochish tezroq
        if platform.system() == "Windows":
            self.cap = cv2.VideoCapture(self.kamera_id, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.kamera_id)

        if not self.cap.isOpened():
            print(f"[Kamera] Kamera {self.kamera_id} ochilmadi, boshqa indeks sinab ko'rilmoqda...")
            # Boshqa indekslarni sinash: 0, 1, 2
            for idx in [0, 1, 2]:
                if idx == self.kamera_id:
                    continue
                if platform.system() == "Windows":
                    test = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                else:
                    test = cv2.VideoCapture(idx)
                if test.isOpened():
                    ret, _ = test.read()
                    if ret:
                        self.cap = test
                        self.kamera_id = idx
                        print(f"[Kamera] Kamera {idx} topildi ✓")
                        break
                    test.release()

        if not self.cap.isOpened():
            print("[Kamera] Hech qanday kamera topilmadi!")
            return False

        # Kadr o'lchami
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Birinchi kadrni sinash
        ret, test_kadr = self.cap.read()
        if not ret or test_kadr is None:
            print("[Kamera] Kadr olib bo'lmadi!")
            self.cap.release()
            return False

        self.joriy_kadr = test_kadr
        self.ishlayapti = True
        self._ip = threading.Thread(target=self._kadr_olish_loop, daemon=True)
        self._ip.start()

        if self.ishchi_rejim:
            yuzlarni_yuklash()

        h, w = test_kadr.shape[:2]
        print(f"[Kamera] Kamera {self.kamera_id} ishga tushdi ✓  ({w}x{h})")
        return True

    def toxtatish(self):
        """Kamerani to'xtatish"""
        self.ishlayapti = False
        if self.cap:
            self.cap.release()
        print("[Kamera] To'xtatildi.")

    def _kadr_olish_loop(self):
        """Fon ipida kadrlarni olish"""
        while self.ishlayapti:
            ret, kadr = self.cap.read()
            if ret:
                with self.lock:
                    self.joriy_kadr = kadr.copy()
            time.sleep(0.033)  # ~30 FPS

    def kadr_base64(self):
        """Frontend uchun kadrni base64 ga aylantirish"""
        with self.lock:
            if self.joriy_kadr is None:
                # Demo kadr - qora fon, matn bilan
                demo = np.zeros((480, 640, 3), dtype=np.uint8)
                vaqt = datetime.now().strftime("%H:%M:%S")
                cv2.putText(demo, "KAMERA ULANMAGAN", (120, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 100, 255), 2)
                cv2.putText(demo, vaqt, (260, 260),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
                cv2.putText(demo, "Kamerani tekshiring", (160, 320),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 1)
                _, buf = cv2.imencode('.jpg', demo)
                return base64.b64encode(buf).decode('utf-8')
            kadr = self.joriy_kadr.copy()

        kadr = self._overlay_chizish(kadr)
        _, buf = cv2.imencode('.jpg', kadr, [cv2.IMWRITE_JPEG_QUALITY, 75])
        return base64.b64encode(buf).decode('utf-8')

    def _overlay_chizish(self, kadr: np.ndarray) -> np.ndarray:
        """Kadrga ma'lumot yozish (vaqt, holat)"""
        vaqt = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        cv2.putText(kadr, vaqt, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        holat = "MONITORING FAOL"
        cv2.putText(kadr, holat, (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

        # Ko'rsatkich chiziq (zonani belgilash)
        h, w = kadr.shape[:2]
        cv2.line(kadr, (0, h//2), (w, h//2), (255, 255, 0), 1)

        return kadr

    def transport_skan(self, harakat: str = "kirdi") -> dict | None:
        """
        Hozirgi kadrdan transport ma'lumotlarini olish va saqlash
        harakat: 'kirdi' yoki 'chiqdi'
        """
        with self.lock:
            if self.joriy_kadr is None:
                return None
            kadr = self.joriy_kadr.copy()

        natija = transport_qayta_ishlash(kadr, harakat)

        # Bazaga saqlash
        transport_qoshish(
            raqam=natija["raqam"],
            tur=natija["tur"],
            rang=natija["rang"],
            davlat=natija["davlat"],
            viloyat=natija["viloyat"],
            harakat=harakat,
            rasm_yol=natija["rasm_yol"]
        )

        print(f"[Transport] {harakat.upper()}: {natija['tur']} | "
              f"{natija['raqam']} | {natija['rang']} | "
              f"{natija['davlat']}/{natija['viloyat']}")
        return natija

    def ishchi_skan(self) -> list:
        """Hozirgi kadrdan ishchilarni aniqlash"""
        with self.lock:
            if self.joriy_kadr is None:
                return []
            kadr = self.joriy_kadr.copy()

        natijalar = yuz_tanish(kadr)

        for n in natijalar:
            ishchi_qoshish(
                ism=n["ism"],
                yuz_id=n["yuz_id"],
                harakat="aniqlandi"
            )
            print(f"[Ishchi] Aniqlandi: {n['ism']} ({n['ishonch']*100:.0f}%)")

        return natijalar

    def avtomatik_rejim(self):
        """
        Avtomatik qayta ishlash - har N sekundda bir tekshiradi
        Haqiqiy tizimda harakat sensori yoki darvoza sensori bilan ishlatiladi
        """
        hozir = time.time()

        if self.transport_rejim:
            if hozir - self._oxirgi_transport >= self.qayta_ishlash_oraliq:
                self._oxirgi_transport = hozir
                # Avtomatik rejimda 'kirdi' - real tizimda sensor aniqlaydi
                # self.transport_skan("kirdi")

        if self.ishchi_rejim:
            if hozir - self._oxirgi_ishchi >= self.qayta_ishlash_oraliq:
                self._oxirgi_ishchi = hozir
                # self.ishchi_skan()


# Global kamera instance
kamera = KameraManager(kamera_id=0)
