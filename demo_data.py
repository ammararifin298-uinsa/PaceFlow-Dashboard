# ==========================================================================
# demo_data.py — Offline / Demo Mode Data Provider
# Digunakan saat PostgreSQL tidak tersedia (presentasi, demo, development).
# Fix: tambah is_dnf, season_cumulative_points, get_calendar()
# ==========================================================================
import pandas as pd
import numpy as np
import os
from config import DEMO_CACHE_PATH

_CACHE: pd.DataFrame | None = None

# Status yang dianggap finish (bukan DNF)
FINISHED_STATUSES = {
    'Finished', '+1 Lap', '+2 Laps', '+3 Laps', '+4 Laps',
    '+5 Laps', '+6 Laps', '+7 Laps', '+8 Laps', '+9 Laps', '+10 Laps'
}


def _load() -> pd.DataFrame:
    global _CACHE
    if _CACHE is None:
        df = pd.read_csv(DEMO_CACHE_PATH, low_memory=False)

        # Boolean columns
        for col in ['is_win', 'is_podium', 'is_finished']:
            if col in df.columns:
                df[col] = df[col].astype(bool)

        # Fix is_finished — pakai FINISHED_STATUSES, bukan kolom lama
        if 'status' in df.columns:
            df['is_finished'] = df['status'].isin(FINISHED_STATUSES)
            df['is_dnf']      = ~df['status'].isin(FINISHED_STATUSES)
        else:
            df['is_dnf'] = ~df['is_finished']

        # Tambah season_cumulative_points — hitung ulang per driver per season
        df = df.sort_values(['driver_id', 'season', 'round'])
        df['season_cumulative_points'] = (
            df.groupby(['driver_id', 'season'])['race_points']
            .cumsum()
        )

        _CACHE = df
    return _CACHE


def get_seasons() -> list:
    return sorted(_load()['season'].unique().tolist(), reverse=True)


def get_analytics(season: int) -> pd.DataFrame:
    df = _load()
    return (df[df['season'] == season]
            .sort_values(['round', 'position'])
            .reset_index(drop=True))


def get_kpi(season: int) -> pd.Series:
    df = get_analytics(season)
    if df.empty:
        return pd.Series(dtype=object)

    latest  = df.sort_values('round', ascending=False).drop_duplicates('driver_id')
    top2    = latest.nlargest(2, 'cumulative_points')
    leader  = top2.iloc[0]
    gap     = (float(top2.iloc[0]['cumulative_points']) -
               float(top2.iloc[1]['cumulative_points'])) if len(top2) >= 2 else 0

    total   = len(df)
    dnf     = int(df['is_dnf'].sum()) if 'is_dnf' in df.columns else 0
    avg_pit = df['avg_pit_duration_s'].dropna().mean()

    return pd.Series({
        'season':             season,
        'total_races':        df['race_name'].nunique(),
        'total_drivers':      df['driver_id'].nunique(),
        'total_constructors': df['constructor'].nunique(),
        'points_leader':      leader['driver_name'],
        'leader_points':      float(leader['cumulative_points']),
        'leader_constructor': leader.get('constructor', '—'),
        'gap_to_p2':          gap,
        'season_avg_pit_s':   round(float(avg_pit), 3) if pd.notna(avg_pit) else None,
        'total_dnf':          dnf,
        'total_entries':             total,
        'total_races_scheduled':     df['round'].max(),
    })


def get_constructor_season(season: int) -> pd.DataFrame:
    df = get_analytics(season)
    agg = df.groupby(['constructor', 'constructor_id']).agg(
        total_wins=('is_win', 'sum'),
        total_podiums=('is_podium', 'sum'),
        total_points=('race_points', 'sum'),
        avg_speed_kph=('avg_speed_kph', 'mean'),
        avg_pit_s=('avg_pit_duration_s', 'mean'),
        entries=('driver_id', 'count'),
    ).reset_index()
    agg['win_rate']    = agg['total_wins']    / agg['entries'] * 100
    agg['podium_rate'] = agg['total_podiums'] / agg['entries'] * 100
    return agg.sort_values('total_points', ascending=False).reset_index(drop=True)


def get_calendar() -> pd.DataFrame:
    """
    Buat kalender dari demo_cache.csv.
    Ambil pemenang (position=1) per race sebagai data kalender.
    """
    df = _load()
    races   = df[['season', 'round', 'race_name', 'race_date',
                  'circuit_name', 'city', 'country', 'lat', 'lng']].drop_duplicates()
    winners = df[df['position'] == 1][[
        'season', 'round', 'driver_name', 'constructor',
        'laps', 'fastest_lap_time', 'avg_speed_kph'
    ]]
    cal = races.merge(winners, on=['season', 'round'], how='left')

    # Format
    cal['race_date'] = pd.to_datetime(cal['race_date'], errors='coerce')
    cal['date_fmt']  = cal['race_date'].dt.strftime('%d %b %Y').fillna('—')
    cal['status']    = cal['driver_name'].apply(
        lambda x: 'SELESAI' if pd.notna(x) else 'BELUM')
    for c in ['driver_name', 'constructor', 'fastest_lap_time']:
        cal[c] = cal[c].fillna('—')
    cal['avg_speed_kph'] = cal['avg_speed_kph'].apply(
        lambda x: f"{x:.1f}" if pd.notna(x) else '—')
    cal['laps'] = cal['laps'].fillna(0).astype(int).apply(
        lambda x: str(x) if x > 0 else '—')

    return cal.sort_values(['season', 'round']).reset_index(drop=True)

def get_qualifying(season: int) -> pd.DataFrame:
    try:
        path = os.path.join(os.path.dirname(__file__), "Data", "qualifying.csv")
        df = pd.read_csv(path)
        return df[df["season"] == season].sort_values(["round", "position"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

def get_pit_stops(season: int) -> pd.DataFrame:
    try:
        path = os.path.join(os.path.dirname(__file__), "Data", "pit_stops.csv")
        df = pd.read_csv(path)
        # Note: driver_name is not in pit_stops.csv! We need to join it or just use driver_id
        # Actually, let's load drivers.csv and join if needed.
        drivers_path = os.path.join(os.path.dirname(__file__), "Data", "drivers.csv")
        drivers = pd.read_csv(drivers_path)[["driver_id", "driver_name"]]
        df = df.merge(drivers, on="driver_id", how="left")
        return df[df["season"] == season].sort_values(["round", "driver_name", "stop"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()