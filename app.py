"""
================================================================================
 app.py  –  GEE Geospatial Dashboard v3  (entry point)
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
    page_title="GEE Geospatial Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root{--bg:#07131b;--panel:#0d202a;--panel-2:#102b35;--ink:#e7f6f4;--muted:#8aa7ad;--line:#1c4650;--cyan:#39d9e6;--lime:#b8f35b;--pink:#ef6db2}
    html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{background:radial-gradient(circle at 78% -10%,#123844 0,#07131b 42%,#050d13 100%);color:var(--ink)}
    [data-testid="stHeader"]{display:none!important}
    #MainMenu{visibility:hidden}footer{visibility:hidden}
    header[data-testid="stHeader"]{display:none!important}
    .block-container{max-width:1760px;padding:1.5rem 2.5rem 2.5rem!important}
    .main-header{position:relative;display:flex;align-items:center;gap:.85rem;color:var(--ink);font-size:2.05rem;font-weight:800;letter-spacing:-.04em;padding:.25rem 0 0}
    .main-header:before{content:'GEE';display:inline-flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1a5963,#39d9e6);color:#061218;font-size:.72rem;letter-spacing:.12em;border-radius:8px;width:52px;height:36px;box-shadow:0 0 22px rgba(57,217,230,.28)}
    .main-header:after{content:'';position:absolute;left:0;bottom:-10px;width:190px;height:2px;background:linear-gradient(90deg,var(--cyan),transparent);box-shadow:0 0 12px rgba(57,217,230,.65)}
    .sub-header{color:var(--muted);font-size:.86rem;margin:.6rem 0 1.3rem 3.9rem;letter-spacing:.02em}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#091b24 0%,#07131b 100%);border-right:1px solid var(--line)}
    [data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label,[data-testid="stSidebar"] p{color:var(--ink)}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{color:var(--muted)}
    [data-testid="stMetric"]{background:linear-gradient(145deg,rgba(16,43,53,.94),rgba(10,28,36,.94));border:1px solid var(--line);border-radius:12px;padding:.72rem .9rem;box-shadow:0 8px 24px rgba(0,0,0,.18),inset 0 1px rgba(255,255,255,.04)}
    [data-testid="stMetricLabel"]{color:var(--muted)}
    [data-testid="stMetricValue"]{color:var(--cyan)}
    .stTabs [data-baseweb="tab-list"]{gap:.35rem;border-bottom:1px solid var(--line);background:rgba(7,19,27,.55);padding:.25rem .35rem;border-radius:12px 12px 0 0}
    .stTabs [data-baseweb="tab"]{font-weight:700;padding:.8rem 1rem;color:var(--muted);border-radius:8px 8px 0 0}
    .stTabs [aria-selected="true"]{color:var(--cyan)!important;background:rgba(57,217,230,.08);border-bottom:2px solid var(--cyan)!important;text-shadow:0 0 12px rgba(57,217,230,.35)}
    div[data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px;background:rgba(13,32,42,.72);box-shadow:0 8px 24px rgba(0,0,0,.12)}
    div[data-testid="stAlert"]{border-radius:10px;background:rgba(16,43,53,.9);border:1px solid var(--line);color:var(--ink)}
    div[data-baseweb="input"],div[data-baseweb="select"]>div{background:#0b2029;border-color:var(--line);color:var(--ink)}
    [data-testid="stSlider"] [role="slider"]{background:var(--cyan);border-color:var(--cyan);box-shadow:0 0 10px rgba(57,217,230,.55)}
    button[kind="primary"]{background:linear-gradient(135deg,#138692,#39d9e6);color:#061218;border:0;box-shadow:0 0 18px rgba(57,217,230,.2);font-weight:800}
    button[kind="secondary"]{background:#102b35;color:var(--ink);border:1px solid var(--line)}
    .section-card{background:linear-gradient(145deg,rgba(16,43,53,.92),rgba(9,25,33,.92));border:1px solid var(--line);border-radius:14px;padding:1rem 1.15rem;margin:.4rem 0 1rem}
    .status-pill{display:inline-block;background:rgba(184,243,91,.1);color:var(--lime);border:1px solid rgba(184,243,91,.45);border-radius:999px;padding:.28rem .72rem;font-size:.72rem;letter-spacing:.08em;font-weight:800;box-shadow:0 0 14px rgba(184,243,91,.12)}
    hr{border-color:var(--line)!important}
    .stCaption,[data-testid="stCaptionContainer"]{color:var(--muted)!important}
    @media(max-width:900px){.block-container{padding:1rem .8rem 1.5rem!important}.sub-header{margin-left:0}.main-header{font-size:1.55rem}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">GEE Geospatial Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Sentinel-2 SR · Analisis indeks · Perbandingan temporal · Klasifikasi LULC'
    '</div>',
    unsafe_allow_html=True,
)

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
    st.header("Pengaturan analisis")
    st.caption("AOI, periode citra, dan filter awan berlaku untuk semua panel.")
    st.markdown("---")

    # ── Input AOI ─────────────────────────────────────────────────────────────
    st.subheader("📍 Input AOI")
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
    st.subheader("📅 Rentang Waktu")
    start_date = st.date_input("Mulai",   value=date.today() - timedelta(days=180))
    end_date   = st.date_input("Selesai", value=date.today())
    if start_date >= end_date:
        st.error("Tanggal mulai harus sebelum selesai.")
        st.stop()

    st.markdown("---")

    # ── Filter awan ───────────────────────────────────────────────────────────
    st.subheader("☁️ Filter Awan")
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
    "🛰️ GEE Geospatial Dashboard v3 · Sentinel-2 SR · "
    "Folium + streamlit-folium + Leaflet.js + Google Earth Engine"
    "</div>",
    unsafe_allow_html=True,
)
