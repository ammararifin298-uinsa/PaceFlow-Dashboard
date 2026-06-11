# =============================================================================
# pages/home/layout.py — Halaman Beranda PaceFlow
# Berisi: KPI cards, championship chart (Poin/Posisi) dengan toggle Top N,
#         grafik konstruktor
# Update: bump chart mode, toggle Poin/Posisi, partial badge dinamis dari DB
# =============================================================================

import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import (
    ico, card, sec, info_box, kpi_card,
    empty_state, partial_badge, safe_contains
)
from layout.design_tokens import C, F, CL, ax, legh, rgba, tc, MARKER_SYMBOLS
from services.data_service import get_analytics, get_kpi, get_constructor_season
from pages.home.callbacks import _build_points_fig


def _btn_toggle(btn_id, label, active):
    return html.Button(
        label, id=btn_id, n_clicks=0,
        style=dict(
            background=C["blue"] if active else C["surface"],
            color="#FFF" if active else C["muted"],
            border=f"1px solid {C['blue'] if active else C['border']}",
            borderRadius="6px", padding="4px 14px",
            fontSize="11px", fontWeight="600",
            fontFamily=F, cursor="pointer",
        )
    )


def layout(season: int, flt: dict):
    df_r = get_analytics(season)
    kp   = get_kpi(season)
    dc   = get_constructor_season(season)

    if df_r.empty:
        return empty_state("Tidak ada data.", f"Season {season} belum tersedia.")

    flt    = flt or {}
    search = flt.get("search", "") or ""
    drv_f  = flt.get("drv")
    con_f  = flt.get("con")

    df = df_r.copy()
    if drv_f: df = df[df["driver_name"].isin(drv_f)]
    if con_f: df = df[df["constructor"].isin(con_f)]
    if search:
        mask = (safe_contains(df["driver_name"], search) |
                safe_contains(df["race_name"], search))
        df = df[mask]

    if df.empty:
        return empty_state("Tidak ada data yang cocok.",
                           "Coba ubah atau hapus filter aktif.")

    # KPI
    n_races = int(df_r["round"].nunique())
    lat     = df_r.sort_values("round", ascending=False).drop_duplicates("driver_id")
    t2      = lat.nlargest(2, "cumulative_points")
    gap     = (float(t2.iloc[0]["cumulative_points"]) -
               float(t2.iloc[1]["cumulative_points"])) if len(t2) >= 2 else 0
    leader  = str(kp.get("points_leader", "—"))
    lpts    = float(kp.get("leader_points", 0) or 0)
    ap      = kp.get("season_avg_pit_s")
    dnf     = int(kp.get("total_dnf", 0) or 0)
    tot     = int(kp.get("total_entries", len(df_r)) or len(df_r))
    races   = int(kp.get("total_races", n_races) or n_races)
    pit_d   = f"{float(ap):.3f}s" if ap else "N/A"
    dnf_r   = f"{dnf/tot*100:.1f}%" if tot > 0 else "N/A"
    total_scheduled = int(kp.get("total_races_scheduled", n_races) or n_races)

    # Data grafik
    tr = (df.groupby(["driver_name", "round", "race_name", "constructor"],
                     as_index=False)[["season_cumulative_points", "cumulative_points"]].max()
            .sort_values(["driver_name", "round"]))

    # Grafik konstruktor
    dc_s = dc.sort_values("total_points")
    fig_cb = go.Figure(go.Bar(
        y=dc_s["constructor"], x=dc_s["total_points"], orientation="h",
        marker_color=[tc(t) for t in dc_s["constructor"]],
        marker_line=dict(width=0),
        text=dc_s["total_points"].astype(int),
        textposition="outside",
        textfont=dict(color=C["muted"], size=10),
        hovertemplate="<b>%{y}</b><br>Poin: %{x}<extra></extra>"
    ))
    fig_cb.update_layout(**CL, height=300, showlegend=False,
        xaxis=ax("Total Poin"),
        yaxis=dict(gridcolor=C["grid"], linecolor=C["border"],
                   tickfont=dict(size=10, color=C["text"])),
        margin=dict(l=140, r=50, t=10, b=30))

    is_finished = n_races >= total_scheduled

    return html.Div([
        sec("Indikator Kinerja Utama", "lucide:trending-up"),
        partial_badge(n_races, total_scheduled),
        dbc.Row([
            dbc.Col(kpi_card(
                "Juara Pembalap (WDC)" if is_finished else "Pemimpin Pembalap (WDC)",
                leader,
                f"WDC · Season {season}" if is_finished else f"▲ {lpts:.0f} poin · Gap +{gap:.0f} vs P2",
                C["red"], "lucide:trophy"), width=3),
            dbc.Col(kpi_card(
                "Juara Konstruktor (WCC)" if is_finished else "Pemimpin Konstruktor (WCC)",
                str(kp.get("leader_constructor", "—")),
                f"WCC · Season {season}" if is_finished else f"Sementara · Season {season}",
                C["teal"], "lucide:shield"), width=3),
            dbc.Col(kpi_card("Tingkat DNF", dnf_r,
                f"{dnf} DNF dari {tot} start" + (" · ⚠ Parsial" if n_races < total_scheduled else ""),
                C["orange"], "lucide:circle-x"), width=3),
            dbc.Col(kpi_card("Total Balapan", f"{races} Race",
                f"{df_r['driver_id'].nunique()} pembalap · "
                f"{df_r['constructor'].nunique()} konstruktor",
                C["blue"], "lucide:flag"), width=3),
        ], className="g-3"),

        sec("Perkembangan Poin Championship", "lucide:line-chart"),
        info_box(
            f"**{leader}** memimpin dengan **{lpts:.0f} poin** "
            f"setelah {n_races} race. Gap ke P2: **+{gap:.0f} poin**."
            + ("" if n_races >= total_scheduled
               else " Menampilkan **Top 5 pembalap** berdasarkan poin.")
        ),
        card(
            html.Div([
                html.Div([
                    _btn_toggle("btn-top5",   "Top 5",  True),
                    _btn_toggle("btn-top10",  "Top 10", False),
                    _btn_toggle("btn-topall", "Semua",  False),
                ], style=dict(display="flex", gap="6px")),
                html.Div([
                    _btn_toggle("btn-mode-poin",   "Poin",   True),
                    _btn_toggle("btn-mode-posisi", "Posisi", False),
                ], style=dict(display="flex", gap="6px")),
            ], style=dict(display="flex", justifyContent="space-between",
                          marginBottom="12px")),
            dcc.Graph(id="graph-championship",
                      figure=_build_points_fig(tr, 5),
                      config=dict(displayModeBar=False),
                      style=dict(overflow="visible")),
        ),

        sec("Performa Konstruktor", "lucide:bar-chart-2"),
        card(dcc.Graph(figure=fig_cb, config=dict(displayModeBar=False))),

        html.Div(
            html.Button([
                ico("lucide:download", 13, "#FFF"),
                html.Span(" Download CSV", style=dict(marginLeft="5px")),
            ], id="btn-beranda", n_clicks=0,
            style=dict(display="flex", alignItems="center",
                       background=C["blue"], color="#FFF",
                       border="none", borderRadius="6px",
                       padding="8px 16px", fontSize="11px",
                       fontWeight="600", fontFamily=F,
                       cursor="pointer", marginBottom="16px")),
        style=dict(display="flex", justifyContent="flex-end")),

        dcc.Store(id="store-beranda-data", data=tr.to_dict("records")),
        dcc.Store(id="store-home-top-n",   data=5),
        dcc.Store(id="store-home-mode",    data="poin"),
    ])