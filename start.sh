#!/bin/bash
# ═══════════════════════════════════════════════════════
#  Zavod Monitoring Tizimi - Ishga tushirish skripti
#  Linux / macOS uchun
# ═══════════════════════════════════════════════════════

set -e

LOYIHA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$LOYIHA_DIR/backend"
VENV_DIR="$LOYIHA_DIR/venv"
PYTHON="python3"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     ZAVOD MONITORING TIZIMI v1.0         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Python tekshirish ──────────────────────
if ! command -v $PYTHON &> /dev/null; then
    echo "[❌] Python3 topilmadi! O'rnatng: https://python.org"
    exit 1
fi
echo "[✓] Python: $($PYTHON --version)"

# ── 2. Virtual muhit ─────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "[...] Virtual muhit yaratilmoqda..."
    $PYTHON -m venv "$VENV_DIR"
    echo "[✓] Virtual muhit yaratildi"
fi

source "$VENV_DIR/bin/activate"
echo "[✓] Virtual muhit faollashtirildi"

# ── 3. Kutubxonalar o'rnatish ─────────────────
echo "[...] Kutubxonalar tekshirilmoqda..."
pip install -q --upgrade pip
pip install -q -r "$LOYIHA_DIR/requirements_minimal.txt"
echo "[✓] Kutubxonalar tayyor"

# ── 4. Papkalarni tekshirish ──────────────────
mkdir -p "$BACKEND_DIR/data/rasmlar"
mkdir -p "$BACKEND_DIR/exports"
mkdir -p "$LOYIHA_DIR/models/yuzlar"
echo "[✓] Papkalar tayyor"

# ── 5. Serverni ishga tushirish ───────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 Dashboard:  http://localhost:8000"
echo "  📡 API docs:   http://localhost:8000/docs"
echo "  🛑 To'xtatish: Ctrl+C"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$BACKEND_DIR"
$PYTHON -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
