"""
utils/map_utils.py
──────────────────
Utilitas untuk membangun peta Folium:
  - base_map()      : peta dasar dengan basemap satellite + OSM
  - add_ee_layer()  : tambahkan EE image tile ke Folium map
  - add_roi_layer() : tambahkan ROI boundary sebagai GeoJSON
  - add_legend()    : tambahkan legend ke dalam peta
"""

import folium
import ee
import json
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


def add_roi_layer(
    folium_map: folium.Map,
    _roi: ee.Geometry,
    name: str = "Batas AOI",
    color: str = "yellow",
) -> None:
    """
    Tambahkan ROI boundary sebagai GeoJSON layer (outline saja, tidak filled).

    Parameters
    ----------
    folium_map : folium.Map    – peta tujuan
    _roi       : ee.Geometry   – ROI boundary
    name       : str           – label layer
    color      : str           – warna garis
    """
    try:
        # Konversi Geometry ke GeoJSON langsung
        roi_geojson = _roi.getInfo()
        
        # Tambahkan sebagai GeoJSON dengan style (hanya outline, tidak filled)
        folium.GeoJson(
            roi_geojson,
            style_function=lambda x: {
                "fillColor": "transparent",
                "color": color,
                "weight": 2,
                "opacity": 0.8,
                "dashArray": "5, 5",  # Garis putus-putus
            },
            name=name,
            popup="Area of Interest",
        ).add_to(folium_map)
    except Exception as e:
        print(f"Error adding ROI layer: {e}")


def add_legend(folium_map: folium.Map, legend_dict: dict) -> None:
    """
    Tambahkan legend custom ke dalam peta di pojok kanan bawah.

    Parameters
    ----------
    folium_map  : folium.Map – peta tujuan
    legend_dict : dict       – {'label': 'color', ...}
    """
    legend_html = '''
     <div style="position: fixed; 
     bottom: 50px; right: 10px; width: 220px; height: auto; 
     background-color: white; border:2px solid grey; z-index:9999; font-size:13px;
     padding: 10px; border-radius: 5px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3)">
     <p style="margin: 0 0 10px 0; font-weight: bold;">Legenda LULC (7 Kelas)</p>
    '''
    for label, color in legend_dict.items():
        legend_html += f'''
        <p style="margin: 5px 0;">
            <span style="background-color: {color}; width: 20px; height: 20px; 
            display: inline-block; border-radius: 3px; border: 1px solid #333;"></span>
            {label}
        </p>
        '''
    legend_html += '</div>'
    
    folium_map.get_root().html.add_child(folium.Element(legend_html))


def add_ee_layer(
    folium_map: folium.Map,
    ee_object,
    vis_params: dict,
    name: str,
    show: bool = True,
) -> None:
    """
    Tambahkan layer Earth Engine (Image) sebagai TileLayer ke peta Folium.

    Parameters
    ----------
    folium_map : folium.Map    – peta tujuan
    ee_object  : ee.Image      – citra EE yang akan ditampilkan
    vis_params : dict          – parameter visualisasi
    name       : str           – label layer di LayerControl
    show       : bool          – tampilkan layer by default (True)
    """
    # Asumsikan input adalah Image (bukan Geometry)
    ee_image = ee_object
    
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


