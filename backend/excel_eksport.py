"""
Excel Eksport Moduli
- Kunlik/haftalik/oylik hisobotlar
- Transport va ishchi ma'lumotlari
- Chiroyli formatlangan Excel fayl
"""

import os
from datetime import datetime, date, timedelta
from database import get_connection

try:
    import openpyxl
    from openpyxl.styles import (
        Font, PatternFill, Alignment, Border, Side
    )
    from openpyxl.utils import get_column_letter
    OPENPYXL_MAVJUD = True
except ImportError:
    OPENPYXL_MAVJUD = False
    print("[Excel] openpyxl topilmadi!")

EKSPORT_PAPKA = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EKSPORT_PAPKA, exist_ok=True)


# ─── Rang konstantalar ────────────────────────
SARLAVHA_RANG  = "1F2937"   # Qoʻngʻir-qora
KIRDI_RANG     = "064E3B"   # Toʻq yashil
CHIQDI_RANG    = "7F1D1D"   # Toʻq qizil
ISHCHI_RANG    = "1E3A5F"   # Toʻq ko'k
USTUN_RANG     = "374151"   # Kulrang
MATN_OQ        = "FFFFFF"
MATN_YASHIL    = "6EE7B7"
MATN_QIZIL     = "FCA5A5"
MATN_KO'K      = "93C5FD"


def _chegara():
    chiziq = Side(style='thin', color="4B5563")
    return Border(left=chiziq, right=chiziq, top=chiziq, bottom=chiziq)


def _sarlavha_uslub(font_size=11):
    return {
        "font":      Font(bold=True, color=MATN_OQ, size=font_size, name="Calibri"),
        "fill":      PatternFill("solid", fgColor=SARLAVHA_RANG),
        "alignment": Alignment(horizontal="center", vertical="center"),
        "border":    _chegara(),
    }


def _ustun_uslub(rang=USTUN_RANG):
    return {
        "font":      Font(bold=True, color=MATN_OQ, size=9, name="Calibri"),
        "fill":      PatternFill("solid", fgColor=rang),
        "alignment": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "border":    _chegara(),
    }


def _katak_uslub(qoʻy=False, rang=None):
    uslub = {
        "font":      Font(color=MATN_OQ, size=9, name="Calibri"),
        "alignment": Alignment(horizontal="left", vertical="center"),
        "border":    _chegara(),
    }
    if rang:
        uslub["fill"] = PatternFill("solid", fgColor=rang)
    elif qoʻy:
        uslub["fill"] = PatternFill("solid", fgColor="161B22")
    return uslub


def _uslub_qoʻllash(katak, **uslublar):
    for nom, qiy in uslublar.items():
        setattr(katak, nom, qiy)


def _ustunlar_kengaytir(ws, kengliklar: dict):
    for harf, kengl in kengliklar.items():
        ws.column_dimensions[harf].width = kengl


