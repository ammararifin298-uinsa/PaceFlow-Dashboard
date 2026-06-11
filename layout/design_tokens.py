# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS — PaceFlow
# Semua konstanta warna, font, dan helper chart ada di sini
# ─────────────────────────────────────────────────────────────────────────────
from config import TEAM_COLORS, DEFAULT_TEAM_COLOR

C = {
    "bg":      "#F1F5F9", "surface": "#FFFFFF",
    "sidebar": "#0F172A", "s_active": "#E10600",
    "s_text":  "#CBD5E1", "s_muted":  "#475569",
    "border":  "#E2E8F0", "red":    "#DC2626",
    "blue":    "#1D4ED8", "teal":   "#0891B2",
    "text":    "#0F172A", "muted":  "#64748B",
    "green":   "#059669", "orange": "#D97706",
    "grid":    "#F8FAFC", "yellow": "#92400E",
}

F = "Inter, -apple-system, sans-serif"

CL = dict(
    paper_bgcolor=C["surface"],
    plot_bgcolor=C["surface"],
    font=dict(family=F, color=C["text"], size=11)
)

MARKER_SYMBOLS = [
    "circle", "square", "diamond", "triangle-up",
    "cross", "star", "hexagram", "pentagon",
    "bowtie", "asterisk", "triangle-down", "x"
]

def tc(name):
    if not name:
        return DEFAULT_TEAM_COLOR
    cleaned = str(name).strip().lower()
    # Case-insensitive lookup dictionary
    mapping = {k.strip().lower(): v for k, v in TEAM_COLORS.items()}
    return mapping.get(cleaned, DEFAULT_TEAM_COLOR)

def rgba(h, a=0.15):
    h = h.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

def ax(title="", dtick=None, rev=False, angle=0):
    d = dict(
        gridcolor=C["grid"], zerolinecolor=C["border"],
        linecolor=C["border"],
        tickfont=dict(size=10, color=C["muted"]),
        title_font=dict(size=11, color=C["muted"]),
        title_text=title, tickangle=angle
    )
    if dtick: d["dtick"] = dtick
    if rev:   d["autorange"] = "reversed"
    return d

def legh(y=-0.2):
    return dict(
        orientation="h", y=y, x=0,
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=10, color=C["muted"])
    )