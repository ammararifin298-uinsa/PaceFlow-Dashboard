# =============================================================================
# pages/analytics/layout.py — Halaman Analitik PaceFlow
# Berisi: pit stop heatmap, box plot, speed trend, qualifying scatter
# Fix: handler per season (2024 lengkap, 2025 tanpa speed, 2026 parsial)
# =============================================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import (
    ico, card, sec, info_box, kpi_card, empty_state, safe_col
)
from layout.design_tokens import C, F, CL, ax, legh, rgba, tc, MARKER_SYMBOLS
from services.data_service import get_analytics, get_kpi


def _placeholder(icon, title, desc, color=None):
    c = color or C["muted"]
    return html.Div([
        html.Div([ico(icon, 28, rgba(c, 0.6))],
            style=dict(width="60px", height="60px", borderRadius="50%",
                background=rgba(c, 0.08), border=f"2px dashed {rgba(c, 0.3)}",
                display="flex", alignItems="center",
                justifyContent="center", marginBottom="12px")),
        html.Div(title, style=dict(fontSize="13px", fontWeight="700",
            color=C["text"], fontFamily=F)),
        html.Div(desc, style=dict(fontSize="11px", color=C["muted"],
            fontFamily=F, marginTop="4px", lineHeight="1.6",
            maxWidth="240px", textAlign="center")),
    ], style=dict(display="flex", flexDirection="column", alignItems="center",
        justifyContent="center", padding="40px 20px",
        minHeight="260px", textAlign="center"))


def _stat_badge(label, value, color):
    return html.Div([
        html.Div(value, style=dict(fontSize="20px", fontWeight="900",
            color=color, fontFamily=F, lineHeight="1")),
        html.Div(label, style=dict(fontSize="9px", fontWeight="700",
            color=C["muted"], fontFamily=F, letterSpacing="0.8px",
            textTransform="uppercase", marginTop="3px")),
    ], style=dict(textAlign="center", padding="14px 20px",
        background=rgba(color, 0.07),
        border=f"1px solid {rgba(color, 0.2)}",
        borderRadius="10px", flex="1"))


def _header_banner(status_text, status_icon, detail_text, gradient, value, value_sub):
    return html.Div([
        html.Div([
            html.Div([
                ico(status_icon, 16, "#FFF"),
                html.Span(status_text, style=dict(fontSize="11px", fontWeight="800",
                    letterSpacing="2px", color="#FFF", marginLeft="8px", fontFamily=F)),
            ], style=dict(display="flex", alignItems="center", marginBottom="6px")),
            html.Div(detail_text, style=dict(fontSize="12px",
                color="rgba(255,255,255,0.8)", fontFamily=F)),
        ]),
        html.Div([
            html.Div(value, style=dict(fontSize="28px", fontWeight="900",
                color="#FFF", fontFamily=F, lineHeight="1")),
            html.Div(value_sub, style=dict(fontSize="11px",
                color="rgba(255,255,255,0.7)", fontFamily=F)),
        ], style=dict(textAlign="right")),
    ], style=dict(background=gradient, borderRadius="12px", padding="18px 24px",
        display="flex", justifyContent="space-between",
        alignItems="center", marginBottom="16px"))


def _download_btn():
    return html.Div(
        html.Button([
            ico("lucide:download", 13, "#FFF"),
            html.Span(" Download CSV", style=dict(marginLeft="5px")),
        ], id="btn-analitik", n_clicks=0,
        style=dict(display="flex", alignItems="center",
                   background=C["blue"], color="#FFF",
                   border="none", borderRadius="6px",
                   padding="8px 16px", fontSize="11px",
                   fontWeight="600", fontFamily=F, cursor="pointer")),
    style=dict(display="flex", justifyContent="flex-end", marginBottom="16px"))


