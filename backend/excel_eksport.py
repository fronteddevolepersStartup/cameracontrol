"""
Excel Eksport Moduli - Chiroyli dizayn + Rasmlar
"""

import os
from datetime import datetime, date, timedelta
from database import get_connection

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.drawing.image import Image as XLImage
    OPENPYXL_MAVJUD = True
except ImportError:
    OPENPYXL_MAVJUD = False

EKSPORT_PAPKA = os.path.join(os.path.dirname(__file__), "exports")
RASM_PAPKA   = os.path.join(os.path.dirname(__file__), "data", "rasmlar")
os.makedirs(EKSPORT_PAPKA, exist_ok=True)

# ── Ranglar ──────────────────────────────────────────
R_SARLAVHA  = "0F172A"   # Qoraga yaqin ko'k
R_USTUN     = "1E293B"   # To'q ko'k-kulrang
R_KIRDI     = "14532D"   # To'q yashil
R_CHIQDI    = "7F1D1D"   # To'q qizil
R_ISHCHI    = "1E3A5F"   # To'q ko'k
R_JUFT      = "1A2233"   # Juft qator
R_TOQ       = "0F172A"   # Toq qator
OQ          = "FFFFFF"
YASHIL_M    = "86EFAC"
QIZIL_M     = "FCA5A5"
KOK_M       = "93C5FD"
SARIQ_M     = "FDE68A"


def chiziq():
    c = Side(style="thin", color="334155")
    return Border(left=c, right=c, top=c, bottom=c)


def qalin_chiziq():
    c = Side(style="medium", color="475569")
    return Border(left=c, right=c, top=c, bottom=c)


def stil(font_color=OQ, font_size=10, bold=False, bg=None,
         h_align="left", v_align="center", wrap=False, border=True):
    s = {}
    s["font"] = Font(color=font_color, size=font_size, bold=bold, name="Calibri")
    if bg:
        s["fill"] = PatternFill("solid", fgColor=bg)
    s["alignment"] = Alignment(
        horizontal=h_align, vertical=v_align,
        wrap_text=wrap
    )
    if border:
        s["border"] = chiziq()
    return s


def qollay(katak, **s):
    for k, v in s.items():
        setattr(katak, k, v)


