# =============================================================================
# pages/home/layout.py — Halaman Beranda PaceFlow
# Berisi: KPI cards, grafik poin championship, grafik konstruktor
# Fix: default top-10 driver, marker dibedakan dari garis
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

    # Data grafik — pakai season_cumulative_points
    tr = (df.groupby(["driver_name", "round", "race_name", "constructor"],
                     as_index=False)["season_cumulative_points"].max()
            .sort_values(["driver_name", "round"]))

    # Default top-10 driver berdasarkan poin tertinggi
    top_drivers = (tr.groupby("driver_name")["season_cumulative_points"]
                   .max().nlargest(10).index.tolist())
    tr_plot = tr[tr["driver_name"].isin(top_drivers)]
    show_all = len(tr["driver_name"].unique()) <= 10

    # Grafik poin progression — marker dibedakan dari garis
    fig = go.Figure()
    for i, drv in enumerate(tr_plot["driver_name"].unique()):
        d     = tr_plot[tr_plot["driver_name"] == drv].sort_values("round")
        color = tc(d["constructor"].iloc[0] if not d.empty else "")
        fig.add_trace(go.Scatter(
            x=d["round"],
            y=d["season_cumulative_points"],
            mode="lines+markers",
            name=drv,
            line=dict(width=2, color=color),
            marker=dict(
                size=8,
                color="#FFFFFF",
                symbol=MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)],
                line=dict(width=2, color=color),
            ),
            customdata=d["race_name"],
            hovertemplate=(f"<b>{drv}</b><br>Putaran %{{x}} — %{{customdata}}"
                           f"<br>Poin: <b>%{{y}}</b><extra></extra>")
        ))

    fig.update_layout(**CL, height=380, legend=legh(-0.18),
        xaxis=ax("Putaran", dtick=2),
        yaxis=ax("Poin Kumulatif per Season"),
        hovermode="x unified",
        margin=dict(l=55, r=20, t=20, b=80))

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

    return html.Div([
        sec("Indikator Kinerja Utama", "lucide:trending-up"),
        partial_badge(n_races) if n_races < 24 else html.Span(),
        dbc.Row([
            dbc.Col(kpi_card("Pemimpin Klasemen", leader,
                f"▲ {lpts:.0f} poin · Gap +{gap:.0f} vs P2",
                C["red"], "lucide:trophy"), width=3),
            dbc.Col(kpi_card("Rata-rata Pit Stop", pit_d,
                "Rata-rata musim", C["teal"], "lucide:timer"), width=3),
            dbc.Col(kpi_card("Tingkat DNF", dnf_r,
                f"{dnf} DNF dari {tot} start",
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
            + ("" if show_all else " Menampilkan **Top 10 pembalap** berdasarkan poin.")
        ),
        card(dcc.Graph(figure=fig, config=dict(displayModeBar=False))),

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
    ])