# =============================================================================
# components.py — Reusable UI components untuk semua halaman PaceFlow
# Berisi: card, kpi_card, sec, info_box, empty_state, tbl_hdr, tbar, dll.
# Diimpor oleh semua pages/ agar tidak duplikasi kode (DRY principle)
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from layout.design_tokens import C, F, rgba, tc


def ico(name, size=16, color=None):
    """Icon wrapper menggunakan DashIconify."""
    return DashIconify(icon=name, width=size, height=size, color=color or C["muted"])


def card(*children, p="20px", extra=None):
    """Card container standar dengan border dan shadow."""
    s = dict(
        background=C["surface"], border=f"1px solid {C['border']}",
        borderRadius="10px", padding=p, marginBottom="16px",
        boxShadow="0 1px 4px rgba(15,23,42,0.06)"
    )
    if extra: s.update(extra)
    return html.Div(list(children), style=s)


def sec(title, icon_name=None):
    """Section header dengan garis bawah biru — pemisah antar bagian halaman."""
    return html.Div([
        ico(icon_name, 13, C["blue"]) if icon_name else None,
        html.Span(title, style=dict(marginLeft="6px" if icon_name else "0")),
    ], style=dict(
        fontSize="10px", fontWeight="700", letterSpacing="2px",
        textTransform="uppercase", color=C["blue"],
        borderBottom=f"2px solid {C['border']}", paddingBottom="8px",
        marginBottom="14px", marginTop="20px", fontFamily=F,
        display="flex", alignItems="center"
    ))


def info_box(text, color=None):
    """Info box dengan border kiri berwarna — untuk notifikasi atau insight."""
    c = color or C["blue"]
    return html.Div(
        dcc.Markdown(text, dangerously_allow_html=False),
        style=dict(
            background=rgba(c, 0.07), borderLeft=f"3px solid {c}",
            borderRadius="0 6px 6px 0", padding="10px 16px",
            marginBottom="14px", fontSize="12px", color=C["text"],
            lineHeight="1.7", fontFamily=F
        ))


def kpi_card(label, value, sub, color=None, icon_name=None):
    """KPI card dengan garis atas berwarna — untuk metrik utama di beranda."""
    c = color or C["blue"]
    return html.Div([
        html.Div(style=dict(
            position="absolute", top=0, left=0, right=0,
            height="3px", background=c, borderRadius="10px 10px 0 0"
        )),
        html.Div([
            ico(icon_name, 12, C["muted"]) if icon_name else None,
            html.Span(label, style=dict(
                fontSize="9px", fontWeight="700", letterSpacing="1.5px",
                textTransform="uppercase", color=C["muted"],
                marginLeft="5px", fontFamily=F
            )),
        ], style=dict(display="flex", alignItems="center", marginBottom="8px")),
        html.Div(str(value), style=dict(
            fontSize="24px", fontWeight="800",
            color=C["text"], lineHeight="1.1", fontFamily=F
        )),
        html.Div(sub, style=dict(fontSize="11px", color=c, marginTop="5px", fontFamily=F)),
    ], style=dict(
        background=C["surface"], border=f"1px solid {C['border']}",
        borderRadius="10px", padding="16px 18px",
        position="relative", overflow="hidden",
        boxShadow="0 1px 4px rgba(15,23,42,0.06)"
    ))


def tbl_hdr(*cols):
    """Header row untuk tabel HTML — uppercase, background abu muda."""
    return html.Thead(html.Tr([
        html.Th(c, style=dict(
            color=C["muted"], fontSize="10px", fontWeight="700",
            letterSpacing="0.5px", textTransform="uppercase",
            padding="10px 10px", fontFamily=F,
            borderBottom=f"2px solid {C['border']}", background=C["grid"],
            whiteSpace="nowrap", textAlign="center" if i > 0 else "left"
        )) for i, c in enumerate(cols)
    ]))


def tbar(con):
    """Color bar kecil untuk identitas konstruktor di tabel."""
    return html.Div(style=dict(
        width="3px", height="18px", borderRadius="2px",
        background=tc(con), display="inline-block",
        marginRight="8px", verticalAlign="middle"
    ))


def empty_state(title="Tidak ada data.", desc=""):
    """Empty state — tampil ketika tidak ada data untuk dirender."""
    return html.Div([
        ico("lucide:inbox", 40, C["border"]),
        html.Div(title, style=dict(
            color=C["text"], fontSize="14px",
            fontWeight="600", fontFamily=F, marginTop="12px"
        )),
        html.Div(desc, style=dict(
            color=C["muted"], fontSize="12px",
            fontFamily=F, marginTop="4px"
        )),
    ], style=dict(
        display="flex", flexDirection="column", alignItems="center",
        justifyContent="center", padding="60px 20px", textAlign="center"
    ))


def welcome_state():
    """Welcome screen — tampil saat belum ada season yang dipilih."""
    return html.Div(
        html.Div([
            ico("lucide:gauge", 56, C["border"]),
            html.Div("Selamat Datang di PaceFlow", style=dict(
                fontSize="22px", fontWeight="800",
                color=C["text"], fontFamily=F, marginTop="20px"
            )),
            html.Div("F1 Relational Analytics Dashboard", style=dict(
                fontSize="13px", color=C["muted"], fontFamily=F, marginTop="4px"
            )),
            html.Div([
                ico("lucide:mouse-pointer-click", 14, C["blue"]),
                html.Span(" Pilih musim di sidebar untuk memulai", style=dict(
                    fontSize="12px", color=C["blue"],
                    fontFamily=F, marginLeft="6px"
                )),
            ], style=dict(
                display="flex", alignItems="center", justifyContent="center",
                marginTop="24px", background=rgba(C["blue"], 0.07),
                padding="12px 24px", borderRadius="8px",
                border=f"1px dashed {rgba(C['blue'], 0.4)}"
            )),
        ], style=dict(
            display="flex", flexDirection="column", alignItems="center",
            justifyContent="center", minHeight="65vh", textAlign="center"
        )),
    )


def partial_badge(n_races, total=24):
    """Badge 'DATA PARSIAL' — tampil jika season belum selesai."""
    if n_races >= total:
        return html.Span()
    return html.Span(
        f" DATA PARSIAL — {n_races} dari {total} race",
        style=dict(
            background=rgba(C["orange"], 0.12), color=C["orange"],
            fontSize="10px", fontWeight="700", padding="2px 10px",
            borderRadius="4px", fontFamily=F,
            marginLeft="8px", verticalAlign="middle"
        ))


def safe_contains(series, query):
    """str.contains aman — tidak crash jika ada karakter regex."""
    try:
        return series.str.lower().str.contains(query.lower(), na=False, regex=False)
    except Exception:
        import pandas as pd
        return pd.Series([False] * len(series), index=series.index)


def safe_col(df, col):
    """Cek apakah kolom ada di DataFrame sebelum diakses."""
    return col in df.columns