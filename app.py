# =============================================================================
# app.py — Entry Point PaceFlow (Modular Monolith)
# Hanya berisi: inisialisasi Dash, register callbacks, routing halaman
# Semua logika ada di pages/, components/, layout/, services/
# Update: tambah Settings page + Comparison page
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
from pages.settings.layout   import layout as page_settings
from pages.comparison.layout import layout as page_comparison

# ── Callbacks ─────────────────────────────────────────────────────────────────
from pages.home.callbacks      import register_callbacks as reg_home
from pages.analytics.callbacks import register_callbacks as reg_analytics
from pages.h2h.callbacks       import register_callbacks as reg_h2h
from pages.datatable.callbacks import register_callbacks as reg_datatable
from pages.standings.callbacks  import register_callbacks as reg_standings
from pages.settings.callbacks   import register_callbacks as reg_settings
from pages.comparison.callbacks import register_callbacks as reg_comparison
from pages.benchmark.callbacks   import register_callbacks as reg_benchmark



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

# ── Help Modal builder ───────────────────────────────────────────────
# Selalu ada di semua halaman — tidak bergantung pada season/page
def _help_modal():
    from layout.components import ico
    from layout.design_tokens import rgba

    def _gloss(term, definition):
        return html.Div([
            html.Span(term, style=dict(
                fontWeight="700", color=C["text"],
                fontFamily=F, fontSize="12px", display="block", marginBottom="2px",
            )),
            html.Span(definition, style=dict(
                color="#64748b", fontFamily=F, fontSize="11px",
                lineHeight="1.6", display="block",
            )),
        ], style=dict(
            paddingBottom="10px", marginBottom="10px",
            borderBottom="1px solid #E2E8F0",
        ))

    def _feat(icon_name, title, desc):
        return html.Div([
            ico(icon_name, 14, C["blue"]),
            html.Div([
                html.Div(title, style=dict(
                    fontWeight="700", color=C["text"],
                    fontFamily=F, fontSize="12px",
                )),
                html.Div(desc, style=dict(
                    color="#64748b", fontFamily=F, fontSize="11px",
                    lineHeight="1.5",
                )),
            ], style=dict(marginLeft="8px")),
        ], style=dict(display="flex", marginBottom="10px"))

    return dbc.Modal([
        dbc.ModalHeader(
            html.Div([
                html.Div("Panduan dan Glosarium F1", style=dict(
                    fontWeight="800", fontSize="15px",
                    color=C["text"], fontFamily=F,
                )),
                html.Div("PaceFlow — F1 Analytics Dashboard", style=dict(
                    fontSize="11px", color="#64748b", fontFamily=F,
                )),
            ]),
            close_button=True,
        ),
        dbc.ModalBody([
            html.Div("FITUR DASBOR", style=dict(
                fontSize="9px", fontWeight="700", letterSpacing="2px",
                color="#64748b", fontFamily=F, marginBottom="10px",
                textTransform="uppercase",
            )),
            _feat("lucide:home",        "Beranda",
                  "Progres poin dan posisi championship musim berjalan. Toggle Top 5/10/Semua."),
            _feat("lucide:trophy",      "Klasemen",
                  "Tabel standings pembalap dan konstruktor, profil statistik driver."),
            _feat("lucide:bar-chart-2", "Analitik",
                  "Scatter plot speed vs konsistensi, violin plot DNF, kualifikasi dan pit stop."),
            _feat("lucide:users",       "H2H (Duel)",
                  "Perbandingan duel langsung antara dua pembalap pilihan Anda."),
            _feat("lucide:git-compare", "Perbandingan Musim",
                  "Bandingkan hingga 3 musim dalam satu grafik interaktif."),
            _feat("lucide:zap",         "Benchmark",
                  "Analisis kecepatan dan performa teknis rata-rata per sirkuit."),
            html.Hr(style=dict(borderColor="#E2E8F0", margin="14px 0")),
            html.Div("GLOSARIUM ISTILAH F1", style=dict(
                fontSize="9px", fontWeight="700", letterSpacing="2px",
                color="#64748b", fontFamily=F, marginBottom="10px",
                textTransform="uppercase",
            )),
            _gloss("DNF (Did Not Finish)",
                   "Pembalap yang tidak menyelesaikan balapan karena insiden teknis atau kecelakaan."),
            _gloss("Pole Position",
                   "Posisi start terdepan (P1) yang diraih melalui sesi kualifikasi tercepat."),
            _gloss("Fastest Lap",
                   "Lap time tercepat dalam satu balapan. Memberikan 1 poin bonus jika finis di Top 10."),
            _gloss("Pit Stop",
                   "Singgah ke pit lane untuk ganti ban dan/atau perbaikan komponen mobil."),
            _gloss("Constructor",
                   "Tim yang merancang dan memasok mobil F1 (contoh: Red Bull, Mercedes, Ferrari)."),
            _gloss("Sprint Race",
                   "Balapan pendek (~100 km) di beberapa sirkuit pilihan. Memberikan poin tambahan."),
            _gloss("Poin Kumulatif",
                   "Total poin yang terkumpul dari putaran pertama hingga putaran yang dipilih."),
            _gloss("Consistency Score",
                   "Skor 0–100 yang mencerminkan konsistensi pembalap meraih podium dan menyelesaikan balapan."),
            _gloss("Gap P1 vs P2",
                   "Selisih poin antara pemimpin klasemen dan runner-up setelah setiap putaran."),
            _gloss("DNF Rate (%)",
                   "Persentase balapan di mana pembalap atau tim tidak menyelesaikan balapan."),
        ], style=dict(maxHeight="60vh", overflowY="auto")),
        dbc.ModalFooter(
            html.Span("Klik ✕ atau di luar modal untuk menutup", style=dict(
                fontSize="10px", color="#94a3b8", fontFamily=F,
            ))
        ),
    ],
        id="help-modal",
        is_open=False,
        centered=True,
        size="lg",
        backdrop=True,
    )

