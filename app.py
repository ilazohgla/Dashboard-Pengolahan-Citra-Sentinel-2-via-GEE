"""
================================================================================
 app.py  –  S2 Geo Dashboard v3  (entry point)
================================================================================
 Stack : Python | Streamlit | Folium | streamlit-folium | Google Earth Engine
 ─────────────────────────────────────────────────────────────────────────────
 Struktur proyek:
   app.py                      ← entry point (file ini)
   config.py                   ← konfigurasi & vis params
   utils/
     gee_utils.py              ← GEE auth, komposit, indeks
     geo_utils.py              ← GeoJSON / shapefile helpers
     map_utils.py              ← Folium map builder
     download_utils.py         ← URL download PNG / GeoTIFF
   pages/
     tab_main_map.py           ← Tab 1: Peta Utama & Download
     tab_split_panel.py        ← Tab 2: Split-Panel Temporal
================================================================================
"""

import ee
import json
import streamlit as st
from datetime import date, timedelta

from config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_ZOOM
from utils.gee_utils import initialize_gee, get_s2_composite, add_indices
from utils.geo_utils import geojson_to_ee, get_centroid, shapefile_to_ee, GEOPANDAS_OK
from pages.tab_main_map import render_tab_main_map
from pages.tab_split_panel import render_tab_split_panel
from pages.tab_lulc_classification import render_tab_lulc

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="S2 Geo Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ════════════════════════════════════════════════════════════════
       GEE SENTINEL-2 — precise scientific monitor theme
       Flat surfaces · luminance stacking · single accent
       ════════════════════════════════════════════════════════════════ */
    :root {
        --bg: #0a0d12;
        --panel: #0e1219;
        --surface: #131926;
        --surface-2: #1a2130;
        --border: rgba(255, 255, 255, 0.06);
        --border-strong: rgba(255, 255, 255, 0.12);
        --accent: #22d3ee;
        --accent-hover: #4ce0f7;
        --accent-dim: rgba(34, 211, 238, 0.10);
        --text: #e8ecf3;
        --text-2: #9aa5b5;
        --text-3: #5c6675;
        --success: #34d399;
        --warning: #fbbf24;
        --danger: #f87171;
        --mono: 'JetBrains Mono', ui-monospace, monospace;
        --sans: 'Space Grotesk', system-ui, sans-serif;
    }

    html, body, [class*="css"] {
        font-family: var(--sans);
    }

    /* Ikon Material — jangan tertimpa override font global */
    [data-testid="stIconMaterial"], [data-testid="stIcon"] {
        font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
    }

    /* ── Flat canvas ── */
    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: var(--sans);
        font-weight: 600;
        letter-spacing: -0.015em;
    }

    .main .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3.5rem;
        max-width: 1440px;
    }

    /* ════════════════════════════════════════════════════════════════
       HEADER
       ════════════════════════════════════════════════════════════════ */
    .app-header {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem 1.9rem 1.35rem;
        margin-bottom: 1.5rem;
    }

    .header-kicker {
        font-family: var(--mono);
        font-size: 0.68rem;
        font-weight: 500;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: var(--text-3);
        margin-bottom: 0.45rem;
    }

    .stMarkdown .header-title {
        font-family: var(--sans);
        font-size: 1.85rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: var(--text);
        margin: 0;
        line-height: 1.15;
    }

    .header-title .accent {
        color: var(--accent);
    }

    .header-sub {
        color: var(--text-2);
        font-size: 0.9rem;
        margin-top: 0.35rem;
    }

    .header-badges {
        margin-top: 0.95rem;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .chip {
        display: inline-block;
        background: transparent;
        border: 1px solid var(--border-strong);
        border-radius: 6px;
        padding: 3px 10px;
        font-family: var(--mono);
        font-size: 0.62rem;
        font-weight: 500;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-2);
        transition: color 0.15s ease, border-color 0.15s ease;
    }

    .chip:hover {
        color: var(--text);
        border-color: var(--accent);
    }

    /* ════════════════════════════════════════════════════════════════
       METRIC CARDS
       ════════════════════════════════════════════════════════════════ */
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.15rem 0.95rem;
        text-align: left;
        transition: border-color 0.15s ease, background 0.15s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--border-strong);
        background: var(--surface-2);
    }

    [data-testid="stMetricLabel"] {
        font-family: var(--mono);
        font-size: 0.62rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-3);
        margin-bottom: 0.45rem;
        white-space: nowrap;
    }

    [data-testid="stMetricValue"] {
        font-family: var(--mono);
        font-size: 1.55rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: var(--text);
        line-height: 1.1;
    }

    [data-testid="stMetricDelta"] {
        font-family: var(--mono);
        font-size: 0.72rem;
        color: var(--text-3);
    }

    /* ════════════════════════════════════════════════════════════════
       SECTION TITLES
       ════════════════════════════════════════════════════════════════ */
    .section-title {
        font-family: var(--mono);
        font-size: 0.66rem;
        font-weight: 500;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--text-3);
        margin: 0 0 10px 0;
    }

    /* ════════════════════════════════════════════════════════════════
       SIDEBAR
       ════════════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: var(--panel);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] hr { border-color: var(--border); }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: var(--text); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: var(--text-2); }

    /* Status pill — flat, mono, tanpa glow */
    .status-pill {
        display: inline-block;
        background: transparent;
        border: 1px solid var(--border-strong);
        border-radius: 6px;
        padding: 3px 10px;
        font-family: var(--mono);
        font-size: 0.62rem;
        font-weight: 500;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-2);
    }

    /* ════════════════════════════════════════════════════════════════
       PANELS & ALERTS
       ════════════════════════════════════════════════════════════════ */
    .info-panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.95rem 1.2rem;
        font-size: 0.88rem;
        color: var(--text-2);
        margin: 0.8rem 0;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
        border: 1px solid var(--border);
        background: var(--surface);
    }

    .status-success { color: var(--success); }
    .status-warning { color: var(--warning); }
    .status-error   { color: var(--danger); }

    /* ════════════════════════════════════════════════════════════════
       BUTTONS
       ════════════════════════════════════════════════════════════════ */
    .stButton > button {
        background: var(--accent);
        color: #07131a;
        font-weight: 600;
        letter-spacing: 0.02em;
        border: none;
        border-radius: 8px;
        padding: 0.55rem 1.4rem;
        width: 100%;
        transition: background 0.15s ease;
    }

    .stButton > button:hover { background: var(--accent-hover); }
    .stButton > button:active { background: #17b7d1; }

    .stDownloadButton > button,
    [data-testid="stBaseButton-secondary"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--border-strong);
        color: var(--text-2);
        border-radius: 8px;
        font-weight: 500;
        transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    }

    .stDownloadButton > button:hover {
        background: rgba(255, 255, 255, 0.07);
        color: var(--text);
        border-color: var(--accent);
    }

    /* ════════════════════════════════════════════════════════════════
       INPUTS & WIDGETS
       ════════════════════════════════════════════════════════════════ */
    .stSelectbox > div > div,
    .stDateInput > div > div,
    .stTextInput > div > div,
    .stNumberInput > div > div,
    .stTextArea > div > div {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 8px !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .stSelectbox > div > div:focus-within,
    .stDateInput > div > div:focus-within,
    .stTextInput > div > div:focus-within,
    .stNumberInput > div > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.15) !important;
    }

    .stSelectbox [data-baseweb="select"] > div { background: transparent !important; border: none !important; }
    .stSelectbox [data-baseweb="popover"] [role="listbox"] { background: var(--surface-2); border: 1px solid var(--border-strong); border-radius: 8px; }
    .stSelectbox [data-baseweb="popover"] [role="option"]:hover { background: var(--accent-dim); }

    /* Radio — flat options */
    [data-testid="stRadio"] div[role="radiogroup"] > label {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 7px 12px;
        margin-bottom: 4px;
        transition: background 0.15s ease, border-color 0.15s ease;
    }

    [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.04);
    }

    [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
        background: var(--accent-dim);
        border-color: rgba(34, 211, 238, 0.35);
    }

    /* Sliders */
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div {
        background: var(--accent) !important;
    }

    [data-testid="stSlider"] [role="slider"] {
        background: #ffffff !important;
        border: 1px solid var(--accent) !important;
    }

    /* Expander */
    div[data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
        transition: border-color 0.15s ease;
    }

    div[data-testid="stExpander"]:hover { border-color: var(--border-strong); }
    div[data-testid="stExpander"] summary { border-radius: 10px; }

    /* Tabs — underline indicator */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: transparent;
        border: none;
        border-bottom: 1px solid var(--border);
        border-radius: 0;
        padding: 0;
        width: 100%;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-2);
        border-radius: 6px 6px 0 0;
        padding: 8px 14px;
        font-weight: 500;
        letter-spacing: 0.01em;
        border: none;
        border-bottom: 2px solid transparent;
        transition: color 0.15s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text);
        background: rgba(255, 255, 255, 0.03);
    }

    .stTabs [aria-selected="true"] {
        color: var(--text) !important;
        background: transparent !important;
        box-shadow: none !important;
        border-bottom: 2px solid var(--accent) !important;
    }

    /* Progress */
    [data-testid="stProgress"] > div > div { background: rgba(255, 255, 255, 0.07); border-radius: 999px; }
    [data-testid="stProgress"] > div > div > div > div {
        background: var(--accent);
    }

    /* File uploader */
    [data-testid="stFileUploader"] section {
        background: rgba(255, 255, 255, 0.02);
        border: 1px dashed var(--border-strong);
        border-radius: 10px;
        transition: border-color 0.15s ease;
    }

    [data-testid="stFileUploader"] section:hover { border-color: var(--accent); }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
    }

    /* ════════════════════════════════════════════════════════════════
       CHARTS & MISC
       ════════════════════════════════════════════════════════════════ */
    .js-plotly-plot .plotly .main-svg { background: transparent !important; }

    /* Hide Streamlit chrome */
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; height: 0; }
    header[data-testid="stHeader"] { background: transparent; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: #232c3d; border-radius: 6px; border: 2px solid var(--bg); }
    ::-webkit-scrollbar-thumb:hover { background: #2e3a50; }

    ::selection { background: rgba(34, 211, 238, 0.25); color: #ffffff; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div class="header-kicker">Sentinel-2 · Google Earth Engine</div>
    <h1 class="header-title">S2 Geo <span class="accent">Dashboard</span></h1>
    <div class="header-sub">Citra Sentinel-2 SR · Indeks spektral · Split-panel temporal · Klasifikasi LULC</div>
    <div class="header-badges">
        <span class="chip">Sentinel-2 SR</span>
        <span class="chip">NDVI · NDWI · NDBI</span>
        <span class="chip">LULC</span>
        <span class="chip">PNG / GeoTIFF</span>
        <span class="chip">Earth Engine</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# GEE AUTH
# ──────────────────────────────────────────────────────────────────────────────
if not initialize_gee():
    st.error("❌ Autentikasi GEE gagal. Jalankan `earthengine authenticate` lalu refresh.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR – AOI, tanggal, filter awan
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<span class="status-pill">● SYSTEM READY</span>', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="margin-top:12px;">Pengaturan Analisis</div>', unsafe_allow_html=True)
    st.caption("AOI, periode citra, dan filter awan berlaku untuk semua panel.")
    st.markdown("---")

    # ── Input AOI ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Input AOI</div>', unsafe_allow_html=True)
    aoi_mode = st.radio("Mode AOI", ["✏️ Gambar Polygon", "📂 Upload Shapefile"])

    center_lat, center_lon = DEFAULT_LAT, DEFAULT_LON
    roi = None

    if aoi_mode == "📂 Upload Shapefile":
        if not GEOPANDAS_OK:
            st.error("Install geopandas:\n```\npip install geopandas\n```")
        else:
            st.markdown("Upload **.shp + .shx + .dbf** bersamaan:")
            uploaded_shp = st.file_uploader(
                "Shapefile",
                type=["shp", "shx", "dbf", "prj", "cpg"],
                accept_multiple_files=True,
            )
            if uploaded_shp:
                exts = {f.name.split(".")[-1].lower() for f in uploaded_shp}
                if not {"shp", "shx", "dbf"}.issubset(exts):
                    st.warning("Upload minimal .shp, .shx, dan .dbf.")
                else:
                    with st.spinner("Membaca shapefile..."):
                        ee_shp, geojson_shp = shapefile_to_ee(uploaded_shp)
                    if ee_shp:
                        roi = ee_shp
                        st.session_state["aoi_geojson"] = geojson_shp
                        center_lat, center_lon = get_centroid(geojson_shp)
                        st.success("✅ Shapefile dimuat!")
        if roi is None and "aoi_geojson" in st.session_state:
            roi = geojson_to_ee(st.session_state["aoi_geojson"])
            center_lat, center_lon = get_centroid(st.session_state["aoi_geojson"])

    else:  # Draw Polygon
        if st.session_state.get("aoi_geojson"):
            fc = st.session_state["aoi_geojson"]
            n  = len(fc.get("features", []))
            st.success(f"✅ {n} polygon aktif")
            center_lat, center_lon = get_centroid(fc)
            roi = geojson_to_ee(fc)
            if st.button("🗑️ Hapus & Gambar Ulang", type="secondary"):
                st.session_state["aoi_geojson"] = None
                st.rerun()
        else:
            st.info("Gunakan toolbar ✏️ di **Tab Peta** untuk menggambar polygon.")

    if roi is None:
        roi = ee.Geometry.Point([DEFAULT_LON, DEFAULT_LAT]).buffer(10000).bounds()
        if aoi_mode == "✏️ Gambar Polygon" and not st.session_state.get("aoi_geojson"):
            st.caption(f"📍 ROI sementara: ({DEFAULT_LAT}, {DEFAULT_LON})")

    st.markdown("---")

    # ── Rentang waktu ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Rentang Waktu</div>', unsafe_allow_html=True)
    start_date = st.date_input("Mulai",   value=date.today() - timedelta(days=180))
    end_date   = st.date_input("Selesai", value=date.today())
    if start_date >= end_date:
        st.error("Tanggal mulai harus sebelum selesai.")
        st.stop()

    st.markdown("---")

    # ── Filter awan ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Filter Awan</div>', unsafe_allow_html=True)
    max_cloud = st.slider("Maks. Tutupan Awan (%)", 5, 50, 20)
    st.markdown("---")
    st.caption("🛰️ COPERNICUS/S2_SR_HARMONIZED")

# ──────────────────────────────────────────────────────────────────────────────
# LOAD KOMPOSIT UTAMA
# ──────────────────────────────────────────────────────────────────────────────
roi_json = roi.getInfo()

with st.spinner("🔄 Memuat komposit Sentinel-2..."):
    composite_raw, img_count = get_s2_composite(roi_json, start_date, end_date, max_cloud)

if composite_raw is None:
    st.error("⚠️ Tidak ada citra. Perluas rentang tanggal atau naikkan batas awan.")
    st.stop()

composite = add_indices(composite_raw)

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🗺️ Peta Utama & Indeks", "↔️ Split-Panel", "🗺️ Klasifikasi LULC"])

with tab1:
    render_tab_main_map(
        composite, roi, roi_json, img_count,
        start_date, end_date, max_cloud,
        center_lat, center_lon, aoi_mode,
    )

with tab2:
    render_tab_split_panel(roi, roi_json, max_cloud, center_lat, center_lon)

with tab3:
    # Ambil satellite dari dropdownSatelit (dari sidebar)
    satellite_selected = "S2"  # Default Sentinel-2
    render_tab_lulc(composite, roi, roi_json, satellite_selected, center_lat, center_lon)

# ──────────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:.78rem;color:#aaa'>"
    "🛰️ S2 Geo Dashboard v3 · Sentinel-2 SR · "
    "Folium + streamlit-folium + Leaflet.js + Google Earth Engine"
    "</div>",
    unsafe_allow_html=True,
)
