@echo off
REM ═══════════════════════════════════════════════════════
REM  Zavod Monitoring Tizimi - Ishga tushirish skripti
REM  Windows uchun
REM ═══════════════════════════════════════════════════════

setlocal enabledelayedexpansion

set LOYIHA_DIR=%~dp0
set BACKEND_DIR=%LOYIHA_DIR%backend
set VENV_DIR=%LOYIHA_DIR%venv

echo.
echo ╔══════════════════════════════════════════╗
echo ║     ZAVOD MONITORING TIZIMI v1.0         ║
echo ╚══════════════════════════════════════════╝
echo.

REM ── 1. Python tekshirish ──────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python topilmadi! O'rnatng: https://python.org
    pause
    exit /b 1
)
echo [OK] Python topildi

REM ── 2. Virtual muhit ─────────────────────────
if not exist "%VENV_DIR%" (
    echo [...] Virtual muhit yaratilmoqda...
    python -m venv "%VENV_DIR%"
    echo [OK] Virtual muhit yaratildi
)

call "%VENV_DIR%\Scripts\activate.bat"
echo [OK] Virtual muhit faollashtirildi

REM ── 3. Kutubxonalar ───────────────────────────
echo [...] Kutubxonalar o'rnatilmoqda...
pip install -q --upgrade pip
pip install -q -r "%LOYIHA_DIR%requirements_minimal.txt"
echo [OK] Kutubxonalar tayyor

REM ── 4. Papkalar ───────────────────────────────
if not exist "%BACKEND_DIR%\data\rasmlar" mkdir "%BACKEND_DIR%\data\rasmlar"
if not exist "%BACKEND_DIR%\exports"      mkdir "%BACKEND_DIR%\exports"
if not exist "%LOYIHA_DIR%models\yuzlar"  mkdir "%LOYIHA_DIR%models\yuzlar"
echo [OK] Papkalar tayyor

REM ── 5. Brauzer ochish ─────────────────────────
timeout /t 2 /nobreak >nul
start "" "http://localhost:8000"

REM ── 6. Server ─────────────────────────────────
echo.
echo ══════════════════════════════════════════
echo   Dashboard:  http://localhost:8000
echo   API docs:   http://localhost:8000/docs
echo   To'xtatish: Ctrl+C
echo ══════════════════════════════════════════
echo.

cd /d "%BACKEND_DIR%"
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause
