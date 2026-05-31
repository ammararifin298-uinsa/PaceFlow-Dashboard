# =============================================================================
# data_service.py — Service layer PaceFlow
# Tanggung jawab: ambil data dari DAL (db.py / demo_data.py), enforce schema,
# dan sediakan data siap pakai untuk semua pages/
# Tidak ada HTML, tidak ada query SQL langsung di sini
# Update: tambah fungsi baru untuk view baru (driver_summary, progression, dll)
# =============================================================================

import os, sys
from functools import lru_cache
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEMO_MODE

_use_demo = DEMO_MODE
if not _use_demo:
    try:
        import db
        db.get_seasons()
    except Exception as e:
        _use_demo = True
        print(f"[DataService] PostgreSQL gagal ({e}), fallback demo mode.")

import demo_data as demo

# Kolom yang dijamin ada di setiap DataFrame analytics
REQUIRED_COLS = {
    "season":                   0,
    "round":                    0,
    "race_name":                "",
    "driver_id":                "",
    "driver_name":              "",
    "driver_nat":               "",
    "driver_code":              "",
    "constructor":              "",
    "constructor_id":           "",
    "position":                 None,
    "race_points":              0.0,
    "cumulative_points":        0.0,
    "season_cumulative_points": 0.0,
    "championship_pos":         None,
    "cumulative_wins":          0,
    "is_win":                   False,
    "is_podium":                False,
    "is_dnf":                   False,
    "is_finished":              True,
    "avg_pit_duration_s":       None,
    "best_pit_duration_s":      None,
    "avg_speed_kph":            None,
    "qualifying_pos":           None,
    "fastest_lap_rank":         None,
    "grid_pos":                 None,
    "status":                   "",
    "laps":                     None,
    "lat":                      None,
    "lng":                      None,
}


