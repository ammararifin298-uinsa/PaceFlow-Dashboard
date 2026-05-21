"""
demo_data.py — Offline / Demo Mode Data Provider
Digunakan saat PostgreSQL tidak tersedia (presentasi, demo, development).
Memuat demo_cache.csv yang di-generate dari data real saat ETL.
"""
import pandas as pd
import numpy as np
import os
from config import DEMO_CACHE_PATH

_CACHE: pd.DataFrame | None = None

def _load() -> pd.DataFrame:
    global _CACHE
    if _CACHE is None:
        _CACHE = pd.read_csv(DEMO_CACHE_PATH, low_memory=False)
        # Ensure boolean columns parsed correctly
        for col in ['is_win','is_podium','is_finished']:
            if col in _CACHE.columns:
                _CACHE[col] = _CACHE[col].astype(bool)
    return _CACHE


def get_seasons() -> list[int]:
    return sorted(_load()['season'].unique().tolist(), reverse=True)


def get_analytics(season: int) -> pd.DataFrame:
    df = _load()
    return df[df['season']==season].sort_values(['round','position']).reset_index(drop=True)


def get_kpi(season: int) -> pd.Series:
    df = get_analytics(season)
    if df.empty:
        return pd.Series(dtype=object)

    latest = df.sort_values('round', ascending=False).drop_duplicates('driver_id')
    top2 = latest.nlargest(2, 'cumulative_points')
    leader = top2.iloc[0]
    gap = float(top2.iloc[0]['cumulative_points'] - top2.iloc[1]['cumulative_points']) if len(top2)>=2 else 0

    total = len(df)
    dnf   = int((df['is_finished']==False).sum())
    avg_pit = df['avg_pit_duration_s'].dropna().mean()

    return pd.Series({
        'season':          season,
        'total_races':     df['race_name'].nunique(),
        'total_drivers':   df['driver_id'].nunique(),
        'total_constructors': df['constructor'].nunique(),
        'points_leader':   leader['driver_name'],
        'leader_points':   float(leader['cumulative_points']),
        'leader_constructor': leader['constructor'],
        'gap_to_p2':       gap,
        'season_avg_pit_s': round(float(avg_pit), 3) if not np.isnan(avg_pit) else None,
        'total_dnf':       dnf,
        'total_entries':   total,
    })


def get_constructor_season(season: int) -> pd.DataFrame:
    df = get_analytics(season)
    agg = df.groupby(['constructor','constructor_id']).agg(
        total_wins=('is_win','sum'),
        total_podiums=('is_podium','sum'),
        total_points=('race_points','sum'),
        avg_speed_kph=('avg_speed_kph','mean'),
        avg_pit_s=('avg_pit_duration_s','mean'),
        entries=('driver_id','count'),
    ).reset_index()
    agg['win_rate']    = agg['total_wins']    / agg['entries'] * 100
    agg['podium_rate'] = agg['total_podiums'] / agg['entries'] * 100
    return agg.sort_values('total_points', ascending=False).reset_index(drop=True)


def get_pit_detail(season: int) -> pd.DataFrame:
    pit = pd.read_csv(
        os.path.join(os.path.dirname(DEMO_CACHE_PATH), '..', '..', 'uploads', 'pit_stops.csv')
    )
    pit = pit[(pit['season']==season) & (pit['is_red_flag_hold']==False)]
    pit = pit.dropna(subset=['duration_s'])

    # join driver_name
    df = get_analytics(season)[['round','driver_id','driver_name']].drop_duplicates()
    pit = pit.merge(df, on=['round','driver_id'], how='left')
    return pit.sort_values(['round','driver_id','stop']).reset_index(drop=True)
