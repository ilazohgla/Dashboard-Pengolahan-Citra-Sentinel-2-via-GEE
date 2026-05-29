"""
pages/tab_split_panel.py
────────────────────────
Render Tab 2: Split-Panel Perbandingan Temporal (synchronized zoom via Leaflet JS).
Dipanggil dari app.py:

    from pages.tab_split_panel import render_tab_split_panel
    render_tab_split_panel(roi, roi_json, max_cloud, center_lat, center_lon)
"""

import json
from datetime import date, timedelta

import streamlit as st
import streamlit.components.v1 as components

from config import LAYER_CONFIG
from utils.gee_utils import get_s2_composite, add_indices
from utils.download_utils import get_download_url, get_geotiff_raw_url


def render_tab_split_panel(
    roi,
    roi_json: dict,
    max_cloud: int,
    center_lat: float,
    center_lon: float,
) -> None:
    """Render seluruh konten Tab 2."""

    st.subheader("↔️ Perbandingan Temporal – Synchronized Zoom")
    st.info(
        "Zoom/pan di **salah satu peta** akan otomatis sinkron ke peta lainnya. "
        "Panel kiri = Baseline | Panel kanan = Perbandingan.",
        icon="🔄",
    )

    col_bl, col_cp = st.columns(2)
    with col_bl:
        st.markdown("**⬅️ Baseline**")
        bl_start = st.date_input("Mulai",   value=date.today() - timedelta(days=730), key="bls")
        bl_end   = st.date_input("Selesai", value=date.today() - timedelta(days=365), key="ble")
    with col_cp:
        st.markdown("**➡️ Perbandingan**")
        cp_start = st.date_input("Mulai",   value=date.today() - timedelta(days=180), key="cps")
        cp_end   = st.date_input("Selesai", value=date.today(), key="cpe")

    sp_index = st.selectbox("Layer untuk perbandingan", list(LAYER_CONFIG.keys()), index=0)

    if not st.button("🔄 Render Split-Panel Sinkron", type="primary"):
        st.markdown(
            "<div style='text-align:center;padding:3rem;color:#888'>"
            "👆 Atur periode dan klik <b>Render Split-Panel Sinkron</b></div>",
            unsafe_allow_html=True,
        )
        return

    with st.spinner("Memproses dua komposit..."):
        bl_raw, cnt_bl = get_s2_composite(roi_json, bl_start, bl_end, max_cloud)
        cp_raw, cnt_cp = get_s2_composite(roi_json, cp_start, cp_end, max_cloud)

    if bl_raw is None or cp_raw is None:
        st.error("Salah satu periode tidak memiliki citra. Perluas rentang waktu.")
        return

    bl_img_full = add_indices(bl_raw)
    cp_img_full = add_indices(cp_raw)

    cfg    = LAYER_CONFIG[sp_index]
    img_bl = bl_img_full.select(cfg["band"]) if cfg["band"] else bl_img_full
    img_cp = cp_img_full.select(cfg["band"]) if cfg["band"] else cp_img_full

    tile_bl  = img_bl.getMapId(cfg["vis"])["tile_fetcher"].url_format
    tile_cp  = img_cp.getMapId(cfg["vis"])["tile_fetcher"].url_format
    sat_tile = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"

    st.success(f"✅ Baseline: {cnt_bl} scene | Perbandingan: {cnt_cp} scene")

    # ── Leaflet synchronized dual-map ─────────────────────────────────────────
    roi_coords = json.dumps([
        [c[1], c[0]]
        for c in roi_json.get("coordinates", [[]])[0]
    ])

    sync_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:sans-serif;background:#1a1a2e}}
    #wrapper{{display:flex;width:100%;height:560px;gap:4px}}
    .map-container{{flex:1;display:flex;flex-direction:column}}
    .map-label{{background:rgba(0,0,0,.65);color:#fff;font-size:12px;font-weight:600;
               padding:5px 10px;text-align:center;letter-spacing:.5px}}
    .map-label span{{color:#aef}}
    .leaflet-map{{flex:1}}
    .leaflet-control-attribution{{font-size:9px!important}}
    #divider{{width:4px;background:#e74c3c;cursor:col-resize;flex-shrink:0}}
  </style>
</head>
<body>
<div id="wrapper">
  <div class="map-container">
    <div class="map-label">⬅️ BASELINE &nbsp;<span>{bl_start} → {bl_end}</span></div>
    <div id="mapL" class="leaflet-map"></div>
  </div>
  <div id="divider" title="Tarik untuk resize"></div>
  <div class="map-container">
    <div class="map-label">➡️ PERBANDINGAN &nbsp;<span>{cp_start} → {cp_end}</span></div>
    <div id="mapR" class="leaflet-map"></div>
  </div>
</div>
<script>
  const CENTER=[{center_lat},{center_lon}],ZOOM=12;
  const mapL=L.map('mapL',{{center:CENTER,zoom:ZOOM}});
  const mapR=L.map('mapR',{{center:CENTER,zoom:ZOOM}});
  L.tileLayer('{sat_tile}',{{attribution:'Google',maxZoom:20}}).addTo(mapL);
  L.tileLayer('{sat_tile}',{{attribution:'Google',maxZoom:20}}).addTo(mapR);
  L.tileLayer('{tile_bl}',{{attribution:'GEE',maxZoom:20,opacity:1}}).addTo(mapL);
  L.tileLayer('{tile_cp}',{{attribution:'GEE',maxZoom:20,opacity:1}}).addTo(mapR);

  let syncing=false;
  function syncMaps(src,tgt){{
    if(syncing)return; syncing=true;
    tgt.setView(src.getCenter(),src.getZoom(),{{animate:false}});
    syncing=false;
  }}
  mapL.on('moveend zoomend',()=>syncMaps(mapL,mapR));
  mapR.on('moveend zoomend',()=>syncMaps(mapR,mapL));

  const roiCoords={roi_coords};
  const roiStyle={{color:'#e74c3c',weight:2,fill:true,fillOpacity:0.08}};
  if(roiCoords.length>0){{
    L.polygon(roiCoords,roiStyle).addTo(mapL);
    L.polygon(roiCoords,roiStyle).addTo(mapR);
  }}

  const div=document.getElementById('divider'),wrap=document.getElementById('wrapper');
  let resizing=false;
  div.addEventListener('mousedown',e=>{{resizing=true;e.preventDefault();}});
  document.addEventListener('mousemove',e=>{{
    if(!resizing)return;
    const r=wrap.getBoundingClientRect(),pct=Math.max(20,Math.min(80,((e.clientX-r.left)/(r.width-4))*100));
    wrap.children[0].style.width=pct+'%'; wrap.children[2].style.width=(100-pct)+'%';
    [wrap.children[0],wrap.children[2]].forEach(c=>{{c.style.flex='none';}});
    mapL.invalidateSize(); mapR.invalidateSize();
  }});
  document.addEventListener('mouseup',()=>{{resizing=false;}});

  if(roiCoords.length>0){{
    const b=L.polygon(roiCoords).getBounds();
    mapL.fitBounds(b,{{padding:[20,20]}});
    mapR.fitBounds(b,{{padding:[20,20]}});
  }}
</script>
</body></html>"""

    components.html(sync_html, height=580, scrolling=False)

    # ── Download split-panel ──────────────────────────────────────────────────
    st.markdown("#### ⬇️ Download Citra Split-Panel")
    sp_fmt_col, sp_scale_col = st.columns([2, 1])
    with sp_fmt_col:
        sp_dl_format = st.selectbox(
            "Format",
            ["PNG (preview)", "GeoTIFF – Visualisasi RGB", "GeoTIFF – Nilai Mentah (Float)"],
            key="sp_dl_format",
        )
    with sp_scale_col:
        sp_dl_scale = st.number_input(
            "Resolusi (m/px)", min_value=10, max_value=500, value=30, step=10,
            key="sp_dl_scale",
        )

    def _get_url(img_layer, vis, band):
        if sp_dl_format == "PNG (preview)":
            return get_download_url(img_layer, vis, roi, scale=sp_dl_scale, fmt="png")
        elif sp_dl_format == "GeoTIFF – Visualisasi RGB":
            return get_download_url(img_layer, vis, roi, scale=sp_dl_scale, fmt="geotiff")
        else:
            if band is None:
                bands = vis.get("bands", ["B4", "B3", "B2"])
                return get_geotiff_raw_url(img_layer.select(bands), None, roi, scale=sp_dl_scale)
            return get_geotiff_raw_url(img_layer, band, roi, scale=sp_dl_scale)

    dl1, dl2 = st.columns(2)
    for col, img_layer, label, color in [
        (dl1, img_bl, f"Baseline ({sp_index})",     "#2c3e50"),
        (dl2, img_cp, f"Perbandingan ({sp_index})", "#1a6b3c"),
    ]:
        with col:
            url = _get_url(img_layer, cfg["vis"], cfg["band"])
            if url:
                st.markdown(
                    f'<a href="{url}" target="_blank" style="display:block;text-align:center;'
                    f'background:{color};color:white;padding:.5rem;border-radius:6px;'
                    f'text-decoration:none;">⬇️ Download {label}</a>',
                    unsafe_allow_html=True,
                )
            else:
                st.error("Gagal: area terlalu besar atau batas GEE terlampaui.")
