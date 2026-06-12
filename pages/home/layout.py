# =============================================================================
# pages/home/layout.py — Halaman Beranda PaceFlow
# Update: Race Calendar, Peta Sirkuit (Scattergeo), Demografi Pembalap
#         + pakai btn_toggle global dari layout.components (no local duplicate)
# =============================================================================

import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import (
    ico, card, sec, info_box, kpi_card,
    empty_state, partial_badge, safe_contains,
    btn_toggle, BTN_ACTIVE, BTN_INACTIVE
)
from layout.design_tokens import C, F, CL, ax, legh, rgba, tc, MARKER_SYMBOLS
from services.data_service import (
    get_analytics, get_kpi, get_constructor_season,
    get_calendar, get_circuits, get_drivers_info
)
from pages.home.callbacks import _build_points_fig


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Warna status race calendar
# ─────────────────────────────────────────────────────────────────────────────
def _status_badge(status):
    if status == "SELESAI":
        return html.Span("✓ SELESAI", style=dict(
            background=rgba(C["green"], 0.12), color=C["green"],
            fontSize="9px", fontWeight="700", padding="2px 8px",
            borderRadius="4px", fontFamily=F, whiteSpace="nowrap",
        ))
    return html.Span("— BELUM", style=dict(
        background=rgba(C["muted"], 0.1), color=C["muted"],
        fontSize="9px", fontWeight="700", padding="2px 8px",
        borderRadius="4px", fontFamily=F, whiteSpace="nowrap",
    ))


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Kalender Race — Table rows
# ─────────────────────────────────────────────────────────────────────────────
def _build_calendar(season: int):
    df = get_calendar()
    df = df[df["season"] == season].sort_values("round").reset_index(drop=True)
    if df.empty:
        return html.Div("Data kalender tidak tersedia.",
                        style=dict(fontSize="12px", color=C["muted"], fontFamily=F))

    header = html.Div([
        html.Div("Rnd",      style=dict(width="36px",  fontSize="9px", fontWeight="700", color=C["muted"], fontFamily=F)),
        html.Div("Grand Prix", style=dict(flex="2",    fontSize="9px", fontWeight="700", color=C["muted"], fontFamily=F)),
        html.Div("Lokasi",   style=dict(flex="1",      fontSize="9px", fontWeight="700", color=C["muted"], fontFamily=F)),
        html.Div("Tanggal",  style=dict(flex="1",      fontSize="9px", fontWeight="700", color=C["muted"], fontFamily=F)),
        html.Div("Pemenang", style=dict(flex="1.2",    fontSize="9px", fontWeight="700", color=C["muted"], fontFamily=F)),
        html.Div("Status",   style=dict(width="80px",  fontSize="9px", fontWeight="700", color=C["muted"], fontFamily=F, textAlign="right")),
    ], style=dict(
        display="flex", alignItems="center", gap="8px",
        padding="6px 10px", borderBottom=f"1px solid {C['border']}",
        marginBottom="2px",
    ))

    rows = []
    for _, r in df.iterrows():
        winner = str(r.get("driver_name", "—"))
        con    = str(r.get("constructor", "—"))
        hover_text = f"{winner} ({con})" if winner != "—" else "—"
        rows.append(html.Div([
            html.Div(f"R{int(r['round'])}", style=dict(
                width="36px", fontSize="11px", fontWeight="700",
                color=C["blue"], fontFamily=F,
            )),
            html.Div(str(r["race_name"]), style=dict(
                flex="2", fontSize="11px", fontWeight="600",
                color=C["text"], fontFamily=F, overflow="hidden",
                textOverflow="ellipsis", whiteSpace="nowrap",
            )),
            html.Div(f"{r['city']}, {r['country']}", style=dict(
                flex="1", fontSize="10px", color=C["muted"],
                fontFamily=F, overflow="hidden",
                textOverflow="ellipsis", whiteSpace="nowrap",
            )),
            html.Div(str(r.get("date_fmt", "—")), style=dict(
                flex="1", fontSize="10px", color=C["muted"], fontFamily=F,
            )),
            html.Div(hover_text, style=dict(
                flex="1.2", fontSize="10px", color=C["text"],
                fontFamily=F, overflow="hidden",
                textOverflow="ellipsis", whiteSpace="nowrap",
            )),
            html.Div(_status_badge(str(r.get("status", "BELUM"))),
                     style=dict(width="80px", textAlign="right")),
        ], style=dict(
            display="flex", alignItems="center", gap="8px",
            padding="7px 10px",
            borderBottom=f"1px solid {rgba(C['border'], 0.5)}",
            background="transparent",
        )))

    n_done  = int((df["status"] == "SELESAI").sum())
    n_total = len(df)
    progress = html.Div([
        html.Div(style=dict(
            height="3px", borderRadius="2px",
            width=f"{n_done/n_total*100:.0f}%",
            background=C["blue"],
        )),
    ], style=dict(
        background=rgba(C["blue"], 0.1),
        borderRadius="2px", marginBottom="10px",
        height="3px",
    ))

    summary = html.Div(
        f"{n_done} dari {n_total} balapan selesai "
        f"({n_done/n_total*100:.0f}%)",
        style=dict(fontSize="10px", color=C["muted"],
                   fontFamily=F, marginBottom="8px")
    )
    return html.Div([summary, progress, header, *rows])


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Peta Sirkuit Scattergeo
# ─────────────────────────────────────────────────────────────────────────────
def _build_circuit_map(season: int):
    cal = get_calendar()
    cal = cal[cal["season"] == season].sort_values("round")

    if cal.empty:
        return None

    merged = cal.dropna(subset=["lat", "lng"])
    if merged.empty:
        return None

    done = merged[merged["status"] == "SELESAI"]
    todo = merged[merged["status"] != "SELESAI"]

    fig = go.Figure()

    # Race yang sudah selesai
    if not done.empty:
        fig.add_trace(go.Scattergeo(
            lat=done["lat"], lon=done["lng"],
            mode="markers+text",
            marker=dict(size=9, color=C["blue"],
                        line=dict(width=1, color="#fff")),
            text=done["round"].astype(int).astype(str),
            textposition="top center",
            textfont=dict(size=8, color=C["text"]),
            hovertemplate=(
                "<b>R%{customdata[0]} — %{customdata[1]}</b><br>"
                "%{customdata[2]}, %{customdata[3]}<br>"
                "Pemenang: <b>%{customdata[4]}</b><extra></extra>"
            ),
            customdata=done[["round", "race_name", "city",
                             "country", "driver_name"]].values,
            name="Selesai", showlegend=True,
        ))

    # Race yang belum
    if not todo.empty:
        fig.add_trace(go.Scattergeo(
            lat=todo["lat"], lon=todo["lng"],
            mode="markers+text",
            marker=dict(size=7, color=C["muted"], opacity=0.5,
                        line=dict(width=1, color="#fff")),
            text=todo["round"].astype(int).astype(str),
            textposition="top center",
            textfont=dict(size=8, color=C["muted"]),
            hovertemplate=(
                "<b>R%{customdata[0]} — %{customdata[1]}</b><br>"
                "%{customdata[2]}, %{customdata[3]}<br>"
                "Belum berlangsung<extra></extra>"
            ),
            customdata=todo[["round", "race_name", "city", "country"]].values,
            name="Belum", showlegend=True,
        ))

    fig.update_layout(
        **CL, height=320,
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(
            scope="world",
            showland=True, landcolor="#F1F5F9",
            showocean=True, oceancolor="#E8F4FD",
            showcoastlines=True, coastlinecolor="#CBD5E1",
            showcountries=True, countrycolor="#CBD5E1",
            showframe=False,
            bgcolor=C["bg"],
            projection_type="natural earth",
        ),
        legend=dict(
            orientation="h", x=0.5, y=-0.05,
            xanchor="center", yanchor="top",
            font=dict(size=10, color=C["muted"], family=F),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
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

    # Data grafik championship
    tr = (df.groupby(["driver_name", "round", "race_name", "constructor"],
                     as_index=False)[["season_cumulative_points", "cumulative_points"]].max()
            .sort_values(["driver_name", "round"]))

    # Grafik konstruktor (horizontal bar)
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

    # Peta sirkuit
    fig_map = _build_circuit_map(season)

    # Demografi pembalap (kebangsaan)
    drivers_info = get_drivers_info()

    return html.Div([
        # ── KPI ───────────────────────────────────────────────────────────────
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

        # ── Championship Chart ────────────────────────────────────────────────
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
                    btn_toggle("btn-top5",   "Top 5",  True),
                    btn_toggle("btn-top10",  "Top 10", False),
                    btn_toggle("btn-topall", "Semua",  False),
                ], style=dict(display="flex", gap="6px")),
                html.Div([
                    btn_toggle("btn-mode-poin",   "Poin",   True),
                    btn_toggle("btn-mode-posisi", "Posisi", False),
                ], style=dict(display="flex", gap="6px")),
            ], style=dict(display="flex", justifyContent="space-between",
                          marginBottom="12px")),
            dcc.Graph(id="graph-championship",
                      figure=_build_points_fig(tr, 5),
                      config=dict(displayModeBar=False),
                      style=dict(overflow="visible")),
        ),

        # ── Konstruktor ───────────────────────────────────────────────────────
        sec("Performa Konstruktor", "lucide:bar-chart-2"),
        card(dcc.Graph(figure=fig_cb, config=dict(displayModeBar=False))),

        # ── Peta Sirkuit ──────────────────────────────────────────────────────
        sec("Peta Sirkuit Grand Prix", "lucide:map-pin"),
        card(
            dcc.Graph(
                figure=fig_map,
                config=dict(displayModeBar=False),
                style=dict(height="320px"),
            ) if fig_map else html.Div(
                "Data peta sirkuit belum tersedia.",
                style=dict(fontSize="12px", color=C["muted"],
                           fontFamily=F, padding="20px")
            )
        ),

        # ── Kalender Balapan ──────────────────────────────────────────────────
        sec("Kalender Balapan", "lucide:calendar"),
        card(_build_calendar(season)),

        # ── Demografi Pembalap ────────────────────────────────────────────────
        *(_build_driver_demographics(drivers_info, season, df_r)
          if not drivers_info.empty else []),

        # Download + stores
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


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Demografi Pembalap — Kebangsaan & Usia
# ─────────────────────────────────────────────────────────────────────────────
def _build_driver_demographics(drivers_info, season, df_r):
    import pandas as pd
    from datetime import date

    # Ambil hanya driver yang aktif di musim ini
    active_drivers = df_r["driver_id"].unique()
    ddf = drivers_info[drivers_info["driver_id"].isin(active_drivers)].copy()

    if ddf.empty:
        return []

    # Hitung usia
    today = date.today()
    def calc_age(dob):
        try:
            d = pd.to_datetime(dob)
            return today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        except Exception:
            return None

    ddf["age"] = ddf["date_of_birth"].apply(calc_age)

    # Kebangsaan unik
    nat_counts = ddf["nationality"].value_counts().reset_index()
    nat_counts.columns = ["nationality", "count"]

    # Grafik donut kebangsaan
    flag_colors = [C["blue"], "#7C3AED", C["orange"], C["green"],
                   C["teal"], C["red"], "#F59E0B", "#10B981", "#6366F1",
                   "#EF4444", "#84CC16", "#06B6D4"]

    fig_nat = go.Figure(go.Pie(
        labels=nat_counts["nationality"],
        values=nat_counts["count"],
        hole=0.55,
        marker=dict(colors=flag_colors[:len(nat_counts)],
                    line=dict(color="#fff", width=1.5)),
        textfont=dict(size=9, family=F),
        hovertemplate="<b>%{label}</b>: %{value} pembalap<extra></extra>",
        showlegend=True,
    ))
    fig_nat.update_layout(
        **CL, height=220,
        margin=dict(l=0, r=0, t=10, b=10),
        legend=dict(
            font=dict(size=9, color=C["muted"], family=F),
            orientation="v", x=1.0, y=0.5,
            xanchor="left", yanchor="middle",
        ),
        annotations=[dict(
            text=f"<b>{len(ddf)}</b><br>Pembalap",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color=C["text"], family=F),
        )],
    )

    # Top 5 pembalap muda
    youngest = ddf.dropna(subset=["age"]).nsmallest(5, "age")

    age_cards = []
    for _, row in youngest.iterrows():
        age_cards.append(html.Div([
            html.Div(str(row.get("driver_name", "—")).split()[-1], style=dict(
                fontSize="11px", fontWeight="700",
                color=C["text"], fontFamily=F,
            )),
            html.Div(f"{int(row['age'])} th · #{int(row['driver_number'])}" 
                     if pd.notna(row.get("driver_number")) else f"{int(row['age'])} th",
                     style=dict(fontSize="10px", color=C["muted"], fontFamily=F)),
            html.Div(str(row.get("nationality", "—")), style=dict(
                fontSize="9px", color=C["blue"],
                fontFamily=F, fontWeight="600",
            )),
        ], style=dict(
            background=C["surface"],
            border=f"1px solid {C['border']}",
            borderRadius="8px", padding="10px 12px",
            minWidth="90px",
        )))

    return [
        sec("Demografi Pembalap", "lucide:users"),
        dbc.Row([
            dbc.Col([
                html.Div("Kebangsaan", style=dict(
                    fontSize="9px", fontWeight="700", letterSpacing="1.5px",
                    color=C["muted"], fontFamily=F,
                    textTransform="uppercase", marginBottom="8px",
                )),
                dcc.Graph(figure=fig_nat, config=dict(displayModeBar=False)),
            ], width=5),
            dbc.Col([
                html.Div("5 Pembalap Termuda", style=dict(
                    fontSize="9px", fontWeight="700", letterSpacing="1.5px",
                    color=C["muted"], fontFamily=F,
                    textTransform="uppercase", marginBottom="8px",
                )),
                html.Div(age_cards, style=dict(
                    display="flex", flexWrap="wrap", gap="8px",
                )),
            ], width=7),
        ], className="g-3"),
        html.Div(style=dict(marginBottom="16px")),
    ]