# =============================================================================
# pages/datatable/layout.py — Halaman Tabel Data PaceFlow
# Berisi: driver standings, constructor standings, race calendar
# Fix: filter tahun in-page, nationality dari DB, kalender dari DB
# Fix: speed warning dynamic — auto-detect dari data, bukan hardcoded season
# =============================================================================

import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import (
    ico, card, sec, info_box, tbl_hdr, tbar,
    empty_state, safe_col
)
from layout.design_tokens import C, F, rgba, tc
from services.data_service import (
    get_analytics, get_constructor_season,
    get_calendar, get_seasons
)


def layout(season: int, flt: dict):
    df_r = get_analytics(season)
    dc   = get_constructor_season(season)
    cal  = get_calendar()

    if df_r.empty:
        return empty_state("Tidak ada data.", f"Season {season} belum tersedia.")

    flt    = flt or {}
    stat_f = flt.get("status")

    seasons     = get_seasons()
    season_opts = [{"label": "Semua Tahun", "value": "all"}] + \
                  [{"label": str(s), "value": s} for s in seasons]

    # ── Driver standings ─────────────────────────────────────────────────────
    lat = (df_r.sort_values("round", ascending=False)
               .drop_duplicates("driver_id"))
    lat["championship_pos"] = pd.to_numeric(
        lat["championship_pos"], errors="coerce").fillna(99)
    lat = lat.sort_values("championship_pos").reset_index(drop=True)
    lat["nat3"] = lat["driver_nat"].str[:3].str.upper().fillna("—")

    drw = []
    for i, (_, row) in enumerate(lat.iterrows()):
        pos  = int(row.get("championship_pos", 99) or 99)
        pc   = C["orange"] if pos == 1 else C["teal"] if pos <= 3 else C["text"]
        pod  = int(df_r[(df_r["driver_id"] == row["driver_id"]) &
                        (df_r["is_podium"] == True)].shape[0])
        fl   = int(df_r[(df_r["driver_id"] == row["driver_id"]) &
                        (df_r["fastest_lap_rank"] == 1)].shape[0]) \
               if safe_col(df_r, "fastest_lap_rank") else 0
        pole = int(df_r[(df_r["driver_id"] == row["driver_id"]) &
                        (df_r["qualifying_pos"] == 1)].shape[0]) \
               if safe_col(df_r, "qualifying_pos") else 0
        dnf  = int(df_r[(df_r["driver_id"] == row["driver_id"]) &
                        (df_r["is_dnf"] == True)].shape[0]) \
               if safe_col(df_r, "is_dnf") else 0
        drw.append(html.Tr([
            html.Td(str(pos) if pos < 99 else "—",
                style=dict(color=pc, fontWeight="800", fontSize="13px",
                           textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td([tbar(row["constructor"]), html.Div([
                html.Div(row["driver_name"], style=dict(color=C["text"],
                    fontSize="12px", fontWeight="600", fontFamily=F)),
                html.Div(str(row.get("driver_code", ""))[:3],
                    style=dict(color=C["muted"], fontSize="10px", fontFamily=F)),
            ], style=dict(display="inline-block", verticalAlign="middle"))],
            style=dict(padding="8px 10px")),
            html.Td(row["constructor"], style=dict(color=C["muted"],
                fontSize="11px", padding="8px 8px", fontFamily=F)),
            html.Td(row.get("nat3", "—"), style=dict(color=C["muted"],
                fontSize="11px", textAlign="center", padding="8px 6px", fontFamily=F)),
            html.Td(f"{row['cumulative_points']:.0f}", style=dict(color=C["text"],
                fontSize="13px", fontWeight="800", textAlign="center",
                padding="8px 8px", fontFamily=F)),
            html.Td(str(int(row.get("cumulative_wins", 0) or 0)),
                style=dict(color=C["orange"], fontWeight="700", fontSize="12px",
                           textAlign="center", padding="8px 6px", fontFamily=F)),
            html.Td(str(pod), style=dict(color=C["teal"], fontWeight="600",
                fontSize="12px", textAlign="center", padding="8px 6px", fontFamily=F)),
            html.Td(str(pole), style=dict(color=C["blue"], fontSize="11px",
                textAlign="center", padding="8px 6px", fontFamily=F)),
            html.Td(str(fl), style=dict(color=C["green"], fontSize="11px",
                textAlign="center", padding="8px 6px", fontFamily=F)),
            html.Td(str(dnf), style=dict(color=C["red"], fontSize="11px",
                fontWeight="600", textAlign="center", padding="8px 6px", fontFamily=F)),
        ], style=dict(borderBottom=f"1px solid {C['border']}",
            background=(rgba(C["red"], 0.04) if pos == 1
                        else C["grid"] if i % 2 == 0 else C["surface"]))))

    # ── Constructor standings ────────────────────────────────────────────────
    crw = []
    for i, (_, row) in enumerate(
            dc.sort_values("total_points", ascending=False).iterrows()):
        drv_names = " · ".join(sorted(set(
            df_r[df_r["constructor"] == row["constructor"]]
            ["driver_name"].dropna().unique().tolist()))[:2])
        spd   = row.get("avg_speed_kph")
        spd_s = f"{spd:.1f}" if pd.notna(spd) and float(spd or 0) > 0 else "—"
        crw.append(html.Tr([
            html.Td(str(i + 1), style=dict(color=C["muted"], fontSize="12px",
                textAlign="center", padding="10px 8px", fontFamily=F)),
            html.Td([tbar(row["constructor"]),
                html.Span(row["constructor"], style=dict(color=C["text"],
                    fontSize="12px", fontWeight="600", fontFamily=F))],
                style=dict(padding="10px 12px")),
            html.Td(drv_names, style=dict(color=C["muted"], fontSize="11px",
                padding="10px 10px", fontFamily=F)),
            html.Td(str(int(row["total_points"])), style=dict(color=C["text"],
                fontWeight="800", fontSize="13px", textAlign="center",
                padding="10px 8px", fontFamily=F)),
            html.Td(str(int(row["total_wins"])), style=dict(color=C["orange"],
                fontWeight="700", fontSize="12px", textAlign="center",
                padding="10px 8px", fontFamily=F)),
            html.Td(str(int(row["total_podiums"])), style=dict(color=C["teal"],
                fontWeight="600", fontSize="12px", textAlign="center",
                padding="10px 8px", fontFamily=F)),
            html.Td(spd_s, style=dict(color=C["muted"], fontSize="11px",
                textAlign="center", padding="10px 8px", fontFamily=F)),
        ], style=dict(borderBottom=f"1px solid {C['border']}",
            background=C["grid"] if i % 2 == 0 else C["surface"])))

    # ── Race calendar ────────────────────────────────────────────────────────
    cal_s = (cal[cal["season"] == season].sort_values("round")
             .reset_index(drop=True) if not cal.empty else pd.DataFrame())
    if stat_f and not cal_s.empty:
        cal_s = cal_s[cal_s["status"].isin(stat_f)]

    # Fix: speed warning dynamic — auto-detect dari data
    has_speed_cal = (not cal_s.empty and
        cal_s["avg_speed_kph"].apply(lambda x: x != "—").any())

    cal_rows = []
    for i, (_, row) in enumerate(cal_s.iterrows()):
        done = row.get("status", "") == "SELESAI"
        cal_rows.append(html.Tr([
            html.Td(str(int(row["round"])), style=dict(color=C["muted"],
                fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(row.get("date_fmt", "—"), style=dict(color=C["muted"],
                fontSize="11px", padding="9px 8px", fontFamily=F, whiteSpace="nowrap")),
            html.Td(html.B(row["race_name"], style=dict(color=C["text"],
                fontFamily=F, fontSize="11px")), style=dict(padding="9px 8px")),
            html.Td(row.get("circuit_name", "—"), style=dict(color=C["muted"],
                fontSize="10px", padding="9px 8px", fontFamily=F)),
            html.Td(str(row.get("laps", "—")), style=dict(color=C["muted"],
                fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(
                [tbar(row.get("constructor", "")) if done else html.Span(),
                 html.Span(row.get("driver_name", "—"),
                    style=dict(color=C["text"] if done else C["muted"],
                               fontSize="11px",
                               fontWeight="600" if done else "400",
                               fontFamily=F))]
                if done else html.Span("—", style=dict(
                    color=C["muted"], fontSize="11px", fontFamily=F)),
                style=dict(padding="9px 8px")),
            html.Td(str(row.get("fastest_lap_time", "—")),
                style=dict(color=C["green"] if done else C["muted"],
                           fontSize="11px", textAlign="center",
                           padding="9px 6px", fontFamily=F)),
            html.Td(str(row.get("avg_speed_kph", "—")),
                style=dict(color=C["teal"] if done else C["muted"],
                           fontSize="11px", textAlign="center",
                           padding="9px 6px", fontFamily=F)),
            html.Td(
                html.Span("● SELESAI", style=dict(color=C["green"],
                    fontSize="10px", fontWeight="700", fontFamily=F))
                if done else
                html.Span("○ BELUM", style=dict(color=C["muted"],
                    fontSize="10px", fontFamily=F)),
                style=dict(padding="9px 6px", textAlign="center")),
        ], style=dict(borderBottom=f"1px solid {C['border']}",
            background=C["grid"] if i % 2 == 0 else C["surface"])))

    n_done  = int((cal_s["status"] == "SELESAI").sum()) if not cal_s.empty else 0
    n_total = len(cal_s)

    return html.Div([
        sec("Tabel Data", "lucide:table"),

        # Filter tahun in-page — sesuai feedback dosen
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
            ], width=3),
            dbc.Col([
                html.Div("TAMPILKAN", style=dict(
                    fontSize="10px", fontWeight="700", letterSpacing="1px",
                    textTransform="uppercase", color=C["muted"],
                    marginBottom="5px", fontFamily=F)),
                dcc.RadioItems(
                    id="tbl-view-mode",
                    options=[
                        {"label": " Musim Ini", "value": "season"},
                        {"label": " Semua Musim", "value": "all"},
                    ],
                    value="season",
                    inline=True,
                    inputStyle=dict(marginRight="4px"),
                    labelStyle=dict(fontSize="12px", color=C["muted"],
                                    fontFamily=F, marginRight="16px"),
                ),
            ], width=4),
        ], className="g-3"), p="16px"),

        dcc.Tabs(value="drv", id="tabel-tabs", children=[
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
        ], style=dict(marginBottom="16px")),

        html.Div([
            html.Div(f"{len(lat)} pembalap · Season {season}",
                style=dict(fontSize="11px", color=C["muted"],
                           marginBottom="10px", fontFamily=F)),
            card(html.Div([
                html.Table([
                    tbl_hdr("Pos", "Pembalap", "Tim", "Nat", "Pts",
                            "W", "Pod", "Pole", "FL", "DNF"),
                    html.Tbody(drw),
                ], style=dict(width="100%", borderCollapse="collapse")),
            ], style=dict(overflowX="auto", overflowY="auto", maxHeight="550px"))),
        ], id="tabel-drv", style=dict(display="block")),

        html.Div([
            html.Div(f"{len(dc)} konstruktor · Season {season}",
                style=dict(fontSize="11px", color=C["muted"],
                           marginBottom="10px", fontFamily=F)),
            card(html.Table([
                tbl_hdr("Pos", "Konstruktor", "Pembalap", "Poin",
                        "Menang", "Podium", "Speed"),
                html.Tbody(crw),
            ], style=dict(width="100%", borderCollapse="collapse"))),
        ], id="tabel-con", style=dict(display="none")),

        html.Div([
            info_box("⚠️ Data kecepatan tidak tersedia untuk musim ini.",
                C["orange"]) if not has_speed_cal else html.Div(),
            html.Div(f"{n_done} selesai dari {n_total} race · Season {season}",
                style=dict(fontSize="11px", color=C["muted"],
                           marginBottom="10px", fontFamily=F)),
            card(html.Div([
                html.Table([
                    tbl_hdr("Rd", "Tanggal", "Grand Prix", "Sirkuit",
                            "Lap", "Pemenang", "Fastest Lap", "Speed", "Status"),
                    html.Tbody(cal_rows),
                ], style=dict(width="100%", borderCollapse="collapse")),
            ], style=dict(overflowX="auto", overflowY="auto", maxHeight="550px"))),
        ], id="tabel-cal", style=dict(display="none")),

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

        dcc.Store(id="store-tabel-data", data=lat.to_dict("records")),
    ])