# ─────────────────────────────────────────────────────────────────
# TRANSPORT VARAQI
# ─────────────────────────────────────────────────────────────────
def _transport_varaqi(wb, boshlanish: str, tugash: str):
    ws = wb.create_sheet("🚛 Transport")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"

    conn = get_connection()
    qatorlar = conn.execute("""
        SELECT * FROM transport_log
        WHERE date(vaqt) BETWEEN ? AND ?
        ORDER BY vaqt DESC
    """, (boshlanish, tugash)).fetchall()
    conn.close()

    # ── Sarlavha ──────────────────────────────
    ws.merge_cells("A1:H1")
    katak = ws["A1"]
    katak.value = f"🚛  TRANSPORT HISOBOTI  |  {boshlanish}  →  {tugash}"
    _uslub_qoʻllash(katak, **_sarlavha_uslub(13))
    ws.row_dimensions[1].height = 32

    ws.merge_cells("A2:H2")
    katak = ws["A2"]
    katak.value = f"Jami yozuv: {len(qatorlar)}"
    _uslub_qoʻllash(katak,
        font=Font(color="9CA3AF", size=9, italic=True),
        fill=PatternFill("solid", fgColor="0D1117"),
        alignment=Alignment(horizontal="right"),
    )
    ws.row_dimensions[2].height = 16

    # ── Ustun sarlavhalar ─────────────────────
    ustunlar = ["#", "Vaqt", "Raqam", "Tur", "Rang", "Davlat", "Viloyat", "Harakat"]
    for col_idx, nom in enumerate(ustunlar, 1):
        katak = ws.cell(row=3, column=col_idx, value=nom)
        _uslub_qoʻllash(katak, **_ustun_uslub())
    ws.row_dimensions[3].height = 22

    # ── Ma'lumotlar ───────────────────────────
    for i, q in enumerate(qatorlar, 1):
        qator = i + 3
        juft = (i % 2 == 0)

        if q["harakat"] == "kirdi":
            h_rang = KIRDI_RANG
        elif q["harakat"] == "chiqdi":
            h_rang = CHIQDI_RANG
        else:
            h_rang = None

        qiymatlar = [
            i,
            q["vaqt"],
            q["raqam"],
            q["tur"],
            q["rang"],
            q["davlat"],
            q["viloyat"],
            (q["harakat"] or "").upper(),
        ]

        for col_idx, qiy in enumerate(qiymatlar, 1):
            katak = ws.cell(row=qator, column=col_idx, value=qiy)
            if col_idx == 8 and h_rang:
                _uslub_qoʻllash(katak, **_katak_uslub(rang=h_rang))
                katak.font = Font(bold=True, color=MATN_OQ, size=9)
            else:
                _uslub_qoʻllash(katak, **_katak_uslub(juft))
        ws.row_dimensions[qator].height = 18

    _ustunlar_kengaytir(ws, {
        "A": 5, "B": 18, "C": 14, "D": 10,
        "E": 10, "F": 14, "G": 18, "H": 10
    })

    # ── Xulosalar ────────────────────────────
    kirdi_son  = sum(1 for q in qatorlar if q["harakat"] == "kirdi")
    chiqdi_son = sum(1 for q in qatorlar if q["harakat"] == "chiqdi")
    fura_son   = sum(1 for q in qatorlar if q["tur"] == "Fura")
    yengil_son = sum(1 for q in qatorlar if q["tur"] == "Yengil")

    xulosa_qator = len(qatorlar) + 5
    ws.merge_cells(f"A{xulosa_qator}:H{xulosa_qator}")
    katak = ws.cell(row=xulosa_qator, value="📊  XULOSA")
    _uslub_qoʻllash(katak, **_sarlavha_uslub(10))

    xulosa = [
        ("Jami kirdi:", kirdi_son),
        ("Jami chiqdi:", chiqdi_son),
        ("Furalar:", fura_son),
        ("Yengil mashinalar:", yengil_son),
    ]
    for j, (nom, son) in enumerate(xulosa):
        r = xulosa_qator + 1 + j
        ws.cell(row=r, column=1, value=nom).font = Font(color="9CA3AF", size=9)
        ws.cell(row=r, column=2, value=son).font = Font(bold=True, color=MATN_OQ, size=10)

    return ws


