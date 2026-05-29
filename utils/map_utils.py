"""
utils/map_utils.py
──────────────────
Utilitas untuk membangun peta Folium:
  - base_map()      : peta dasar dengan basemap satellite + OSM
  - add_ee_layer()  : tambahkan EE image tile ke Folium map
"""

import folium
import ee
from config import DEFAULT_ZOOM


def base_map(
    center_lat: float,
    center_lon: float,
    zoom: int = DEFAULT_ZOOM,
) -> folium.Map:
    """
    Buat objek peta Folium dengan dua basemap:
      • Google Satellite (aktif by default)
      • OpenStreetMap (opsional)

    Parameters
    ----------
    center_lat : float – lintang pusat peta
    center_lon : float – bujur pusat peta
    zoom       : int   – zoom level awal

    Returns
    -------
    folium.Map
    """
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        control_scale=True,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="🛰️ Satellite",
        show=True,
    ).add_to(m)
    folium.TileLayer("openstreetmap", name="OpenStreetMap", show=False).add_to(m)
    return m


def add_ee_layer(
    folium_map: folium.Map,
    ee_image: ee.Image,
    vis_params: dict,
    name: str,
    show: bool = True,
) -> None:
    """
    Tambahkan layer Earth Engine sebagai TileLayer ke peta Folium.

    Parameters
    ----------
    folium_map : folium.Map  – peta tujuan
    ee_image   : ee.Image   – citra EE yang akan ditampilkan
    vis_params : dict       – parameter visualisasi
    name       : str        – label layer di LayerControl
    show       : bool       – tampilkan layer by default (True)
    """
    map_id_dict = ee_image.getMapId(vis_params)
    folium.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
        show=show,
        opacity=1.0,
    ).add_to(folium_map)
