# =============================================================================
# app.py — Entry Point PaceFlow (Modular Monolith)
# Hanya berisi: inisialisasi Dash, register callbacks, routing halaman
# Semua logika ada di pages/, components/, layout/, services/
# =============================================================================

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc

from config import DEMO_MODE
from layout.design_tokens import C, F
from layout.components import welcome_state
from layout.sidebar import make_sidebar
from services.data_service import get_seasons, is_demo_mode

# ── Halaman ──────────────────────────────────────────────────────────────────
from pages.home.layout      import layout as page_home
from pages.standings.layout import layout as page_standings
from pages.analytics.layout import layout as page_analytics
from pages.h2h.layout       import layout as page_h2h
from pages.datatable.layout import layout as page_datatable
from pages.benchmark.layout import layout as page_benchmark
from pages.about.layout     import layout as page_about

# ── Callbacks halaman yang punya callbacks sendiri ────────────────────────────
from pages.h2h.callbacks      import register_callbacks as reg_h2h
from pages.datatable.callbacks import register_callbacks as reg_datatable

# ── App ──────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="PaceFlow — F1 Analytics",
)

SL = get_seasons()

# ── Layout ───────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id="store-page",   data="beranda"),
    dcc.Store(id="store-season", data=None),
    dcc.Store(id="store-filter",
              data={"search": "", "drv": None, "con": None, "status": None}),
    dcc.Download(id="dl-beranda"),
    dcc.Download(id="dl-klasemen"),
    dcc.Download(id="dl-analitik"),
    dcc.Download(id="dl-tabel"),
    dcc.Download(id="dl-benchmark"),
    html.Div(id="sidebar-wrap"),
    html.Div([
        dcc.Loading(
            html.Div(id="page-content"),
            type="circle", color=C["blue"],
            style=dict(minHeight="200px")
        ),
        html.Div([
            html.Span(
                "PaceFlow · F1 Relational Analytics · "
                "SoC (ISO/IEC 25010) · PostgreSQL → Dash → Plotly",
                style=dict(fontSize="10px", color=C["muted"], fontFamily=F)
            ),
        ], style=dict(padding="12px 0", marginTop="8px",
                      borderTop=f"1px solid {C['border']}")),
    ], style=dict(marginLeft="220px", padding="20px 28px",
                  minHeight="100vh", background=C["bg"], fontFamily=F)),
], style=dict(background=C["bg"], minHeight="100vh", fontFamily=F))

# ── Navigation callback ───────────────────────────────────────────────────────
NAV_IDS = ["beranda", "klasemen", "analitik", "h2h", "tabel", "benchmark", "tentang"]

@app.callback(
    Output("store-page", "data"),
    [Input({"type": "nav", "index": pid}, "n_clicks") for pid in NAV_IDS],
    State("store-page", "data"),
    prevent_initial_call=True,
)
def nav_click(*args):
    ctx = callback_context
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        return no_update
    tid = ctx.triggered[0]["prop_id"]
    for pid in NAV_IDS:
        if f'"index":"{pid}"' in tid:
            return pid
    return args[-1]


# ── Season callback ───────────────────────────────────────────────────────────
@app.callback(
    Output("store-season", "data"),
    Input("dd-season", "value"),
    prevent_initial_call=True,
)
def season_change(val):
    return val if val else no_update


# ── Filter callback ───────────────────────────────────────────────────────────
@app.callback(
    Output("store-filter", "data"),
    Input("store-season", "data"),
    Input("store-page",   "data"),
    Input("sf-search",    "value"),
    Input("sf-drv",       "value"),
    Input("sf-con",       "value"),
    Input("sf-status",    "value"),
    State("store-filter", "data"),
    prevent_initial_call=True,
)
def manage_filter(season, page, search, drv, con, status, current):
    ctx     = callback_context
    if not ctx.triggered:
        return no_update
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger in ("store-season", "store-page"):
        return {"search": "", "drv": None, "con": None, "status": None}
    return {"search": search or "", "drv": drv, "con": con, "status": status}


# ── Sidebar callback ──────────────────────────────────────────────────────────
@app.callback(
    Output("sidebar-wrap", "children"),
    Input("store-page",   "data"),
    Input("store-season", "data"),
    Input("store-filter", "data"),
)
def render_sidebar(page, season, flt):
    return make_sidebar(page, season, SL, flt or {}, is_demo_mode())


# ── Page render callback ──────────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    Input("store-page",   "data"),
    Input("store-season", "data"),
    Input("store-filter", "data"),
)
def render_page(page, season, flt):
    flt = flt or {}
    if page == "benchmark": return page_benchmark()
    if page == "tentang":   return page_about()
    if season is None:      return welcome_state()
    if page == "beranda":   return page_home(season, flt)
    if page == "klasemen":  return page_standings(season, flt)
    if page == "analitik":  return page_analytics(season, flt)
    if page == "h2h":       return page_h2h(season)
    if page == "tabel":     return page_datatable(season, flt)
    return page_home(season, flt)


# ── Tab tabel callback ────────────────────────────────────────────────────────
@app.callback(
    Output("tabel-drv", "style"),
    Output("tabel-con", "style"),
    Output("tabel-cal", "style"),
    Input("tabel-tabs", "value"),
    prevent_initial_call=True,
)
def switch_tabel(tab):
    show = dict(display="block")
    hide = dict(display="none")
    if tab == "drv": return show, hide, hide
    if tab == "con": return hide, show, hide
    return hide, hide, show


# ── Download callbacks ────────────────────────────────────────────────────────
import pandas as pd

@app.callback(Output("dl-beranda", "data"),
    Input("btn-beranda", "n_clicks"),
    State("store-beranda-data", "data"),
    prevent_initial_call=True)
def dl_beranda(n, data):
    if not n or not data: return no_update
    return dict(content=pd.DataFrame(data).to_csv(index=False),
                filename="paceflow_championship.csv")

@app.callback(Output("dl-klasemen", "data"),
    Input("btn-klasemen", "n_clicks"),
    State("store-klasemen-data", "data"),
    prevent_initial_call=True)
def dl_klasemen(n, data):
    if not n or not data: return no_update
    return dict(content=pd.DataFrame(data).to_csv(index=False),
                filename="paceflow_klasemen.csv")

@app.callback(Output("dl-analitik", "data"),
    Input("btn-analitik", "n_clicks"),
    State("store-analitik-data", "data"),
    prevent_initial_call=True)
def dl_analitik(n, data):
    if not n or not data: return no_update
    return dict(content=pd.DataFrame(data).to_csv(index=False),
                filename="paceflow_analitik.csv")

@app.callback(Output("dl-tabel", "data"),
    Input("btn-tabel", "n_clicks"),
    State("store-tabel-data", "data"),
    prevent_initial_call=True)
def dl_tabel(n, data):
    if not n or not data: return no_update
    return dict(content=pd.DataFrame(data).to_csv(index=False),
                filename="paceflow_tabel.csv")


# ── Register callbacks dari pages ─────────────────────────────────────────────
reg_h2h(app)
reg_datatable(app)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)