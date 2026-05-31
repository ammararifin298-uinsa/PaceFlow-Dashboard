# =============================================================================
# sidebar.py — Sidebar navigasi PaceFlow
# Berisi: make_sidebar() dengan dropdown season dinamis (OCP compliant)
# Filter per halaman di-render sesuai FILTER_PAGES mapping
# =============================================================================

from dash import html, dcc
from layout.design_tokens import C, F, rgba, tc
from layout.components import ico

NAV = [
    ("beranda",   "lucide:home",        "Beranda"),
    ("klasemen",  "lucide:bar-chart-2", "Klasemen"),
    ("analitik",  "lucide:activity",    "Analitik"),
    ("h2h",       "lucide:users",       "Head-to-Head"),
    ("tabel",     "lucide:table",       "Tabel Data"),
    ("benchmark", "lucide:zap",         "Benchmark"),
    ("tentang",   "lucide:info",        "Tentang"),
]

# Filter yang aktif per halaman
FILTER_PAGES = {
    "beranda":  ["search", "drv", "con"],
    "klasemen": ["search"],
    "analitik": ["drv"],
    "tabel":    ["search", "status"],
}


def make_sidebar(page, season, seasons, flt, use_demo=False):
    """
    Render sidebar dengan:
    - Dropdown season dinamis (OCP — auto tambah jika dataset baru)
    - Filter kontekstual per halaman
    - Navigation aktif
    """
    import pandas as pd
    flt = flt or {}
    season_ok = season is not None
    active_f = FILTER_PAGES.get(page, [])

    def _hidden_filters():
        return html.Div([
            dcc.Input(id="sf-search", style=dict(display="none"), value=""),
            dcc.Dropdown(id="sf-drv", style=dict(display="none"), value=None),
            dcc.Dropdown(id="sf-con", style=dict(display="none"), value=None),
            dcc.Dropdown(id="sf-status", style=dict(display="none"), value=None),
        ], style=dict(display="none"))

    def flt_input(df_s):
        drv_opts = ([{"label": d, "value": d}
                     for d in sorted(df_s["driver_name"].dropna().unique())]
                    if not df_s.empty else [])
        con_opts = ([{"label": c, "value": c}
                     for c in sorted(df_s["constructor"].dropna().unique())]
                    if not df_s.empty else [])
        st_opts  = ([{"label": s, "value": s}
                     for s in sorted(df_s["status"].dropna().unique())]
                    if not df_s.empty else [])

        if not season_ok or not active_f:
            return html.Div([
                html.Div(style=dict(borderTop="1px solid #1E293B", margin="0 0 8px")),
                html.Div("FILTER", style=dict(
                    fontSize="9px", fontWeight="700", letterSpacing="2px",
                    color=C["s_muted"], marginBottom="6px",
                    fontFamily=F, padding="0 16px"
                )),
                html.Div(
                    "Pilih musim terlebih dahulu" if not season_ok else "Tidak ada filter",
                    style=dict(fontSize="11px", color=C["s_muted"],
                               fontFamily=F, padding="0 16px 8px", fontStyle="italic")
                ),
                _hidden_filters(),
            ])

        items = [
            html.Div(style=dict(borderTop="1px solid #1E293B", margin="0 0 8px")),
            html.Div("FILTER", style=dict(
                fontSize="9px", fontWeight="700", letterSpacing="2px",
                color=C["s_muted"], marginBottom="8px",
                fontFamily=F, padding="0 16px"
            )),
        ]

        if "search" in active_f:
            items.append(html.Div([
                ico("lucide:search", 13, C["s_muted"]),
                dcc.Input(id="sf-search", type="text",
                    placeholder="Cari driver / race...",
                    value=flt.get("search", "") or "",
                    debounce=True,
                    style=dict(border="none", outline="none",
                               background="transparent", fontSize="11px",
                               color=C["s_text"], fontFamily=F,
                               width="100%", marginLeft="6px")),
            ], style=dict(display="flex", alignItems="center",
                          background="#1E293B", borderRadius="6px",
                          padding="7px 10px", margin="0 16px 8px")))
        else:
            items.append(html.Div(
                dcc.Input(id="sf-search", style=dict(display="none"), value=""),
                style=dict(display="none")))

        if "drv" in active_f:
            items.append(html.Div(
                dcc.Dropdown(id="sf-drv", options=drv_opts,
                    value=flt.get("drv"), placeholder="Semua Driver",
                    multi=True, clearable=True, style=dict(fontSize="11px")),
                style=dict(padding="0 16px 8px")))
        else:
            items.append(html.Div(
                dcc.Dropdown(id="sf-drv", style=dict(display="none"), value=None),
                style=dict(display="none")))

        if "con" in active_f:
            items.append(html.Div(
                dcc.Dropdown(id="sf-con", options=con_opts,
                    value=flt.get("con"), placeholder="Semua Konstruktor",
                    multi=True, clearable=True, style=dict(fontSize="11px")),
                style=dict(padding="0 16px 8px")))
        else:
            items.append(html.Div(
                dcc.Dropdown(id="sf-con", style=dict(display="none"), value=None),
                style=dict(display="none")))

        if "status" in active_f:
            items.append(html.Div(
                dcc.Dropdown(id="sf-status", options=st_opts,
                    value=flt.get("status"), placeholder="Semua Status",
                    multi=True, clearable=True, style=dict(fontSize="11px")),
                style=dict(padding="0 16px 8px")))
        else:
            items.append(html.Div(
                dcc.Dropdown(id="sf-status", style=dict(display="none"), value=None),
                style=dict(display="none")))

        return html.Div(items)

    # Ambil data untuk filter options
    from services.data_service import get_analytics
    df_s = get_analytics(season) if season_ok else pd.DataFrame()

    # Season dropdown — dinamis dari DB, OCP compliant
    season_opts = [{"label": f"Musim {s}", "value": s} for s in seasons]

    return html.Div([
        # Logo
        html.Div([
            html.Div([
                ico("lucide:gauge", 22, "#FFF"),
                html.Span("PaceFlow", style=dict(
                    fontSize="20px", fontWeight="900",
                    color="#FFF", fontFamily=F, marginLeft="10px"
                ))],
                style=dict(display="flex", alignItems="center")),
            html.Div("F1 Relational Analytics", style=dict(
                fontSize="10px", color=C["s_muted"], fontFamily=F, marginTop="3px"
            )),
        ], style=dict(padding="20px 16px 14px", borderBottom="1px solid #1E293B")),

        # DB status
        html.Div([
            html.Div(style=dict(
                width="7px", height="7px", borderRadius="50%",
                background=C["green"] if not use_demo else C["orange"],
                marginRight="8px", flexShrink="0"
            )),
            html.Span(
                "PostgreSQL Terhubung" if not use_demo else "Mode Demo",
                style=dict(fontSize="11px", color=C["s_muted"], fontFamily=F)
            ),
        ], style=dict(display="flex", alignItems="center",
                      padding="8px 16px", borderBottom="1px solid #1E293B")),

        # Navigation
        html.Div([
            html.Div([
                ico(ic, 15, "#FFF" if page == pid else C["s_muted"]),
                html.Span(lb, style=dict(
                    marginLeft="10px", fontSize="13px",
                    fontWeight="600" if page == pid else "400",
                    color="#FFF" if page == pid else C["s_text"],
                    fontFamily=F
                )),
            ], id={"type": "nav", "index": pid}, n_clicks=0,
            style=dict(
                display="flex", alignItems="center",
                padding="9px 14px", borderRadius="8px",
                cursor="pointer", marginBottom="2px",
                background=C["s_active"] if page == pid else "transparent"
            ))
            for pid, ic, lb in NAV
        ], style=dict(padding="10px 8px")),

        html.Div(style=dict(borderTop="1px solid #1E293B", margin="4px 0")),

        # Season dropdown — BARU, dinamis, OCP compliant
        html.Div([
            html.Div("MUSIM", style=dict(
                fontSize="9px", fontWeight="700", letterSpacing="2px",
                color=C["s_muted"], marginBottom="8px", fontFamily=F
            )),
            dcc.Dropdown(
                id="dd-season",
                options=season_opts,
                value=season,
                clearable=False,
                searchable=False,
                placeholder="Pilih musim...",
                style=dict(fontSize="12px", color=C["text"]),
            ),
        ], style=dict(padding="0 16px 10px")),

        # Filter section
        flt_input(df_s),

        # Footer
        html.Div([
            html.Div("Arsitektur: SoC · ISO/IEC 25010",
                style=dict(fontSize="9px", color="#334155", fontFamily=F, lineHeight="1.9")),
            html.Div("PostgreSQL → Dash → Plotly",
                style=dict(fontSize="9px", color="#334155", fontFamily=F)),
        ], style=dict(padding="8px 16px 20px", marginTop="auto")),

    ], style=dict(
        width="220px", minWidth="220px", background=C["sidebar"],
        height="100vh", position="fixed", top=0, left=0,
        display="flex", flexDirection="column",
        overflowY="auto", zIndex=100
    ))