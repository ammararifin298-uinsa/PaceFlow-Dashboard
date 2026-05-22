"""
db.py — Database Access Layer (Dash-compatible, NO Streamlit)
Repository Pattern: app.py tidak pernah menulis SQL secara langsung.
Cache menggunakan functools.lru_cache — kompatibel dengan Dash.
"""
from functools import lru_cache
import pandas as pd
from sqlalchemy import create_engine, text
from config import DB_URL

# ── Engine (singleton, dibuat sekali) ─────────────────────────────────────────
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

# ── Public API ────────────────────────────────────────────────────────────────

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
