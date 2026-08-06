"""
utils/geo_utils.py
──────────────────
Utilitas geometri / GeoJSON:
  - geojson_to_ee()    : konversi GeoJSON → ee.Geometry
  - get_centroid()     : hitung centroid dari GeoJSON
  - shapefile_to_ee()  : baca shapefile upload → ee.Geometry + GeoJSON dict
"""

import os
import tempfile
import math
import ee
import streamlit as st
from config import DEFAULT_LAT, DEFAULT_LON

# Coba impor geopandas (opsional – hanya diperlukan untuk upload shapefile)
try:
    import geopandas as gpd
    from shapely.geometry import mapping
    GEOPANDAS_OK = True
except ImportError:
    GEOPANDAS_OK = False


def geojson_to_ee(geojson_dict: dict):
    """
    Konversi GeoJSON (FeatureCollection / Feature / Geometry) → ee.Geometry.
    Mengembalikan None jika gagal.
    """
    gtype = geojson_dict.get("type", "")
    if gtype == "FeatureCollection":
        feats = [f for f in geojson_dict.get("features", []) if f.get("geometry")]
        if not feats:
            return None
        try:
            # Preserve every polygon/rectangle drawn by the user. The previous
            # implementation silently used only features[0].
            return ee.FeatureCollection(feats).geometry()
        except Exception:
            return None
    elif gtype == "Feature":
        geom = geojson_dict.get("geometry", geojson_dict)
    else:
        geom = geojson_dict
    try:
        return ee.Geometry(geom)
    except Exception:
        return None


def get_centroid(geojson_dict: dict) -> tuple[float, float]:
    """
    Hitung centroid sederhana dari GeoJSON → (lat, lon).
    Fallback ke DEFAULT_LAT/DEFAULT_LON jika gagal.
    """
    gtype = geojson_dict.get("type", "")
    if gtype == "FeatureCollection":
        feats = geojson_dict.get("features", [])
        coords_list = (feats[0].get("geometry", {}).get("coordinates", [[[]]])
                       if feats else [[[]]])
    elif gtype == "Feature":
        coords_list = geojson_dict.get("geometry", {}).get("coordinates", [[[]]])
    else:
        coords_list = geojson_dict.get("coordinates", [[[]]])

    try:
        flat = coords_list[0] if isinstance(coords_list[0][0], list) else coords_list
        lons = [c[0] for c in flat if isinstance(c, (list, tuple)) and len(c) >= 2]
        lats = [c[1] for c in flat if isinstance(c, (list, tuple)) and len(c) >= 2]
        if lons and lats:
            return sum(lats) / len(lats), sum(lons) / len(lons)
    except (IndexError, TypeError):
        pass
    return DEFAULT_LAT, DEFAULT_LON


def utm_epsg_from_latlon(lat: float, lon: float) -> str:
    """Return the metric UTM CRS covering an AOI centroid."""
    zone = int(math.floor((lon + 180) / 6) + 1)
    code = 32600 + zone if lat >= 0 else 32700 + zone
    return f"EPSG:{code}"


def shapefile_to_ee(uploaded_files) -> tuple:
    """
    Baca berkas shapefile yang di-upload (list UploadedFile) →
    (ee.Geometry | None, geojson_dict | None).

    Membutuhkan geopandas.  Jika tidak tersedia, kembalikan (None, None).
    """
    if not GEOPANDAS_OK:
        return None, None

    with tempfile.TemporaryDirectory() as tmpdir:
        shp_path = None
        for uf in uploaded_files:
            fp = os.path.join(tmpdir, uf.name)
            with open(fp, "wb") as f:
                f.write(uf.read())
            if uf.name.endswith(".shp"):
                shp_path = fp

        if not shp_path:
            return None, None

        try:
            gdf = gpd.read_file(shp_path)
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
            dissolved = gdf.dissolve()
            geom_dict = mapping(dissolved.geometry.iloc[0])
            fc = {
                "type": "FeatureCollection",
                "features": [{"type": "Feature",
                               "geometry": geom_dict,
                               "properties": {}}],
            }
            return ee.Geometry(geom_dict), fc
        except Exception as e:
            st.error(f"Gagal membaca shapefile: {e}")
            return None, None
