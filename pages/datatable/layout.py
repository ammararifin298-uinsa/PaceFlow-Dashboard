# =============================================================================
# pages/datatable/layout.py — Halaman Tabel Data PaceFlow
# Arsitektur baru: skeleton statis + konten tabel via callback reaktif
# Tidak ada lagi full re-render saat filter berubah
# =============================================================================

import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import ico, card, sec
from layout.design_tokens import C, F
from services.data_service import get_analytics, get_seasons


def layout(season: int, flt: dict):
    """
    Hanya render shell/skeleton halaman.
    Konten tabel (driver, constructor, calendar) diisi oleh callbacks reaktif.
    """
    flt    = flt or {}
    seasons = get_seasons()
    season_opts = [{"label": str(s), "value": s} for s in seasons]

    # Ambil opsi driver & constructor untuk season saat ini
    df_raw = get_analytics(season)
    all_drivers      = sorted(df_raw["driver_name"].dropna().unique()) if not df_raw.empty else []
    all_constructors = sorted(df_raw["constructor"].dropna().unique())  if not df_raw.empty else []
    drv_opts = [{"label": d, "value": d} for d in all_drivers]
    con_opts = [{"label": c, "value": c} for c in all_constructors]

    return html.Div([
        sec("Tabel Data", "lucide:table"),

        # ── Filter card ──────────────────────────────────────────────────────
        card(dbc.Row([
            dbc.Col([
                html.Div("FILTER TAHUN", style=dict(
                    fontSize="10px", fontWeight="700", letterSpacing="1px",
                    textTransform="uppercase", color=C["muted"],
                    marginBottom="5px", fontFamily=F)),
                dcc.Dropdown(
                    id="tbl-year-filter",
                    options=season_opts,
                    value=season,
                    clearable=False,
                    style=dict(fontSize="12px")
                ),
            ], width=4),
            dbc.Col([
                html.Div("FILTER PEMBALAP", style=dict(
                    fontSize="10px", fontWeight="700", letterSpacing="1px",
                    textTransform="uppercase", color=C["muted"],
                    marginBottom="5px", fontFamily=F)),
                dcc.Dropdown(
                    id="tbl-drv-filter",
                    options=drv_opts,
                    value=None,
                    multi=True,
                    placeholder="Semua Pembalap",
                    style=dict(fontSize="12px")
                ),
            ], width=4),
            dbc.Col([
                html.Div("FILTER KONSTRUKTOR", style=dict(
                    fontSize="10px", fontWeight="700", letterSpacing="1px",
                    textTransform="uppercase", color=C["muted"],
                    marginBottom="5px", fontFamily=F)),
                dcc.Dropdown(
                    id="tbl-con-filter",
                    options=con_opts,
                    value=None,
                    multi=True,
                    placeholder="Semua Konstruktor",
                    style=dict(fontSize="12px")
                ),
            ], width=4),
        ], className="g-3"), p="16px"),

        # ── Tab header ──────────────────────────────────────────────────────
        dcc.Tabs(
            value="drv",
            id="tabel-tabs",
            children=[
                dcc.Tab(label="Driver Standings", value="drv",
                    style=dict(fontFamily=F, fontSize="12px"),
                    selected_style=dict(fontFamily=F, fontSize="12px",
                        fontWeight="700", color=C["blue"],
                        borderBottom=f"2px solid {C['blue']}")),
                dcc.Tab(label="Constructor Standings", value="con",
                    style=dict(fontFamily=F, fontSize="12px"),
                    selected_style=dict(fontFamily=F, fontSize="12px",
                        fontWeight="700", color=C["blue"],
                        borderBottom=f"2px solid {C['blue']}")),
                dcc.Tab(label="Race Calendar", value="cal",
                    style=dict(fontFamily=F, fontSize="12px"),
                    selected_style=dict(fontFamily=F, fontSize="12px",
                        fontWeight="700", color=C["blue"],
                        borderBottom=f"2px solid {C['blue']}")),
            ],
            style=dict(marginBottom="16px")
        ),

        # ── Panel: Driver Standings (callback mengisi konten) ────────────────
        html.Div([
            dcc.Loading(
                html.Div(id="tbl-drv-content"),
                type="dot", color=C["blue"]
            ),
        ], id="tabel-drv", style=dict(display="block")),

        # ── Panel: Constructor Standings ─────────────────────────────────────
        html.Div([
            dcc.Loading(
                html.Div(id="tbl-con-content"),
                type="dot", color=C["blue"]
            ),
        ], id="tabel-con", style=dict(display="none")),

        # ── Panel: Race Calendar ─────────────────────────────────────────────
        html.Div([
            dcc.Loading(
                html.Div(id="tbl-cal-content"),
                type="dot", color=C["blue"]
            ),
        ], id="tabel-cal", style=dict(display="none")),

        # Download button
        html.Div(
            html.Button([
                ico("lucide:download", 13, "#FFF"),
                html.Span(" Download CSV", style=dict(marginLeft="5px")),
            ], id="btn-tabel", n_clicks=0,
            style=dict(display="flex", alignItems="center",
                       background=C["blue"], color="#FFF",
                       border="none", borderRadius="6px",
                       padding="8px 16px", fontSize="11px",
                       fontWeight="600", fontFamily=F,
                       cursor="pointer", marginBottom="16px")),
        style=dict(display="flex", justifyContent="flex-end")),

        # Store untuk export
        dcc.Store(id="store-tabel-data", data=[]),
    ])