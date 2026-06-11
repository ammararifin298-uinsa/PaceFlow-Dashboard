# =============================================================================
# pages/analytics/layout.py — Halaman Analitik PaceFlow
# Berisi: pit stop heatmap, bar chart pit, speed trend, qualifying scatter
# Update: toggle Top N speed chart, button group konsisten dengan beranda
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
        minHeight="260px", textAlign="center",
        background=C["surface"], border=f"1px solid {C['border']}",
        borderRadius="10px", boxShadow="0 1px 4px rgba(15,23,42,0.06)"))


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


def _chart_label(text):
    return html.Div(text, style=dict(
        fontSize="11px", fontWeight="600",
        color=C["muted"], marginBottom="8px", fontFamily=F))


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


def _speed_unavailable():
    return _placeholder(
        "lucide:gauge",
        "Data Kecepatan Belum Tersedia",
        "Data tren kecepatan rata-rata konstruktor tidak tersedia untuk musim ini. "
        "Coba pilih musim lain untuk melihat analitik kecepatan penuh.",
        C["orange"])


def layout(season: int, flt: dict):
    df_r = get_analytics(season)
    if df_r.empty:
        return empty_state("Tidak ada data.", f"Season {season} belum tersedia.")

    flt   = flt or {}
    drv_f = flt.get("drv")
    df    = (df_r[df_r["driver_name"].isin(drv_f)].copy()
             if drv_f else df_r.copy())

    pit = df[["driver_name", "constructor", "round", "best_pit_duration_s"]].dropna(
              subset=["best_pit_duration_s"]).reset_index(drop=True)

    # Speed
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
    n_con  = int(df_r["constructor"].nunique())

    total_r_scheduled = int(kpi_s.get("total_races_scheduled", 0) or 0)
    is_current = (total_r_scheduled > 0 and n_race < total_r_scheduled)
    n_rounds   = int(df_r["round"].nunique())
    pct_done   = round(n_rounds / total_r_scheduled * 100, 1) if total_r_scheduled > 0 else 100.0

    pit_txt = ""
    if not pit.empty:
        br = pit.loc[pit["best_pit_duration_s"].idxmin()]
        pit_txt = (f"**{br['driver_name']}** mencatat pit stop tercepat: "
                   f"**{br['best_pit_duration_s']:.3f}s** "
                   f"(Putaran {int(br['round'])}).")

    # ── Chart 1: Box Plot Durasi Pit Stop per Pembalap ──────────────────────────
    fig_box_pit = go.Figure()
    if not pit.empty:
        driver_medians = (pit.groupby("driver_name")["best_pit_duration_s"]
                          .median().sort_values(ascending=False))
        for drv in driver_medians.index:
            drv_pit = pit[pit["driver_name"] == drv]
            con = drv_pit["constructor"].iloc[0]
            fig_box_pit.add_trace(go.Box(
                x=drv_pit["best_pit_duration_s"],
                name=drv,
                orientation="h",
                marker_color=tc(con),
                boxpoints="outliers",
                jitter=0.3,
                pointpos=-1.8,
                showlegend=False,
                hovertemplate=f"<b>{drv} ({con})</b><br>Durasi: <b>%{{x:.3f}}s</b><extra></extra>"
            ))
        fig_box_pit.update_layout(
            **CL, height=max(300, len(driver_medians) * 28),
            xaxis=ax("Durasi Pit Stop (detik)"),
            yaxis=dict(gridcolor=C["grid"], linecolor=C["border"],
                       tickfont=dict(size=10, color=C["text"])),
            margin=dict(l=130, r=20, t=10, b=20)
        )

    # ── Chart 2: Bar chart pit tercepat per driver ──────────────────────────
    fig_fastest_pit = go.Figure()
    if not pit.empty:
        fastest_pit = (pit.loc[pit.groupby("driver_name")["best_pit_duration_s"].idxmin()]
                       .sort_values("best_pit_duration_s", ascending=True))
        fig_fastest_pit.add_trace(go.Bar(
            x=fastest_pit["best_pit_duration_s"],
            y=fastest_pit["driver_name"],
            orientation="h",
            marker_color=[tc(t) for t in fastest_pit["constructor"]],
            marker_line=dict(width=0),
            text=fastest_pit["best_pit_duration_s"].apply(lambda v: f"{v:.3f}s"),
            textposition="outside",
            textfont=dict(size=9, color=C["muted"]),
            hovertemplate="<b>%{y}</b><br>Tercepat: <b>%{x:.3f}s</b><extra></extra>",
            showlegend=False,
        ))
        fig_fastest_pit.update_layout(**CL, height=max(300, len(fastest_pit) * 28),
            showlegend=False,
            xaxis=ax("Durasi Pit Tercepat (detik)"),
            yaxis=dict(gridcolor=C["grid"], linecolor=C["border"],
                       tickfont=dict(size=10, color=C["text"])),
            margin=dict(l=140, r=60, t=10, b=30))

    # Store data
    store_cols = ["season", "round", "race_name", "driver_name", "constructor",
                  "avg_pit_duration_s", "best_pit_duration_s",
                  "avg_speed_kph", "qualifying_pos", "position"]
    analitik_store = dcc.Store(id="store-analitik-data",
                               data=df_r[store_cols].to_dict("records"))

    # ── Header banner ────────────────────────────────────────────────────────
    if is_current:
        banner = _header_banner(
            "MUSIM SEDANG BERLANGSUNG", "lucide:flag",
            f"{n_rounds} dari {total_r_scheduled} Race Selesai · {pct_done}%",
            f"linear-gradient(135deg, {C['red']} 0%, #9B1C1C 100%)",
            f"{lpts:.0f}", f"poin · {leader}")
    else:
        banner = _header_banner(
            f"MUSIM {season} SELESAI", "lucide:check-circle",
            f"Juara Dunia: {leader} ({lcon})",
            "linear-gradient(135deg, #059669 0%, #065F46 100%)",
            f"{lpts:.0f}", "poin · juara")

    # ── KPI row ──────────────────────────────────────────────────────────────
    if is_current:
        kpi_row = dbc.Row([
            dbc.Col(kpi_card("Pemimpin Saat Ini", leader,
                f"{lpts:.0f} poin · {lcon}", C["red"], "lucide:trophy"), width=4),
            dbc.Col(kpi_card("Race Selesai", f"{n_rounds}",
                f"dari {total_r_scheduled} Grand Prix", C["orange"], "lucide:flag"), width=4),
            dbc.Col(kpi_card("Pembalap Aktif", f"{n_drv}",
                f"Season {season}", C["blue"], "lucide:users"), width=4),
        ], className="g-3")
    else:
        kpi_row = dbc.Row([
            dbc.Col(kpi_card(f"Juara Dunia {season}", leader,
                f"▲ {lpts:.0f} poin · {lcon}", C["red"], "lucide:trophy"), width=3),
            dbc.Col(kpi_card("Total Race", f"{n_race}",
                "Grand Prix selesai", C["teal"], "lucide:flag"), width=3),
            dbc.Col(kpi_card("Pembalap", f"{n_drv}",
                "Aktif sepanjang musim", C["blue"], "lucide:users"), width=3),
            dbc.Col(kpi_card("Konstruktor", f"{n_con}",
                "Tim peserta", C["orange"], "lucide:shield"), width=3),
        ], className="g-3")

    # ── Pit section ──────────────────────────────────────────────────────────
    pit_card = card(
        info_box(pit_txt) if pit_txt else html.Div(),
        dbc.Row([
            dbc.Col([
                _chart_label("Distribusi Durasi Pit Stop per Pembalap (Box Plot)"),
                dcc.Graph(figure=fig_box_pit, config=dict(displayModeBar=False))
                if not pit.empty else
                _placeholder("lucide:grid-3x3",
                             "Data Pit Belum Tersedia" if is_current else "Data Pit Tidak Tersedia",
                             "Data akan muncul setelah race selesai." if is_current else "",
                             C["orange"] if is_current else C["muted"]),
            ], width=7),
            dbc.Col([
                _chart_label("Durasi Pit Stop Tercepat per Pembalap"),
                dcc.Graph(figure=fig_fastest_pit, config=dict(displayModeBar=False))
                if not pit.empty else
                _placeholder("lucide:bar-chart-2",
                             "Data Belum Tersedia" if is_current else "Tidak Ada Data",
                             "Perlu minimal 3 race." if is_current else "",
                             C["orange"] if is_current else C["muted"]),
            ], width=5),
        ], className="g-3"),
    )

    # ── Speed col dengan toggle ───────────────────────────────────────────────
    spd_col = dbc.Col([
        _chart_label("Tren Kecepatan Rata-rata Per Konstruktor"),
        html.Div([
            _btn_toggle("btn-spd-top5",   "Top 5",  True),
            _btn_toggle("btn-spd-top10",  "Top 10", False),
            _btn_toggle("btn-spd-topall", "Semua",  False),
        ], style=dict(display="flex", gap="6px", marginBottom="10px"))
        if has_spd else html.Div(),
        dcc.Graph(id="graph-analitik-spd",
                  config=dict(displayModeBar=False))
        if has_spd else _speed_unavailable(),
    ], width=6)

    # ── Qualifying col ────────────────────────────────────────────────────────
    qvr_col = dbc.Col([
        _chart_label("Posisi Kualifikasi vs Posisi Finish"),
        html.Div([
            _btn_toggle("btn-qvr-top5",   "Top 5",  True),
            _btn_toggle("btn-qvr-top10",  "Top 10", False),
            _btn_toggle("btn-qvr-topall", "Semua",  False),
        ], style=dict(display="flex", gap="6px", marginBottom="10px"))
        if not qvr.empty else html.Div(),
        dcc.Graph(id="graph-analitik-qvr",
                  config=dict(displayModeBar=False))
        if not qvr.empty else
        _placeholder("lucide:target", "Data Kualifikasi Tidak Tersedia",
                     "Data akan tersedia setelah race berjalan."
                     if is_current else "", C["muted"]),
    ], width=6)

    speed_qual_card = card(dbc.Row([spd_col, qvr_col], className="g-3"))

    # ── Chart 3: Donut DNF Causes ─────────────────────────────────────────────
    from services.data_service import get_dnf_causes
    dnf_df = get_dnf_causes(season)
    has_dnf = not dnf_df.empty

    fig_dnf = go.Figure()
    if has_dnf:
        top_dnf = dnf_df.nlargest(8, "total")          # max 8 slice
        others  = dnf_df[~dnf_df.index.isin(top_dnf.index)]
        if not others.empty:
            import pandas as pd
            top_dnf = pd.concat([top_dnf, pd.DataFrame([{
                "dnf_cause": "Lainnya",
                "total":     others["total"].sum(),
                "percentage":others["percentage"].sum(),
                "season":    season,
            }])], ignore_index=True)

        dnf_colors = [
            "#DC2626","#D97706","#059669","#1D4ED8",
            "#0891B2","#7C3AED","#DB2777","#64748B",
        ]
        fig_dnf.add_trace(go.Pie(
            labels=top_dnf["dnf_cause"],
            values=top_dnf["total"],
            hole=0.55,
            marker=dict(colors=dnf_colors[:len(top_dnf)],
                        line=dict(color=C["surface"], width=2)),
            textinfo="label+percent",
            textfont=dict(size=10, family=F, color=C["text"]),
            hovertemplate="<b>%{label}</b><br>Kejadian: <b>%{value}</b><br>%{percent}<extra></extra>",
            insidetextorientation="radial",
        ))
        total_dnf_count = int(dnf_df["total"].sum())
        fig_dnf.update_layout(
            **CL, height=300,
            showlegend=True,
            legend=dict(
                orientation="v", x=1.0, y=0.5,
                font=dict(size=9, color=C["muted"]),
                bgcolor="rgba(0,0,0,0)"
            ),
            margin=dict(l=10, r=10, t=20, b=10),
            annotations=[dict(
                text=f"<b>{total_dnf_count}</b><br><span style='font-size:9px'>Total DNF</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=13, color=C["text"], family=F),
                xanchor="center"
            )]
        )

    dnf_card = card(dbc.Row([
        dbc.Col([
            _chart_label("Distribusi Penyebab DNF"),
            dcc.Graph(figure=fig_dnf, config=dict(displayModeBar=False))
            if has_dnf else
            _placeholder("lucide:alert-circle", "Tidak Ada DNF",
                         "Tidak ada DNF yang tercatat di musim ini.", C["green"]),
        ], width=6),
        dbc.Col([
            _chart_label("Top Penyebab DNF"),
            html.Div([
                html.Div([
                    html.Div(style=dict(
                        width="8px", height="8px", borderRadius="50%",
                        background=["#DC2626","#D97706","#059669","#1D4ED8",
                                    "#0891B2","#7C3AED","#DB2777","#64748B"]
                                   [i % 8],
                        flexShrink="0", marginTop="3px")),
                    html.Div([
                        html.Div(str(row["dnf_cause"]),
                            style=dict(fontSize="11px", fontWeight="600",
                                       color=C["text"], fontFamily=F)),
                        html.Div(f"{int(row['total'])} kejadian · {row['percentage']:.1f}%",
                            style=dict(fontSize="10px", color=C["muted"], fontFamily=F)),
                    ], style=dict(flex="1")),
                ], style=dict(display="flex", alignItems="flex-start",
                              gap="10px", marginBottom="10px"))
                for i, (_, row) in enumerate(dnf_df.nlargest(8, "total").iterrows())
            ]) if has_dnf else
            html.Div("Semua pembalap finish.", style=dict(
                color=C["green"], fontSize="12px", fontFamily=F,
                padding="20px", textAlign="center")),
        ], width=6),
    ], className="g-3"))

    # ── Rakit halaman ─────────────────────────────────────────────────────────
    children = [
        sec(f"Analitik Musim {season}", "lucide:activity"),
        banner,
        kpi_row,
        sec(f"Strategi Pit Stop{'  (Data Parsial)' if is_current else ''}", "lucide:wrench"),
        pit_card,
        sec("Penyebab DNF", "lucide:alert-triangle"),
        dnf_card,
    ]

    if has_spd or not qvr.empty or not is_current:
        children += [
            sec("Kecepatan dan Kualifikasi", "lucide:gauge"),
            speed_qual_card,
        ]

    children += [
        analitik_store,
        dcc.Store(id="store-spd-topn", data=5),
        dcc.Store(id="store-qvr-topn", data=5),
        _download_btn(),
    ]
    return html.Div(children)