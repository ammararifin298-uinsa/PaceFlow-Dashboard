# =============================================================================
# pages/home/callbacks.py — Callbacks Halaman Beranda PaceFlow
# Berisi: toggle Top N + toggle mode Poin/Posisi championship chart
# Dipanggil via register_callbacks(app) dari app.py
# =============================================================================

from dash import Input, Output, State, no_update, callback_context
import plotly.graph_objects as go
import pandas as pd
from layout.design_tokens import C, CL, tc, MARKER_SYMBOLS

F = "Inter, -apple-system, sans-serif"

BTN_ACTIVE   = dict(background=C["blue"], color="#FFF",
                    border=f"1px solid {C['blue']}", borderRadius="6px",
                    padding="4px 14px", fontSize="11px", fontWeight="600",
                    fontFamily=F, cursor="pointer")
BTN_INACTIVE = dict(background=C["surface"], color=C["muted"],
                    border=f"1px solid {C['border']}", borderRadius="6px",
                    padding="4px 14px", fontSize="11px", fontWeight="600",
                    fontFamily=F, cursor="pointer")

_LEGEND_SIDE = dict(
    orientation="v",
    x=1.01, y=1,
    xanchor="left", yanchor="top",
    bgcolor="rgba(0,0,0,0)",
    font=dict(size=9, color=C["muted"]),
    itemsizing="constant",
    itemclick="toggleothers",
    itemdoubleclick="toggle",
)
_LEGEND_BOTTOM = dict(
    orientation="h", y=-0.25, x=0.5,
    xanchor="center", yanchor="top",
    bgcolor="rgba(0,0,0,0)",
    font=dict(size=9, color=C["muted"]),
    itemsizing="constant",
    itemclick="toggleothers",
    itemdoubleclick="toggle",
)
_XAXIS = dict(
    title_font=dict(size=11, color=C["muted"]),
    tickfont=dict(size=10, color=C["muted"]),
    dtick=1, gridcolor="#E2E8F0",
    linecolor=C["border"], zerolinecolor=C["border"],
    showgrid=True,
)
_YAXIS = dict(
    title_font=dict(size=11, color=C["muted"]),
    tickfont=dict(size=10, color=C["muted"]),
    gridcolor="#E2E8F0",
    linecolor=C["border"], zerolinecolor=C["border"],
    showgrid=True,
)


def _parse_restyle(restyle_data, traces):
    """
    Parse restyleData dari klik legend (toggleothers) untuk menentukan
    driver mana yang sedang dipilih user.
    Returns nama driver (str) atau None jika tidak ada seleksi.
    """
    try:
        style_updates = restyle_data[0]
        trace_indices = restyle_data[1]
        visibilities  = style_updates.get("visible", [])
        if not visibilities:
            return None

        # Kasus 1: deteksi grup legenda mana saja yang diaktifkan (True)
        if not isinstance(visibilities, list):
            visibilities = [visibilities]

        apply_single_val = (len(visibilities) == 1)
        trues = set()

        for j, idx in enumerate(trace_indices):
            vis = visibilities[0] if apply_single_val else (visibilities[j] if j < len(visibilities) else None)
            if idx < len(traces):
                grp = traces[idx].get("legendgroup")
                if grp and vis is True:
                    trues.add(grp)

        # Jika ada lebih dari satu grup diubah menjadi True -> reset/show-all
        if len(trues) > 1:
            return None

        # Jika hanya ada tepat satu grup diubah menjadi True -> isolasi grup tersebut
        if len(trues) == 1:
            return list(trues)[0]

        # Kasus 2: semua menjadi legendonly → temukan driver aktif berdasarkan exclusion
        is_all_legendonly = False
        if apply_single_val and visibilities[0] == "legendonly":
            is_all_legendonly = True
        elif not apply_single_val and all(v == "legendonly" for v in visibilities):
            is_all_legendonly = True

        if is_all_legendonly:
            hidden_set = set(trace_indices)
            for i, trace in enumerate(traces):
                if i not in hidden_set:
                    grp   = trace.get("legendgroup")
                    x_val = trace.get("x")
                    # skip dummy trace (x=[None])
                    if grp and x_val is not None and x_val != [None]:
                        return grp

        return None
    except Exception:
        return None


