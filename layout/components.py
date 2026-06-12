# =============================================================================
# components.py — Reusable UI components untuk semua halaman PaceFlow
# Berisi: card, kpi_card, sec, info_box, empty_state, tbl_hdr, tbar, dll.
# Diimpor oleh semua pages/ agar tidak duplikasi kode (DRY principle)
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from layout.design_tokens import C, F, rgba, tc


# ───────────────────────────────────────────────────────────────────────────────
# GLOBAL BUTTON STYLES & COMPONENT — dipakai di semua halaman
# (Satu definisi = konsistensi 100% "plek ketiplek" di seluruh aplikasi)
# ───────────────────────────────────────────────────────────────────────────────
BTN_ACTIVE = dict(
    background=C["blue"], color="#FFF",
    border=f"1px solid {C['blue']}", borderRadius="6px",
    padding="4px 14px", fontSize="11px", fontWeight="600",
    fontFamily=F, cursor="pointer",
)
BTN_INACTIVE = dict(
    background=C["surface"], color=C["muted"],
    border=f"1px solid {C['border']}", borderRadius="6px",
    padding="4px 14px", fontSize="11px", fontWeight="600",
    fontFamily=F, cursor="pointer",
)


def btn_toggle(btn_id, label, active):
    """Tombol toggle standar — dipakai di Home, Analytics, Comparison."""
    return html.Button(
        label, id=btn_id, n_clicks=0,
        style=BTN_ACTIVE if active else BTN_INACTIVE,
    )


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
        justifyContent="center", padding="60px 20px", textAlign="center",
        background=C["surface"], border=f"1px solid {C['border']}",
        borderRadius="10px", boxShadow="0 1px 4px rgba(15,23,42,0.06)"
    ))


