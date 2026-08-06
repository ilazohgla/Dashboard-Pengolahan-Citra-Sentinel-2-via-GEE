"""
pages/tab_main_map.py
─────────────────────
Render Tab 1: Peta Utama + Draw AOI + Download Citra.
Dipanggil dari app.py:

    from pages.tab_main_map import render_tab_main_map
    render_tab_main_map(composite, roi, roi_json, img_count,
                        start_date, end_date, max_cloud,
                        center_lat, center_lon, aoi_mode)
"""

import json
import folium
import streamlit as st
from streamlit_folium import st_folium
from folium.plugins import Draw, Fullscreen, MeasureControl

from config import LAYER_CONFIG
from utils.map_utils import base_map, add_ee_layer
from utils.geo_utils import geojson_to_ee
from utils.download_utils import get_download_url, get_geotiff_raw_url


def render_tab_main_map(
    composite,
    roi,
    roi_json: dict,
    img_count: int,
    start_date,
    end_date,
    max_cloud: int,
    center_lat: float,
    center_lon: float,
    aoi_mode: str,
) -> None:
    """Render seluruh konten Tab 1."""

    # ── Header status ─────────────────────────────────────────────────────────
    st.markdown('<span class="status-pill">● LIVE GEE COMPOSITE</span>', unsafe_allow_html=True)
    st.markdown("### Peta utama dan analisis indeks")
    m1c, m2c, m3c, m4c = st.columns(4)
    m1c.metric("Scene tersedia", img_count)
    m2c.metric("Periode analisis", f"{start_date} → {end_date}")
    m3c.metric("Batas awan", f"{max_cloud}%")
    m4c.metric("Mode AOI", "Polygon" if "Gambar" in aoi_mode else "Shapefile")

    # ── Pilih layer & opsi peta ───────────────────────────────────────────────
    with st.expander("🎛️ Layer, visualisasi, dan tools peta", expanded=True):
        layers_active = st.multiselect(
            "Layer aktif:",
            list(LAYER_CONFIG.keys()),
            default=["True Color", "NDVI"],
        )

    # ── Bangun peta utama ─────────────────────────────────────────────────────
    Map1 = base_map(center_lat, center_lon, zoom=12)

    for lname in layers_active:
        cfg = LAYER_CONFIG[lname]
        img = composite.select(cfg["band"]) if cfg["band"] else composite
        add_ee_layer(Map1, img, cfg["vis"], f"{cfg['icon']} {lname}")

    # Tampilkan AOI yang sudah dikonfirmasi
    if st.session_state.get("aoi_geojson"):
        folium.GeoJson(
            st.session_state["aoi_geojson"],
            name="✅ AOI Aktif",
            style_function=lambda x: {
                "color": "#e74c3c", "weight": 3,
                "fillColor": "#e74c3c", "fillOpacity": 0.12,
            },
        ).add_to(Map1)

    # Draw toolbar
    if aoi_mode == "✏️ Gambar Polygon":
        Draw(
            export=False,
            draw_options={
                "polyline": False, "circle": False,
                "circlemarker": False, "marker": False,
                "polygon":   {"allowIntersection": False, "showArea": True},
                "rectangle": {"showArea": True},
            },
            edit_options={"edit": True, "remove": True},
        ).add_to(Map1)

    Fullscreen(position="topright").add_to(Map1)
    MeasureControl(
        position="bottomleft",
        primary_length_unit="kilometers",
        secondary_length_unit="miles",
        primary_area_unit="sqkilometers",
    ).add_to(Map1)
    folium.LayerControl(collapsed=False, position="topright").add_to(Map1)

    map_result = st_folium(
        Map1,
        height=640,
        width="stretch",
        returned_objects=["all_drawings", "last_active_drawing"],
        key="main_map",
    )

    # ── Konfirmasi AOI ────────────────────────────────────────────────────────
    if aoi_mode == "✏️ Gambar Polygon":
        all_drawn = map_result.get("all_drawings") if map_result else None
        if all_drawn:
            col_cfm, col_rst, _ = st.columns([1.2, 1, 4])
            with col_cfm:
                if st.button("✅ Konfirmasi AOI", type="primary"):
                    fc = {
                        "type": "FeatureCollection",
                        "features": all_drawn if isinstance(all_drawn, list) else [all_drawn],
                    }
                    if geojson_to_ee(fc):
                        st.session_state["aoi_geojson"] = fc
                        st.success("AOI dikonfirmasi!")
                        st.rerun()
                    else:
                        st.error("Geometri tidak valid, coba gambar ulang.")
            with col_rst:
                if st.button("🗑️ Hapus Gambar"):
                    st.session_state["aoi_geojson"] = None
                    st.rerun()

    st.markdown("---")

    # ── Download section ──────────────────────────────────────────────────────
    st.subheader("⬇️ Download Citra per Layer")

    dl_fmt_col, dl_scale_col, dl_info_col = st.columns([1.5, 1, 3])
    with dl_fmt_col:
        dl_format = st.selectbox(
            "Format Download",
            ["PNG (preview)", "GeoTIFF – Visualisasi RGB", "GeoTIFF – Nilai Mentah (Float)"],
            key="dl_format_select",
        )
    with dl_scale_col:
        dl_scale = st.number_input(
            "Resolusi (m/px)", min_value=10, max_value=500, value=30, step=10,
            key="dl_scale",
            help="Hanya berlaku untuk GeoTIFF. PNG selalu 1024px.",
        )
    with dl_info_col:
        if "GeoTIFF" in dl_format:
            st.info(
                "ℹ️ **GeoTIFF** georeferenced, bisa dibuka di QGIS/ArcGIS. "
                "**Nilai Mentah** = band float asli. "
                "Untuk AOI >100 km², pakai `Export.image.toDrive` di GEE Code Editor.",
                icon="🗺️",
            )
        else:
            st.caption("PNG resolusi 1024px, cocok untuk pratinjau cepat.")

    dl_cols = st.columns(len(LAYER_CONFIG))
    for i, (lname, cfg) in enumerate(LAYER_CONFIG.items()):
        with dl_cols[i]:
            if st.button(f"{cfg['icon']} {lname}", key=f"dl_{lname}", width="stretch"):
                with st.spinner(f"Menyiapkan {lname}..."):
                    img_dl = composite.select(cfg["band"]) if cfg["band"] else composite

                    if dl_format == "PNG (preview)":
                        url = get_download_url(img_dl, cfg["vis"], roi, scale=dl_scale, fmt="png")
                        label, color = f"PNG – {lname}", "#1a6b3c"
                    elif dl_format == "GeoTIFF – Visualisasi RGB":
                        url = get_download_url(img_dl, cfg["vis"], roi, scale=dl_scale, fmt="geotiff")
                        label, color = f"GeoTIFF RGB – {lname}", "#1a5276"
                    else:
                        band = cfg["band"]
                        if band is None:
                            bands = cfg["vis"].get("bands", ["B4", "B3", "B2"])
                            url = get_geotiff_raw_url(composite.select(bands), None, roi, scale=dl_scale)
                        else:
                            url = get_geotiff_raw_url(composite, band, roi, scale=dl_scale)
                        label, color = f"GeoTIFF Raw – {lname}", "#6e2f8a"

                if url:
                    st.markdown(
                        f'<a href="{url}" target="_blank" style="display:block;text-align:center;'
                        f'background:{color};color:white;padding:.4rem .8rem;border-radius:6px;'
                        f'text-decoration:none;font-size:.85rem;">⬇️ {label}</a>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error("Gagal menghasilkan URL. Area terlalu besar atau melebihi batas GEE.")

    # ── Legenda ───────────────────────────────────────────────────────────────
    if any(l in layers_active for l in ["NDVI", "NDWI", "NDBI"]):
        with st.expander("🎨 Legenda Indeks"):
            lc1, lc2, lc3 = st.columns(3)
            lc1.markdown("**🌿 NDVI**\n- 🟥 < 0: Air / lahan gersang\n- 🟨 0–0.4: Vegetasi jarang\n- 🟩 > 0.6: Vegetasi lebat")
            lc2.markdown("**💧 NDWI**\n- ⬜ < 0: Daratan kering\n- 🔵 > 0.3: Badan air / basah")
            lc3.markdown("**🏙️ NDBI**\n- 🟩 < 0: Vegetasi\n- 🟥 > 0.1: Lahan terbangun")
