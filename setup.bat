@echo off
chcp 65001 >nul
title PaceFlow — F1 Analytics Setup

echo.
echo ============================================================
echo   PaceFlow F1 Analytics — Auto Setup
echo ============================================================
echo.

REM ── 1. Cek Python ────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan. Install Python 3.10+ dulu.
    pause
    exit /b 1
)
echo [OK] Python ditemukan.

REM ── 2. Buat .env jika belum ada ──────────────────────────────
if not exist .env (
    echo [INFO] File .env belum ada, membuat dari .env.example...
    copy .env.example .env >nul
    echo [OK] .env dibuat. Edit .env jika ingin pakai PostgreSQL.
    echo      Default: Demo Mode (tanpa PostgreSQL) - langsung jalan!
) else (
    echo [OK] File .env sudah ada.
)

REM ── 3. Install dependencies ───────────────────────────────────
echo.
echo [INFO] Menginstall dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Gagal install requirements. Cek requirements.txt.
    pause
    exit /b 1
)
echo [OK] Dependencies terinstall.

REM ── 4. Cek mode (Demo atau PostgreSQL) ───────────────────────
echo.
findstr /i "F1_DEMO_MODE=true" .env >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Mode: DEMO (menggunakan demo_cache.csv)
    echo [INFO] Tidak perlu PostgreSQL - langsung jalankan dashboard!
    goto :run_app
)

REM ── 5. Jika PostgreSQL mode, jalankan ETL ────────────────────
echo [INFO] Mode: PostgreSQL
echo [INFO] Menjalankan ETL (load data + create views)...
python etl_load.py
if errorlevel 1 (
    echo [WARN] ETL gagal atau PostgreSQL tidak tersedia.
    echo [WARN] Otomatis fallback ke Demo Mode.
)

:run_app
REM ── 6. Jalankan Dashboard ─────────────────────────────────────
echo.
echo ============================================================
echo   Menjalankan PaceFlow Dashboard di http://localhost:8050
echo   Tekan Ctrl+C untuk berhenti
echo ============================================================
echo.
python app.py
pause
