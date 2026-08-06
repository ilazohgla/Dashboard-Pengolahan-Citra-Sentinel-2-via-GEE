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

# ── Kombinasi Band False Color (Sentinel-2) ──────────────────────────────────
# Band yang tersedia pada komposit (COPERNICUS/S2_SR_HARMONIZED + indeks).
S2_BANDS: list = [
    "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12",
    "NDVI", "NDWI", "NDBI",
]
S2_BAND_LABELS: dict = {
    "B2":  "B2 (Blue, 10 m)",
    "B3":  "B3 (Green, 10 m)",
    "B4":  "B4 (Red, 10 m)",
    "B5":  "B5 (Red Edge 1, 20 m)",
    "B6":  "B6 (Red Edge 2, 20 m)",
    "B7":  "B7 (Red Edge 3, 20 m)",
    "B8":  "B8 (NIR, 10 m)",
    "B8A": "B8A (NIR narrow, 20 m)",
    "B11": "B11 (SWIR 1, 20 m)",
    "B12": "B12 (SWIR 2, 20 m)",
    "NDVI": "NDVI (Vegetasi)",
    "NDWI": "NDWI (Air)",
    "NDBI": "NDBI (Terbangun)",
}

# Preset kombinasi RGB (urutan = R, G, B) dengan vis default & keterangan.
FALSE_COLOR_PRESETS: dict = {
    "False Color Klasik (NIR-R-G)": {
        "bands": ["B8", "B4", "B3"],
        "vis": {"min": 0, "max": 0.4, "gamma": 1.4},
        "desc": "NIR=merah, Red=hijau, Green=biru. Vegetasi tampak merah terang; "
                "terbaik untuk menonjolkan tutupan vegetasi & kesehatan tanaman.",
    },
    "Agriculture (SWIR1-NIR-Blue)": {
        "bands": ["B11", "B8", "B2"],
        "vis": {"min": 0, "max": 0.5, "gamma": 1.4},
        "desc": "SWIR1=merah, NIR=hijau, Blue=biru. Lahan pertanian & vegetasi "
                "hijau terang; tanah terbuka kecoklatan — umum dipakai untuk "
                "pemetaan lahan pertanian.",
    },
    "Urban / Built-up (SWIR2-SWIR1-Red)": {
        "bands": ["B12", "B11", "B4"],
        "vis": {"min": 0, "max": 0.5, "gamma": 1.5},
        "desc": "SWIR2=merah, SWIR1=hijau, Red=biru. Area terbangun (beton, "
                "aspal) tampak ungu/magenta; vegetasi hijau gelap — cocok untuk "
                "deteksi urban.",
    },
    "Geologi (SWIR2-SWIR1-Blue)": {
        "bands": ["B12", "B11", "B2"],
        "vis": {"min": 0, "max": 0.6, "gamma": 1.5},
        "desc": "SWIR2=merah, SWIR1=hijau, Blue=biru. Membedakan tipe batuan & "
                "mineral; sering dipakai untuk eksplorasi geologi/tanah terbuka.",
    },
    "Air / Moisture (NIR-SWIR1-Red)": {
        "bands": ["B8", "B11", "B4"],
        "vis": {"min": 0, "max": 0.5, "gamma": 1.4},
        "desc": "NIR=merah, SWIR1=hijau, Red=biru. Badan air tampak biru tua/"
                "hitam; area basah & kelembaban tanah lebih jelas.",
    },
    "Vegetasi Sehat (NIR-RedEdge2-Red)": {
        "bands": ["B8", "B7", "B4"],
        "vis": {"min": 0, "max": 0.4, "gamma": 1.4},
        "desc": "NIR=merah, Red Edge 3=hijau, Red=biru. Vegetasi yang sangat "
                "sehat/rapat tampak merah-oranye; membedakan tingkat vigor.",
    },
}

# ── Parameter Download ────────────────────────────────────────────────────────
DEFAULT_SCALE:  int = 30      # resolusi default GeoTIFF (meter/piksel)
MAX_THUMB_DIM:  int = 1024    # dimensi maks PNG/JPG preview
