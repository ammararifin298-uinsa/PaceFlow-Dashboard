# =============================================================================
# pages/standings/layout.py — Halaman Klasemen PaceFlow
# Berisi: driver standings, constructor standings
# Fix: nationality dari driver_nat (DB), bukan drivers.csv
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import (
    ico, card, sec, kpi_card, tbl_hdr, tbar,
    empty_state, safe_contains, safe_col
)
from layout.design_tokens import C, F, CL, ax, rgba, tc
from services.data_service import get_analytics, get_constructor_season


def layout(season: int, flt: dict):
    df_r = get_analytics(season)
    dc   = get_constructor_season(season)

    if df_r.empty:
        return empty_state("Tidak ada data.", f"Season {season} belum tersedia.")

    flt    = flt or {}
    search = flt.get("search", "") or ""

    # Latest standing per driver
    lat = (df_r.sort_values("round", ascending=False)
               .drop_duplicates("driver_id"))

    if search:
        lat = lat[safe_contains(lat["driver_name"], search)]

    lat["championship_pos"] = pd.to_numeric(
        lat["championship_pos"], errors="coerce").fillna(99)
    lat = lat.sort_values("championship_pos").reset_index(drop=True)

    # Nationality dari driver_nat — tidak perlu drivers.csv lagi
    lat["nat3"] = lat["driver_nat"].str[:3].str.upper().fillna("—")

    # Grafik driver
    fig_d = go.Figure()
    for _, row in lat.sort_values("cumulative_points").iterrows():
        fig_d.add_trace(go.Bar(
            y=[row["driver_name"]], x=[row["cumulative_points"]],
            orientation="h", showlegend=False,
            marker_color=tc(row["constructor"]),
            marker_line=dict(width=0),
            hovertemplate=(f"<b>{row['driver_name']}</b><br>"
                           f"{row['constructor']}<br>"
                           f"Poin: <b>{row['cumulative_points']:.0f}</b>"
                           f"<extra></extra>")
        ))
    fig_d.update_layout(**CL, height=max(300, len(lat) * 22),
        showlegend=False, barmode="overlay",
        xaxis=ax("Poin Kumulatif"),
        yaxis=dict(gridcolor=C["grid"], linecolor=C["border"],
                   tickfont=dict(size=10, color=C["text"])),
        margin=dict(l=160, r=40, t=10, b=30))

    # Tabel driver
    drw = []
    for i, (_, row) in enumerate(lat.iterrows()):
        pos  = int(row.get("championship_pos", 99) or 99)
        pc   = C["orange"] if pos == 1 else C["teal"] if pos <= 3 else C["text"]
        pod  = int(df_r[(df_r["driver_id"] == row["driver_id"]) &
                        (df_r["is_podium"] == True)].shape[0])
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
        ], style=dict(borderBottom=f"1px solid {C['border']}",
            background=(rgba(C["red"], 0.04) if pos == 1
                        else C["grid"] if i % 2 == 0 else C["surface"]))))

    # Grafik konstruktor
    dc_s = dc.sort_values("total_points", ascending=True)
    fig_c = go.Figure()
    for _, row in dc_s.iterrows():
        fig_c.add_trace(go.Bar(
            y=[row["constructor"]], x=[row["total_points"]],
            orientation="h", showlegend=False,
            marker_color=tc(row["constructor"]),
            marker_line=dict(width=0),
            hovertemplate=(f"<b>{row['constructor']}</b><br>"
                           f"Poin: <b>{row['total_points']:.0f}</b><extra></extra>")
        ))
    fig_c.update_layout(**CL, height=320, showlegend=False, barmode="overlay",
        xaxis=ax("Total Poin"),
        yaxis=dict(gridcolor=C["grid"], linecolor=C["border"],
                   tickfont=dict(size=10, color=C["text"])),
        margin=dict(l=140, r=40, t=10, b=30))

    # Tabel konstruktor
    crw = []
    for i, (_, row) in enumerate(
            dc.sort_values("total_points", ascending=False).iterrows()):
        spd = row.get("avg_speed_kph")
        spd_s = (f"{spd:.1f}" if pd.notna(spd) and float(spd or 0) > 0 else "—")
        crw.append(html.Tr([
            html.Td(str(i + 1), style=dict(color=C["muted"], fontSize="12px",
                                            textAlign="center", padding="10px 8px", fontFamily=F)),
            html.Td([tbar(row["constructor"]),
                html.Span(row["constructor"], style=dict(color=C["text"],
                    fontSize="12px", fontWeight="600", fontFamily=F))],
                style=dict(padding="10px 12px")),
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

    # ── Constructor Championship Progression (Line Chart) ────────────────────
    from services.data_service import get_constructor_progression
    prog_df = get_constructor_progression(season)

    fig_prog = go.Figure()
    if not prog_df.empty:
        for con in prog_df["constructor"].unique():
            sub = prog_df[prog_df["constructor"] == con].sort_values("round")
            fig_prog.add_trace(go.Scatter(
                x=sub["round"],
                y=sub["cumulative_points"],
                mode="lines+markers",
                name=con,
                line=dict(color=tc(con), width=2.5),
                marker=dict(size=5, color=tc(con)),
                hovertemplate=(f"<b>{con}</b><br>Round %{{x}}<br>"
                               "Poin: <b>%{y:.0f}</b><extra></extra>")
            ))
        fig_prog.update_layout(
            **CL, height=320,
            xaxis=ax("Round", dtick=1),
            yaxis=ax("Poin Kumulatif"),
            legend=dict(
                orientation="h", y=-0.25, x=0,
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=9, color=C["muted"])
            ),
            margin=dict(l=40, r=20, t=10, b=60),
            hovermode="x unified",
        )

    # ── Treemap Konstruktor ────────────────────────────────────────────────────
    import plotly.express as px
    fig_tree = go.Figure()
    if not dc.empty:
        dc_tree = dc.sort_values("total_points", ascending=False).copy()
        dc_tree["color_val"] = dc_tree["total_points"].astype(float)
        dc_tree["label_txt"] = dc_tree.apply(
            lambda r: f"{r['constructor']}<br>{int(r['total_points'])} pts<br>"
                      f"{int(r['total_wins'])}W · {int(r['total_podiums'])}P",
            axis=1)
        fig_tree.add_trace(go.Treemap(
            labels=dc_tree["constructor"],
            parents=[""] * len(dc_tree),
            values=dc_tree["total_points"],
            text=dc_tree["label_txt"],
            textinfo="text",
            textfont=dict(family=F, size=11),
            marker=dict(
                colors=[tc(c) for c in dc_tree["constructor"]],
                line=dict(width=2, color=C["surface"]),
                pad=dict(t=4, b=4, l=4, r=4),
            ),
            hovertemplate="<b>%{label}</b><br>Poin: <b>%{value:.0f}</b><extra></extra>",
        ))
        fig_tree.update_layout(
            **CL, height=280,
            margin=dict(l=0, r=0, t=10, b=0),
        )

    return html.Div([
        sec("Klasemen Pembalap", "lucide:user"),
        dbc.Row([
            dbc.Col(card(dcc.Graph(figure=fig_d,
                config=dict(displayModeBar=False))), width=5),
            dbc.Col(card(html.Div([
                html.Table([
                    tbl_hdr("Pos", "Pembalap", "Tim", "Nat", "Pts", "W", "Pod"),
                    html.Tbody(drw),
                ], style=dict(width="100%", borderCollapse="collapse")),
            ], style=dict(overflowY="auto", maxHeight="500px"))), width=7),
        ], className="g-3"),

        sec("Klasemen Konstruktor", "lucide:shield"),
        dbc.Row([
            dbc.Col(card(dcc.Graph(figure=fig_c,
                config=dict(displayModeBar=False))), width=5),
            dbc.Col(card(html.Table([
                tbl_hdr("Pos", "Konstruktor", "Poin", "Menang", "Podium", "Speed"),
                html.Tbody(crw),
            ], style=dict(width="100%", borderCollapse="collapse"))), width=7),
        ], className="g-3"),

        sec("Progres Poin Konstruktor", "lucide:trending-up"),
        card(dcc.Graph(figure=fig_prog, config=dict(displayModeBar=False)))
        if not prog_df.empty else
        html.Div("Data progres konstruktor belum tersedia.",
            style=dict(color=C["muted"], fontSize="12px", fontFamily=F,
                       padding="20px", textAlign="center")),

        sec("Distribusi Poin Konstruktor (Treemap)", "lucide:layout-grid"),
        card(dcc.Graph(figure=fig_tree, config=dict(displayModeBar=False)))
        if not dc.empty else html.Div(),

        html.Div(
            html.Button([
                ico("lucide:download", 13, "#FFF"),
                html.Span(" Download CSV", style=dict(marginLeft="5px")),
            ], id="btn-klasemen", n_clicks=0,
            style=dict(display="flex", alignItems="center",
                       background=C["blue"], color="#FFF",
                       border="none", borderRadius="6px",
                       padding="8px 16px", fontSize="11px",
                       fontWeight="600", fontFamily=F,
                       cursor="pointer", marginBottom="16px")),
        style=dict(display="flex", justifyContent="flex-end")),

        dcc.Store(id="store-klasemen-data", data=lat.to_dict("records")),
    ])