def enforce_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Pastikan semua kolom wajib ada — isi default jika tidak ada di DB."""
    for col, default in REQUIRED_COLS.items():
        if col not in df.columns:
            df[col] = default
    return df


def invalidate_cache():
    """Invalidate semua cache — dipanggil setelah ETL atau upload CSV."""
    get_analytics.cache_clear()
    get_kpi.cache_clear()
    get_constructor_season.cache_clear()
    get_seasons.cache_clear()
    get_calendar.cache_clear()
    get_driver_season_summary.cache_clear()
    get_championship_progression.cache_clear()
    get_constructor_progression.cache_clear()
    get_dnf_causes.cache_clear()
    get_drivers_info.cache_clear()
    get_circuits.cache_clear()
    print("[DataService] Cache cleared.")


# ─────────────────────────────────────────────────────────────────────────────
# EXISTING FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=8)
def get_analytics(season: int) -> pd.DataFrame:
    """Ambil data analytics per season dari v_f1_analytics."""
    try:
        df = demo.get_analytics(season) if _use_demo else db.get_analytics(season)
        return enforce_schema(df)
    except Exception as e:
        print(f"[DataService] get_analytics({season}) error: {e}")
        return pd.DataFrame(columns=list(REQUIRED_COLS.keys()))


@lru_cache(maxsize=8)
def get_kpi(season: int) -> pd.Series:
    """Ambil KPI summary per season dari v_kpi_summary."""
    try:
        return demo.get_kpi(season) if _use_demo else db.get_kpi(season)
    except Exception as e:
        print(f"[DataService] get_kpi({season}) error: {e}")
        return pd.Series(dtype=object)


@lru_cache(maxsize=8)
def get_constructor_season(season: int) -> pd.DataFrame:
    """Ambil data konstruktor per season dari v_constructor_season."""
    try:
        return demo.get_constructor_season(season) if _use_demo else db.get_constructor_season(season)
    except Exception as e:
        print(f"[DataService] get_constructor_season({season}) error: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=1)
def get_seasons() -> list:
    """Ambil list season yang tersedia di database."""
    try:
        return demo.get_seasons() if _use_demo else db.get_seasons()
    except Exception:
        return [2024]


@lru_cache(maxsize=1)
def get_calendar() -> pd.DataFrame:
    """Ambil data kalender race dari PostgreSQL via db.py."""
    try:
        if _use_demo:
            return demo.get_calendar()
        return db.get_calendar()
    except Exception as e:
        print(f"[DataService] get_calendar() error: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# NEW FUNCTIONS — view baru
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=8)
def get_driver_season_summary(season: int) -> pd.DataFrame:
    """
    Ambil driver summary per season dari v_driver_season_summary.
    Sudah include win_rate, podium_rate, dnf_rate, consistency_score.
    Tidak perlu hitung di Python.
    """
    try:
        if _use_demo:
            return _demo_driver_summary(season)
        return db.get_driver_season_summary(season)
    except Exception as e:
        print(f"[DataService] get_driver_season_summary({season}) error: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=8)
def get_championship_progression(season: int) -> pd.DataFrame:
    """
    Ambil data perkembangan poin championship per round dari v_championship_progression.
    Dipakai untuk grafik line chart di Beranda dan Perbandingan Musim.
    """
    try:
        if _use_demo:
            return _demo_championship_progression(season)
        return db.get_championship_progression(season)
    except Exception as e:
        print(f"[DataService] get_championship_progression({season}) error: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=8)
def get_constructor_progression(season: int) -> pd.DataFrame:
    """
    Ambil data perkembangan poin konstruktor per round dari v_constructor_progression.
    Dipakai untuk Constructor Championship Progression di Klasemen.
    """
    try:
        if _use_demo:
            return _demo_constructor_progression(season)
        return db.get_constructor_progression(season)
    except Exception as e:
        print(f"[DataService] get_constructor_progression({season}) error: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=8)
def get_dnf_causes(season: int) -> pd.DataFrame:
    """
    Ambil breakdown penyebab DNF per season dari v_dnf_causes.
    Dipakai untuk donut chart di Analitik.
    """
    try:
        if _use_demo:
            return _demo_dnf_causes(season)
        return db.get_dnf_causes(season)
    except Exception as e:
        print(f"[DataService] get_dnf_causes({season}) error: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=1)
def get_drivers_info() -> pd.DataFrame:
    """
    Ambil info driver dari tabel drivers.
    Dipakai untuk Driver Profile Tooltip dan About page.
    """
    try:
        if _use_demo:
            return pd.DataFrame()
        return db.get_drivers_info()
    except Exception as e:
        print(f"[DataService] get_drivers_info() error: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=1)
def get_circuits() -> pd.DataFrame:
    """
    Ambil data sirkuit dari tabel circuits.
    Dipakai untuk peta sirkuit Grand Prix.
    """
    try:
        if _use_demo:
            return pd.DataFrame()
        return db.get_circuits()
    except Exception as e:
        print(f"[DataService] get_circuits() error: {e}")
        return pd.DataFrame()


def is_demo_mode() -> bool:
    """Cek apakah app berjalan dalam demo mode."""
    return _use_demo


def set_demo_mode(value: bool):
    """Toggle demo mode dari Settings page — tanpa restart app."""
    global _use_demo
    _use_demo = value
    invalidate_cache()
    print(f"[DataService] Mode: {'Demo' if value else 'PostgreSQL'}")


# ─────────────────────────────────────────────────────────────────────────────
# DEMO FALLBACKS — kalkulasi dari demo_cache.csv
# ─────────────────────────────────────────────────────────────────────────────

def _demo_driver_summary(season: int) -> pd.DataFrame:
    """Hitung driver summary dari demo_cache untuk mode demo."""
    df = demo.get_analytics(season)
    if df.empty:
        return pd.DataFrame()
    grp = df.groupby(["driver_id","driver_name","driver_nat",
                      "driver_code","constructor","constructor_id"])
    agg = grp.agg(
        total_races=("race_points","count"),
        total_points=("race_points","sum"),
        avg_points_per_race=("race_points","mean"),
        total_wins=("is_win","sum"),
        total_podiums=("is_podium","sum"),
        total_dnf=("is_dnf","sum"),
    ).reset_index()
    agg["season"]       = season
    agg["win_rate"]     = (agg["total_wins"]   / agg["total_races"] * 100).round(1)
    agg["podium_rate"]  = (agg["total_podiums"]/ agg["total_races"] * 100).round(1)
    agg["dnf_rate"]     = (agg["total_dnf"]    / agg["total_races"] * 100).round(1)
    agg["consistency_score"] = (
        agg["podium_rate"] * 0.4 +
        (100 - agg["dnf_rate"]) * 0.3 +
        (agg["avg_points_per_race"] /
         agg["avg_points_per_race"].max() * 30)
    ).round(1)
    return agg


def _demo_championship_progression(season: int) -> pd.DataFrame:
    """Ambil progression dari demo_cache."""
    df = demo.get_analytics(season)
    if df.empty:
        return pd.DataFrame()
    cols = ["season","round","race_name","driver_id","driver_name",
            "driver_code","constructor","race_points",
            "season_cumulative_points","championship_pos",
            "is_win","is_podium","is_dnf"]
    return df[[c for c in cols if c in df.columns]].sort_values(
        ["driver_id","round"])


def _demo_constructor_progression(season: int) -> pd.DataFrame:
    """Hitung constructor progression dari demo_cache."""
    df = demo.get_analytics(season)
    if df.empty:
        return pd.DataFrame()
    grp = df.groupby(["season","round","constructor","constructor_id"],
                     as_index=False)["race_points"].sum()
    grp = grp.sort_values(["constructor_id","round"])
    grp["cumulative_points"] = grp.groupby("constructor_id")["race_points"].cumsum()
    return grp


def _demo_dnf_causes(season: int) -> pd.DataFrame:
    """Hitung DNF causes dari demo_cache."""
    df = demo.get_analytics(season)
    if df.empty:
        return pd.DataFrame()
    finished = {'Finished','+1 Lap','+2 Laps','+3 Laps','+4 Laps',
                '+5 Laps','+6 Laps','+7 Laps','+8 Laps','+9 Laps','+10 Laps'}
    dnf = df[~df["status"].isin(finished)].copy()
    if dnf.empty:
        return pd.DataFrame()
    counts = dnf.groupby("status").size().reset_index(name="total")
    counts["season"]     = season
    counts["dnf_cause"]  = counts["status"]
    counts["percentage"] = (counts["total"] / counts["total"].sum() * 100).round(1)
    return counts[["season","dnf_cause","total","percentage"]]