# ─────────────────────────────────────────────────────────
# TRANSPORT VARAQI (Rasmli)
# ─────────────────────────────────────────────────────────
def transport_varaqi(wb, bosh, tug):
    # Rasmlar bo'lsa ustunlar keng bo'ladi
    ws = wb.create_sheet("Transport Jurnali")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A5"
    ws.sheet_properties.tabColor = "14532D"

    conn = get_connection()
    qatorlar = conn.execute("""
        SELECT * FROM transport_log
        WHERE date(vaqt) BETWEEN ? AND ?
        ORDER BY vaqt DESC
    """, (bosh, tug)).fetchall()
    conn.close()

    # ── Sarlavha (1-2 qator) ─────────────────
    ws.row_dimensions[1].height = 36
    ws.row_dimensions[2].height = 20
    ws.row_dimensions[3].height = 8
    ws.row_dimensions[4].height = 26

    ws.merge_cells("A1:I1")
    k = ws["A1"]
    k.value = "  ZAVOD MONITORING  —  TRANSPORT JURNALI"
    qollay(k,
        font=Font(color=OQ, size=16, bold=True, name="Calibri"),
        fill=PatternFill("solid", fgColor=R_SARLAVHA),
        alignment=Alignment(horizontal="left", vertical="center"),
        border=Border(),
    )

    ws.merge_cells("A2:I2")
    k = ws["A2"]
    k.value = "  Davr: {}  →  {}        Hisobot: {}        Jami: {} ta yozuv".format(
        bosh, tug, datetime.now().strftime("%d.%m.%Y %H:%M"), len(qatorlar)
    )
    qollay(k,
        font=Font(color="94A3B8", size=9, italic=True, name="Calibri"),
        fill=PatternFill("solid", fgColor="0A0F1A"),
        alignment=Alignment(horizontal="left", vertical="center"),
        border=Border(),
    )

    # Bo'sh ajratgich
    ws.merge_cells("A3:I3")
    ws["A3"].fill = PatternFill("solid", fgColor="1E3A5F")

    # ── Ustun sarlavhalar (4-qator) ───────────
    ustunlar = [
        ("#",        4,  "center"),
        ("Vaqt",    18,  "center"),
        ("Raqam",   14,  "center"),
        ("Tur",     10,  "center"),
        ("Rang",    10,  "center"),
        ("Davlat",  14,  "center"),
        ("Viloyat", 18,  "center"),
        ("Harakat", 11,  "center"),
        ("Rasm",    18,  "center"),
    ]
    for col_i, (nom, kengl, align) in enumerate(ustunlar, 1):
        ws.column_dimensions[get_column_letter(col_i)].width = kengl
        k = ws.cell(row=4, column=col_i, value=nom)
        qollay(k,
            font=Font(color=SARIQ_M, size=9, bold=True, name="Calibri"),
            fill=PatternFill("solid", fgColor=R_USTUN),
            alignment=Alignment(horizontal=align, vertical="center"),
            border=qalin_chiziq(),
        )

    # ── Ma'lumotlar ───────────────────────────
    for i, q in enumerate(qatorlar, 1):
        qator_num = i + 4
        juft = (i % 2 == 0)
        bg = R_JUFT if juft else R_TOQ
        ws.row_dimensions[qator_num].height = 56  # Rasm uchun baland

        harakat = (q["harakat"] or "").lower()
        if harakat == "kirdi":
            h_bg   = R_KIRDI
            h_rang = YASHIL_M
            h_matn = "▶  KIRDI"
        elif harakat == "chiqdi":
            h_bg   = R_CHIQDI
            h_rang = QIZIL_M
            h_matn = "◀  CHIQDI"
        else:
            h_bg   = R_USTUN
            h_rang = OQ
            h_matn = harakat.upper()

        qiymatlar = [
            (i,              bg,   OQ,      "center"),
            (q["vaqt"],      bg,   "CBD5E1", "center"),
            (q["raqam"],     bg,   OQ,      "center"),
            (q["tur"],       bg,   KOK_M,   "center"),
            (q["rang"],      bg,   OQ,      "center"),
            (q["davlat"],    bg,   OQ,      "left"),
            (q["viloyat"],   bg,   OQ,      "left"),
            (h_matn,         h_bg, h_rang,  "center"),
        ]

        for col_i, (qiy, bg_c, fg_c, align) in enumerate(qiymatlar, 1):
            k = ws.cell(row=qator_num, column=col_i, value=qiy)
            qollay(k,
                font=Font(
                    color=fg_c, size=9,
                    bold=(col_i in (3, 8)),
                    name="Calibri"
                ),
                fill=PatternFill("solid", fgColor=bg_c),
                alignment=Alignment(horizontal=align, vertical="center"),
                border=chiziq(),
            )

        # ── Rasm qo'shish ──────────────────────
        rasm_yol = q["rasm_yol"] if q["rasm_yol"] else ""
        if rasm_yol and os.path.exists(rasm_yol):
            try:
                img = XLImage(rasm_yol)
                img.width  = 90
                img.height = 50
                hujayra = "{}{}".format(get_column_letter(9), qator_num)
                ws.add_image(img, hujayra)
                # Bo'sh katak
                k = ws.cell(row=qator_num, column=9, value="")
                qollay(k,
                    fill=PatternFill("solid", fgColor=bg),
                    border=chiziq(),
                )
            except Exception:
                k = ws.cell(row=qator_num, column=9, value="Rasm xato")
                qollay(k, **stil(font_color="94A3B8", bg=bg, h_align="center"))
        else:
            k = ws.cell(row=qator_num, column=9, value="—")
            qollay(k, **stil(font_color="475569", bg=bg, h_align="center"))

    # ── Xulosa ────────────────────────────────
    kirdi_son  = sum(1 for q in qatorlar if q["harakat"] == "kirdi")
    chiqdi_son = sum(1 for q in qatorlar if q["harakat"] == "chiqdi")
    fura_son   = sum(1 for q in qatorlar if q["tur"] == "Fura")
    yengil_son = sum(1 for q in qatorlar if q["tur"] == "Yengil")

    bosh_xulosa = len(qatorlar) + 6
    ws.merge_cells("A{}:I{}".format(bosh_xulosa, bosh_xulosa))
    k = ws.cell(row=bosh_xulosa, column=1, value="  XULOSA")
    qollay(k,
        font=Font(color=SARIQ_M, size=10, bold=True),
        fill=PatternFill("solid", fgColor=R_USTUN),
        alignment=Alignment(horizontal="left", vertical="center"),
        border=qalin_chiziq(),
    )
    ws.row_dimensions[bosh_xulosa].height = 22

    xulosa_data = [
        ("Jami kirdi", kirdi_son, YASHIL_M),
        ("Jami chiqdi", chiqdi_son, QIZIL_M),
        ("Furalar", fura_son, KOK_M),
        ("Yengil mashinalar", yengil_son, SARIQ_M),
    ]
    for j, (nom, son, rang) in enumerate(xulosa_data):
        r = bosh_xulosa + 1 + j
        ws.row_dimensions[r].height = 20
        k = ws.cell(row=r, column=1, value="  " + nom)
        qollay(k, font=Font(color="94A3B8", size=9, name="Calibri"),
               fill=PatternFill("solid", fgColor=R_TOQ),
               alignment=Alignment(horizontal="left", vertical="center"),
               border=chiziq())
        k = ws.cell(row=r, column=2, value=son)
        qollay(k, font=Font(color=rang, size=11, bold=True, name="Calibri"),
               fill=PatternFill("solid", fgColor=R_TOQ),
               alignment=Alignment(horizontal="center", vertical="center"),
               border=chiziq())

    return ws


