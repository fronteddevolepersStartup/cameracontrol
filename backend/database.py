"""
Ma'lumotlar bazasi moduli - SQLite
Barcha kirish/chiqish ma'lumotlari shu yerda saqlanadi
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "zavod.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Jadvallarni yaratish"""
    conn = get_connection()
    cur = conn.cursor()

    # Transportlar jadvali (furalar + yengil mashinalar)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transport_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raqam TEXT,
            tur TEXT DEFAULT 'noma''lum',       -- 'fura' yoki 'yengil'
            rang TEXT DEFAULT 'noma''lum',
            davlat TEXT DEFAULT 'noma''lum',
            viloyat TEXT DEFAULT 'noma''lum',
            harakat TEXT,                        -- 'kirdi' yoki 'chiqdi'
            vaqt TEXT,
            rasm_yol TEXT,
            qoshimcha TEXT
        )
    """)

    # Ishchilar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ishchi_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ism TEXT DEFAULT 'Noma''lum',
            yuz_id TEXT,
            harakat TEXT,                        -- 'kirdi' yoki 'chiqdi'
            vaqt TEXT,
            rasm_yol TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Ma'lumotlar bazasi tayyor.")


def transport_qoshish(raqam, tur, rang, davlat, viloyat, harakat, rasm_yol="", qoshimcha=""):
    """Yangi transport yozuvi qo'shish"""
    conn = get_connection()
    vaqt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO transport_log (raqam, tur, rang, davlat, viloyat, harakat, vaqt, rasm_yol, qoshimcha)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (raqam, tur, rang, davlat, viloyat, harakat, vaqt, rasm_yol, qoshimcha))
    conn.commit()
    conn.close()
    return vaqt


def ishchi_qoshish(ism, yuz_id, harakat, rasm_yol=""):
    """Ishchi kirdi/chiqdi yozuvi"""
    conn = get_connection()
    vaqt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO ishchi_log (ism, yuz_id, harakat, vaqt, rasm_yol)
        VALUES (?, ?, ?, ?, ?)
    """, (ism, yuz_id, harakat, vaqt, rasm_yol))
    conn.commit()
    conn.close()
    return vaqt


def transport_royxat(limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transport_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def ishchi_royxat(limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM ishchi_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
