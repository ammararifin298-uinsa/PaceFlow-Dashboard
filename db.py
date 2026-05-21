"""
db.py — Database Access Layer
Semua query terpusat di sini. app.py tidak pernah menulis SQL secara langsung.
Prinsip: Repository Pattern — presentasi layer tidak tahu detail storage.
"""
import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st
from config import DB_URL, DEMO_CACHE_PATH, CACHE_TTL

# ── Engine (singleton) ────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_size=3, max_overflow=2)

# ── Generic query ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _run_query(sql: str) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn)

# ── Public data access functions ──────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_seasons() -> list[int]:
    df = _run_query("SELECT DISTINCT season FROM races ORDER BY season DESC")
    return df["season"].tolist()

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_analytics(season: int) -> pd.DataFrame:
    return _run_query(
        f"SELECT * FROM v_f1_analytics WHERE season={season} ORDER BY round, position"
    )

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_kpi(season: int) -> pd.Series:
    df = _run_query(f"SELECT * FROM v_kpi_summary WHERE season={season}")
    return df.iloc[0] if not df.empty else pd.Series(dtype=object)

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_constructor_season(season: int) -> pd.DataFrame:
    return _run_query(
        f"SELECT * FROM v_constructor_season WHERE season={season} ORDER BY total_points DESC"
    )

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_pit_detail(season: int) -> pd.DataFrame:
    return _run_query(f"""
        SELECT season, round, race_name, driver_id, stop, lap, duration_s
        FROM pit_stops
        WHERE season={season} AND is_red_flag_hold=FALSE AND duration_s IS NOT NULL
        ORDER BY round, driver_id, stop
    """)
