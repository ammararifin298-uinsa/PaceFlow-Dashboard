"""
=============================================================================
PaceFlow — F1 Relational Analytics Dashboard
=============================================================================
Stack     : PostgreSQL → SQLAlchemy → Dash + Plotly
Tema      : Dark theme, Inter font, Lucide icons
Bahasa    : Bahasa Indonesia
=============================================================================
"""

import os
import sys
import json

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify

sys.path.insert(0, os.path.dirname(__file__))
from config import TEAM_COLORS, DEFAULT_TEAM_COLOR, DEMO_MODE
import demo_data as demo

# ─────────────────────────────────────────────────────────────────────────────
# DATA PROVIDER
# ─────────────────────────────────────────────────────────────────────────────
_use_demo = DEMO_MODE
if not _use_demo:
    try:
        import db
        db.get_seasons()
    except Exception:
        _use_demo = True

def get_data(fn_demo, fn_db, *args):
    try:
        return fn_demo(*args) if _use_demo else fn_db(*args)
    except Exception as e:
        print(f"Data error: {e}")
        return pd.DataFrame()

def get_seasons():
    return get_data(demo.get_seasons, db.get_seasons)

def get_analytics(season):
    return get_data(demo.get_analytics, db.get_analytics, season)

def get_kpi(season):
    return get_data(demo.get_kpi, db.get_kpi, season)

def get_constructor(season):
    return get_data(demo.get_constructor_season, db.get_constructor_season, season)

def team_color(name):
    return TEAM_COLORS.get(name, DEFAULT_TEAM_COLOR)

# ─────────────────────────────────────────────────────────────────────────────
# APP INIT
# ─────────────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="PaceFlow — F1 Analytics",
)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":        "#0F0F13",
    "card":      "#1A1A2E",
    "sidebar":   "#111118",
    "border":    "#2D2D44",
    "red":       "#E10600",
    "teal":      "#00D2BE",
    "text":      "#FFFFFF",
    "muted":     "#9BA3AF",
    "green":     "#00C853",
    "orange":    "#FF8000",
    "yellow":    "#FFD700",
}

FONT = "Inter, -apple-system, sans-serif"

CHART_LAYOUT = dict(
    paper_bgcolor=C["card"],
    plot_bgcolor=C["card"],
    font=dict(family=FONT, color=C["text"], size=11),
)

# Default axis style — gunakan di setiap update_layout
AXIS_STYLE = dict(gridcolor=C["border"], zerolinecolor=C["border"],
                  linecolor=C["border"], tickfont=dict(size=10))
MARGIN_DEFAULT = dict(l=40, r=20, t=30, b=40)

LEGEND_H = dict(
    orientation="h", y=-0.15, x=0,
    bgcolor="rgba(0,0,0,0)",
    font=dict(size=10, color=C["muted"])
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def icon(name, size=18, color=C["muted"]):
    return DashIconify(icon=name, width=size, height=size, color=color)

def card(children, style=None):
    base = dict(
        background=C["card"],
        border=f"1px solid {C['border']}",
        borderRadius="10px",
        padding="20px",
        marginBottom="16px",
    )
    if style:
        base.update(style)
    return html.Div(children, style=base)

def sec_header(title):
    return html.Div(title, style=dict(
        fontSize="10px", fontWeight="700",
        letterSpacing="2px", textTransform="uppercase",
        color=C["red"], borderBottom=f"1px solid {C['border']}",
        paddingBottom="8px", marginBottom="14px", marginTop="20px",
        fontFamily=FONT,
    ))

def insight_box(text):
    return html.Div(
        dcc.Markdown(text, dangerously_allow_html=False),
        style=dict(
            background="#1E1E3A",
            borderLeft=f"3px solid {C['teal']}",
            borderRadius="0 6px 6px 0",
            padding="10px 16px",
            marginBottom="14px",
            fontSize="12px",
            color=C["muted"],
            lineHeight="1.7",
            fontFamily=FONT,
        )
    )

def kpi_card(label, value, sub, color=C["red"], icon_name=None):
    return html.Div([
        html.Div(style=dict(
            position="absolute", top=0, left=0, right=0, height="3px",
            background=color, borderRadius="10px 10px 0 0"
        )),
        html.Div([
            icon(icon_name, size=14, color=C["muted"]) if icon_name else None,
            html.Span(label, style=dict(
                fontSize="10px", fontWeight="700", letterSpacing="1.5px",
                textTransform="uppercase", color=C["muted"],
                marginLeft="6px", fontFamily=FONT,
            )),
        ], style=dict(display="flex", alignItems="center", marginBottom="10px")),
        html.Div(str(value), style=dict(
            fontSize="28px", fontWeight="800", color=C["text"],
            lineHeight="1.1", fontFamily=FONT,
            fontVariantNumeric="tabular-nums",
        )),
        html.Div(sub, style=dict(
            fontSize="11px", color=color,
            marginTop="6px", fontFamily=FONT,
        )),
    ], style=dict(
        background=C["card"],
        border=f"1px solid {C['border']}",
        borderRadius="10px",
        padding="18px 20px",
        position="relative",
        overflow="hidden",
    ))

def export_btn(btn_id, label="Unduh Data CSV"):
    return html.Div([
        dcc.Download(id=f"dl-{btn_id}"),
        dbc.Button([
            icon("lucide:download", size=14, color="#fff"),
            html.Span(label, style=dict(marginLeft="6px")),
        ],
        id=f"btn-{btn_id}",
        size="sm",
        style=dict(
            background=C["border"],
            border=f"1px solid {C['border']}",
            color=C["muted"],
            fontSize="11px",
            borderRadius="6px",
            padding="6px 14px",
            fontFamily=FONT,
            cursor="pointer",
        )),
    ], style=dict(marginTop="12px", textAlign="right"))

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("beranda",    "lucide:flag",         "Beranda"),
    ("klasemen",   "lucide:bar-chart-2",  "Klasemen"),
    ("analitik",   "lucide:activity",     "Analitik"),
    ("h2h",        "lucide:users",        "Head-to-Head"),
    ("tabel",      "lucide:table",        "Tabel Data"),
    ("benchmark",  "lucide:zap",          "Benchmark"),
    ("sus",        "lucide:clipboard-list","Evaluasi SUS"),
]

def make_nav_item(page_id, icon_name, label, active_page):
    is_active = active_page == page_id
    return html.Div([
        icon(icon_name, size=16,
             color=C["text"] if is_active else C["muted"]),
        html.Span(label, style=dict(
            marginLeft="10px", fontSize="13px", fontWeight="600" if is_active else "400",
            color=C["text"] if is_active else C["muted"],
            fontFamily=FONT,
        )),
    ],
    id={"type": "nav-item", "index": page_id},
    n_clicks=0,
    style=dict(
        display="flex", alignItems="center",
        padding="10px 16px", borderRadius="8px", cursor="pointer",
        background=C["red"] if is_active else "transparent",
        marginBottom="4px",
        transition="all 0.2s",
    ))

