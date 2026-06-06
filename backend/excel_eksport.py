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
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_MAVJUD = True
except ImportError:
    OPENPYXL_MAVJUD = False
    print("[Excel] openpyxl topilmadi!")

EKSPORT_PAPKA = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EKSPORT_PAPKA, exist_ok=True)

# Rang konstantalar
SARLAVHA_RANG = "1F2937"
KIRDI_RANG    = "064E3B"
CHIQDI_RANG   = "7F1D1D"
ISHCHI_RANG   = "1E3A5F"
USTUN_RANG    = "374151"
MATN_OQ       = "FFFFFF"
MATN_YASHIL   = "6EE7B7"
MATN_QIZIL    = "FCA5A5"
MATN_KOK      = "93C5FD"


def chegara():
    chiziq = Side(style="thin", color="4B5563")
    return Border(left=chiziq, right=chiziq, top=chiziq, bottom=chiziq)


def sarlavha_uslub(font_size=11):
    return {
        "font":      Font(bold=True, color=MATN_OQ, size=font_size, name="Calibri"),
        "fill":      PatternFill("solid", fgColor=SARLAVHA_RANG),
        "alignment": Alignment(horizontal="center", vertical="center"),
        "border":    chegara(),
    }


def ustun_uslub(rang=None):
    if rang is None:
        rang = USTUN_RANG
    return {
        "font":      Font(bold=True, color=MATN_OQ, size=9, name="Calibri"),
        "fill":      PatternFill("solid", fgColor=rang),
        "alignment": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "border":    chegara(),
    }


def katak_uslub(juft=False, rang=None):
    uslub = {
        "font":      Font(color=MATN_OQ, size=9, name="Calibri"),
        "alignment": Alignment(horizontal="left", vertical="center"),
        "border":    chegara(),
    }
    if rang:
        uslub["fill"] = PatternFill("solid", fgColor=rang)
    elif juft:
        uslub["fill"] = PatternFill("solid", fgColor="161B22")
    return uslub


def uslub_qollay(katak, **uslublar):
    for nom, qiy in uslublar.items():
        setattr(katak, nom, qiy)


def ustunlar_kengaytir(ws, kengliklar):
    for harf, kengl in kengliklar.items():
        ws.column_dimensions[harf].width = kengl