# ─────────────────────────────────────────────────────────────────
# ISHCHILAR VARAQI
# ─────────────────────────────────────────────────────────────────
def _ishchilar_varaqi(wb, boshlanish: str, tugash: str):
    ws = wb.create_sheet("👷 Ishchilar")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"

    conn = get_connection()
    qatorlar = conn.execute("""
        SELECT * FROM ishchi_log
        WHERE date(vaqt) BETWEEN ? AND ?
        ORDER BY vaqt DESC
    """, (boshlanish, tugash)).fetchall()

    # Ishchi davomiylik statistikasi
    davomiylik = conn.execute("""
        SELECT ism, COUNT(*) as son, MIN(vaqt) as birinchi, MAX(vaqt) as oxirgi
        FROM ishchi_log
        WHERE date(vaqt) BETWEEN ? AND ?
        GROUP BY ism
        ORDER BY son DESC
    """, (boshlanish, tugash)).fetchall()
    conn.close()

    # ── Sarlavha ──────────────────────────────
    ws.merge_cells("A1:D1")
    katak = ws["A1"]
    katak.value = f"👷  ISHCHILAR HISOBOTI  |  {boshlanish}  →  {tugash}"
    _uslub_qoʻllash(katak, **_sarlavha_uslub(13))
    ws.row_dimensions[1].height = 32

    ws.merge_cells("A2:D2")
    katak = ws["A2"]
    katak.value = f"Jami qaydlar: {len(qatorlar)}"
    _uslub_qoʻllash(katak,
        font=Font(color="9CA3AF", size=9, italic=True),
        fill=PatternFill("solid", fgColor="0D1117"),
        alignment=Alignment(horizontal="right"),
    )

    # ── Ustunlar ──────────────────────────────
    ustunlar = ["#", "Vaqt", "Ism", "Harakat"]
    for col_idx, nom in enumerate(ustunlar, 1):
        katak = ws.cell(row=3, column=col_idx, value=nom)
        _uslub_qoʻllash(katak, **_ustun_uslub(ISHCHI_RANG))
    ws.row_dimensions[3].height = 22

    for i, q in enumerate(qatorlar, 1):
        qator = i + 3
        juft = (i % 2 == 0)
        for col_idx, qiy in enumerate([i, q["vaqt"], q["ism"], q["harakat"]], 1):
            katak = ws.cell(row=qator, column=col_idx, value=qiy)
            _uslub_qoʻllash(katak, **_katak_uslub(juft))
        ws.row_dimensions[qator].height = 18

    _ustunlar_kengaytir(ws, {"A": 5, "B": 18, "C": 22, "D": 12})

    # ── Davomiylik jadvali ────────────────────
    if davomiylik:
        bosh_q = len(qatorlar) + 6
        ws.merge_cells(f"A{bosh_q}:D{bosh_q}")
        katak = ws.cell(row=bosh_q, value="📋  ISHCHI DAVOMIYLIK JADVALI")
        _uslub_qoʻllash(katak, **_sarlavha_uslub(10))

        ustunlar2 = ["Ism", "Qaydlar soni", "Birinchi", "Oxirgi"]
        for ci, nom in enumerate(ustunlar2, 1):
            katak = ws.cell(row=bosh_q + 1, column=ci, value=nom)
            _uslub_qoʻllash(katak, **_ustun_uslub(ISHCHI_RANG))

        for j, d in enumerate(davomiylik):
            r = bosh_q + 2 + j
            for ci, qiy in enumerate([d["ism"], d["son"], d["birinchi"], d["oxirgi"]], 1):
                katak = ws.cell(row=r, column=ci, value=qiy)
                _uslub_qoʻllash(katak, **_katak_uslub(j % 2 == 0))

    return ws


