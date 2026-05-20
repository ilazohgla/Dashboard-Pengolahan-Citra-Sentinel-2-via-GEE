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
import streamlit as st
from datetime import date, timedelta

from config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_ZOOM
from utils.gee_utils import initialize_gee, get_s2_composite, add_indices
from utils.geo_utils import geojson_to_ee, get_centroid, shapefile_to_ee, GEOPANDAS_OK
from pages.tab_main_map import render_tab_main_map
from pages.tab_split_panel import render_tab_split_panel

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
    .main-header{font-size:1.8rem;font-weight:700;color:#1a6b3c;text-align:center;padding:.4rem 0 .2rem 0}
    .sub-header{font-size:.85rem;color:#6c757d;text-align:center;margin-bottom:.8rem}
    .block-container{padding-top:1rem!important;padding-bottom:0!important}
    .stTabs [data-baseweb="tab"]{font-weight:600}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🌍 GEE Geospatial Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Sentinel-2 SR · NDVI · NDWI · NDBI | Draw AOI · Upload Shapefile · Download PNG / GeoTIFF'
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
    st.header("⚙️ Pengaturan Global")
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
tab1, tab2 = st.tabs(["🗺️ Peta Utama & Indeks", "↔️ Split-Panel"])

with tab1:
    render_tab_main_map(
        composite, roi, roi_json, img_count,
        start_date, end_date, max_cloud,
        center_lat, center_lon, aoi_mode,
    )

with tab2:
    render_tab_split_panel(roi, roi_json, max_cloud, center_lat, center_lon)

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