def layout(season: int, flt: dict):
    df_r = get_analytics(season)
    if df_r.empty:
        return empty_state("Tidak ada data.", f"Season {season} belum tersedia.")

    flt   = flt or {}
    drv_f = flt.get("drv")
    df    = (df_r[df_r["driver_name"].isin(drv_f)].copy()
             if drv_f else df_r.copy())

    # Data pit stop
    pit = df[["driver_name", "round", "best_pit_duration_s"]].dropna(
              subset=["best_pit_duration_s"])
    pb  = df[["driver_name", "constructor", "avg_pit_duration_s"]].dropna(
              subset=["avg_pit_duration_s"])

    # Speed — cek dari df_r (semua driver, bukan filtered)
    sg = (df_r.dropna(subset=["avg_speed_kph"])
              .groupby(["constructor", "race_name", "round"])["avg_speed_kph"]
              .mean().reset_index().sort_values("round"))
    has_spd = not sg.empty and float(sg["avg_speed_kph"].sum()) > 0

    # Qualifying
    qvr = df[["driver_name", "constructor", "qualifying_pos",
               "position", "race_name"]].dropna(
                   subset=["qualifying_pos", "position"])

    # KPI
    kpi_s  = get_kpi(season)
    leader = str(kpi_s.get("points_leader", "—"))
    lpts   = float(kpi_s.get("leader_points", 0) or 0)
    lcon   = str(kpi_s.get("leader_constructor", "—"))
    n_race = int(kpi_s.get("total_races", 0) or 0)
    n_drv  = int(df_r["driver_id"].nunique())

    pit_txt = ""
    if not pit.empty:
        br = pit.loc[pit["best_pit_duration_s"].idxmin()]
        pit_txt = (f"**{br['driver_name']}** mencatat pit stop tercepat: "
                   f"**{br['best_pit_duration_s']:.3f}s** "
                   f"(Putaran {int(br['round'])}).")

    # Chart 1: Heatmap pit
    fig_hm = go.Figure()
    if not pit.empty:
        pv = pit.pivot_table(index="driver_name", columns="round",
                             values="best_pit_duration_s", aggfunc="min")
        show_text = len(pv.columns) <= 12
        fig_hm.add_trace(go.Heatmap(
            z=[[float(v) if pd.notna(v) else None for v in row] for row in pv.values],
            x=[f"R{int(c)}" for c in pv.columns],
            y=list(pv.index),
            text=[[f"{float(v):.2f}s" if pd.notna(v) else "" for v in row]
                  for row in pv.values],
            texttemplate="%{text}" if show_text else "",
            textfont=dict(size=8, color="white"),
            colorscale=[[0, "#059669"], [0.5, "#D97706"], [1, "#DC2626"]],
            hoverongaps=False,
            hovertemplate="<b>%{y}</b> — %{x}<br>Pit: <b>%{z:.3f}s</b><extra></extra>",
            colorbar=dict(title=dict(text="Detik", side="right"),
                          tickfont=dict(size=9, color=C["muted"]), len=0.9, thickness=12)
        ))
        fig_hm.update_layout(**CL, height=360, margin=dict(l=130, r=20, t=10, b=20))

    # Chart 2: Box plot pit
    fig_box = go.Figure()
    if not pb.empty:
        order = (pb.groupby("driver_name")["avg_pit_duration_s"]
                   .median().sort_values().index)
        for drv in order:
            d     = pb[pb["driver_name"] == drv]
            color = tc(d["constructor"].iloc[0] if not d.empty else "")
            fig_box.add_trace(go.Box(
                y=d["avg_pit_duration_s"].tolist(), name=drv[:12],
                marker_color=color, line_color=color,
                fillcolor=rgba(color, 0.25), boxmean="sd", showlegend=False,
                hovertemplate=f"<b>{drv}</b><br>%{{y:.3f}}s<extra></extra>"
            ))
        fig_box.update_layout(**CL, height=340, showlegend=False,
            yaxis=ax("Durasi Pit (detik)"), xaxis=ax(angle=-35),
            margin=dict(l=55, r=20, t=10, b=100))

    # Chart 3: Speed trend — marker dibedakan
    fig_spd = go.Figure()
    if has_spd:
        for i, team in enumerate(sg["constructor"].unique()):
            d     = sg[sg["constructor"] == team].sort_values("round")
            color = tc(team)
            fig_spd.add_trace(go.Scatter(
                x=d["round"].tolist(), y=d["avg_speed_kph"].tolist(),
                mode="lines+markers", name=team,
                line=dict(width=2, color=color),
                marker=dict(size=7, color="#FFFFFF",
                            symbol=MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)],
                            line=dict(width=2, color=color)),
                customdata=d["race_name"].tolist(),
                hovertemplate=(f"<b>{team}</b><br>%{{customdata}}<br>"
                               f"Kecepatan: %{{y:.1f}} km/h<extra></extra>")
            ))
        fig_spd.update_layout(**CL, height=320, legend=legh(-0.25),
            xaxis=ax("Putaran", dtick=2),
            yaxis=ax("Kecepatan Rata-rata (km/h)"),
            hovermode="x unified", margin=dict(l=65, r=20, t=10, b=100))

    # Chart 4: Qualifying scatter
    fig_qvr = go.Figure()
    if not qvr.empty:
        for team in qvr["constructor"].unique():
            d     = qvr[qvr["constructor"] == team]
            color = tc(team)
            fig_qvr.add_trace(go.Scatter(
                x=d["qualifying_pos"].tolist(), y=d["position"].tolist(),
                mode="markers", name=team,
                marker=dict(size=7, color=color, opacity=0.75,
                            line=dict(width=1, color=C["surface"])),
                customdata=d[["driver_name", "race_name"]].values.tolist(),
                hovertemplate=("<b>%{customdata[0]}</b><br>%{customdata[1]}"
                               "<br>Kualifikasi: %{x} → Finish: %{y}<extra></extra>")
            ))
        mp = int(qvr[["qualifying_pos", "position"]].max().max())
        fig_qvr.add_shape(type="line", x0=1, y0=1, x1=mp, y1=mp,
            line=dict(color=C["red"], dash="dash", width=1.5))
        fig_qvr.add_annotation(x=mp * 0.6, y=mp * 0.5,
            text="Balapan Sempurna", showarrow=False,
            font=dict(color=C["red"], size=10, family=F))
        fig_qvr.update_layout(**CL, height=320, legend=legh(-0.25),
            xaxis=ax("Posisi Kualifikasi", dtick=2),
            yaxis=ax("Posisi Finish", dtick=2, rev=True),
            margin=dict(l=55, r=20, t=10, b=100))

    # Store data
    store_cols = ["season", "round", "race_name", "driver_name", "constructor",
                  "avg_pit_duration_s", "best_pit_duration_s",
                  "avg_speed_kph", "qualifying_pos", "position"]
    analitik_store = dcc.Store(id="store-analitik-data",
                               data=df_r[store_cols].to_dict("records"))

    # ── Season 2026: Musim Berjalan ──────────────────────────────────────────
    if season == 2026:
        total_r  = 24
        n_rounds = int(df_r["round"].nunique())
        pct      = round(n_rounds / total_r * 100, 1)
        return html.Div([
            sec("Analitik Musim 2026", "lucide:activity"),
            _header_banner("MUSIM SEDANG BERLANGSUNG", "lucide:flag",
                f"{n_rounds} dari {total_r} Race Selesai · {pct}%",
                f"linear-gradient(135deg, {C['red']} 0%, #9B1C1C 100%)",
                f"{lpts:.0f}", f"poin · {leader}"),
            dbc.Row([
                dbc.Col(kpi_card("Pemimpin Saat Ini", leader,
                    f"{lpts:.0f} poin · {lcon}", C["red"], "lucide:trophy"), width=4),
                dbc.Col(kpi_card("Race Selesai", f"{n_rounds}",
                    f"dari {total_r} Grand Prix", C["orange"], "lucide:flag"), width=4),
                dbc.Col(kpi_card("Pembalap Aktif", f"{n_drv}",
                    f"Season {season}", C["blue"], "lucide:users"), width=4),
            ], className="g-3"),
            sec("Strategi Pit Stop (Data Parsial)", "lucide:wrench"),
            card(dbc.Row([
                dbc.Col([
                    html.Div("Heatmap Durasi Pit Stop", style=dict(
                        fontSize="11px", fontWeight="600",
                        color=C["muted"], marginBottom="8px", fontFamily=F)),
                    dcc.Graph(figure=fig_hm, config=dict(displayModeBar=False))
                    if not pit.empty else
                    _placeholder("lucide:grid-3x3", "Pit Data Belum Tersedia",
                                 "Data muncul setelah race selesai.", C["orange"]),
                ], width=7),
                dbc.Col([
                    html.Div("Konsistensi Per Pembalap", style=dict(
                        fontSize="11px", fontWeight="600",
                        color=C["muted"], marginBottom="8px", fontFamily=F)),
                    dcc.Graph(figure=fig_box, config=dict(displayModeBar=False))
                    if not pb.empty else
                    _placeholder("lucide:bar-chart-2", "Box Plot Belum Tersedia",
                                 "Perlu minimal 3 race.", C["orange"]),
                ], width=5),
            ], className="g-3")),
            analitik_store, _download_btn(),
        ])

    # ── Season 2025: Selesai tanpa speed ────────────────────────────────────
    if season == 2025:
        n_con = int(df_r["constructor"].nunique())
        return html.Div([
            sec("Analitik Musim 2025", "lucide:activity"),
            _header_banner("MUSIM 2025 SELESAI", "lucide:check-circle",
                f"Juara Dunia: {leader} ({lcon})",
                f"linear-gradient(135deg, {C['blue']} 0%, #1E3A8A 100%)",
                f"{lpts:.0f}", "poin total"),
            dbc.Row([
                dbc.Col(kpi_card("Juara Dunia 2025", leader,
                    f"▲ {lpts:.0f} poin · {lcon}", C["red"], "lucide:trophy"), width=3),
                dbc.Col(kpi_card("Total Race", f"{n_race}",
                    "Grand Prix selesai", C["teal"], "lucide:flag"), width=3),
                dbc.Col(kpi_card("Pembalap", f"{n_drv}",
                    "Aktif sepanjang musim", C["blue"], "lucide:users"), width=3),
                dbc.Col(kpi_card("Konstruktor", f"{n_con}",
                    "Tim peserta", C["orange"], "lucide:shield"), width=3),
            ], className="g-3"),
            sec("Strategi Pit Stop Musim 2025", "lucide:wrench"),
            card(
                info_box(pit_txt) if pit_txt else html.Div(),
                dbc.Row([
                    dbc.Col([
                        html.Div("Heatmap Durasi Pit Stop", style=dict(
                            fontSize="11px", fontWeight="600",
                            color=C["muted"], marginBottom="8px", fontFamily=F)),
                        dcc.Graph(figure=fig_hm, config=dict(displayModeBar=False))
                        if not pit.empty else
                        _placeholder("lucide:grid-3x3", "Data Pit Tidak Tersedia", "", C["muted"]),
                    ], width=7),
                    dbc.Col([
                        html.Div("Konsistensi Per Pembalap", style=dict(
                            fontSize="11px", fontWeight="600",
                            color=C["muted"], marginBottom="8px", fontFamily=F)),
                        dcc.Graph(figure=fig_box, config=dict(displayModeBar=False))
                        if not pb.empty else
                        _placeholder("lucide:bar-chart-2", "Box Plot Tidak Tersedia", "", C["muted"]),
                    ], width=5),
                ], className="g-3"),
            ),
            info_box("Data kecepatan (avg_speed_kph) tidak tersedia untuk Season 2025. "
                     "Lihat Season 2024 untuk analitik kecepatan penuh.", C["orange"]),
            sec("Kualifikasi vs Hasil Balapan", "lucide:target") if not qvr.empty else html.Div(),
            card(dcc.Graph(figure=fig_qvr, config=dict(displayModeBar=False))) if not qvr.empty else html.Div(),
            analitik_store, _download_btn(),
        ])

    # ── Season 2024: Analitik Lengkap ───────────────────────────────────────
    return html.Div([
        sec("Analitik Musim 2024", "lucide:activity"),
        _header_banner("MUSIM 2024 SELESAI", "lucide:check-circle",
            f"Juara Dunia: {leader} ({lcon})",
            "linear-gradient(135deg, #059669 0%, #065F46 100%)",
            f"{lpts:.0f}", "poin · juara"),
        dbc.Row([
            dbc.Col(kpi_card("Juara Dunia 2024", leader,
                f"▲ {lpts:.0f} poin · {lcon}", C["red"], "lucide:trophy"), width=3),
            dbc.Col(kpi_card("Total Race", f"{n_race}",
                "Grand Prix selesai", C["teal"], "lucide:flag"), width=3),
            dbc.Col(kpi_card("Pembalap", f"{n_drv}",
                "Aktif sepanjang musim", C["blue"], "lucide:users"), width=3),
            dbc.Col(kpi_card("Data Pit", f"{len(pit)}",
                "entri pit stop tercatat", C["orange"], "lucide:wrench"), width=3),
        ], className="g-3"),
        sec("Strategi Pit Stop", "lucide:wrench"),
        card(
            info_box(pit_txt) if pit_txt else html.Div(),
            dbc.Row([
                dbc.Col([
                    html.Div("Heatmap Durasi Pit Stop per Pembalap", style=dict(
                        fontSize="11px", fontWeight="600",
                        color=C["muted"], marginBottom="8px", fontFamily=F)),
                    dcc.Graph(figure=fig_hm, config=dict(displayModeBar=False))
                    if not pit.empty else
                    _placeholder("lucide:grid-3x3", "Tidak Ada Data", ""),
                ], width=7),
                dbc.Col([
                    html.Div("Konsistensi Pit Stop per Pembalap", style=dict(
                        fontSize="11px", fontWeight="600",
                        color=C["muted"], marginBottom="8px", fontFamily=F)),
                    dcc.Graph(figure=fig_box, config=dict(displayModeBar=False))
                    if not pb.empty else
                    _placeholder("lucide:bar-chart-2", "Tidak Ada Data", ""),
                ], width=5),
            ], className="g-3"),
        ),
        sec("Kecepatan dan Kualifikasi", "lucide:gauge"),
        card(dbc.Row([
            dbc.Col([
                html.Div("Tren Kecepatan Rata-rata Per Konstruktor", style=dict(
                    fontSize="11px", fontWeight="600",
                    color=C["muted"], marginBottom="8px", fontFamily=F)),
                dcc.Graph(figure=fig_spd, config=dict(displayModeBar=False))
                if has_spd else
                _placeholder("lucide:trending-up", "Data Kecepatan Tidak Tersedia", ""),
            ], width=6),
            dbc.Col([
                html.Div("Posisi Kualifikasi vs Posisi Finish", style=dict(
                    fontSize="11px", fontWeight="600",
                    color=C["muted"], marginBottom="8px", fontFamily=F)),
                dcc.Graph(figure=fig_qvr, config=dict(displayModeBar=False))
                if not qvr.empty else
                _placeholder("lucide:target", "Data Kualifikasi Tidak Tersedia", ""),
            ], width=6),
        ], className="g-3")),
        analitik_store, _download_btn(),
    ])