def _build_points_fig(tr, top_n, selected_driver=None):
    top_drivers = (tr.groupby("driver_name")["season_cumulative_points"]
                   .max().nlargest(top_n).index.tolist())
    top5 = (tr.groupby("driver_name")["season_cumulative_points"]
            .max().nlargest(5).index.tolist())
    all_drivers = tr["driver_name"].unique()
    is_all      = top_n >= 999
    fig         = go.Figure()

    for i, drv in enumerate(all_drivers):
        d     = tr[tr["driver_name"] == drv].sort_values("round")
        color = tc(d["constructor"].iloc[0] if not d.empty else "")

        if is_all:
            is_highlight = drv in top5

            if selected_driver is not None:
                # Mode highlight: driver terpilih cerah, lainnya pudar & tersembunyi
                if drv == selected_driver:
                    line_width    = 2.5
                    marker_size   = 8
                    opacity       = 1.0
                    trace_visible = True
                else:
                    line_width    = 1.0
                    marker_size   = 5
                    opacity       = 0.15
                    trace_visible = "legendonly"
            else:
                # Mode default: top5 cerah, lainnya pudar tapi berwarna
                line_width    = 2.5 if is_highlight else 1.0
                marker_size   = 8   if is_highlight else 5
                opacity       = 1.0 if is_highlight else 0.2
                trace_visible = True
        else:
            if drv not in top_drivers:
                continue
            if selected_driver is not None:
                if drv == selected_driver:
                    line_width    = 2
                    marker_size   = 7
                    opacity       = 1.0
                    trace_visible = True
                else:
                    line_width    = 1.0
                    marker_size   = 5
                    opacity       = 0.15
                    trace_visible = "legendonly"
            else:
                line_width    = 2
                marker_size   = 7
                opacity       = 1.0
                trace_visible = True

        # Dummy trace: selalu tampil di legend dengan warna penuh
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines+markers", name=drv,
            legendgroup=drv, showlegend=True,
            visible=True if (selected_driver is None or drv == selected_driver) else "legendonly",
            line=dict(width=2, color=color),
            marker=dict(size=7, color="#FFFFFF",
                        symbol=MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)],
                        line=dict(width=2, color=color))
        ))

        # Trace aktual di grafik
        fig.add_trace(go.Scatter(
            x=d["round"], y=d["season_cumulative_points"],
            mode="lines+markers", name=drv,
            legendgroup=drv, showlegend=False,
            visible=trace_visible,
            opacity=opacity,
            line=dict(width=line_width, color=color),
            marker=dict(size=marker_size, color="#FFFFFF",
                        symbol=MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)],
                        line=dict(width=2, color=color)),
            customdata=d["race_name"],
            hovertemplate=(f"<b>{drv}</b><br>"
                           f"Putaran %{{x}} — %{{customdata}}<br>"
                           f"Poin: <b>%{{y}}</b><extra></extra>")
        ))

    max_round = int(tr["round"].max()) if not tr.empty else 1
    fig.update_layout(
        **CL, height=420,
        legend=_LEGEND_BOTTOM,
        xaxis={**_XAXIS, "title_text": "Putaran",
               "range": [0.5, max_round + 0.5]},
        yaxis={**_YAXIS, "title_text": "Poin Kumulatif"},
        hovermode="closest",
        margin=dict(l=55, r=20, t=20, b=120)
    )
    return fig


def _build_bump_fig(tr, top_n, selected_driver=None):
    rounds   = sorted(tr["round"].unique())
    pos_rows = []
    for r in rounds:
        snap = (tr[tr["round"] == r]
                .groupby(["driver_name", "constructor"])["season_cumulative_points"]
                .max().reset_index()
                .sort_values("season_cumulative_points", ascending=False)
                .reset_index(drop=True))
        snap["pos"]       = snap.index + 1
        snap["round"]     = r
        snap["race_name"] = (tr[tr["round"] == r]["race_name"].iloc[0]
                             if not tr[tr["round"] == r].empty else "")
        pos_rows.append(snap)

    pos_df      = pd.concat(pos_rows, ignore_index=True)
    last_round  = pos_df["round"].max()
    top_drivers = (pos_df[pos_df["round"] == last_round]
                   .nsmallest(min(top_n, len(pos_df)), "pos")["driver_name"].tolist())
    top5_final  = (pos_df[pos_df["round"] == last_round]
                   .nsmallest(5, "pos")["driver_name"].tolist())
    all_drivers = pos_df["driver_name"].unique()
    is_all      = top_n >= 999

    fig = go.Figure()
    for i, drv in enumerate(all_drivers):
        d           = pos_df[pos_df["driver_name"] == drv].sort_values("round")
        constructor = d["constructor"].iloc[0] if not d.empty else ""
        color       = tc(constructor)

        if is_all:
            is_highlight = drv in top5_final

            if selected_driver is not None:
                if drv == selected_driver:
                    line_width    = 2.5
                    marker_size   = 9
                    opacity       = 1.0
                    trace_visible = True
                else:
                    line_width    = 1.0
                    marker_size   = 5
                    opacity       = 0.15
                    trace_visible = "legendonly"
            else:
                line_width    = 2.5 if is_highlight else 1.0
                marker_size   = 9   if is_highlight else 5
                opacity       = 1.0 if is_highlight else 0.2
                trace_visible = True
        else:
            if drv not in top_drivers:
                continue
            if selected_driver is not None:
                if drv == selected_driver:
                    line_width    = 2.5
                    marker_size   = 9
                    opacity       = 1.0
                    trace_visible = True
                else:
                    line_width    = 1.0
                    marker_size   = 5
                    opacity       = 0.15
                    trace_visible = "legendonly"
            else:
                line_width    = 2.5
                marker_size   = 9
                opacity       = 1.0
                trace_visible = True

        # Dummy trace: selalu tampil di legend dengan warna penuh
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines+markers", name=drv,
            legendgroup=drv, showlegend=True,
            visible=True if (selected_driver is None or drv == selected_driver) else "legendonly",
            line=dict(width=2.5, color=color),
            marker=dict(size=9, color="#FFFFFF",
                        symbol=MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)],
                        line=dict(width=2, color=color))
        ))

        # Trace aktual di grafik
        fig.add_trace(go.Scatter(
            x=d["round"], y=d["pos"],
            mode="lines+markers", name=drv,
            legendgroup=drv, showlegend=False,
            visible=trace_visible,
            opacity=opacity,
            line=dict(width=line_width, color=color),
            marker=dict(size=marker_size, color="#FFFFFF",
                        symbol=MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)],
                        line=dict(width=2, color=color)),
            customdata=list(zip(d["race_name"],
                                d["season_cumulative_points"].astype(int))),
            hovertemplate=(f"<b>{drv}</b><br>"
                           f"Putaran %{{x}} — %{{customdata[0]}}<br>"
                           f"Posisi: <b>P%{{y}}</b> · %{{customdata[1]}} poin"
                           f"<extra></extra>")
        ))

    max_round = int(pos_df["round"].max()) if not pos_df.empty else 1
    n_drivers = int(pos_df["pos"].max()) if not pos_df.empty else 20

    fig.update_layout(
        **CL, height=420,
        legend=_LEGEND_BOTTOM,
        xaxis={**_XAXIS, "title_text": "Putaran",
               "range": [0.5, max_round + 0.5]},
        yaxis={**_YAXIS, "title_text": "Posisi Championship",
               "autorange": "reversed", "dtick": 1,
               "range": [n_drivers + 0.5, 0.5],
               "tickprefix": "P"},
        hovermode="closest",
        margin=dict(l=55, r=20, t=20, b=120)
    )
    return fig