# ─────────────────────────────────────────────────────────
# ISHCHILAR VARAQI
# ─────────────────────────────────────────────────────────
def ishchilar_varaqi(wb, bosh, tug):
    ws = wb.create_sheet("Ishchilar Jurnali")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A5"
    ws.sheet_properties.tabColor = "1E3A5F"

    conn = get_connection()
    qatorlar = conn.execute("""
        SELECT * FROM ishchi_log WHERE date(vaqt) BETWEEN ? AND ?
        ORDER BY vaqt DESC
    """, (bosh, tug)).fetchall()
    davomiylik = conn.execute("""
        SELECT ism, COUNT(*) as son, MIN(vaqt) as birinchi, MAX(vaqt) as oxirgi
        FROM ishchi_log WHERE date(vaqt) BETWEEN ? AND ?
        GROUP BY ism ORDER BY son DESC
    """, (bosh, tug)).fetchall()
    conn.close()

    ws.row_dimensions[1].height = 36
    ws.row_dimensions[2].height = 20
    ws.row_dimensions[3].height = 8
    ws.row_dimensions[4].height = 26

    ws.merge_cells("A1:E1")
    k = ws["A1"]
    k.value = "  ZAVOD MONITORING  —  ISHCHILAR JURNALI"
    qollay(k,
        font=Font(color=OQ, size=16, bold=True, name="Calibri"),
        fill=PatternFill("solid", fgColor=R_SARLAVHA),
        alignment=Alignment(horizontal="left", vertical="center"),
        border=Border(),
    )

    ws.merge_cells("A2:E2")
    k = ws["A2"]
    k.value = "  Davr: {}  →  {}        Jami: {} ta qayd".format(bosh, tug, len(qatorlar))
    qollay(k,
        font=Font(color="94A3B8", size=9, italic=True),
        fill=PatternFill("solid", fgColor="0A0F1A"),
        alignment=Alignment(horizontal="left", vertical="center"),
        border=Border(),
    )

    ws.merge_cells("A3:E3")
    ws["A3"].fill = PatternFill("solid", fgColor=R_ISHCHI)

    ustunlar = [("#", 5), ("Vaqt", 20), ("Ism", 25), ("Harakat", 14), ("ID", 20)]
    for col_i, (nom, kengl) in enumerate(ustunlar, 1):
        ws.column_dimensions[get_column_letter(col_i)].width = kengl
        k = ws.cell(row=4, column=col_i, value=nom)
        qollay(k,
            font=Font(color=SARIQ_M, size=9, bold=True, name="Calibri"),
            fill=PatternFill("solid", fgColor=R_USTUN),
            alignment=Alignment(horizontal="center", vertical="center"),
            border=qalin_chiziq(),
        )

    for i, q in enumerate(qatorlar, 1):
        qator_num = i + 4
        juft = (i % 2 == 0)
        bg = R_JUFT if juft else R_TOQ
        ws.row_dimensions[qator_num].height = 20

        for col_i, qiy in enumerate([i, q["vaqt"], q["ism"], q["harakat"], q["yuz_id"]], 1):
            k = ws.cell(row=qator_num, column=col_i, value=qiy)
            qollay(k,
                font=Font(color=OQ, size=9, bold=(col_i == 3), name="Calibri"),
                fill=PatternFill("solid", fgColor=bg),
                alignment=Alignment(horizontal="center" if col_i in (1,2,4) else "left",
                                    vertical="center"),
                border=chiziq(),
            )

    # Davomiylik jadvali
    if davomiylik:
        bosh_d = len(qatorlar) + 6
        ws.merge_cells("A{}:E{}".format(bosh_d, bosh_d))
        k = ws.cell(row=bosh_d, column=1, value="  ISHCHI DAVOMIYLIK JADVALI")
        qollay(k,
            font=Font(color=SARIQ_M, size=10, bold=True),
            fill=PatternFill("solid", fgColor=R_USTUN),
            alignment=Alignment(horizontal="left", vertical="center"),
            border=qalin_chiziq(),
        )
        ws.row_dimensions[bosh_d].height = 22

        for col_i, nom in enumerate(["Ism", "Qaydlar", "Birinchi", "Oxirgi", ""], 1):
            k = ws.cell(row=bosh_d + 1, column=col_i, value=nom)
            qollay(k,
                font=Font(color=KOK_M, size=9, bold=True),
                fill=PatternFill("solid", fgColor=R_USTUN),
                alignment=Alignment(horizontal="center", vertical="center"),
                border=chiziq(),
            )
        ws.row_dimensions[bosh_d + 1].height = 20

        for j, d in enumerate(davomiylik):
            r = bosh_d + 2 + j
            bg = R_JUFT if j % 2 == 0 else R_TOQ
            ws.row_dimensions[r].height = 20
            for col_i, qiy in enumerate([d["ism"], d["son"], d["birinchi"], d["oxirgi"], ""], 1):
                k = ws.cell(row=r, column=col_i, value=qiy)
                qollay(k,
                    font=Font(color=OQ, size=9, bold=(col_i == 2), name="Calibri"),
                    fill=PatternFill("solid", fgColor=bg),
                    alignment=Alignment(horizontal="center" if col_i == 2 else "left",
                                        vertical="center"),
                    border=chiziq(),
                )

    return ws


