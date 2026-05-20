"""
================================================================================
 config.py  –  Konfigurasi terpusat GEE Geospatial Dashboard
 Semua nilai sensitif (project ID, dll.) dibaca dari environment variable
 atau file .env  →  jangan pernah commit file .env ke Git!
================================================================================
"""

import os
from dotenv import load_dotenv

# Muat .env jika ada (diabaikan di production / Streamlit Cloud yang pakai Secrets)
load_dotenv()

# ── Google Earth Engine ───────────────────────────────────────────────────────
# Isi GEE_PROJECT di file .env (lokal) atau Streamlit Secrets (cloud)
GEE_PROJECT: str = os.getenv("GEE_PROJECT", "YOUR_GEE_PROJECT_ID")

# ── Lokasi default (fallback jika AOI belum digambar) ────────────────────────
DEFAULT_LAT:  float = float(os.getenv("DEFAULT_LAT",  "-6.9175"))
DEFAULT_LON:  float = float(os.getenv("DEFAULT_LON",  "107.6191"))
DEFAULT_ZOOM: int   = int(os.getenv("DEFAULT_ZOOM",   "11"))

# ── Vis Params Sentinel-2 ────────────────────────────────────────────────────
VIS_TC   = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 0.3,  "gamma": 1.4}
VIS_FC   = {"bands": ["B8", "B4", "B3"], "min": 0, "max": 0.5}
VIS_NDVI = {"min": -0.2, "max": 0.8,
            "palette": ["d73027", "fc8d59", "fee08b", "ffffbf", "91cf60", "1a9850"]}
VIS_NDWI = {"min": -0.3, "max": 0.6,
            "palette": ["ffffff", "a6cee3", "74b9ff", "0984e3", "023e8a"]}
VIS_NDBI = {"min": -0.5, "max": 0.3,
            "palette": ["1a9850", "ffffbf", "d73027"]}

LAYER_CONFIG: dict = {
    "True Color":  {"vis": VIS_TC,   "band": None,   "icon": "🟢"},
    "False Color": {"vis": VIS_FC,   "band": None,   "icon": "🔴"},
    "NDVI":        {"vis": VIS_NDVI, "band": "NDVI", "icon": "🌿"},
    "NDWI":        {"vis": VIS_NDWI, "band": "NDWI", "icon": "💧"},
    "NDBI":        {"vis": VIS_NDBI, "band": "NDBI", "icon": "🏙️"},
}

# ── Parameter Download ────────────────────────────────────────────────────────
DEFAULT_SCALE:  int = 30      # resolusi default GeoTIFF (meter/piksel)
MAX_THUMB_DIM:  int = 1024    # dimensi maks PNG/JPG preview