# ─────────────────────────────────────────────────────────────────
# UMUMIY XULOSA VARAQI
# ─────────────────────────────────────────────────────────────────
def _xulosa_varaqi(wb, boshlanish: str, tugash: str):
    ws = wb.create_sheet("📊 Xulosa", 0)
    ws.sheet_view.showGridLines = False

    conn = get_connection()

    kirdi_son  = conn.execute("SELECT COUNT(*) FROM transport_log WHERE harakat='kirdi'  AND date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]
    chiqdi_son = conn.execute("SELECT COUNT(*) FROM transport_log WHERE harakat='chiqdi' AND date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]
    fura_son   = conn.execute("SELECT COUNT(*) FROM transport_log WHERE tur='Fura'                                        AND date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]
    yengil_son = conn.execute("SELECT COUNT(*) FROM transport_log WHERE tur='Yengil'                                      AND date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]
    ishchi_son = conn.execute("SELECT COUNT(DISTINCT ism) FROM ishchi_log                                                  WHERE date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]

    kunlik = conn.execute("""
        SELECT date(vaqt) as kun, harakat, COUNT(*) as son
        FROM transport_log WHERE date(vaqt) BETWEEN ? AND ?
        GROUP BY kun, harakat ORDER BY kun
    """, (boshlanish, tugash)).fetchall()
    conn.close()

    # ── Bosh sarlavha ─────────────────────────
    ws.merge_cells("A1:F1")
    katak = ws["A1"]
    katak.value = "⚙️  ZAVOD MONITORING  —  UMUMIY XULOSA"
    _uslub_qoʻllash(katak, **_sarlavha_uslub(15))
    ws.row_dimensions[1].height = 40

    ws.merge_cells("A2:F2")
    katak = ws["A2"]
    katak.value = f"Davr:  {boshlanish}  →  {tugash}   |   Hisobot yaratildi: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    _uslub_qoʻllash(katak,
        font=Font(color="6B7280", size=10, italic=True),
        fill=PatternFill("solid", fgColor="0D1117"),
        alignment=Alignment(horizontal="center"),
    )
    ws.row_dimensions[2].height = 20

    # ── Asosiy raqamlar ───────────────────────
    kartalar = [
        ("🚛  Jami Kirdi",       kirdi_son,  KIRDI_RANG,  MATN_YASHIL),
        ("🔄  Jami Chiqdi",      chiqdi_son, CHIQDI_RANG, MATN_QIZIL),
        ("🚚  Furalar",          fura_son,   "1C3D2B",    MATN_YASHIL),
        ("🚗  Yengil Mashinalar", yengil_son, "1C2B3D",    MATN_KO'K),
        ("👷  Ishchilar (unikal)", ishchi_son, ISHCHI_RANG, MATN_KO'K),
        ("📈  Jami Transport",   kirdi_son + chiqdi_son, SARLAVHA_RANG, MATN_OQ),
    ]

    for idx, (nom, son, bg, fg) in enumerate(kartalar):
        kol = idx + 1
        ws.column_dimensions[get_column_letter(kol)].width = 22

        ws.row_dimensions[4].height = 20
        ws.row_dimensions[5].height = 44
        ws.row_dimensions[6].height = 18

        katak = ws.cell(row=4, column=kol, value=nom)
        _uslub_qoʻllash(katak,
            font=Font(color="9CA3AF", size=8, bold=True),
            fill=PatternFill("solid", fgColor=bg),
            alignment=Alignment(horizontal="center", vertical="center"),
            border=_chegara(),
        )

        katak = ws.cell(row=5, column=kol, value=son)
        _uslub_qoʻllash(katak,
            font=Font(color=fg, size=28, bold=True, name="Calibri"),
            fill=PatternFill("solid", fgColor=bg),
            alignment=Alignment(horizontal="center", vertical="center"),
            border=_chegara(),
        )

    # ── Kunlik jadval ─────────────────────────
    ws.merge_cells("A8:F8")
    katak = ws.cell(row=8, value="📅  KUNLIK TRANSPORT HARAKATI")
    _uslub_qoʻllash(katak, **_sarlavha_uslub(11))
    ws.row_dimensions[8].height = 28

    ustunlar = ["Sana", "Kirdi", "Chiqdi", "Jami"]
    for ci, nom in enumerate(ustunlar, 1):
        katak = ws.cell(row=9, column=ci, value=nom)
        _uslub_qoʻllash(katak, **_ustun_uslub())

    # Kunlik ma'lumotlarni qayta ishlash
    kunlar = {}
    for q in kunlik:
        k = q["kun"]
        if k not in kunlar:
            kunlar[k] = {"kirdi": 0, "chiqdi": 0}
        kunlar[k][q["harakat"]] = q["son"]

    for j, (kun, h) in enumerate(sorted(kunlar.items())):
        r = 10 + j
        jami = h["kirdi"] + h["chiqdi"]
        for ci, qiy in enumerate([kun, h["kirdi"], h["chiqdi"], jami], 1):
            katak = ws.cell(row=r, column=ci, value=qiy)
            _uslub_qoʻllash(katak, **_katak_uslub(j % 2 == 0))
        ws.row_dimensions[r].height = 18

    return ws


# ─────────────────────────────────────────────────────────────────
# ASOSIY EKSPORT FUNKSIYA
# ─────────────────────────────────────────────────────────────────
def excel_yaratish(davr: str = "bugun") -> str:
    """
    Excel hisobot yaratish
    davr: 'bugun' | 'hafta' | 'oy' | 'hammasi'
    Qaytaradi: fayl yo'li
    """
    if not OPENPYXL_MAVJUD:
        raise ImportError("openpyxl o'rnatilmagan: pip install openpyxl")

    bugun = date.today()

    if davr == "bugun":
        boshlanish = tugash = str(bugun)
    elif davr == "hafta":
        boshlanish = str(bugun - timedelta(days=bugun.weekday()))
        tugash = str(bugun)
    elif davr == "oy":
        boshlanish = str(bugun.replace(day=1))
        tugash = str(bugun)
    else:  # hammasi
        boshlanish = "2000-01-01"
        tugash = str(bugun)

    wb = openpyxl.Workbook()
    # Default varaqni o'chirish
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    _xulosa_varaqi(wb, boshlanish, tugash)
    _transport_varaqi(wb, boshlanish, tugash)
    _ishchilar_varaqi(wb, boshlanish, tugash)

    vaqt = datetime.now().strftime("%Y%m%d_%H%M%S")
    fayl_nomi = f"zavod_hisobot_{davr}_{vaqt}.xlsx"
    yol = os.path.join(EKSPORT_PAPKA, fayl_nomi)
    wb.save(yol)
    print(f"[Excel] Hisobot saqlandi: {yol}")
    return yol
