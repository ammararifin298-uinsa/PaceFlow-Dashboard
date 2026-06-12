# =============================================================================
# db.py — Database Access Layer (Dash-compatible, NO Streamlit)
# Repository Pattern: semua query SQL di sini, tidak ada di pages/
# Update: HAPUS @lru_cache dari sini — caching HANYA dilakukan di data_service.py
#         agar invalidate_cache() di Settings benar-benar efektif (single cache layer).
# =============================================================================

import pandas as pd
from sqlalchemy import create_engine, text
from config import DB_URL

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            DB_URL,
            pool_pre_ping=True,
            pool_size=3,
            max_overflow=2,
        )
    return _engine

def _query(sql: str, params: dict = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

def health_check() -> dict:
    """Cek koneksi dan info database — untuk Settings page."""
    try:
        result = _query("SELECT COUNT(*) as total FROM race_results")
        seasons = _query("SELECT DISTINCT season FROM races ORDER BY season DESC")
        tables  = _query("""
            SELECT table_name,
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        return {
            "status":     "connected",
            "total_rows": int(result.iloc[0]["total"]),
            "seasons":    seasons["season"].tolist(),
            "tables":     tables.to_dict("records"),
        }
    except Exception as e:
        print(f"Error in health_check: {e}")
        return {"status": "error", "message": str(e)}

# ─────────────────────────────────────────────────────────────────────────────
# EXISTING FUNCTIONS — NO @lru_cache here (caching in data_service.py only)
# ─────────────────────────────────────────────────────────────────────────────

def get_seasons() -> list:
    df = _query("SELECT DISTINCT season FROM races ORDER BY season DESC")
    return df["season"].tolist()

def get_analytics(season: int) -> pd.DataFrame:
    return _query(
        "SELECT * FROM v_f1_analytics WHERE season = :season ORDER BY round, position",
        params={"season": season}
    )

def get_kpi(season: int) -> pd.Series:
    df = _query("SELECT * FROM v_kpi_summary WHERE season = :season", params={"season": season})
    return df.iloc[0] if not df.empty else pd.Series(dtype=object)

def get_constructor_season(season: int) -> pd.DataFrame:
    return _query(
        "SELECT * FROM v_constructor_season WHERE season = :season ORDER BY total_points DESC",
        params={"season": season}
    )

def get_calendar() -> pd.DataFrame:
    df = _query("""
        SELECT
            r.season, r.round, r.race_name, r.race_date,
            r.circuit_name, r.city, r.country,
            r.lat, r.lng,
            rr.driver_name, rr.constructor,
            rr.laps, rr.fastest_lap_time, rr.avg_speed_kph,
            TO_CHAR(r.race_date, 'DD Mon YYYY') AS date_fmt,
            CASE WHEN rr.driver_name IS NOT NULL
                 THEN 'SELESAI' ELSE 'BELUM' END AS status
        FROM races r
        LEFT JOIN race_results rr
            ON r.season = rr.season
            AND r.round = rr.round
            AND rr.position = 1
        ORDER BY r.season, r.round
    """)
    for c in ["fastest_lap_time", "driver_name", "constructor"]:
        if c in df.columns:
            df[c] = df[c].fillna("—")
    # M-7 Fix: simpan kolom numerik asli (untuk CSV download), hanya format di UI layer
    # avg_speed_kph dan laps tetap numerik di sini — formatting dilakukan di layout
    if "avg_speed_kph" in df.columns:
        df["avg_speed_kph"] = pd.to_numeric(df["avg_speed_kph"], errors="coerce")
    if "laps" in df.columns:
        df["laps"] = pd.to_numeric(df["laps"], errors="coerce").fillna(0).astype(int)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# NEW FUNCTIONS — view dan tabel baru
# ─────────────────────────────────────────────────────────────────────────────

def get_driver_season_summary(season: int) -> pd.DataFrame:
    """Ambil driver summary dari v_driver_season_summary."""
    return _query(
        "SELECT * FROM v_driver_season_summary WHERE season = :season ORDER BY championship_pos",
        params={"season": season}
    )

def get_championship_progression(season: int) -> pd.DataFrame:
    """Ambil progression poin per round per driver dari v_championship_progression."""
    return _query(
        "SELECT * FROM v_championship_progression WHERE season = :season ORDER BY driver_id, round",
        params={"season": season}
    )

def get_constructor_progression(season: int) -> pd.DataFrame:
    """Ambil progression poin konstruktor per round dari v_constructor_progression."""
    return _query(
        "SELECT * FROM v_constructor_progression WHERE season = :season ORDER BY constructor_id, round",
        params={"season": season}
    )

def get_dnf_causes(season: int) -> pd.DataFrame:
    """Ambil breakdown DNF causes per season dari v_dnf_causes."""
    return _query(
        "SELECT * FROM v_dnf_causes WHERE season = :season ORDER BY total DESC",
        params={"season": season}
    )

def get_drivers_info() -> pd.DataFrame:
    """Ambil info lengkap driver dari tabel drivers."""
    return _query("SELECT * FROM drivers ORDER BY driver_name")

def get_circuits() -> pd.DataFrame:
    """Ambil data sirkuit dari tabel circuits — untuk peta Grand Prix."""
    return _query("SELECT * FROM circuits ORDER BY country")

def get_etl_info() -> dict:
    """Info terakhir ETL — untuk Settings page data freshness indicator."""
    try:
        result = _query("""
            SELECT
                MAX(race_date) as latest_race,
                COUNT(DISTINCT season) as total_seasons,
                COUNT(DISTINCT race_name) as total_races,
                COUNT(*) as total_entries
            FROM race_results
        """)
        row = result.iloc[0]
        return {
            "latest_race":   str(row["latest_race"]),
            "total_seasons": int(row["total_seasons"]),
            "total_races":   int(row["total_races"]),
            "total_entries": int(row["total_entries"]),
        }
    except Exception as e:
        print(f"Error in get_etl_info: {e}")
        return {"error": str(e)}

def get_qualifying(season: int) -> pd.DataFrame:
    """Ambil data kualifikasi untuk musim tertentu."""
    return _query(
        "SELECT * FROM qualifying WHERE season = :season ORDER BY round, position",
        params={"season": season}
    )

def get_pit_stops(season: int) -> pd.DataFrame:
    """Ambil data pit stop untuk musim tertentu."""
    return _query("""
        SELECT p.*, d.driver_name, d.driver_code
        FROM pit_stops p
        LEFT JOIN drivers d ON p.driver_id = d.driver_id
        WHERE p.season = :season
        ORDER BY p.round, d.driver_name, p.stop
    """, params={"season": season})