# =============================================================================
# db.py — Database Access Layer (Dash-compatible, NO Streamlit)
# Repository Pattern: semua query SQL di sini, tidak ada di pages/
# Update: tambah fungsi baru untuk view baru
# =============================================================================

from functools import lru_cache
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

def _query(sql: str) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn)

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
            "status":    "connected",
            "total_rows": int(result.iloc[0]["total"]),
            "seasons":   seasons["season"].tolist(),
            "tables":    tables.to_dict("records"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ─────────────────────────────────────────────────────────────────────────────
# EXISTING FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_seasons() -> list:
    df = _query("SELECT DISTINCT season FROM races ORDER BY season DESC")
    return df["season"].tolist()

@lru_cache(maxsize=8)
def get_analytics(season: int) -> pd.DataFrame:
    return _query(
        f"SELECT * FROM v_f1_analytics "
        f"WHERE season={season} ORDER BY round, position"
    )

@lru_cache(maxsize=8)
def get_kpi(season: int) -> pd.Series:
    df = _query(f"SELECT * FROM v_kpi_summary WHERE season={season}")
    return df.iloc[0] if not df.empty else pd.Series(dtype=object)

@lru_cache(maxsize=8)
def get_constructor_season(season: int) -> pd.DataFrame:
    return _query(
        f"SELECT * FROM v_constructor_season "
        f"WHERE season={season} ORDER BY total_points DESC"
    )

@lru_cache(maxsize=1)
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
    if "avg_speed_kph" in df.columns:
        df["avg_speed_kph"] = df["avg_speed_kph"].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "—"
        )
    if "laps" in df.columns:
        df["laps"] = df["laps"].fillna(0).astype(int).apply(
            lambda x: str(x) if x > 0 else "—"
        )
    return df

# ─────────────────────────────────────────────────────────────────────────────
# NEW FUNCTIONS — view dan tabel baru
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=8)
def get_driver_season_summary(season: int) -> pd.DataFrame:
    """Ambil driver summary dari v_driver_season_summary — sudah include rates dan consistency_score."""
    return _query(
        f"SELECT * FROM v_driver_season_summary "
        f"WHERE season={season} ORDER BY championship_pos"
    )

@lru_cache(maxsize=8)
def get_championship_progression(season: int) -> pd.DataFrame:
    """Ambil progression poin per round per driver dari v_championship_progression."""
    return _query(
        f"SELECT * FROM v_championship_progression "
        f"WHERE season={season} ORDER BY driver_id, round"
    )

@lru_cache(maxsize=8)
def get_constructor_progression(season: int) -> pd.DataFrame:
    """Ambil progression poin konstruktor per round dari v_constructor_progression."""
    return _query(
        f"SELECT * FROM v_constructor_progression "
        f"WHERE season={season} ORDER BY constructor_id, round"
    )

@lru_cache(maxsize=8)
def get_dnf_causes(season: int) -> pd.DataFrame:
    """Ambil breakdown DNF causes per season dari v_dnf_causes."""
    return _query(
        f"SELECT * FROM v_dnf_causes "
        f"WHERE season={season} ORDER BY total DESC"
    )

@lru_cache(maxsize=1)
def get_drivers_info() -> pd.DataFrame:
    """Ambil info lengkap driver dari tabel drivers — untuk profile tooltip."""
    return _query("SELECT * FROM drivers ORDER BY driver_name")

@lru_cache(maxsize=1)
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
            "latest_race":    str(row["latest_race"]),
            "total_seasons":  int(row["total_seasons"]),
            "total_races":    int(row["total_races"]),
            "total_entries":  int(row["total_entries"]),
        }
    except Exception as e:
        return {"error": str(e)}