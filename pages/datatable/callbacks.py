# =============================================================================
# pages/datatable/callbacks.py — Callbacks reaktif halaman Tabel Data
# Arsitektur: konten tabel diisi via callback, bukan full re-render
# Ini memastikan:
#   1. Tab tidak reset ketika season/filter berubah
#   2. Filter langsung berefek ke tabel tanpa reload halaman
#   3. Tidak ada konflik dengan global store-season / store-filter
# =============================================================================

import pandas as pd
from dash import Input, Output, State, no_update, html, dcc
import dash_bootstrap_components as dbc

from layout.components import (
    card, info_box, tbl_hdr, tbar, empty_state, safe_col, ico
)
from layout.design_tokens import C, F, rgba, tc
from services.data_service import (
    get_analytics, get_constructor_season, get_calendar, get_seasons,
    get_qualifying, get_pit_stops
)


# ─── helper ────────────────────────────────────────────────────────────────────
def _safe_float(v):
    try:
        val = float(v)
        return val if pd.notna(val) else 0.0
    except Exception:
        return 0.0


def _is_valid_speed(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip()
    return s not in ("", "—", "None", "nan", "0", "0.0")


# ─── Bangun baris tabel driver ─────────────────────────────────────────────────
def _build_driver_rows(df_r):
    if df_r.empty:
        return []
    lat = (df_r.sort_values("round", ascending=False)
               .drop_duplicates("driver_id"))
    lat["championship_pos"] = pd.to_numeric(
        lat["championship_pos"], errors="coerce").fillna(99)
    lat = lat.sort_values("championship_pos").reset_index(drop=True)
    lat["nat3"] = lat["driver_nat"].str[:3].str.upper().fillna("—")

    rows = []
    for i, (_, row) in enumerate(lat.iterrows()):
        pos  = int(row.get("championship_pos", 99) or 99)
        pc   = C["orange"] if pos == 1 else C["teal"] if pos <= 3 else C["text"]
        did  = row["driver_id"]
        pod  = int(df_r[(df_r["driver_id"] == did) & (df_r["is_podium"] == True)].shape[0])
        fl   = int(df_r[(df_r["driver_id"] == did) & (df_r["fastest_lap_rank"] == 1)].shape[0]) \
               if safe_col(df_r, "fastest_lap_rank") else 0
        pole = int(df_r[(df_r["driver_id"] == did) & (df_r["qualifying_pos"] == 1)].shape[0]) \
               if safe_col(df_r, "qualifying_pos") else 0
        dnf  = int(df_r[(df_r["driver_id"] == did) & (df_r["is_dnf"] == True)].shape[0]) \
               if safe_col(df_r, "is_dnf") else 0
        rows.append(html.Tr([
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
        ], style=dict(
            borderBottom=f"1px solid {C['border']}",
            background=(rgba(C["red"], 0.04) if pos == 1
                        else C["grid"] if i % 2 == 0 else C["surface"])
        )))
    return rows, lat


# ─── Bangun baris tabel constructor ────────────────────────────────────────────
def _build_constructor_rows(dc, df_r):
    if dc.empty:
        return []
    rows = []
    for i, (_, row) in enumerate(dc.sort_values("total_points", ascending=False).iterrows()):
        drv_names = " · ".join(sorted(set(
            df_r[df_r["constructor"] == row["constructor"]]
            ["driver_name"].dropna().unique().tolist()))[:2])
        spd   = _safe_float(row.get("avg_speed_kph"))
        spd_s = f"{spd:.1f}" if spd > 0 else "—"
        rows.append(html.Tr([
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
        ], style=dict(
            borderBottom=f"1px solid {C['border']}",
            background=C["grid"] if i % 2 == 0 else C["surface"]
        )))
    return rows


# ─── Bangun baris kalender ──────────────────────────────────────────────────────
def _build_calendar_rows(cal_s):
    if cal_s.empty:
        return []
    rows = []
    for i, (_, row) in enumerate(cal_s.iterrows()):
        done = row.get("status", "") == "SELESAI"
        rows.append(html.Tr([
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
        ], style=dict(
            borderBottom=f"1px solid {C['border']}",
            background=C["grid"] if i % 2 == 0 else C["surface"]
        )))
    return rows


def _build_qualifying_rows(df):
    if df.empty:
        return []
    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        rows.append(html.Tr([
            html.Td(str(int(row["round"])), style=dict(color=C["muted"],
                fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(html.B(row["race_name"], style=dict(color=C["text"],
                fontFamily=F, fontSize="11px")), style=dict(padding="9px 8px")),
            html.Td(str(int(row["position"])) if pd.notna(row["position"]) else "—", style=dict(color=C["blue"],
                fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F, fontWeight="700")),
            html.Td([
                tbar(row.get("constructor", "")),
                html.Span(row.get("driver_name", "—"), style=dict(color=C["text"], fontSize="11px", fontWeight="600", fontFamily=F))
            ], style=dict(padding="9px 8px")),
            html.Td(str(row.get("q1", "—")), style=dict(color=C["muted"], fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(str(row.get("q2", "—")), style=dict(color=C["muted"], fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(str(row.get("q3", "—")), style=dict(color=C["teal"], fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F, fontWeight="600")),
        ], style=dict(
            borderBottom=f"1px solid {C['border']}",
            background=C["grid"] if i % 2 == 0 else C["surface"]
        )))
    return rows


def _build_pitstop_rows(df):
    if df.empty:
        return []
    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        rows.append(html.Tr([
            html.Td(str(int(row["round"])), style=dict(color=C["muted"],
                fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(html.B(row["race_name"], style=dict(color=C["text"],
                fontFamily=F, fontSize="11px")), style=dict(padding="9px 8px")),
            html.Td(html.Span(row.get("driver_name", "—"), style=dict(color=C["text"], fontSize="11px", fontWeight="600", fontFamily=F)), style=dict(padding="9px 8px")),
            html.Td(str(int(row["stop"])) if pd.notna(row["stop"]) else "—", style=dict(color=C["blue"], fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(str(int(row["lap"])) if pd.notna(row["lap"]) else "—", style=dict(color=C["muted"], fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(str(row.get("stop_time", "—")), style=dict(color=C["muted"], fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F)),
            html.Td(str(row.get("duration_s", "—")), style=dict(color=C["teal"], fontSize="11px", textAlign="center", padding="9px 6px", fontFamily=F, fontWeight="600")),
        ], style=dict(
            borderBottom=f"1px solid {C['border']}",
            background=C["grid"] if i % 2 == 0 else C["surface"]
        )))
    return rows

# ═══════════════════════════════════════════════════════════════════════════════
def register_callbacks(app):

    # ── 1. Sinkronisasi tahun → store-season (allow_duplicate) ────────────
    @app.callback(
        Output("store-season", "data", allow_duplicate=True),
        Input("tbl-year-filter", "value"),
        prevent_initial_call=True,
    )
    def sync_year_filter(year):
        if year:
            return int(year)
        return no_update

    # ── 2. Update opsi dropdown driver & constructor saat tahun berubah ────
    @app.callback(
        Output("tbl-drv-filter", "options"),
        Output("tbl-drv-filter", "value"),
        Output("tbl-con-filter", "options"),
        Output("tbl-con-filter", "value"),
        Input("tbl-year-filter", "value"),
        prevent_initial_call=True,
    )
    def update_filter_options(year):
        if not year:
            return [], None, [], None
        df = get_analytics(int(year))
        if df.empty:
            return [], None, [], None
        drv_opts = [{"label": d, "value": d}
                    for d in sorted(df["driver_name"].dropna().unique())]
        con_opts = [{"label": c, "value": c}
                    for c in sorted(df["constructor"].dropna().unique())]
        return drv_opts, None, con_opts, None

    # ── 3. Render Konten Tab Aktif ─────────────────────────────────────────
    @app.callback(
        Output("tab-content", "children"),
        Input("tabel-tabs", "value"),
        Input("tbl-year-filter", "value"),
        Input("tbl-drv-filter", "value"),
        Input("tbl-con-filter", "value"),
    )
    def render_active_tab(tab, year, drv_filter, con_filter):
        if not year:
            return empty_state("Pilih tahun terlebih dahulu.", "")
            
        y = int(year)

        if tab == "drv":
            df_r = get_analytics(y).copy()
            if df_r.empty:
                return empty_state("Tidak ada data driver.", f"Season {y} belum tersedia.")
            if drv_filter:
                df_r = df_r[df_r["driver_name"].isin(
                    drv_filter if isinstance(drv_filter, list) else [drv_filter])]
            if con_filter:
                df_r = df_r[df_r["constructor"].isin(
                    con_filter if isinstance(con_filter, list) else [con_filter])]
            if df_r.empty:
                return empty_state("Tidak ada data.", "Coba ubah filter pembalap/konstruktor.")
            result = _build_driver_rows(df_r)
            if not result:
                return empty_state("Tidak ada data.", "")
            drw, lat = result
            return html.Div([
                html.Div(f"{len(lat)} pembalap · Season {y}",
                    style=dict(fontSize="11px", color=C["muted"],
                               marginBottom="10px", fontFamily=F)),
                card(html.Div([
                    html.Table([
                        tbl_hdr("Pos", "Pembalap", "Tim", "Nat", "Pts",
                                "W", "Pod", "Pole", "FL", "DNF"),
                        html.Tbody(drw),
                    ], style=dict(width="100%", borderCollapse="collapse")),
                ], style=dict(overflowX="auto", overflowY="auto", maxHeight="550px"))),
            ])

        elif tab == "con":
            dc   = get_constructor_season(y).copy()
            df_r = get_analytics(y).copy()
            if dc.empty:
                return empty_state("Tidak ada data konstruktor.", f"Season {y} belum tersedia.")
            if con_filter:
                flt = con_filter if isinstance(con_filter, list) else [con_filter]
                dc   = dc[dc["constructor"].isin(flt)]
                df_r = df_r[df_r["constructor"].isin(flt)]
            crw = _build_constructor_rows(dc, df_r)
            if not crw:
                return empty_state("Tidak ada data.", "Coba ubah filter konstruktor.")
            return html.Div([
                html.Div(f"{len(dc)} konstruktor · Season {y}",
                    style=dict(fontSize="11px", color=C["muted"],
                               marginBottom="10px", fontFamily=F)),
                card(html.Table([
                    tbl_hdr("Pos", "Konstruktor", "Pembalap", "Poin",
                            "Menang", "Podium", "Speed"),
                    html.Tbody(crw),
                ], style=dict(width="100%", borderCollapse="collapse"))),
            ])

        elif tab == "cal":
            cal = get_calendar()
            cal_s = (cal[cal["season"] == y].sort_values("round")
                     .reset_index(drop=True)) if not cal.empty else pd.DataFrame()
            if cal_s.empty:
                return empty_state("Tidak ada kalender.", f"Season {y} tidak ditemukan.")
            has_speed = cal_s["avg_speed_kph"].apply(_is_valid_speed).any() \
                        if "avg_speed_kph" in cal_s.columns else False
            cal_rows = _build_calendar_rows(cal_s)
            n_done   = int((cal_s["status"] == "SELESAI").sum())
            n_total  = len(cal_s)
            return html.Div([
                info_box("⚠️ Data kecepatan tidak tersedia untuk musim ini.", C["orange"])
                    if not has_speed else html.Div(),
                html.Div(f"{n_done} selesai dari {n_total} race · Season {y}",
                    style=dict(fontSize="11px", color=C["muted"],
                               marginBottom="10px", fontFamily=F)),
                card(html.Div([
                    html.Table([
                        tbl_hdr("Rd", "Tanggal", "Grand Prix", "Sirkuit",
                                "Lap", "Pemenang", "Fastest Lap", "Speed", "Status"),
                        html.Tbody(cal_rows),
                    ], style=dict(width="100%", borderCollapse="collapse")),
                ], style=dict(overflowX="auto", overflowY="auto", maxHeight="550px"))),
            ])

        elif tab == "qua":
            qua = get_qualifying(y)
            if qua.empty:
                return empty_state("Tidak ada data kualifikasi.", f"Season {y} belum tersedia.")
            if drv_filter:
                flt = drv_filter if isinstance(drv_filter, list) else [drv_filter]
                qua = qua[qua["driver_name"].isin(flt)]
            if con_filter:
                flt = con_filter if isinstance(con_filter, list) else [con_filter]
                qua = qua[qua["constructor"].isin(flt)]
            if qua.empty:
                return empty_state("Tidak ada data.", "Coba ubah filter.")
            qua_rows = _build_qualifying_rows(qua)
            return html.Div([
                html.Div(f"{len(qua)} rekor kualifikasi · Season {y}",
                    style=dict(fontSize="11px", color=C["muted"],
                               marginBottom="10px", fontFamily=F)),
                card(html.Div([
                    html.Table([
                        tbl_hdr("Rd", "Grand Prix", "Pos", "Pembalap", "Q1", "Q2", "Q3"),
                        html.Tbody(qua_rows),
                    ], style=dict(width="100%", borderCollapse="collapse")),
                ], style=dict(overflowX="auto", overflowY="auto", maxHeight="550px"))),
            ])

        elif tab == "pit":
            pit = get_pit_stops(y)
            if pit.empty:
                return empty_state("Tidak ada data pit stop.", f"Season {y} belum tersedia.")
            if drv_filter:
                flt = drv_filter if isinstance(drv_filter, list) else [drv_filter]
                pit = pit[pit["driver_name"].isin(flt)]
            if pit.empty:
                return empty_state("Tidak ada data.", "Coba ubah filter.")
            pit_rows = _build_pitstop_rows(pit)
            return html.Div([
                html.Div(f"{len(pit)} rekor pit stop · Season {y}",
                    style=dict(fontSize="11px", color=C["muted"],
                               marginBottom="10px", fontFamily=F)),
                card(html.Div([
                    html.Table([
                        tbl_hdr("Rd", "Grand Prix", "Pembalap", "Stop", "Lap", "Time", "Duration (s)"),
                        html.Tbody(pit_rows),
                    ], style=dict(width="100%", borderCollapse="collapse")),
                ], style=dict(overflowX="auto", overflowY="auto", maxHeight="550px"))),
            ])

        return empty_state("Tab tidak ditemukan.", "")