# ─────────────────────────────────────────────────────────────────
# TRANSPORT VARAQI
# ─────────────────────────────────────────────────────────────────
def transport_varaqi(wb, boshlanish, tugash):
    ws = wb.create_sheet("Transport")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"

    conn = get_connection()
    qatorlar = conn.execute("""
        SELECT * FROM transport_log
        WHERE date(vaqt) BETWEEN ? AND ?
        ORDER BY vaqt DESC
    """, (boshlanish, tugash)).fetchall()
    conn.close()

    # Sarlavha
    ws.merge_cells("A1:H1")
    k = ws["A1"]
    k.value = "TRANSPORT HISOBOTI  |  {} -> {}".format(boshlanish, tugash)
    uslub_qollay(k, **sarlavha_uslub(13))
    ws.row_dimensions[1].height = 32

    ws.merge_cells("A2:H2")
    k = ws["A2"]
    k.value = "Jami yozuv: {}".format(len(qatorlar))
    uslub_qollay(k,
        font=Font(color="9CA3AF", size=9, italic=True),
        fill=PatternFill("solid", fgColor="0D1117"),
        alignment=Alignment(horizontal="right"),
    )
    ws.row_dimensions[2].height = 16

    # Ustun sarlavhalar
    ustunlar = ["#", "Vaqt", "Raqam", "Tur", "Rang", "Davlat", "Viloyat", "Harakat"]
    for col_idx, nom in enumerate(ustunlar, 1):
        k = ws.cell(row=3, column=col_idx, value=nom)
        uslub_qollay(k, **ustun_uslub())
    ws.row_dimensions[3].height = 22

    # Ma'lumotlar
    for i, q in enumerate(qatorlar, 1):
        qator_num = i + 3
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
            k = ws.cell(row=qator_num, column=col_idx, value=qiy)
            if col_idx == 8 and h_rang:
                uslub_qollay(k, **katak_uslub(rang=h_rang))
                k.font = Font(bold=True, color=MATN_OQ, size=9)
            else:
                uslub_qollay(k, **katak_uslub(juft))
        ws.row_dimensions[qator_num].height = 18

    ustunlar_kengaytir(ws, {
        "A": 5, "B": 18, "C": 14, "D": 10,
        "E": 10, "F": 14, "G": 18, "H": 10
    })

    # Xulosa
    kirdi_son  = sum(1 for q in qatorlar if q["harakat"] == "kirdi")
    chiqdi_son = sum(1 for q in qatorlar if q["harakat"] == "chiqdi")
    fura_son   = sum(1 for q in qatorlar if q["tur"] == "Fura")
    yengil_son = sum(1 for q in qatorlar if q["tur"] == "Yengil")

    xulosa_qator = len(qatorlar) + 5
    ws.merge_cells("A{}:H{}".format(xulosa_qator, xulosa_qator))
    k = ws.cell(row=xulosa_qator, value="XULOSA")
    uslub_qollay(k, **sarlavha_uslub(10))

    xulosa = [
        ("Jami kirdi:", kirdi_son),
        ("Jami chiqdi:", chiqdi_son),
        ("Furalar:", fura_son),
        ("Yengil mashinalar:", yengil_son),
    ]
    for j, (nom, son) in enumerate(xulosa):
        r = xulosa_qator + 1 + j
        ws.cell(row=r, column=1, value=nom).font = Font(color="9CA3AF", size=9)
        ws.cell(row=r, column=2, value=son).font  = Font(bold=True, color=MATN_OQ, size=10)

    return ws


# ─────────────────────────────────────────────────────────────────
# ISHCHILAR VARAQI
# ─────────────────────────────────────────────────────────────────
def ishchilar_varaqi(wb, boshlanish, tugash):
    ws = wb.create_sheet("Ishchilar")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"

    conn = get_connection()
    qatorlar = conn.execute("""
        SELECT * FROM ishchi_log
        WHERE date(vaqt) BETWEEN ? AND ?
        ORDER BY vaqt DESC
    """, (boshlanish, tugash)).fetchall()

    davomiylik = conn.execute("""
        SELECT ism, COUNT(*) as son, MIN(vaqt) as birinchi, MAX(vaqt) as oxirgi
        FROM ishchi_log
        WHERE date(vaqt) BETWEEN ? AND ?
        GROUP BY ism
        ORDER BY son DESC
    """, (boshlanish, tugash)).fetchall()
    conn.close()

    # Sarlavha
    ws.merge_cells("A1:D1")
    k = ws["A1"]
    k.value = "ISHCHILAR HISOBOTI  |  {} -> {}".format(boshlanish, tugash)
    uslub_qollay(k, **sarlavha_uslub(13))
    ws.row_dimensions[1].height = 32

    ws.merge_cells("A2:D2")
    k = ws["A2"]
    k.value = "Jami qaydlar: {}".format(len(qatorlar))
    uslub_qollay(k,
        font=Font(color="9CA3AF", size=9, italic=True),
        fill=PatternFill("solid", fgColor="0D1117"),
        alignment=Alignment(horizontal="right"),
    )

    # Ustunlar
    for col_idx, nom in enumerate(["#", "Vaqt", "Ism", "Harakat"], 1):
        k = ws.cell(row=3, column=col_idx, value=nom)
        uslub_qollay(k, **ustun_uslub(ISHCHI_RANG))
    ws.row_dimensions[3].height = 22

    for i, q in enumerate(qatorlar, 1):
        qator_num = i + 3
        juft = (i % 2 == 0)
        for col_idx, qiy in enumerate([i, q["vaqt"], q["ism"], q["harakat"]], 1):
            k = ws.cell(row=qator_num, column=col_idx, value=qiy)
            uslub_qollay(k, **katak_uslub(juft))
        ws.row_dimensions[qator_num].height = 18

    ustunlar_kengaytir(ws, {"A": 5, "B": 18, "C": 22, "D": 12})

    # Davomiylik jadvali
    if davomiylik:
        bosh_q = len(qatorlar) + 6
        ws.merge_cells("A{}:D{}".format(bosh_q, bosh_q))
        k = ws.cell(row=bosh_q, value="ISHCHI DAVOMIYLIK JADVALI")
        uslub_qollay(k, **sarlavha_uslub(10))

        for ci, nom in enumerate(["Ism", "Qaydlar soni", "Birinchi", "Oxirgi"], 1):
            k = ws.cell(row=bosh_q + 1, column=ci, value=nom)
            uslub_qollay(k, **ustun_uslub(ISHCHI_RANG))

        for j, d in enumerate(davomiylik):
            r = bosh_q + 2 + j
            for ci, qiy in enumerate([d["ism"], d["son"], d["birinchi"], d["oxirgi"]], 1):
                k = ws.cell(row=r, column=ci, value=qiy)
                uslub_qollay(k, **katak_uslub(j % 2 == 0))

    return ws