# ── Layout ───────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id="store-page",   data="beranda"),
    dcc.Store(id="store-season",  data=None),
    dcc.Store(id="store-seasons", data=[]),
    dcc.Store(id="store-filter",
              data={"search": "", "drv": None, "con": None, "status": None}),
    dcc.Download(id="dl-beranda"),
    dcc.Download(id="dl-klasemen"),
    dcc.Download(id="dl-analitik"),
    dcc.Download(id="dl-tabel"),
    dcc.Download(id="dl-benchmark"),
    dcc.Store(id="store-bench-ts", data=0),
    dcc.Interval(id="bench-interval", interval=2000, n_intervals=0, disabled=True),
    html.Div([
        dcc.Input(id="sf-search", style=dict(display="none"), value=""),
        dcc.Dropdown(id="sf-drv", style=dict(display="none"), value=None),
        dcc.Dropdown(id="sf-con", style=dict(display="none"), value=None),
        dcc.Dropdown(id="sf-status", style=dict(display="none"), value=None),
        dcc.Dropdown(id="dd-season", style=dict(display="none"), value=None),
    ], id="sidebar-wrap"),
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

    # ── Floating Help Button [???] ──────────────────────────────────────────
    html.Button(
        "?",
        id="btn-help-open",
        n_clicks=0,
        title="Panduan & Glosarium F1",
        style=dict(
            position="fixed", bottom="24px", right="24px",
            width="44px", height="44px", borderRadius="50%",
            background=f"linear-gradient(135deg, {C['blue']}, #7C3AED)",
            color="#fff", border="none", cursor="pointer",
            fontSize="18px", fontWeight="900", fontFamily=F,
            boxShadow="0 4px 16px rgba(29,78,216,0.4)",
            zIndex="9999",
            lineHeight="44px", textAlign="center",
        ),
    ),

    # ── Help Modal ────────────────────────────────────────────────────
    _help_modal(),

], style=dict(background=C["bg"], minHeight="100vh", fontFamily=F))

# ── Navigation callback ───────────────────────────────────────────────────────
NAV_IDS = ["beranda", "klasemen", "analitik", "h2h", "tabel",
           "comparison", "benchmark", "tentang", "settings"]

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