# ─────────────────────────────────────────────────────────
# XULOSA VARAQI
# ─────────────────────────────────────────────────────────
def xulosa_varaqi(wb, bosh, tug):
    ws = wb.create_sheet("Umumiy Xulosa", 0)
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = "F59E0B"

    conn = get_connection()
    kirdi_son  = conn.execute("SELECT COUNT(*) FROM transport_log WHERE harakat='kirdi'  AND date(vaqt) BETWEEN ? AND ?", (bosh, tug)).fetchone()[0]
    chiqdi_son = conn.execute("SELECT COUNT(*) FROM transport_log WHERE harakat='chiqdi' AND date(vaqt) BETWEEN ? AND ?", (bosh, tug)).fetchone()[0]
    fura_son   = conn.execute("SELECT COUNT(*) FROM transport_log WHERE tur='Fura'   AND date(vaqt) BETWEEN ? AND ?", (bosh, tug)).fetchone()[0]
    yengil_son = conn.execute("SELECT COUNT(*) FROM transport_log WHERE tur='Yengil' AND date(vaqt) BETWEEN ? AND ?", (bosh, tug)).fetchone()[0]
    ishchi_son = conn.execute("SELECT COUNT(DISTINCT ism) FROM ishchi_log WHERE date(vaqt) BETWEEN ? AND ?", (bosh, tug)).fetchone()[0]
    kunlik = conn.execute("""
        SELECT date(vaqt) as kun, harakat, COUNT(*) as son
        FROM transport_log WHERE date(vaqt) BETWEEN ? AND ?
        GROUP BY kun, harakat ORDER BY kun
    """, (bosh, tug)).fetchall()
    conn.close()

    # Ustun kengliklari
    for col_i, kengl in enumerate([6, 22, 18, 18, 18, 18], 1):
        ws.column_dimensions[get_column_letter(col_i)].width = kengl

    # ── Katta sarlavha ────────────────────────
    ws.row_dimensions[1].height = 50
    ws.merge_cells("A1:F1")
    k = ws["A1"]
    k.value = "ZAVOD MONITORING TIZIMI"
    qollay(k,
        font=Font(color=OQ, size=22, bold=True, name="Calibri"),
        fill=PatternFill("solid", fgColor=R_SARLAVHA),
        alignment=Alignment(horizontal="center", vertical="center"),
        border=Border(),
    )

    ws.row_dimensions[2].height = 22
    ws.merge_cells("A2:F2")
    k = ws["A2"]
    k.value = "Davr: {}  →  {}          Hisobot sanasi: {}".format(
        bosh, tug, datetime.now().strftime("%d.%m.%Y  %H:%M")
    )
    qollay(k,
        font=Font(color="64748B", size=10, italic=True, name="Calibri"),
        fill=PatternFill("solid", fgColor="060D1A"),
        alignment=Alignment(horizontal="center", vertical="center"),
        border=Border(),
    )

    ws.row_dimensions[3].height = 10
    ws.merge_cells("A3:F3")
    ws["A3"].fill = PatternFill("solid", fgColor="1E3A5F")

    # ── Statistika kartalar ───────────────────
    kartalar = [
        ("KIRDI",             kirdi_son,              R_KIRDI,   YASHIL_M, "▶"),
        ("CHIQDI",            chiqdi_son,             R_CHIQDI,  QIZIL_M,  "◀"),
        ("FURALAR",           fura_son,               "1C3D2B",  YASHIL_M, "🚛"),
        ("YENGIL",            yengil_son,             "1C2B3D",  KOK_M,    "🚗"),
        ("ISHCHILAR",         ishchi_son,             R_ISHCHI,  KOK_M,    "👷"),
        ("JAMI",              kirdi_son + chiqdi_son, R_USTUN,   SARIQ_M,  "📊"),
    ]

    ws.row_dimensions[4].height = 18
    ws.row_dimensions[5].height = 50
    ws.row_dimensions[6].height = 22
    ws.row_dimensions[7].height = 10

    for idx, (nom, son, bg, fg, icon) in enumerate(kartalar):
        kol = idx + 1
        ws.column_dimensions[get_column_letter(kol)].width = 18

        # Sarlavha
        k = ws.cell(row=4, column=kol, value="{} {}".format(icon, nom))
        qollay(k,
            font=Font(color="94A3B8", size=8, bold=True, name="Calibri"),
            fill=PatternFill("solid", fgColor=bg),
            alignment=Alignment(horizontal="center", vertical="center"),
            border=Border(top=Side(style="medium", color="334155"),
                         left=Side(style="medium", color="334155"),
                         right=Side(style="medium", color="334155")),
        )

        # Son
        k = ws.cell(row=5, column=kol, value=son)
        qollay(k,
            font=Font(color=fg, size=32, bold=True, name="Calibri"),
            fill=PatternFill("solid", fgColor=bg),
            alignment=Alignment(horizontal="center", vertical="center"),
            border=Border(left=Side(style="medium", color="334155"),
                         right=Side(style="medium", color="334155")),
        )

        # Ta
        k = ws.cell(row=6, column=kol, value="ta")
        qollay(k,
            font=Font(color="475569", size=9, name="Calibri"),
            fill=PatternFill("solid", fgColor=bg),
            alignment=Alignment(horizontal="center", vertical="center"),
            border=Border(bottom=Side(style="medium", color="334155"),
                         left=Side(style="medium", color="334155"),
                         right=Side(style="medium", color="334155")),
        )

    # Ajratgich
    ws.merge_cells("A7:F7")
    ws["A7"].fill = PatternFill("solid", fgColor="0A0F1A")

    # ── Kunlik jadval ─────────────────────────
    ws.row_dimensions[8].height = 26
    ws.merge_cells("A8:F8")
    k = ws.cell(row=8, column=1, value="  KUNLIK TRANSPORT HARAKATI")
    qollay(k,
        font=Font(color=SARIQ_M, size=11, bold=True, name="Calibri"),
        fill=PatternFill("solid", fgColor=R_USTUN),
        alignment=Alignment(horizontal="left", vertical="center"),
        border=qalin_chiziq(),
    )

    ws.row_dimensions[9].height = 22
    for col_i, (nom, align) in enumerate(
        [("Sana", "center"), ("Kirdi", "center"), ("Chiqdi", "center"),
         ("Jami", "center"), ("Kirdi %", "center"), ("Chiqdi %", "center")], 1
    ):
        k = ws.cell(row=9, column=col_i, value=nom)
        qollay(k,
            font=Font(color=KOK_M, size=9, bold=True, name="Calibri"),
            fill=PatternFill("solid", fgColor=R_USTUN),
            alignment=Alignment(horizontal=align, vertical="center"),
            border=chiziq(),
        )

    # Kunlik ma'lumotlar
    kunlar = {}
    for q in kunlik:
        kk = q["kun"]
        if kk not in kunlar:
            kunlar[kk] = {"kirdi": 0, "chiqdi": 0}
        kunlar[kk][q["harakat"]] = q["son"]

    for j, (kun, h) in enumerate(sorted(kunlar.items())):
        r = 10 + j
        ws.row_dimensions[r].height = 20
        juft = (j % 2 == 0)
        bg = R_JUFT if juft else R_TOQ
        jami = h["kirdi"] + h["chiqdi"]
        kirdi_prc  = "{}%".format(round(h["kirdi"]  / jami * 100) if jami else 0)
        chiqdi_prc = "{}%".format(round(h["chiqdi"] / jami * 100) if jami else 0)

        for col_i, (qiy, fg) in enumerate([
            (kun,         "CBD5E1"),
            (h["kirdi"],  YASHIL_M),
            (h["chiqdi"], QIZIL_M),
            (jami,        SARIQ_M),
            (kirdi_prc,   YASHIL_M),
            (chiqdi_prc,  QIZIL_M),
        ], 1):
            k = ws.cell(row=r, column=col_i, value=qiy)
            qollay(k,
                font=Font(color=fg, size=9, bold=(col_i == 4), name="Calibri"),
                fill=PatternFill("solid", fgColor=bg),
                alignment=Alignment(horizontal="center", vertical="center"),
                border=chiziq(),
            )

    return ws


# ─────────────────────────────────────────────────────────
# ASOSIY FUNKSIYA
# ─────────────────────────────────────────────────────────
def excel_yaratish(davr="bugun"):
    if not OPENPYXL_MAVJUD:
        raise ImportError("openpyxl topilmadi. Terminal: pip install openpyxl")

    bugun = date.today()
    if davr == "bugun":
        bosh = tug = str(bugun)
    elif davr == "hafta":
        bosh = str(bugun - timedelta(days=bugun.weekday()))
        tug  = str(bugun)
    elif davr == "oy":
        bosh = str(bugun.replace(day=1))
        tug  = str(bugun)
    else:
        bosh = "2000-01-01"
        tug  = str(bugun)

    wb = openpyxl.Workbook()
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    xulosa_varaqi(wb, bosh, tug)
    transport_varaqi(wb, bosh, tug)
    ishchilar_varaqi(wb, bosh, tug)

    vaqt      = datetime.now().strftime("%Y%m%d_%H%M%S")
    fayl_nomi = "zavod_hisobot_{}_{}.xlsx".format(davr, vaqt)
    yol       = os.path.join(EKSPORT_PAPKA, fayl_nomi)
    wb.save(yol)
    print("[Excel] Saqlandi: {}".format(yol))
    return yol
