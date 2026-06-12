# =============================================================================
# pages/settings/callbacks.py — Callbacks Halaman Settings PaceFlow
# Fix v2:
#   - Guard "if not n" di SEMUA button callback (prevent auto-trigger saat load)
#   - mode-indicator: callback reaktif agar mode tampil update tanpa page re-render
#   - toggle_mode: store-season hanya update jika benar-benar ada season aktif
#   - export_backup: guard n_clicks + error message yang jelas
# =============================================================================

import base64, io, os
import pandas as pd
from dash import Input, Output, State, no_update, html
from layout.design_tokens import C, F, rgba
from layout.components import info_box


# ── Helpers ────────────────────────────────────────────────────────────────────
def _row(label, value):
    """Baris info label–value standar."""
    return html.Div([
        html.Span(label, style=dict(
            fontSize="11px", fontWeight="700",
            color=C["muted"], fontFamily=F, width="160px",
            display="inline-block")),
        html.Span(str(value), style=dict(
            fontSize="11px", color=C["text"], fontFamily=F)),
    ], style=dict(marginBottom="6px"))


# ══════════════════════════════════════════════════════════════════════════════
def register_callbacks(app):

    # ── 0. Mode Indicator — reactive, bukan static ────────────────────────────
    # Dipanggil oleh: store-season (setelah toggle_mode update store-season)
    # Ini yang bikin indikator mode otomatis update setelah toggle
    @app.callback(
        Output("mode-indicator", "children"),
        Input("store-season", "data"),
    )
    def update_mode_indicator(_):
        from services.data_service import is_demo_mode
        from dash_iconify import DashIconify
        demo = is_demo_mode()
        dot_color = C["orange"] if demo else C["green"]
        label = "Mode Demo"       if demo else "PostgreSQL Terhubung"
        sub   = "Menggunakan demo_cache.csv" if demo else "Koneksi aktif ke database lokal"
        return html.Div([
            html.Div(style=dict(
                width="8px", height="8px", borderRadius="50%",
                background=dot_color, marginRight="8px", marginTop="3px",
                flexShrink="0")),
            html.Div([
                html.Div(label, style=dict(fontSize="14px", fontWeight="700",
                                           color=C["text"], fontFamily=F)),
                html.Div(sub,   style=dict(fontSize="11px", color=C["muted"],
                                           fontFamily=F)),
            ]),
        ], style=dict(display="flex", alignItems="flex-start"))

    # ── 1. Toggle PostgreSQL / Demo ───────────────────────────────────────────
    @app.callback(
        Output("toggle-mode-result", "children"),
        Output("store-season", "data", allow_duplicate=True),
        Input("btn-toggle-mode", "n_clicks"),
        State("store-season", "data"),
        prevent_initial_call=True,
    )
    def toggle_mode(n, current_season):
        # Guard: jangan jalankan jika bukan klik nyata
        if not n:
            return no_update, no_update

        from services.data_service import is_demo_mode, set_demo_mode, invalidate_cache
        current  = is_demo_mode()
        new_mode = not current
        set_demo_mode(new_mode)
        invalidate_cache()

        if new_mode:
            msg   = "✅ Beralih ke **Mode Demo** — menggunakan demo_cache.csv."
            color = C["orange"]
        else:
            # Coba koneksi PostgreSQL
            try:
                import db as _db
                _db.get_seasons()
                msg   = "✅ Beralih ke **PostgreSQL** — koneksi database aktif."
                color = C["green"]
            except Exception as e:
                print(f"Error in toggle_mode: {e}")
                # Kalau gagal, balik ke demo lagi
                set_demo_mode(True)
                invalidate_cache()
                msg   = f"❌ PostgreSQL gagal ({e}). Tetap di Mode Demo."
                color = C["red"]

        # Kembalikan season yang sama → memicu update_mode_indicator + render_sidebar
        # FIX: Jangan fallback ke 0. Cari season terbaru yang valid dari database.
        safe_season = current_season
        if not safe_season:
            try:
                from services.data_service import get_seasons as _gs
                avail = _gs()
                safe_season = avail[0] if avail else None
            except Exception:
                safe_season = None
        return info_box(msg, color), safe_season

    # ── 2. DB Health Check ────────────────────────────────────────────────────
    @app.callback(
        Output("db-health-result", "children"),
        Input("btn-db-health", "n_clicks"),
        prevent_initial_call=True,
    )
    def check_health(n):
        if not n:
            return no_update
        from services.data_service import is_demo_mode
        try:
            if is_demo_mode():
                from config import DEMO_CACHE_PATH
                df = pd.read_csv(DEMO_CACHE_PATH, low_memory=False)
                seasons_list = sorted(df["season"].unique().tolist(), reverse=True)
                return html.Div([
                    _row("Status",      "ℹ️ Demo Mode (offline)"),
                    _row("Sumber Data", "demo_cache.csv"),
                    _row("Total Baris", f"{len(df):,} rows"),
                    _row("Seasons",     ", ".join(str(s) for s in seasons_list)),
                    _row("Kolom",       ", ".join(df.columns.tolist()[:6]) + " ..."),
                ])

            from db import health_check
            info = health_check()
            if info.get("status") == "connected":
                rows = [
                    _row("Status",        "✅ Terhubung"),
                    _row("Total Entries", f"{info.get('total_rows', 0):,} rows"),
                    _row("Seasons",       ", ".join(str(s) for s in info.get("seasons", []))),
                ]
                tables = info.get("tables", [])
                if tables:
                    rows.append(html.Div("Tabel dan Ukuran:", style=dict(
                        fontSize="11px", fontWeight="700", color=C["muted"],
                        fontFamily=F, marginTop="8px", marginBottom="4px")))
                    for t in tables:
                        rows.append(html.Div(
                            f"  {t['table_name']} — {t['size']}",
                            style=dict(fontSize="11px", color=C["text"],
                                       fontFamily=F, marginBottom="2px")))
                return html.Div(rows)
            else:
                return info_box(f"❌ Error: {info.get('message', 'Unknown')}", C["red"])
        except Exception as e:
            print(f"Error in check_health: {e}")
            return info_box(f"❌ Tidak dapat terhubung: {str(e)}", C["red"])

    # ── 3. Clear Cache ────────────────────────────────────────────────────────
    @app.callback(
        Output("clear-cache-result", "children"),
        Input("btn-clear-cache", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_cache(n):
        if not n:
            return no_update
        try:
            from services.data_service import invalidate_cache
            invalidate_cache()
            return info_box(
                "✅ Cache berhasil di-clear. Data akan di-fetch ulang dari sumber.",
                C["green"]
            )
        except Exception as e:
            print(f"Error in clear_cache: {e}")
            return info_box(f"❌ Gagal clear cache: {str(e)}", C["red"])

    # ── 4. ETL dan Data Info ──────────────────────────────────────────────────
    @app.callback(
        Output("etl-info-result", "children"),
        Input("btn-etl-info", "n_clicks"),
        prevent_initial_call=True,
    )
    def etl_info(n):
        if not n:
            return no_update
        from services.data_service import is_demo_mode
        try:
            if is_demo_mode():
                from config import DEMO_CACHE_PATH
                df = pd.read_csv(DEMO_CACHE_PATH, low_memory=False)
                seasons = sorted(df["season"].unique().tolist(), reverse=True)
                if "race_date" in df.columns:
                    latest_date = pd.to_datetime(
                        df["race_date"], errors="coerce").max()
                    latest_date = latest_date.strftime("%Y-%m-%d") \
                        if pd.notna(latest_date) else "—"
                else:
                    latest_date = "—"
                return html.Div([
                    _row("Sumber",        "demo_cache.csv (Mode Demo)"),
                    _row("Race Terakhir", latest_date),
                    _row("Total Seasons", len(seasons)),
                    _row("Total Races",   df["race_name"].nunique()
                                          if "race_name" in df.columns else "—"),
                    _row("Total Entries", f"{len(df):,}"),
                    _row("Seasons",       ", ".join(str(s) for s in seasons)),
                ])

            from db import get_etl_info
            info = get_etl_info()
            if "error" in info:
                return info_box(f"❌ {info['error']}", C["red"])
            return html.Div([
                _row("Race Terakhir", info.get("latest_race", "—")),
                _row("Total Seasons", info.get("total_seasons", "—")),
                _row("Total Races",   info.get("total_races", "—")),
                _row("Total Entries", f"{info.get('total_entries', 0):,}"),
            ])
        except Exception as e:
            print(f"Error in etl_info: {e}")
            return info_box(f"❌ Error: {str(e)}", C["red"])


    # ── 5. Upload CSV — Production-Grade Schema Validator ─────────────────────
    # Whitelist: hanya file bernama sesuai skema F1 yang diperbolehkan
    # Schema: dicek per-file sebelum disimpan ke disk
    CSV_SCHEMA = {
        "races.csv": [
            "season", "round", "race_name", "circuit_id", "circuit_name",
            "city", "country",
        ],
        "results.csv": [
            "season", "round", "driver_id", "points",
        ],
        "race_results.csv": [
            "season", "round", "driver_id", "points",
        ],
        "driver_standings.csv": [
            "season", "round", "driver_id", "points", "position",
        ],
        "constructor_standings.csv": [
            "season", "round", "constructor_id", "points", "position",
        ],
        "pit_stops.csv": [
            "season", "round", "driver_id",
        ],
        "qualifying.csv": [
            "season", "round", "driver_id", "position",
        ],
        "drivers.csv": [
            "driverRef",
        ],
        "circuits.csv": [
            "circuitRef",
        ],
    }

    @app.callback(
        Output("upload-csv-result", "children"),
        Input("upload-csv", "contents"),
        State("upload-csv", "filename"),
        prevent_initial_call=True,
    )
    def handle_upload(contents, filename):
        if not contents or not filename:
            return no_update

        # ── Guard 1: Ekstensi wajib .csv ──────────────────────────────────────
        if not filename.lower().endswith(".csv"):
            return info_box(
                f"❌ **Ekstensi tidak valid**: '{filename}' bukan file CSV."
                " Hanya file `.csv` yang diterima.", C["red"]
            )

        # ── Guard 2: Nama file harus ada di whitelist resmi ───────────────────
        allowed_names = set(CSV_SCHEMA.keys())
        if filename.lower() not in allowed_names:
            return info_box(
                f"❌ **File tidak dikenali**: `{filename}` bukan bagian dari skema F1 PaceFlow. "
                f"File yang diizinkan: `{'`, `'.join(sorted(allowed_names))}`.",
                C["red"]
            )

        # ── Parse CSV di memori (belum disimpan) ──────────────────────────────
        try:
            _, content_string = contents.split(",", 1)
            decoded = base64.b64decode(content_string)
            try:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            except UnicodeDecodeError:
                df = pd.read_csv(io.StringIO(decoded.decode("latin-1")))
            except pd.errors.ParserError as pe:
                return info_box(
                    f"❌ **File CSV rusak / tidak valid**: {str(pe)}", C["red"]
                )
        except Exception as e:
            print(f"Error in handle_upload decode: {e}")
            return info_box(
                f"❌ **Gagal mendekode file**: {str(e)}", C["red"]
            )

        if df.empty:
            return info_box(
                "⚠️ **File CSV kosong** — tidak ada baris data di dalam file.",
                C["orange"]
            )

        # ── Guard 3: Validasi kolom wajib (schema check) ──────────────────────
        required_cols = CSV_SCHEMA.get(filename.lower(), [])
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return info_box(
                f"❌ **Skema tidak cocok** untuk `{filename}`. "
                f"Kolom wajib yang hilang: `{'`, `'.join(missing)}`. "
                f"Kolom ditemukan: `{'`, `'.join(df.columns.tolist()[:8])}` ...",
                C["red"]
            )

        # ── Simpan ke ./Data/{filename} (hanya jika semua validasi lolos) ─────
        try:
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)))),
                "Data"
            )
            os.makedirs(data_dir, exist_ok=True)
            df.to_csv(os.path.join(data_dir, filename), index=False, encoding="utf-8")
        except Exception as e:
            print(f"Error in handle_upload save: {e}")
            return info_box(
                f"❌ **Gagal menyimpan file**: {str(e)}", C["red"]
            )

        return info_box(
            f"✅ **{filename}** berhasil divalidasi dan disimpan ke `Data/{filename}` — "
            f"{len(df):,} baris, {len(df.columns)} kolom. "
            f"Tekan **DB Health** lalu jalankan ETL dari terminal untuk update database.",
            C["green"]
        )

