"""
Asosiy Server - FastAPI
WebSocket orqali real-time video stream
REST API orqali ma'lumotlar
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

from database import (
    init_db, transport_royxat, ishchi_royxat,
    transport_qoshish, ishchi_qoshish
)
from kamera import kamera

# ─────────────────────────────────────────────
app = FastAPI(title="Zavod Monitoring Tizimi", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static fayllar
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

# ─────────────────────────────────────────────
# Startup
@app.on_event("startup")
async def startup():
    init_db()
    boshlandi = kamera.boshlash()
    if not boshlandi:
        print("[Server] Kamera ishga tushmadi - demo rejimda davom etadi")


@app.on_event("shutdown")
async def shutdown():
    kamera.toxtatish()


# ─────────────────────────────────────────────
# HTML Sahifalar

@app.get("/", response_class=HTMLResponse)
async def bosh_sahifa():
    fayl = os.path.join(FRONTEND_DIR, "templates", "index.html")
    with open(fayl, encoding="utf-8") as f:
        return f.read()


# ─────────────────────────────────────────────
# REST API

@app.get("/api/transport")
async def transport_api(limit: int = 50):
    """So'nggi transport yozuvlari"""
    return transport_royxat(limit)


@app.get("/api/ishchilar")
async def ishchilar_api(limit: int = 50):
    """So'nggi ishchi yozuvlari"""
    return ishchi_royxat(limit)


@app.post("/api/transport/kirdi")
async def transport_kirdi():
    """Qo'lda transport kirdi tugmasi"""
    natija = kamera.transport_skan("kirdi")
    if natija:
        return {"holat": "ok", "ma'lumot": natija}
    return {"holat": "xato", "xabar": "Kamera yoki kadr mavjud emas"}


@app.post("/api/transport/chiqdi")
async def transport_chiqdi():
    """Qo'lda transport chiqdi tugmasi"""
    natija = kamera.transport_skan("chiqdi")
    if natija:
        return {"holat": "ok", "ma'lumot": natija}
    return {"holat": "xato", "xabar": "Kamera yoki kadr mavjud emas"}


@app.post("/api/ishchi/skan")
async def ishchi_skan_api():
    """Qo'lda ishchi skanlash"""
    natijalar = kamera.ishchi_skan()
    return {"holat": "ok", "ishchilar": natijalar, "son": len(natijalar)}


@app.get("/api/excel/yuklash")
async def excel_yuklash(davr: str = Query(default="bugun", regex="^(bugun|hafta|oy|hammasi)$")):
    """Excel hisobotni yuklab olish"""
    try:
        from excel_eksport import excel_yaratish
        yol = excel_yaratish(davr)
        fayl_nomi = os.path.basename(yol)
        return FileResponse(
            path=yol,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=fayl_nomi
        )
    except ImportError as e:
        return JSONResponse({"xato": str(e)}, status_code=500)
    except Exception as e:
        return JSONResponse({"xato": f"Hisobot yaratishda xatolik: {e}"}, status_code=500)


@app.get("/api/statistika")
async def statistika():
    """Kunlik statistika"""
    from database import get_connection
    conn = get_connection()

    bugun_transport = conn.execute("""
        SELECT COUNT(*) as son, harakat
        FROM transport_log
        WHERE date(vaqt) = date('now')
        GROUP BY harakat
    """).fetchall()

    bugun_ishchi = conn.execute("""
        SELECT COUNT(DISTINCT yuz_id) as son
        FROM ishchi_log
        WHERE date(vaqt) = date('now')
    """).fetchone()

    jami_transport = conn.execute(
        "SELECT COUNT(*) as son FROM transport_log"
    ).fetchone()

    conn.close()

    stat = {
        "bugun_transport": {r["harakat"]: r["son"] for r in bugun_transport},
        "bugun_ishchilar": bugun_ishchi["son"] if bugun_ishchi else 0,
        "jami_transport": jami_transport["son"] if jami_transport else 0,
    }
    return stat


# ─────────────────────────────────────────────
# WebSocket - real-time video stream

@app.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    """Real-time kamera stream"""
    await websocket.accept()
    print("[WS] Video ulanish o'rnatildi")
    try:
        while True:
            kadr_b64 = kamera.kadr_base64()
            if kadr_b64:
                await websocket.send_json({
                    "tur": "video",
                    "kadr": kadr_b64
                })
            await asyncio.sleep(0.05)  # ~20 FPS
    except WebSocketDisconnect:
        print("[WS] Video ulanish uzildi")
    except Exception as e:
        print(f"[WS] Xatolik: {e}")


@app.websocket("/ws/hodisalar")
async def hodisalar_stream(websocket: WebSocket):
    """Real-time hodisalar stream"""
    await websocket.accept()
    oxirgi_transport_id = 0
    oxirgi_ishchi_id = 0
    print("[WS] Hodisalar ulanish o'rnatildi")
    try:
        while True:
            # Yangi transport yozuvlarini tekshirish
            transportlar = transport_royxat(5)
            if transportlar and transportlar[0]["id"] != oxirgi_transport_id:
                oxirgi_transport_id = transportlar[0]["id"]
                await websocket.send_json({
                    "tur": "transport",
                    "ma'lumot": transportlar[0]
                })

            # Yangi ishchi yozuvlarini tekshirish
            ishchilar = ishchi_royxat(5)
            if ishchilar and ishchilar[0]["id"] != oxirgi_ishchi_id:
                oxirgi_ishchi_id = ishchilar[0]["id"]
                await websocket.send_json({
                    "tur": "ishchi",
                    "ma'lumot": ishchilar[0]
                })

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("[WS] Hodisalar ulanish uzildi")


# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