def make_sidebar(active_page, seasons, sel_season):
    return html.Div([
        # Logo
        html.Div([
            html.Div("PaceFlow", style=dict(
                fontSize="20px", fontWeight="900",
                color=C["text"], fontFamily=FONT,
                letterSpacing="-0.5px",
            )),
            html.Div("F1 Relational Analytics", style=dict(
                fontSize="10px", color=C["muted"],
                fontFamily=FONT, marginTop="2px",
                letterSpacing="0.5px",
            )),
        ], style=dict(padding="20px 16px 16px", borderBottom=f"1px solid {C['border']}")),

        # Status DB
        html.Div([
            html.Div(style=dict(
                width="7px", height="7px", borderRadius="50%",
                background=C["green"] if not _use_demo else C["orange"],
                marginRight="8px",
            )),
            html.Span(
                "PostgreSQL Terhubung" if not _use_demo else "Demo Mode",
                style=dict(fontSize="11px", color=C["muted"], fontFamily=FONT)
            ),
        ], style=dict(display="flex", alignItems="center", padding="10px 16px")),

        html.Hr(style=dict(borderColor=C["border"], margin="4px 0 8px")),

        # Navigation
        html.Div([
            make_nav_item(pid, ic, lb, active_page)
            for pid, ic, lb in NAV_ITEMS
        ], style=dict(padding="0 8px")),

        html.Hr(style=dict(borderColor=C["border"], margin="8px 0")),

        # Season selector
        html.Div([
            html.Div("MUSIM", style=dict(
                fontSize="10px", fontWeight="700", letterSpacing="1.5px",
                color=C["muted"], marginBottom="8px", fontFamily=FONT,
            )),
            html.Div([
                html.Div(
                    str(s),
                    id={"type": "season-btn", "index": s},
                    n_clicks=0,
                    style=dict(
                        padding="6px 14px", borderRadius="6px", cursor="pointer",
                        fontSize="12px", fontWeight="700", fontFamily=FONT,
                        background=C["red"] if s == sel_season else C["border"],
                        color=C["text"],
                        border=f"1px solid {C['red'] if s == sel_season else C['border']}",
                        marginRight="6px",
                    )
                ) for s in seasons
            ], style=dict(display="flex", flexWrap="wrap", gap="4px")),
        ], style=dict(padding="0 16px 16px")),

        # Info
        html.Div([
            html.Div("Arsitektur: SoC (ISO/IEC 25010)", style=dict(
                fontSize="9px", color="#44446A", fontFamily=FONT, lineHeight="1.8")),
            html.Div("Stack: PostgreSQL → Dash → Plotly", style=dict(
                fontSize="9px", color="#44446A", fontFamily=FONT)),
        ], style=dict(padding="0 16px", marginTop="auto")),

    ], style=dict(
        width="240px", minWidth="240px",
        background=C["sidebar"],
        borderRight=f"1px solid {C['border']}",
        height="100vh", position="fixed", top=0, left=0,
        display="flex", flexDirection="column",
        overflowY="auto",
        zIndex=100,
    ))

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: BERANDA (Championship)
# ─────────────────────────────────────────────────────────────────────────────
def page_beranda(season):
    df = get_analytics(season)
    kpi = get_kpi(season)
    df_c = get_constructor(season)

    if df.empty:
        return html.Div("Tidak ada data.", style=dict(color=C["muted"]))

    # KPI values
    latest = df.sort_values("round", ascending=False).drop_duplicates("driver_id")
    top2 = latest.nlargest(2, "cumulative_points")
    gap = 0.0
    if len(top2) >= 2:
        gap = float(top2.iloc[0]["cumulative_points"]) - float(top2.iloc[1]["cumulative_points"])

    leader     = str(kpi.get("points_leader", "—"))
    leader_pts = float(kpi.get("leader_points", 0) or 0)
    avg_pit    = kpi.get("season_avg_pit_s")
    dnf_count  = int(kpi.get("total_dnf", 0) or 0)
    total_entries = int(kpi.get("total_entries", len(df)) or len(df))
    dnf_rate   = f"{dnf_count/total_entries*100:.1f}%" if total_entries > 0 else "N/A"
    total_races= int(kpi.get("total_races", df["race_name"].nunique()) or 0)
    n_drivers  = int(kpi.get("total_drivers", df["driver_id"].nunique()) or 0)
    pit_display= f"{float(avg_pit):.3f}d" if avg_pit else "N/A"

    # Championship line chart
    trend = (df.groupby(["driver_name","round","race_name","constructor"], as_index=False)
             ["cumulative_points"].max().sort_values(["driver_name","round"]))

    fig_trend = go.Figure()
    for driver in trend["driver_name"].unique():
        d = trend[trend["driver_name"]==driver].sort_values("round")
        color = team_color(d["constructor"].iloc[0] if not d.empty else "")
        fig_trend.add_trace(go.Scatter(
            x=d["round"], y=d["cumulative_points"],
            mode="lines+markers", name=driver,
            line=dict(width=2, color=color),
            marker=dict(size=5, color=color),
            customdata=d["race_name"],
            hovertemplate=f"<b>{driver}</b><br>Round %{{x}} — %{{customdata}}<br>Poin: <b>%{{y}}</b><extra></extra>",
        ))
    fig_trend.update_layout(
        **CHART_LAYOUT, height=400,
        legend=LEGEND_H,
        xaxis=dict(title="Putaran", gridcolor=C["border"], dtick=2,
                   tickfont=dict(size=10), linecolor=C["border"]),
        yaxis=dict(title="Poin Kumulatif", gridcolor=C["border"],
                   tickfont=dict(size=10), linecolor=C["border"]),
        hovermode="x unified",
    )

    # Constructor bar
    df_cs = df_c.sort_values("total_points")
    fig_cbar = go.Figure(go.Bar(
        y=df_cs["constructor"],
        x=df_cs["total_points"],
        orientation="h",
        marker_color=[team_color(t) for t in df_cs["constructor"]],
        text=df_cs["total_points"].astype(int),
        textposition="outside",
        textfont=dict(color=C["text"], size=10),
        hovertemplate="<b>%{y}</b><br>Poin: %{x}<extra></extra>",
    ))
    fig_cbar.update_layout(
        **CHART_LAYOUT, height=300, showlegend=False,
        xaxis=dict(title="Total Poin", gridcolor=C["border"],
                   linecolor=C["border"], tickfont=dict(size=10)),
        yaxis=dict(gridcolor=C["border"], linecolor=C["border"],
                   tickfont=dict(size=10)),
        margin=dict(l=10, r=60, t=10, b=30),
    )

    # Constructor table
    tbl_data = df_c[["constructor","total_wins","total_podiums","total_points","avg_pit_s"]].copy()
    tbl_data.columns = ["Konstruktor","Menang","Podium","Poin","Avg Pit (d)"]
    tbl_data["Avg Pit (d)"] = tbl_data["Avg Pit (d)"].round(2)
    tbl_rows = [
        html.Tr([
            html.Td([
                html.Div(style=dict(
                    width="3px", height="16px", borderRadius="2px",
                    background=team_color(row["Konstruktor"]),
                    display="inline-block", marginRight="8px",
                    verticalAlign="middle",
                )),
                html.Span(row["Konstruktor"], style=dict(
                    color=C["text"], fontSize="12px", fontFamily=FONT, fontWeight="500"
                )),
            ], style=dict(padding="10px 12px")),
            html.Td(str(int(row["Menang"])), style=dict(
                color=C["yellow"], fontSize="12px", fontWeight="700",
                textAlign="center", padding="10px 12px", fontFamily=FONT,
            )),
            html.Td(str(int(row["Podium"])), style=dict(
                color=C["teal"], fontSize="12px", fontWeight="600",
                textAlign="center", padding="10px 12px", fontFamily=FONT,
            )),
            html.Td(str(int(row["Poin"])), style=dict(
                color=C["text"], fontSize="12px", fontWeight="700",
                textAlign="center", padding="10px 12px", fontFamily=FONT,
            )),
            html.Td(str(row["Avg Pit (d)"]), style=dict(
                color=C["muted"], fontSize="11px",
                textAlign="center", padding="10px 12px", fontFamily=FONT,
            )),
        ], style=dict(borderBottom=f"1px solid {C['border']}"))
        for _, row in tbl_data.iterrows()
    ]

    return html.Div([
        # KPI Cards
        sec_header("Indikator Kinerja Utama"),
        dbc.Row([
            dbc.Col(kpi_card("Pemimpin Klasemen", leader,
                             f"▲ {leader_pts:.0f} poin · Gap +{gap:.0f} vs P2",
                             C["red"], "lucide:trophy"), width=3),
            dbc.Col(kpi_card("Rata-rata Pit Stop", pit_display,
                             "Rata-rata musim (red flag diabaikan)",
                             C["teal"], "lucide:timer"), width=3),
            dbc.Col(kpi_card("Tingkat DNF", dnf_rate,
                             f"{dnf_count} pensiun dari {total_entries} start",
                             C["orange"], "lucide:circle-x"), width=3),
            dbc.Col(kpi_card("Statistik Musim", f"{total_races} Balapan",
                             f"{n_drivers} pembalap · {int(kpi.get('total_constructors',0))} konstruktor",
                             C["yellow"], "lucide:flag"), width=3),
        ], className="g-3"),

        # Championship chart
        sec_header("Perkembangan Poin Championship"),
        insight_box(f"**{leader}** memimpin dengan **{leader_pts:.0f} poin**. Gap ke P2: **+{gap:.0f} poin**."),
        card(dcc.Graph(figure=fig_trend, config=dict(displayModeBar=False))),

        # Constructor section
        sec_header("Klasemen Konstruktor"),
        dbc.Row([
            dbc.Col(card(dcc.Graph(figure=fig_cbar, config=dict(displayModeBar=False))), width=7),
            dbc.Col(card(html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(col, style=dict(
                            color=C["muted"], fontSize="10px", fontWeight="700",
                            letterSpacing="1px", textTransform="uppercase",
                            padding="8px 12px", textAlign="center" if i > 0 else "left",
                            fontFamily=FONT, borderBottom=f"1px solid {C['border']}",
                        )) for i, col in enumerate(["Konstruktor","W","P","Pts","Pit"])
                    ])),
                    html.Tbody(tbl_rows),
                ], style=dict(width="100%", borderCollapse="collapse")),
            ])), width=5),
        ], className="g-3"),

        export_btn("championship"),
        dcc.Store(id="store-championship", data=trend.to_dict("records")),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: KLASEMEN