# ── Help Modal callback ───────────────────────────────────────────────────────
@app.callback(
    Output("help-modal", "is_open"),
    Input("btn-help-open", "n_clicks"),
    State("help-modal",   "is_open"),
    prevent_initial_call=True,
)
def toggle_help(n, is_open):
    if n:
        return not is_open
    return is_open


# ── Season callback ───────────────────────────────────────────────────────────
@app.callback(
    Output("store-season",  "data"),
    Output("store-seasons", "data"),
    Input("dd-season", "value"),
    prevent_initial_call=True,
)
def season_change(val):
    """dd-season sekarang single-select. Kembalikan:
       store-season  = season aktif (int)
       store-seasons = list berisi season aktif tersebut [season] untuk multi-compat.
    """
    if not val:
        return None, []
    if isinstance(val, list):
        primary = val[0] if val else None
        return primary, val
    return val, [val]


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
    if trigger == "store-page":
        return {"search": "", "drv": None, "con": None, "status": None}
    if trigger == "store-season" and page != "tabel":
        return {"search": "", "drv": None, "con": None, "status": None}
    return {"search": search or "", "drv": drv, "con": con, "status": status}


# ── Sidebar callback ──────────────────────────────────────────────────────────
@app.callback(
    Output("sidebar-wrap", "children"),
    Input("store-page",   "data"),
    Input("store-seasons", "data"),
    Input("store-filter", "data"),
)
def render_sidebar(page, seasons_list, flt):
    # Pass seasons_list to make_sidebar
    return make_sidebar(page, seasons_list, SL, flt or {}, is_demo_mode())


# ── Page render callback ──────────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    Input("store-page",   "data"),
    Input("store-season", "data"),
    Input("store-filter", "data"),
)
def render_page(page, season, flt):
    flt = flt or {}
    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

    if page == "benchmark": return page_benchmark()
    if page == "tentang":   return page_about()
    if page == "settings":
        # Settings punya state internal — jangan re-render saat store-season/filter berubah
        if triggered in ("store-season", "store-filter"):
            return no_update
        return page_settings()
    if season is None:      return welcome_state()
    if page == "beranda":   return page_home(season, flt)
    if page == "klasemen":  return page_standings(season, flt)
    if page == "analitik":  return page_analytics(season, flt)
    if page == "h2h":       return page_h2h(season)
    if page == "comparison":
        # Comparison punya season selector internal — jangan re-render saat store-season berubah
        if triggered in ("store-season", "store-filter"):
            return no_update
        return page_comparison()
    if page == "tabel":
        # Halaman tabel punya filter dan tahun lokal — jangan re-render saat store-filter
        # atau store-season berubah (callback internal tabel yang handle)
        if triggered in ("store-filter", "store-season"):
            return no_update
        return page_datatable(season, {})
    return page_home(season, flt)


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

from services.data_service import get_analytics, get_constructor_season, get_calendar, get_qualifying, get_pit_stops

@app.callback(Output("dl-tabel", "data"),
    Input("btn-tabel", "n_clicks"),
    State("tabel-tabs", "value"),
    State("tbl-year-filter", "value"),
    prevent_initial_call=True)
def dl_tabel(n, tab, year):
    if not n or not year: return no_update
    year = int(year)
    if tab == "drv":
        df = get_analytics(year)
    elif tab == "con":
        df = get_constructor_season(year)
    elif tab == "cal":
        cal = get_calendar()
        df = cal[cal["season"] == year] if not cal.empty else pd.DataFrame()
    elif tab == "qua":
        df = get_qualifying(year)
    elif tab == "pit":
        df = get_pit_stops(year)
    else:
        df = pd.DataFrame()
        
    if df.empty: return no_update
    
    return dict(content=df.to_csv(index=False),
                filename=f"paceflow_{tab}_{year}.csv")


# ── Register callbacks dari pages ─────────────────────────────────────────────
reg_settings(app)
reg_home(app)
reg_analytics(app)
reg_h2h(app)
reg_datatable(app)
reg_standings(app)
reg_comparison(app)
reg_benchmark(app)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)