def welcome_state():
    """Welcome + Tutorial Onboarding — tampil saat belum ada season yang dipilih."""

    def _feature_card(icon, title, desc, color):
        return html.Div([
            html.Div([
                ico(icon, 22, color),
            ], style=dict(
                width="44px", height="44px", borderRadius="12px",
                background=rgba(color, 0.12),
                display="flex", alignItems="center", justifyContent="center",
                marginBottom="12px",
            )),
            html.Div(title, style=dict(
                fontSize="13px", fontWeight="700",
                color=C["text"], fontFamily=F, marginBottom="4px"
            )),
            html.Div(desc, style=dict(
                fontSize="11px", color=C["muted"], fontFamily=F,
                lineHeight="1.6"
            )),
        ], style=dict(
            background=C["surface"],
            border=f"1px solid {C['border']}",
            borderRadius="12px", padding="16px",
            flex="1", minWidth="0",
        ))

    def _step(num, color, title, desc):
        return html.Div([
            html.Div([
                html.Div(str(num), style=dict(
                    width="28px", height="28px", borderRadius="50%",
                    background=color, color="#fff",
                    display="flex", alignItems="center", justifyContent="center",
                    fontSize="12px", fontWeight="800", fontFamily=F,
                    flexShrink="0",
                )),
                html.Div([
                    html.Div(title, style=dict(
                        fontSize="12px", fontWeight="700",
                        color=C["text"], fontFamily=F
                    )),
                    html.Div(desc, style=dict(
                        fontSize="11px", color=C["muted"], fontFamily=F
                    )),
                ], style=dict(marginLeft="10px")),
            ], style=dict(display="flex", alignItems="center")),
        ], style=dict(marginBottom="10px"))

    return html.Div([

        # ── HERO SECTION ─────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div(style=dict(
                    width="64px", height="64px", borderRadius="18px",
                    background=f"linear-gradient(135deg, {C['blue']}, #7C3AED)",
                    display="flex", alignItems="center", justifyContent="center",
                    boxShadow=f"0 8px 32px {rgba(C['blue'], 0.35)}",
                    margin="0 auto 18px auto",
                ), children=[ico("lucide:gauge", 34, "#fff")]),
                html.Div("Selamat Datang di PaceFlow", style=dict(
                    fontSize="28px", fontWeight="900", letterSpacing="-0.5px",
                    color=C["text"], fontFamily=F, marginBottom="6px",
                )),
                html.Div(
                    "Dasbor analitik F1 berbasis data relasional PostgreSQL — "
                    "rancang khusus untuk mengungkap pola performa balap dari data mentah.",
                    style=dict(
                        fontSize="13px", color=C["muted"], fontFamily=F,
                        maxWidth="520px", lineHeight="1.7", margin="0 auto",
                    )
                ),
                # CTA
                html.Div([
                    ico("lucide:chevrons-right", 14, C["blue"]),
                    html.Span(
                        " Pilih musim di sidebar kiri untuk memulai eksplorasi",
                        style=dict(fontSize="12px", fontWeight="600",
                                   color=C["blue"], fontFamily=F, marginLeft="4px")
                    ),
                ], style=dict(
                    display="inline-flex", alignItems="center",
                    marginTop="18px", background=rgba(C["blue"], 0.08),
                    border=f"1px dashed {rgba(C['blue'], 0.4)}",
                    padding="10px 20px", borderRadius="8px",
                )),
            ], style=dict(textAlign="center", marginBottom="36px")),

            # ── FITUR CARDS ───────────────────────────────────────────────────
            html.Div("FITUR UTAMA DASBOR", style=dict(
                fontSize="9px", fontWeight="700", letterSpacing="2px",
                color=C["muted"], fontFamily=F, marginBottom="12px",
                textTransform="uppercase",
            )),
            html.Div([
                _feature_card(
                    "lucide:home", "Beranda",
                    "Grafik perkembangan poin & posisi championship. Toggle Top 5/10/Semua untuk menyaring pembalap.",
                    C["blue"]
                ),
                _feature_card(
                    "lucide:bar-chart-2", "Analitik",
                    "Scatter speed vs konsistensi, distribusi Violin Plot, performa pit stop & kualifikasi per tim.",
                    "#7C3AED"
                ),
                _feature_card(
                    "lucide:git-compare", "Perbandingan",
                    "Bandingkan hingga 3 musim secara bersamaan — poin, DNF rate, gap P1 vs P2 per putaran.",
                    C["orange"]
                ),
                _feature_card(
                    "lucide:users", "H2H dan Klasemen",
                    "Duel head-to-head dua pembalap, tabel klasemen lengkap + detail statistik musiman.",
                    C["green"]
                ),
            ], style=dict(
                display="flex", gap="12px", marginBottom="28px",
            )),

            # ── TUTORIAL 3 LANGKAH ────────────────────────────────────────────
            html.Div([
                html.Div([
                    html.Div("CARA MENGGUNAKAN", style=dict(
                        fontSize="9px", fontWeight="700", letterSpacing="2px",
                        color=C["muted"], fontFamily=F, marginBottom="14px",
                        textTransform="uppercase",
                    )),
                    _step(1, C["blue"],
                        "Pilih Musim",
                        "Klik dropdown musim di sidebar kiri — tersedia musim 2024, 2025, dan 2026."),
                    _step(2, "#7C3AED",
                        "Pilih Halaman",
                        "Navigasi lewat menu sidebar: Beranda, Klasemen, Analitik, H2H, Perbandingan, dll."),
                    _step(3, C["green"],
                        "Eksplorasi Interaktif",
                        "Klik legenda grafik untuk fokus pada satu pembalap/tim. Klik lagi untuk kembali ke semua."),
                ], style=dict(flex="1")),

                # Divider
                html.Div(style=dict(
                    width="1px", background=C["border"],
                    margin="0 24px", flexShrink="0",
                )),

                # Tips
                html.Div([
                    html.Div("TIPS CEPAT", style=dict(
                        fontSize="9px", fontWeight="700", letterSpacing="2px",
                        color=C["muted"], fontFamily=F, marginBottom="14px",
                        textTransform="uppercase",
                    )),
                    *[html.Div([
                        html.Span("→", style=dict(
                            color=C["blue"], fontWeight="700",
                            marginRight="8px", fontFamily=F,
                        )),
                        html.Span(tip, style=dict(
                            fontSize="11px", color=C["muted"], fontFamily=F,
                            lineHeight="1.6"
                        )),
                    ], style=dict(marginBottom="8px", display="flex"))
                    for tip in [
                        "Toggle Top 5 / Top 10 / Semua untuk menyaring grafik championship.",
                        "Klik 1x nama di legenda → fokus. Klik lagi → tampilkan semua.",
                        "Tombol ? di kanan bawah untuk glosarium istilah F1.",
                        "Halaman Perbandingan memerlukan minimal 2 musim dipilih.",
                        "Settings → DB Health untuk cek koneksi database real-time.",
                    ]],
                ], style=dict(flex="1")),
            ], style=dict(
                display="flex",
                background=C["surface"],
                border=f"1px solid {C['border']}",
                borderRadius="12px", padding="20px",
            )),
        ], style=dict(
            maxWidth="900px", margin="0 auto",
            paddingTop="32px", paddingBottom="40px",
        )),
    ])


def partial_badge(n_races, total=24):
    """Badge 'DATA PARSIAL' — tampil jika season belum selesai."""
    if n_races >= total:
        return html.Span()
    return html.Span(
        f" DATA PARSIAL ({n_races}/{total} Race)",
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