# ─────────────────────────────────────────────────────────────────────────────
def page_klasemen(season):
    df = get_analytics(season)
    df_c = get_constructor(season)

    if df.empty:
        return html.Div("Tidak ada data.", style=dict(color=C["muted"]))

    # Driver standings - ambil round terakhir
    latest = (df.sort_values("round", ascending=False)
              .drop_duplicates("driver_id")
              .sort_values("championship_pos"))

    # Driver bar chart
    latest_top = latest.head(20)
    fig_drv = go.Figure()
    for _, row in latest_top.iterrows():
        fig_drv.add_trace(go.Bar(
            y=[row["driver_name"]],
            x=[row["cumulative_points"]],
            orientation="h",
            marker_color=team_color(row["constructor"]),
            showlegend=False,
            hovertemplate=f"<b>{row['driver_name']}</b><br>{row['constructor']}<br>Poin: <b>{row['cumulative_points']:.0f}</b><extra></extra>",
        ))
    fig_drv.update_layout(
        **CHART_LAYOUT, height=520, showlegend=False,
        barmode="overlay",
        xaxis=dict(title="Poin Kumulatif", gridcolor=C["border"], linecolor=C["border"]),
        yaxis=dict(gridcolor=C["border"], linecolor=C["border"],
                   categoryorder="total ascending", tickfont=dict(size=10)),
        margin=dict(l=10, r=40, t=10, b=30),
    )

    # Constructor bar
    df_cs = df_c.sort_values("total_points", ascending=True)
    fig_con = go.Figure()
    for _, row in df_cs.iterrows():
        fig_con.add_trace(go.Bar(
            y=[row["constructor"]],
            x=[row["total_points"]],
            orientation="h",
            marker_color=team_color(row["constructor"]),
            showlegend=False,
            hovertemplate=f"<b>{row['constructor']}</b><br>Poin: <b>{row['total_points']:.0f}</b><extra></extra>",
        ))
    fig_con.update_layout(
        **CHART_LAYOUT, height=320, showlegend=False,
        barmode="overlay",
        xaxis=dict(title="Total Poin", gridcolor=C["border"], linecolor=C["border"]),
        yaxis=dict(gridcolor=C["border"], linecolor=C["border"],
                   tickfont=dict(size=10)),
        margin=dict(l=10, r=40, t=10, b=30),
    )

    # Driver standings table
    def drv_tbl_rows(data):
        rows = []
        for _, row in data.iterrows():
            pos = int(row.get("championship_pos", 0) or 0)
            pos_color = C["yellow"] if pos == 1 else C["teal"] if pos <= 3 else C["text"]
            rows.append(html.Tr([
                html.Td(str(pos), style=dict(
                    color=pos_color, fontWeight="800", fontSize="14px",
                    textAlign="center", padding="10px 8px", fontFamily=FONT,
                )),
                html.Td([
                    html.Div(style=dict(
                        width="3px", height="20px", borderRadius="2px",
                        background=team_color(row["constructor"]),
                        display="inline-block", marginRight="8px",
                        verticalAlign="middle",
                    )),
                    html.Div([
                        html.Div(row["driver_name"], style=dict(
                            color=C["text"], fontSize="13px",
                            fontWeight="600", fontFamily=FONT,
                        )),
                        html.Div(str(row.get("driver_code",""))[:3], style=dict(
                            color=C["muted"], fontSize="10px",
                            fontFamily=FONT,
                        )),
                    ], style=dict(display="inline-block", verticalAlign="middle")),
                ], style=dict(padding="8px 12px")),
                html.Td(row["constructor"], style=dict(
                    color=C["muted"], fontSize="11px",
                    padding="8px 12px", fontFamily=FONT,
                )),
                html.Td(f"{row['cumulative_points']:.0f}", style=dict(
                    color=C["text"], fontSize="14px", fontWeight="800",
                    textAlign="center", padding="8px 12px", fontFamily=FONT,
                )),
                html.Td(str(int(row.get("cumulative_wins",0) or 0)), style=dict(
                    color=C["yellow"], fontSize="12px", fontWeight="700",
                    textAlign="center", padding="8px 12px", fontFamily=FONT,
                )),
            ], style=dict(borderBottom=f"1px solid {C['border']}",
                          background=C["red"]+"22" if pos == 1 else "transparent")))
        return rows

    return html.Div([
        sec_header("Klasemen Pembalap"),
        dbc.Row([
            dbc.Col(card(dcc.Graph(figure=fig_drv, config=dict(displayModeBar=False))), width=5),
            dbc.Col(card(html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(col, style=dict(
                            color=C["muted"], fontSize="10px", fontWeight="700",
                            letterSpacing="1px", textTransform="uppercase",
                            padding="8px 12px",
                            textAlign="center" if i in [0,3,4] else "left",
                            fontFamily=FONT, borderBottom=f"1px solid {C['border']}",
                        )) for i, col in enumerate(["#","Pembalap","Tim","Pts","W"])
                    ])),
                    html.Tbody(drv_tbl_rows(latest)),
                ], style=dict(width="100%", borderCollapse="collapse")),
            ], style=dict(overflowY="auto", maxHeight="500px"))), width=7),
        ], className="g-3"),

        sec_header("Klasemen Konstruktor"),
        dbc.Row([
            dbc.Col(card(dcc.Graph(figure=fig_con, config=dict(displayModeBar=False))), width=6),
            dbc.Col(card(html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(col, style=dict(
                            color=C["muted"], fontSize="10px", fontWeight="700",
                            letterSpacing="1px", textTransform="uppercase",
                            padding="8px 12px",
                            textAlign="center" if i > 0 else "left",
                            fontFamily=FONT, borderBottom=f"1px solid {C['border']}",
                        )) for i, col in enumerate(["Konstruktor","Poin","Menang","Podium"])
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td([
                                html.Div(style=dict(
                                    width="3px", height="16px", borderRadius="2px",
                                    background=team_color(row["constructor"]),
                                    display="inline-block", marginRight="8px",
                                    verticalAlign="middle",
                                )),
                                html.Span(row["constructor"], style=dict(
                                    color=C["text"], fontSize="12px",
                                    fontWeight="600", fontFamily=FONT,
                                )),
                            ], style=dict(padding="10px 12px")),
                            html.Td(str(int(row["total_points"])), style=dict(
                                color=C["text"], fontWeight="800", fontSize="13px",
                                textAlign="center", padding="10px 12px", fontFamily=FONT,
                            )),
                            html.Td(str(int(row["total_wins"])), style=dict(
                                color=C["yellow"], fontWeight="700", fontSize="12px",
                                textAlign="center", padding="10px 12px", fontFamily=FONT,
                            )),
                            html.Td(str(int(row["total_podiums"])), style=dict(
                                color=C["teal"], fontWeight="600", fontSize="12px",
                                textAlign="center", padding="10px 12px", fontFamily=FONT,
                            )),
                        ], style=dict(borderBottom=f"1px solid {C['border']}"))
                        for _, row in df_c.sort_values("total_points", ascending=False).iterrows()
                    ]),
                ], style=dict(width="100%", borderCollapse="collapse")),
            ])), width=6),
        ], className="g-3"),

        export_btn("klasemen"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ANALITIK (Pit Strategy + Speed)
# ─────────────────────────────────────────────────────────────────────────────
def page_analitik(season):
    df = get_analytics(season)
    if df.empty:
        return html.Div("Tidak ada data.", style=dict(color=C["muted"]))

    # Pit heatmap
    df_pit = df[["driver_name","round","best_pit_duration_s"]].dropna(subset=["best_pit_duration_s"])
    fig_hm = go.Figure()
    if not df_pit.empty:
        pivot = df_pit.pivot_table(index="driver_name", columns="round",
                                    values="best_pit_duration_s", aggfunc="min")
        fig_hm = go.Figure(go.Heatmap(
            z=pivot.values,
            x=[f"R{c}" for c in pivot.columns],
            y=pivot.index.tolist(),
            colorscale=[[0, C["teal"]], [0.5, C["yellow"]], [1, C["red"]]],
            text=np.round(pivot.values, 2),
            texttemplate="%{text}d",
            textfont=dict(size=8),
            hoverongaps=False,
            hovertemplate="<b>%{y}</b> — %{x}<br>Pit Terbaik: <b>%{z:.3f}d</b><extra></extra>",
            colorbar=dict(
                title=dict(text="Dur (d)", side="right"),
                tickfont=dict(size=9, color=C["muted"]),
                title_font=dict(size=10, color=C["muted"]),
            ),
        ))
        fig_hm.update_layout(**CHART_LAYOUT, height=380,
            margin=dict(l=10, r=20, t=10, b=20),
            xaxis=dict(**AXIS_STYLE), yaxis=dict(**AXIS_STYLE))

    # Pit box plot
    df_box = df[["driver_name","constructor","avg_pit_duration_s"]].dropna(subset=["avg_pit_duration_s"])
    fig_box = go.Figure()
    if not df_box.empty:
        order = (df_box.groupby("driver_name")["avg_pit_duration_s"]
                 .median().sort_values().index.tolist())
        for drv in order:
            d = df_box[df_box["driver_name"]==drv]
            color = team_color(d["constructor"].iloc[0] if not d.empty else "")
            fig_box.add_trace(go.Box(
                y=d["avg_pit_duration_s"], name=drv[:12],
                marker_color=color, line_color=color,
                boxmean="sd", showlegend=False,
                hovertemplate=f"<b>{drv}</b><br>Pit: %{{y:.3f}}d<extra></extra>",
            ))
        fig_box.update_layout(**CHART_LAYOUT, height=340, showlegend=False,
            yaxis=dict(title="Durasi Pit (d)", gridcolor=C["border"]),
            xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
            margin=dict(l=40, r=20, t=10, b=80))

    # Speed trend
    speed_df = (df.dropna(subset=["avg_speed_kph"])
                .groupby(["constructor","race_name","round"])["avg_speed_kph"]
                .mean().reset_index().sort_values("round"))
    fig_spd = go.Figure()
    if not speed_df.empty:
        for team in speed_df["constructor"].unique():
            d = speed_df[speed_df["constructor"]==team].sort_values("round")
            color = team_color(team)
            fig_spd.add_trace(go.Scatter(
                x=d["round"], y=d["avg_speed_kph"],
                mode="lines+markers", name=team,
                line=dict(width=2, color=color),
                marker=dict(size=5, color=color),
                customdata=d["race_name"],
                hovertemplate=f"<b>{team}</b><br>%{{customdata}}<br>Kecepatan: %{{y:.1f}} km/h<extra></extra>",
            ))
        fig_spd.update_layout(**CHART_LAYOUT, height=340,
            legend=LEGEND_H,
            xaxis=dict(title="Putaran", dtick=2, gridcolor=C["border"]),
            yaxis=dict(title="Kecepatan Rata-rata (km/h)", gridcolor=C["border"]),
            hovermode="x unified",
        )

    # Qualifying vs Race scatter
    df_qvr = df[["driver_name","constructor","qualifying_pos","position",
                 "race_name"]].dropna(subset=["qualifying_pos","position"])
    fig_qvr = go.Figure()
    if not df_qvr.empty:
        for team in df_qvr["constructor"].unique():
            d = df_qvr[df_qvr["constructor"]==team]
            color = team_color(team)
            fig_qvr.add_trace(go.Scatter(
                x=d["qualifying_pos"], y=d["position"],
                mode="markers", name=team,
                marker=dict(size=7, color=color, opacity=0.75),
                customdata=d[["driver_name","race_name"]].values,
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Kualifikasi: %{x} → Finish: %{y}<extra></extra>",
            ))
        max_pos = int(df_qvr[["qualifying_pos","position"]].max().max())
        fig_qvr.add_shape(type="line", x0=1, y0=1, x1=max_pos, y1=max_pos,
                          line=dict(color=C["red"], dash="dash", width=1.5))
        fig_qvr.add_annotation(x=max_pos*0.7, y=max_pos*0.5,
                                text="Balapan Sempurna", showarrow=False,
                                font=dict(color=C["red"], size=10, family=FONT))
        fig_qvr.update_layout(**CHART_LAYOUT, height=340,
            legend=LEGEND_H,
            xaxis=dict(title="Posisi Kualifikasi", dtick=2, gridcolor=C["border"]),
            yaxis=dict(title="Posisi Finish", dtick=2, autorange="reversed",
                       gridcolor=C["border"]),
        )

    # Pit heatmap insight
    best_pit_text = ""
    if not df_pit.empty:
        best_row = df_pit.loc[df_pit["best_pit_duration_s"].idxmin()]
        best_pit_text = f"**{best_row['driver_name']}** mencatat pit stop tercepat: **{best_row['best_pit_duration_s']:.3f}d** (Putaran {int(best_row['round'])})."

    fastest_team_text = ""
    if not speed_df.empty:
        ft = speed_df.groupby("constructor")["avg_speed_kph"].mean().idxmax()
        fv = speed_df.groupby("constructor")["avg_speed_kph"].mean().max()
        fastest_team_text = f"**{ft}** mencatat kecepatan rata-rata tertinggi: **{fv:.1f} km/h**."

    return html.Div([
        sec_header("Strategi Pit Stop"),
        insight_box(best_pit_text) if best_pit_text else html.Div(),
        dbc.Row([
            dbc.Col(card([
                html.Div("Heatmap Durasi Pit Stop", style=dict(
                    fontSize="12px", fontWeight="600", color=C["muted"],
                    marginBottom="10px", fontFamily=FONT,
                )),
                dcc.Graph(figure=fig_hm, config=dict(displayModeBar=False)),
            ]), width=7),
            dbc.Col(card([
                html.Div("Konsistensi Per Pembalap", style=dict(
                    fontSize="12px", fontWeight="600", color=C["muted"],
                    marginBottom="10px", fontFamily=FONT,
                )),
                dcc.Graph(figure=fig_box, config=dict(displayModeBar=False)),
            ]), width=5),
        ], className="g-3"),

        sec_header("Kecepatan dan Kualifikasi"),
        insight_box(fastest_team_text) if fastest_team_text else html.Div(),
        dbc.Row([
            dbc.Col(card([
                html.Div("Tren Kecepatan Per Konstruktor", style=dict(
                    fontSize="12px", fontWeight="600", color=C["muted"],
                    marginBottom="10px", fontFamily=FONT,
                )),
                dcc.Graph(figure=fig_spd, config=dict(displayModeBar=False)),
            ]), width=6),
            dbc.Col(card([
                html.Div("Kualifikasi vs Hasil Balapan", style=dict(
                    fontSize="12px", fontWeight="600", color=C["muted"],
                    marginBottom="10px", fontFamily=FONT,
                )),
                dcc.Graph(figure=fig_qvr, config=dict(displayModeBar=False)),
            ]), width=6),
        ], className="g-3"),

        export_btn("analitik"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: HEAD-TO-HEAD
# ─────────────────────────────────────────────────────────────────────────────
def page_h2h(season):
    df = get_analytics(season)
    if df.empty:
        return html.Div("Tidak ada data.", style=dict(color=C["muted"]))

    drivers = sorted(df["driver_name"].dropna().unique().tolist())
    default_d1 = drivers[0] if len(drivers) > 0 else None
    default_d2 = drivers[1] if len(drivers) > 1 else None
    default_d3 = drivers[2] if len(drivers) > 2 else None

    return html.Div([
        sec_header("Perbandingan Head-to-Head"),
        insight_box("Pilih hingga 3 pembalap untuk membandingkan performa secara visual menggunakan radar chart dan grafik batang."),

        # Driver selectors
        card(dbc.Row([
            dbc.Col([
                html.Div("Pembalap 1", style=dict(
                    fontSize="10px", color=C["muted"], fontWeight="700",
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="6px", fontFamily=FONT,
                )),
                dcc.Dropdown(
                    id="h2h-d1", options=[{"label":d,"value":d} for d in drivers],
                    value=default_d1, clearable=False,
                    style=dict(fontFamily=FONT),
                ),
            ], width=4),
            dbc.Col([
                html.Div("Pembalap 2", style=dict(
                    fontSize="10px", color=C["muted"], fontWeight="700",
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="6px", fontFamily=FONT,
                )),
                dcc.Dropdown(
                    id="h2h-d2", options=[{"label":d,"value":d} for d in drivers],
                    value=default_d2, clearable=False,
                    style=dict(fontFamily=FONT),
                ),
            ], width=4),
            dbc.Col([
                html.Div("Pembalap 3 (Opsional)", style=dict(
                    fontSize="10px", color=C["muted"], fontWeight="700",
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="6px", fontFamily=FONT,
                )),
                dcc.Dropdown(
                    id="h2h-d3", options=[{"label":d,"value":d} for d in drivers],
                    value=default_d3, clearable=True,
                    style=dict(fontFamily=FONT),
                ),
            ], width=4),
        ], className="g-3")),

        dbc.Row([
            dbc.Col(card(dcc.Graph(id="h2h-radar", config=dict(displayModeBar=False))), width=6),
            dbc.Col(card(dcc.Graph(id="h2h-bar",   config=dict(displayModeBar=False))), width=6),
        ], className="g-3"),

        card(html.Div(id="h2h-table")),

        dcc.Store(id="h2h-season", data=season),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: TABEL DATA
# ─────────────────────────────────────────────────────────────────────────────
def page_tabel(season):
    df = get_analytics(season)
    if df.empty:
        return html.Div("Tidak ada data.", style=dict(color=C["muted"]))

    cols_show = ["season","round","race_name","driver_name","constructor",
                 "position","race_points","cumulative_points","championship_pos",
                 "grid_pos","positions_gained","status","avg_speed_kph",
                 "avg_pit_duration_s","qualifying_pos","is_win","is_podium"]
    cols_avail = [c for c in cols_show if c in df.columns]
    df_disp = df[cols_avail].copy()

    tbl_header = html.Thead(html.Tr([
        html.Th(col.replace("_"," ").title(), style=dict(
            color=C["muted"], fontSize="10px", fontWeight="700",
            letterSpacing="0.5px", textTransform="uppercase",
            padding="10px 12px", fontFamily=FONT,
            borderBottom=f"1px solid {C['border']}",
            whiteSpace="nowrap",
        )) for col in cols_avail
    ]))

    tbl_body = html.Tbody([
        html.Tr([
            html.Td(str(row[col]) if pd.notna(row[col]) else "—", style=dict(
                color=C["text"] if col in ["driver_name","race_points","cumulative_points"]
                      else C["muted"],
                fontSize="11px", padding="8px 12px", fontFamily=FONT,
                fontWeight="600" if col in ["driver_name","cumulative_points"] else "400",
                borderBottom=f"1px solid {C['border']}22",
                whiteSpace="nowrap",
            )) for col in cols_avail
        ]) for _, row in df_disp.head(100).iterrows()
    ])

    return html.Div([
        sec_header("Tabel Data Lengkap"),
        html.Div(f"Menampilkan 100 dari {len(df_disp)} baris · Season {season}", style=dict(
            fontSize="11px", color=C["muted"], marginBottom="12px", fontFamily=FONT,
        )),
        card(html.Div([
            html.Table(
                [tbl_header, tbl_body],
                style=dict(width="100%", borderCollapse="collapse"),
            )
        ], style=dict(overflowX="auto", overflowY="auto", maxHeight="600px"))),
        export_btn("tabel"),
        dcc.Store(id="store-tabel", data=df_disp.to_dict("records")),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: BENCHMARK
# ─────────────────────────────────────────────────────────────────────────────
def page_benchmark():
    bench_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    if not os.path.exists(bench_path):
        return html.Div("File benchmark_results.json tidak ditemukan. Jalankan python benchmark.py",
                        style=dict(color=C["muted"], fontFamily=FONT))

    with open(bench_path) as f:
        bench = json.load(f)

    scenarios    = list(bench.keys())
    labels       = [s.replace("S","").replace("_"," ").title() for s in scenarios]
    p_mean       = [bench[s]["pandas_mean_ms"] for s in scenarios]
    p_std        = [bench[s]["pandas_std_ms"]  for s in scenarios]
    s_mean       = [bench[s]["sql_mean_ms"]    for s in scenarios]
    s_std        = [bench[s]["sql_std_ms"]     for s in scenarios]
    speedup      = [bench[s]["speedup_ratio"]  for s in scenarios]
    rows_list    = [bench[s]["row_count"]      for s in scenarios]

    # Grouped bar
    fig_bench = go.Figure()
    fig_bench.add_trace(go.Bar(
        name="Pandas In-Memory", x=labels, y=p_mean,
        error_y=dict(type="data", array=p_std, visible=True, color=C["red"]+"88"),
        marker_color=C["red"],
        text=[f"{v:.1f}ms" for v in p_mean], textposition="outside",
        textfont=dict(color=C["text"], size=10),
    ))
    fig_bench.add_trace(go.Bar(
        name="SQL View (PostgreSQL)", x=labels, y=s_mean,
        error_y=dict(type="data", array=s_std, visible=True, color=C["teal"]+"88"),
        marker_color=C["teal"],
        text=[f"{v:.1f}ms" for v in s_mean], textposition="outside",
        textfont=dict(color=C["text"], size=10),
    ))
    fig_bench.update_layout(**CHART_LAYOUT, height=360, barmode="group",
        legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=11, color=C["text"])),
        xaxis=dict(title="Skenario", gridcolor=C["border"]),
        yaxis=dict(title="Latensi Rata-rata (ms)", gridcolor=C["border"]),
        margin=dict(l=40, r=20, t=20, b=60),
    )

    # Speedup line
    fig_spup = go.Figure(go.Scatter(
        x=labels, y=speedup,
        mode="lines+markers+text",
        text=[f"{v:.1f}x" for v in speedup],
        textposition="top center",
        textfont=dict(color=C["text"], size=11),
        line=dict(color=C["green"], width=2.5),
        marker=dict(size=10, color=C["green"],
                    line=dict(width=2, color=C["card"])),
    ))
    fig_spup.add_hline(y=1, line_color=C["red"], line_dash="dash",
                       annotation_text="Baseline (1x)",
                       annotation_font_color=C["red"],
                       annotation_font_size=10)
    fig_spup.update_layout(**CHART_LAYOUT, height=280, showlegend=False,
        yaxis=dict(title="Speedup (x lebih cepat)", gridcolor=C["border"]),
        xaxis=dict(gridcolor=C["border"], tickangle=-15),
        margin=dict(l=40, r=20, t=20, b=60),
    )

    # Summary table
    tbl_rows = []
    for i, (s, lbl) in enumerate(zip(scenarios, labels)):
        tbl_rows.append(html.Tr([
            html.Td(lbl, style=dict(color=C["text"], fontSize="12px",
                                    padding="10px 12px", fontFamily=FONT)),
            html.Td(str(rows_list[i]), style=dict(color=C["muted"], fontSize="11px",
                                                   textAlign="center", padding="10px 12px",
                                                   fontFamily=FONT)),
            html.Td(f"{p_mean[i]:.2f} ± {p_std[i]:.2f}", style=dict(
                color=C["red"], fontSize="11px", textAlign="center",
                padding="10px 12px", fontFamily=FONT)),
            html.Td(f"{s_mean[i]:.2f} ± {s_std[i]:.2f}", style=dict(
                color=C["teal"], fontSize="11px", textAlign="center",
                padding="10px 12px", fontFamily=FONT)),
            html.Td(f"{speedup[i]:.1f}x", style=dict(
                color=C["green"], fontSize="12px", fontWeight="700",
                textAlign="center", padding="10px 12px", fontFamily=FONT)),
        ], style=dict(borderBottom=f"1px solid {C['border']}")))

    return html.Div([
        sec_header("Benchmark Performa: SQL View vs Pandas In-Memory"),
        insight_box(
            "**Metodologi:** 5 skenario query × 10 iterasi. "
            "Metrik: latensi rata-rata (ms) ± std dev. "
            "SQL View lebih cepat karena B-tree index dan PostgreSQL query planner "
            "(Kleppmann, 2017)."
        ),

        card(dcc.Graph(figure=fig_bench, config=dict(displayModeBar=False))),

        dbc.Row([
            dbc.Col(card([
                html.Div("Rasio Speedup (x lebih cepat)", style=dict(
                    fontSize="12px", fontWeight="600", color=C["muted"],
                    marginBottom="10px", fontFamily=FONT,
                )),
                dcc.Graph(figure=fig_spup, config=dict(displayModeBar=False)),
            ]), width=6),
            dbc.Col(card([
                html.Div("Tabel Ringkasan (untuk Paper)", style=dict(
                    fontSize="12px", fontWeight="600", color=C["muted"],
                    marginBottom="10px", fontFamily=FONT,
                )),
                html.Table([
                    html.Thead(html.Tr([
                        html.Th(col, style=dict(
                            color=C["muted"], fontSize="10px", fontWeight="700",
                            letterSpacing="0.5px", textTransform="uppercase",
                            padding="8px 12px",
                            textAlign="center" if i > 0 else "left",
                            fontFamily=FONT,
                            borderBottom=f"1px solid {C['border']}",
                        )) for i, col in enumerate(["Skenario","Baris","Pandas (ms)","SQL (ms)","Speedup"])
                    ])),
                    html.Tbody(tbl_rows),
                ], style=dict(width="100%", borderCollapse="collapse")),
            ]), width=6),
        ], className="g-3"),

        insight_box(
            "**Catatan untuk Bab Hasil dan Pembahasan:** "
            "SQL View secara konsisten **3.6x–5.9x lebih cepat** "
            "dibanding Pandas in-memory merge karena: "
            "(1) B-tree index mengurangi kompleksitas JOIN dari O(n²) ke O(n log n), "
            "(2) PostgreSQL query planner mengoptimalkan execution plan berbasis statistik tabel, "
            "(3) Pandas beroperasi di single-threaded Python heap tanpa optimisasi storage-level."
        ),

        export_btn("benchmark"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: EVALUASI SUS
# ─────────────────────────────────────────────────────────────────────────────
def page_sus():
    from sus_tool import SUS_QUESTIONS, get_summary_stats, load_responses

    stats = get_summary_stats()
    responses = load_responses()

    gc_map = {
        "Excellent": C["green"], "Good": C["teal"],
        "Acceptable": C["yellow"], "Marginal": C["orange"],
        "Unacceptable": C["red"],
    }

    # Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=stats["mean"] if stats else 0,
        number=dict(suffix=" pts", font=dict(color=C["text"], size=28, family=FONT)),
        gauge=dict(
            axis=dict(range=[0,100], tickcolor=C["muted"],
                      tickfont=dict(color=C["muted"], size=9)),
            bar=dict(color=gc_map.get(stats["grade"], C["muted"]) if stats else C["border"]),
            bgcolor=C["card"],
            steps=[
                dict(range=[0,50],  color="#2A0A0A"),
                dict(range=[50,68], color="#2A1A0A"),
                dict(range=[68,80], color="#0A2A1A"),
                dict(range=[80,90], color="#0A2A20"),
                dict(range=[90,100],color="#0A3A20"),
            ],
            threshold=dict(
                line=dict(color=C["orange"], width=3),
                thickness=0.75, value=68,
            ),
        ),
    ))
    fig_gauge.update_layout(
        paper_bgcolor=C["card"], font=dict(color=C["text"], family=FONT),
        height=220, margin=dict(l=20,r=20,t=10,b=0)
    )

    form_items = []
    for code, question, direction in SUS_QUESTIONS:
        label = f"**{code}** — {question}"
        if direction == "negative":
            label += " *(pertanyaan negatif)*"
        form_items.append(html.Div([
            dcc.Markdown(label, style=dict(
                color=C["text"], fontSize="12px",
                fontFamily=FONT, marginBottom="4px",
            )),
            dcc.Slider(
                id=f"sus-{code}", min=1, max=5, step=1, value=3,
                marks={i: dict(label=str(i), style=dict(color=C["muted"],
                               fontFamily=FONT, fontSize="10px")) for i in range(1,6)},
            ),
            html.Div(style=dict(marginBottom="16px")),
        ]))

    result_section = html.Div()
    if stats:
        gc = gc_map.get(stats["grade"], C["muted"])
        result_section = html.Div([
            html.Div([
                html.Div(f"{stats['mean']:.1f}", style=dict(
                    fontSize="48px", fontWeight="900", color=gc,
                    fontFamily=FONT, lineHeight="1",
                )),
                html.Div("/ 100", style=dict(
                    fontSize="16px", color=C["muted"],
                    fontFamily=FONT, marginTop="4px",
                )),
            ], style=dict(textAlign="center", marginBottom="16px")),

            html.Div([
                html.Div(stats["grade"], style=dict(
                    background=gc+"33", color=gc,
                    padding="4px 16px", borderRadius="20px",
                    fontSize="12px", fontWeight="700",
                    fontFamily=FONT, display="inline-block",
                )),
            ], style=dict(textAlign="center", marginBottom="20px")),

            dcc.Graph(figure=fig_gauge, config=dict(displayModeBar=False)),
            html.Div("Garis oranye = batas acceptable (68)", style=dict(
                fontSize="10px", color=C["muted"], textAlign="center",
                fontFamily=FONT, marginTop="4px",
            )),

            html.Div([
                dbc.Row([
                    dbc.Col(html.Div([
                        html.Div(f"{stats['n']}", style=dict(
                            fontSize="24px", fontWeight="800",
                            color=C["text"], fontFamily=FONT,
                        )),
                        html.Div("Responden", style=dict(
                            fontSize="10px", color=C["muted"],
                            fontFamily=FONT,
                        )),
                    ], style=dict(textAlign="center")), width=4),
                    dbc.Col(html.Div([
                        html.Div(f"{stats['std']:.2f}", style=dict(
                            fontSize="24px", fontWeight="800",
                            color=C["text"], fontFamily=FONT,
                        )),
                        html.Div("Std Dev", style=dict(
                            fontSize="10px", color=C["muted"],
                            fontFamily=FONT,
                        )),
                    ], style=dict(textAlign="center")), width=4),
                    dbc.Col(html.Div([
                        html.Div(f"{stats['median']:.0f}", style=dict(
                            fontSize="24px", fontWeight="800",
                            color=C["text"], fontFamily=FONT,
                        )),
                        html.Div("Median", style=dict(
                            fontSize="10px", color=C["muted"],
                            fontFamily=FONT,
                        )),
                    ], style=dict(textAlign="center")), width=4),
                ], className="g-2"),
            ], style=dict(marginTop="20px")),
        ])

    return html.Div([
        sec_header("Evaluasi System Usability Scale (SUS)"),
        insight_box(
            "**Tentang SUS:** Kuesioner 10-item skala Likert 1–5, menghasilkan skor 0–100. "
            "Interpretasi: ≥85 = Excellent, ≥70 = Good, ≥68 = Acceptable (Bangor et al., 2008). "
            "Minimal **5 responden** untuk validitas dasar."
        ),

        dbc.Row([
            dbc.Col(card([
                html.Div("Formulir Penilaian SUS", style=dict(
                    fontSize="14px", fontWeight="700", color=C["text"],
                    marginBottom="16px", fontFamily=FONT,
                )),
                html.Div([
                    html.Div("Nama Responden", style=dict(
                        fontSize="11px", color=C["muted"], fontWeight="600",
                        textTransform="uppercase", letterSpacing="0.5px",
                        marginBottom="6px", fontFamily=FONT,
                    )),
                    dcc.Input(
                        id="sus-name", type="text",
                        placeholder="Nama atau inisial",
                        style=dict(
                            background=C["border"], color=C["text"],
                            border=f"1px solid {C['border']}",
                            borderRadius="6px", padding="8px 12px",
                            fontSize="12px", fontFamily=FONT,
                            width="100%", marginBottom="14px",
                        ),
                    ),
                ]),
                html.Div([
                    html.Div("Peran", style=dict(
                        fontSize="11px", color=C["muted"], fontWeight="600",
                        textTransform="uppercase", letterSpacing="0.5px",
                        marginBottom="6px", fontFamily=FONT,
                    )),
                    dcc.Dropdown(
                        id="sus-role",
                        options=[
                            {"label":"Mahasiswa S1","value":"Mahasiswa S1"},
                            {"label":"Mahasiswa S2/S3","value":"Mahasiswa S2/S3"},
                            {"label":"Dosen/Peneliti","value":"Dosen/Peneliti"},
                            {"label":"Praktisi IT","value":"Praktisi IT"},
                            {"label":"Lainnya","value":"Lainnya"},
                        ],
                        value="Mahasiswa S1",
                        clearable=False,
                        style=dict(marginBottom="16px", fontFamily=FONT),
                    ),
                ]),
                html.Div("Penilaian: 1 = Sangat Tidak Setuju · 5 = Sangat Setuju", style=dict(
                    fontSize="11px", color=C["muted"], marginBottom="14px",
                    fontFamily=FONT,
                )),
                html.Div(form_items),
                html.Button([
                    icon("lucide:check-circle", size=14, color="#fff"),
                    html.Span("Hitung dan Simpan Skor SUS", style=dict(marginLeft="8px")),
                ],
                id="sus-submit",
                n_clicks=0,
                style=dict(
                    background=C["red"], color=C["text"],
                    border="none", borderRadius="8px",
                    padding="10px 20px", cursor="pointer",
                    fontSize="13px", fontWeight="600",
                    fontFamily=FONT, width="100%",
                    marginTop="8px",
                )),
                html.Div(id="sus-result-msg", style=dict(marginTop="12px")),
            ]), width=7),

            dbc.Col([
                card([
                    html.Div("Hasil Agregat", style=dict(
                        fontSize="14px", fontWeight="700", color=C["text"],
                        marginBottom="16px", fontFamily=FONT,
                    )),
                    result_section if stats else html.Div(
                        "Belum ada responden. Isi form di sebelah kiri.",
                        style=dict(color=C["muted"], fontSize="12px", fontFamily=FONT)
                    ),
                ]),
                export_btn("sus"),
            ], width=5),
        ], className="g-3"),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
seasons_list = get_seasons()
default_season = seasons_list[0] if seasons_list else 2024

app.layout = html.Div([
    dcc.Store(id="store-page",   data="beranda"),
    dcc.Store(id="store-season", data=default_season),

    # Sidebar
    html.Div(id="sidebar-container"),

    # Main content
    html.Div([
        html.Div(id="page-content"),
    ], style=dict(
        marginLeft="240px",
        padding="24px 28px",
        minHeight="100vh",
        background=C["bg"],
        fontFamily=FONT,
    )),

], style=dict(
    background=C["bg"],
    minHeight="100vh",
    fontFamily=FONT,
))

# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

# Update active page from nav
@app.callback(
    Output("store-page", "data"),
    [Input({"type":"nav-item","index":pid}, "n_clicks") for pid, _, _ in NAV_ITEMS],
    State("store-page", "data"),
    prevent_initial_call=True,
)
def update_page(*args):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    triggered_id = ctx.triggered[0]["prop_id"]
    for pid, _, _ in NAV_ITEMS:
        if f'"index":"{pid}"' in triggered_id or f'"index": "{pid}"' in triggered_id:
            return pid
    return args[-1]

# Update season
@app.callback(
    Output("store-season", "data"),
    [Input({"type":"season-btn","index":s}, "n_clicks") for s in seasons_list],
    prevent_initial_call=True,
)
def update_season(*args):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    triggered_id = ctx.triggered[0]["prop_id"]
    for s in seasons_list:
        if f'"index":{s}' in triggered_id:
            return s
    return default_season

# Render sidebar
@app.callback(
    Output("sidebar-container", "children"),
    Input("store-page", "data"),
    Input("store-season", "data"),
)
def render_sidebar(page, season):
    return make_sidebar(page, seasons_list, season)

# Render page content
@app.callback(
    Output("page-content", "children"),
    Input("store-page", "data"),
    Input("store-season", "data"),
)
def render_page(page, season):
    if page == "beranda":
        return page_beranda(season)
    elif page == "klasemen":
        return page_klasemen(season)
    elif page == "analitik":
        return page_analitik(season)
    elif page == "h2h":
        return page_h2h(season)
    elif page == "tabel":
        return page_tabel(season)
    elif page == "benchmark":
        return page_benchmark()
    elif page == "sus":
        return page_sus()
    return page_beranda(season)

# Head-to-Head charts
@app.callback(
    Output("h2h-radar", "figure"),
    Output("h2h-bar",   "figure"),
    Output("h2h-table", "children"),
    Input("h2h-d1", "value"),
    Input("h2h-d2", "value"),
    Input("h2h-d3", "value"),
    State("h2h-season", "data"),
    prevent_initial_call=False,
)
def update_h2h(d1, d2, d3, season):
    if not season:
        season = default_season
    df = get_analytics(season)

    selected = [d for d in [d1, d2, d3] if d]
    if len(selected) < 2:
        empty = go.Figure()
        empty.update_layout(**CHART_LAYOUT, height=320)
        return empty, empty, html.Div("Pilih minimal 2 pembalap.", style=dict(color=C["muted"]))

    metrics_labels = ["Poin","Menang","Podium","Pole","FL","DNF"]
    radar_fig = go.Figure()
    bar_data   = {m: [] for m in metrics_labels}
    tbl_rows_h2h = []

    drv_colors = [C["red"], C["teal"], C["yellow"]]

    for i, drv in enumerate(selected):
        d = df[df["driver_name"]==drv]
        if d.empty:
            continue
        latest_drv = d.sort_values("round", ascending=False).iloc[0]
        pts  = float(latest_drv.get("cumulative_points", 0) or 0)
        wins = int(d["is_win"].sum())
        pods = int(d["is_podium"].sum())
        poles= int((d["qualifying_pos"]==1).sum())
        fl   = int((d["fastest_lap_rank"]==1).sum()) if "fastest_lap_rank" in d.columns else 0
        dnf  = int((d["is_finished"]==False).sum())

        vals = [pts, wins*20, pods*10, poles*15, fl*10, dnf*5]
        radar_fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=metrics_labels + [metrics_labels[0]],
            fill="toself", name=drv,
            line_color=drv_colors[i % len(drv_colors)],
            fillcolor="rgba(225,6,0,0.2)" if drv_colors[i % len(drv_colors)] == C["red"] else "rgba(0,210,190,0.2)" if drv_colors[i % len(drv_colors)] == C["teal"] else "rgba(255,215,0,0.2)",
        ))

        for m, v in zip(metrics_labels, [pts, wins, pods, poles, fl, dnf]):
            bar_data[m].append(v)

        tbl_rows_h2h.append(html.Tr([
            html.Td(drv, style=dict(
                color=drv_colors[i % len(drv_colors)], fontSize="12px",
                fontWeight="700", padding="10px 12px", fontFamily=FONT,
            )),
            html.Td(f"{pts:.0f}", style=dict(color=C["text"], fontSize="12px",
                                              textAlign="center", padding="10px 12px",
                                              fontFamily=FONT)),
            html.Td(str(wins), style=dict(color=C["yellow"], fontSize="12px",
                                           fontWeight="700", textAlign="center",
                                           padding="10px 12px", fontFamily=FONT)),
            html.Td(str(pods), style=dict(color=C["teal"], fontSize="12px",
                                           fontWeight="600", textAlign="center",
                                           padding="10px 12px", fontFamily=FONT)),
            html.Td(str(poles), style=dict(color=C["muted"], fontSize="12px",
                                            textAlign="center", padding="10px 12px",
                                            fontFamily=FONT)),
            html.Td(str(fl), style=dict(color=C["muted"], fontSize="12px",
                                         textAlign="center", padding="10px 12px",
                                         fontFamily=FONT)),
            html.Td(str(dnf), style=dict(color=C["red"], fontSize="12px",
                                          fontWeight="600", textAlign="center",
                                          padding="10px 12px", fontFamily=FONT)),
        ], style=dict(borderBottom=f"1px solid {C['border']}")))

    radar_fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, None],
                            gridcolor=C["border"], tickfont=dict(size=8, color=C["muted"])),
            angularaxis=dict(tickfont=dict(size=10, color=C["muted"], family=FONT)),
            bgcolor=C["card"],
        ),
        paper_bgcolor=C["card"],
        font=dict(family=FONT, color=C["text"], size=11),
        legend=dict(orientation="h", y=-0.1, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=10, color=C["text"])),
        height=320, margin=dict(l=20, r=20, t=20, b=40),
    )

    bar_fig = go.Figure()
    for i, drv in enumerate(selected):
        d = df[df["driver_name"]==drv]
        if d.empty:
            continue
        latest_drv = d.sort_values("round", ascending=False).iloc[0]
        pts  = float(latest_drv.get("cumulative_points", 0) or 0)
        wins = int(d["is_win"].sum())
        pods = int(d["is_podium"].sum())
        poles= int((d["qualifying_pos"]==1).sum())
        fl   = int((d["fastest_lap_rank"]==1).sum()) if "fastest_lap_rank" in d.columns else 0
        dnf  = int((d["is_finished"]==False).sum())

        bar_fig.add_trace(go.Bar(
            name=drv,
            x=metrics_labels,
            y=[pts/10, wins, pods, poles, fl, dnf],
            marker_color=drv_colors[i % len(drv_colors)],
            hovertemplate=f"<b>{drv}</b><br>%{{x}}: %{{customdata}}<extra></extra>",
            customdata=[f"{pts:.0f}", wins, pods, poles, fl, dnf],
        ))
    bar_fig.update_layout(**CHART_LAYOUT, height=320, barmode="group",
        legend=dict(orientation="h", y=1.08, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=10, color=C["text"])),
        xaxis=dict(gridcolor=C["border"]),
        yaxis=dict(title="Nilai", gridcolor=C["border"]),
        margin=dict(l=30, r=20, t=20, b=40),
    )

    tbl_h2h = html.Div([
        html.Div("Perbandingan Statistik", style=dict(
            fontSize="12px", fontWeight="600", color=C["muted"],
            marginBottom="10px", fontFamily=FONT,
        )),
        html.Table([
            html.Thead(html.Tr([
                html.Th(col, style=dict(
                    color=C["muted"], fontSize="10px", fontWeight="700",
                    letterSpacing="0.5px", textTransform="uppercase",
                    padding="8px 12px",
                    textAlign="center" if i > 0 else "left",
                    fontFamily=FONT,
                    borderBottom=f"1px solid {C['border']}",
                )) for i, col in enumerate(["Pembalap","Poin","W","P","Pole","FL","DNF"])
            ])),
            html.Tbody(tbl_rows_h2h),
        ], style=dict(width="100%", borderCollapse="collapse")),
    ])

    return radar_fig, bar_fig, tbl_h2h

# SUS submit
@app.callback(
    Output("sus-result-msg", "children"),
    Input("sus-submit", "n_clicks"),
    State("sus-name", "value"),
    State("sus-role", "value"),
    [State(f"sus-{code}", "value") for code, _, _ in __import__('sus_tool').SUS_QUESTIONS],
    prevent_initial_call=True,
)
def submit_sus(n_clicks, name, role, *responses):
    if not n_clicks:
        return no_update
    if not name or not name.strip():
        return html.Div("⚠️ Mohon isi nama responden.", style=dict(
            color=C["orange"], fontSize="12px", fontFamily=FONT))
    from sus_tool import save_response
    score, grade = save_response(name.strip(), role or "Lainnya", list(responses))
    gc_map = {
        "Excellent":C["green"],"Good":C["teal"],
        "Acceptable":C["yellow"],"Marginal":C["orange"],"Unacceptable":C["red"]
    }
    color = gc_map.get(grade, C["teal"])
    return html.Div([
        html.Div(f"✅ Skor SUS: {score:.1f} — Grade: {grade}", style=dict(
            color=color, fontSize="13px", fontWeight="700", fontFamily=FONT,
        )),
        html.Div("Refresh halaman untuk melihat hasil terbaru.", style=dict(
            color=C["muted"], fontSize="11px", fontFamily=FONT, marginTop="4px",
        )),
    ])

# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)