def register_callbacks(app):

    @app.callback(
        Output("store-home-top-n", "data"),
        Input("btn-top5",   "n_clicks"),
        Input("btn-top10",  "n_clicks"),
        Input("btn-topall", "n_clicks"),
        State("store-home-top-n", "data"),
        prevent_initial_call=True,
    )
    def update_top_n(n5, n10, nall, current):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if tid == "btn-top5":   return 5
        if tid == "btn-top10":  return 10
        if tid == "btn-topall": return 999
        return current

    @app.callback(
        Output("store-home-mode", "data"),
        Input("btn-mode-poin",   "n_clicks"),
        Input("btn-mode-posisi", "n_clicks"),
        State("store-home-mode", "data"),
        prevent_initial_call=True,
    )
    def update_mode(np, ns, current):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if tid == "btn-mode-poin":   return "poin"
        if tid == "btn-mode-posisi": return "posisi"
        return current

    @app.callback(
        Output("btn-top5",        "style"),
        Output("btn-top10",       "style"),
        Output("btn-topall",      "style"),
        Output("btn-mode-poin",   "style"),
        Output("btn-mode-posisi", "style"),
        Input("store-home-top-n", "data"),
        Input("store-home-mode",  "data"),
    )
    def update_btn_styles(top_n, mode):
        top_n = top_n or 5
        mode  = mode  or "poin"
        s5    = BTN_ACTIVE if top_n == 5   else BTN_INACTIVE
        s10   = BTN_ACTIVE if top_n == 10  else BTN_INACTIVE
        sall  = BTN_ACTIVE if top_n == 999 else BTN_INACTIVE
        sp    = BTN_ACTIVE if mode == "poin"   else BTN_INACTIVE
        ss    = BTN_ACTIVE if mode == "posisi" else BTN_INACTIVE
        return s5, s10, sall, sp, ss

    @app.callback(
        Output("graph-championship", "figure"),
        Input("store-home-top-n",        "data"),
        Input("store-home-mode",         "data"),
        Input("store-beranda-data",      "data"),
        Input("graph-championship",      "restyleData"),
        State("graph-championship",      "figure"),
    )
    def update_chart(top_n, mode, data, restyle_data, current_fig):
        if not data:
            return go.Figure()
        tr    = pd.DataFrame(data)
        top_n = top_n or 5
        mode  = mode  or "poin"

        ctx          = callback_context
        triggered_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        selected_drv = None

        # Deteksi klik legend via restyleData
        if "restyleData" in triggered_id and restyle_data and current_fig:
            selected_drv = _parse_restyle(restyle_data, current_fig["data"])

        if mode == "posisi":
            return _build_bump_fig(tr, top_n, selected_drv)
        return _build_points_fig(tr, top_n, selected_drv)