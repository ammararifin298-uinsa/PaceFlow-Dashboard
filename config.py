# =========================================================================
# config.py — Centralized configuration & constants
# Semua nilai hardcoded dipindahkan ke sini agar reusable dan mudah diubah.
# =========================================================================
import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ─────────────────────────────────────────────────────────────────
DB = {
    "host":     os.getenv("PG_HOST",     "localhost"),
    "port":     os.getenv("PG_PORT",     "5432"),
    "dbname":   os.getenv("PG_DB",       "f1_analytics"),
    "user":     os.getenv("PG_USER",     "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
}
DB_URL = (
    f"postgresql+psycopg2://{DB['user']}:{DB['password']}"
    f"@{DB['host']}:{DB['port']}/{DB['dbname']}"
)

# ── Demo / Offline Mode ───────────────────────────────────────────────────────
DEMO_MODE       = os.getenv("F1_DEMO_MODE", "false").lower() == "true"
DEMO_CACHE_PATH = os.path.join(os.path.dirname(__file__), "demo_cache.csv")

# ── Cache TTL ─────────────────────────────────────────────────────────────────
CACHE_TTL = int(os.getenv("F1_CACHE_TTL", "600"))   # seconds

# ── Team Colors (update here when new teams join) ─────────────────────────────
TEAM_COLORS = {
    "Red Bull":         "#3671C6",
    "Ferrari":          "#E8002D",
    "Mercedes":         "#27F4D2",
    "McLaren":          "#FF8000",
    "Aston Martin":     "#229971",
    "Alpine F1 Team":   "#0093CC",
    "Alpine":           "#0093CC",
    "Williams":         "#64C4FF",
    "RB F1 Team":       "#6692FF",
    "RB":               "#6692FF",
    "Haas F1 Team":     "#B6BABD",
    "Haas":             "#B6BABD",
    "Kick Sauber":      "#52E252",
    "Sauber":           "#52E252",
    # 2026 new constructors
    "Audi":             "#B0B0B0",
    "Cadillac F1 Team": "#C8102E",
}
DEFAULT_TEAM_COLOR = "#888899"

# ── Season defaults ───────────────────────────────────────────────────────────
DEFAULT_SEASON = 2024

# ── SUS Score thresholds (Bangor et al., 2008) ────────────────────────────────
SUS_THRESHOLDS = {
    "Excellent":    (90, 100, "#27AE60"),
    "Good":         (80,  89, "#2ECC71"),
    "Acceptable":   (68,  79, "#F39C12"),
    "Marginal":     (51,  67, "#E67E22"),
    "Unacceptable": ( 0,  50, "#E74C3C"),
}