# ─────────────────────────────────────────────────────────────────
# XULOSA VARAQI
# ─────────────────────────────────────────────────────────────────
def xulosa_varaqi(wb, boshlanish, tugash):
    ws = wb.create_sheet("Xulosa", 0)
    ws.sheet_view.showGridLines = False

    conn = get_connection()
    kirdi_son  = conn.execute("SELECT COUNT(*) FROM transport_log WHERE harakat='kirdi'  AND date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]
    chiqdi_son = conn.execute("SELECT COUNT(*) FROM transport_log WHERE harakat='chiqdi' AND date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]
    fura_son   = conn.execute("SELECT COUNT(*) FROM transport_log WHERE tur='Fura'   AND date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]
    yengil_son = conn.execute("SELECT COUNT(*) FROM transport_log WHERE tur='Yengil' AND date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]
    ishchi_son = conn.execute("SELECT COUNT(DISTINCT ism) FROM ishchi_log WHERE date(vaqt) BETWEEN ? AND ?", (boshlanish, tugash)).fetchone()[0]

    kunlik = conn.execute("""
        SELECT date(vaqt) as kun, harakat, COUNT(*) as son
        FROM transport_log WHERE date(vaqt) BETWEEN ? AND ?
        GROUP BY kun, harakat ORDER BY kun
    """, (boshlanish, tugash)).fetchall()
    conn.close()

    # Bosh sarlavha
    ws.merge_cells("A1:F1")
    k = ws["A1"]
    k.value = "ZAVOD MONITORING  -  UMUMIY XULOSA"
    uslub_qollay(k, **sarlavha_uslub(15))
    ws.row_dimensions[1].height = 40

    ws.merge_cells("A2:F2")
    k = ws["A2"]
    k.value = "Davr: {}  ->  {}   |   Hisobot: {}".format(
        boshlanish, tugash, datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    uslub_qollay(k,
        font=Font(color="6B7280", size=10, italic=True),
        fill=PatternFill("solid", fgColor="0D1117"),
        alignment=Alignment(horizontal="center"),
    )
    ws.row_dimensions[2].height = 20

    # Asosiy raqamlar
    kartalar = [
        ("Jami Kirdi",          kirdi_son,              KIRDI_RANG,    MATN_YASHIL),
        ("Jami Chiqdi",         chiqdi_son,             CHIQDI_RANG,   MATN_QIZIL),
        ("Furalar",             fura_son,               "1C3D2B",      MATN_YASHIL),
        ("Yengil Mashinalar",   yengil_son,             "1C2B3D",      MATN_KOK),
        ("Ishchilar (unikal)",  ishchi_son,             ISHCHI_RANG,   MATN_KOK),
        ("Jami Transport",      kirdi_son + chiqdi_son, SARLAVHA_RANG, MATN_OQ),
    ]

    for idx, (nom, son, bg, fg) in enumerate(kartalar):
        kol = idx + 1
        ws.column_dimensions[get_column_letter(kol)].width = 22
        ws.row_dimensions[4].height = 20
        ws.row_dimensions[5].height = 44

        k = ws.cell(row=4, column=kol, value=nom)
        uslub_qollay(k,
            font=Font(color="9CA3AF", size=8, bold=True),
            fill=PatternFill("solid", fgColor=bg),
            alignment=Alignment(horizontal="center", vertical="center"),
            border=chegara(),
        )
        k = ws.cell(row=5, column=kol, value=son)
        uslub_qollay(k,
            font=Font(color=fg, size=28, bold=True, name="Calibri"),
            fill=PatternFill("solid", fgColor=bg),
            alignment=Alignment(horizontal="center", vertical="center"),
            border=chegara(),
        )

    # Kunlik jadval
    ws.merge_cells("A8:F8")
    k = ws.cell(row=8, value="KUNLIK TRANSPORT HARAKATI")
    uslub_qollay(k, **sarlavha_uslub(11))
    ws.row_dimensions[8].height = 28

    for ci, nom in enumerate(["Sana", "Kirdi", "Chiqdi", "Jami"], 1):
        k = ws.cell(row=9, column=ci, value=nom)
        uslub_qollay(k, **ustun_uslub())

    kunlar = {}
    for q in kunlik:
        kk = q["kun"]
        if kk not in kunlar:
            kunlar[kk] = {"kirdi": 0, "chiqdi": 0}
        kunlar[kk][q["harakat"]] = q["son"]

    for j, (kun, h) in enumerate(sorted(kunlar.items())):
        r = 10 + j
        jami = h["kirdi"] + h["chiqdi"]
        for ci, qiy in enumerate([kun, h["kirdi"], h["chiqdi"], jami], 1):
            k = ws.cell(row=r, column=ci, value=qiy)
            uslub_qollay(k, **katak_uslub(j % 2 == 0))
        ws.row_dimensions[r].height = 18

    return ws


# ─────────────────────────────────────────────────────────────────
# ASOSIY FUNKSIYA
# ─────────────────────────────────────────────────────────────────
def excel_yaratish(davr="bugun"):
    """
    Excel hisobot yaratish
    davr: bugun | hafta | oy | hammasi
    """
    if not OPENPYXL_MAVJUD:
        raise ImportError("openpyxl topilmadi. Terminlada: pip install openpyxl")

    bugun = date.today()

    if davr == "bugun":
        boshlanish = tugash = str(bugun)
    elif davr == "hafta":
        boshlanish = str(bugun - timedelta(days=bugun.weekday()))
        tugash = str(bugun)
    elif davr == "oy":
        boshlanish = str(bugun.replace(day=1))
        tugash = str(bugun)
    else:
        boshlanish = "2000-01-01"
        tugash = str(bugun)

    wb = openpyxl.Workbook()
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    xulosa_varaqi(wb, boshlanish, tugash)
    transport_varaqi(wb, boshlanish, tugash)
    ishchilar_varaqi(wb, boshlanish, tugash)

    vaqt = datetime.now().strftime("%Y%m%d_%H%M%S")
    fayl_nomi = "zavod_hisobot_{}_{}.xlsx".format(davr, vaqt)
    yol = os.path.join(EKSPORT_PAPKA, fayl_nomi)
    wb.save(yol)
    print("[Excel] Hisobot saqlandi: {}".format(yol))
    return yol
