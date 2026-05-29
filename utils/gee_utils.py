"""
utils/gee_utils.py
──────────────────
Fungsi utilitas Google Earth Engine:
  - initialize_gee()    : autentikasi & inisialisasi
  - get_s2_composite()  : komposit median Sentinel-2 dengan cloud masking
  - add_indices()       : tambahkan band NDVI, NDWI, NDBI
"""

import ee
import streamlit as st
from config import GEE_PROJECT


@st.cache_resource(show_spinner="Menghubungkan ke Google Earth Engine...")
def initialize_gee() -> bool:
    """
    Inisialisasi GEE.  Urutan percobaan:
    1. ee.Initialize langsung (token sudah ada / Streamlit Cloud Secrets)
    2. ee.Authenticate() → ee.Initialize (fallback lokal)
    """
    try:
        ee.Initialize(project=GEE_PROJECT)
        return True
    except Exception:
        try:
            ee.Authenticate()
            ee.Initialize(project=GEE_PROJECT)
            return True
        except Exception:
            return False


@st.cache_data(show_spinner="Memproses Sentinel-2...", ttl=3600)
def get_s2_composite(_roi_json: dict, start, end, cloud_pct: int):
    """
    Buat komposit median Sentinel-2 SR yang sudah di-cloud-mask.

    Parameters
    ----------
    _roi_json  : dict  – GeoJSON geometry (di-cache by value)
    start      : date  – tanggal mulai
    end        : date  – tanggal selesai
    cloud_pct  : int   – batas maksimum tutupan awan (%)

    Returns
    -------
    (ee.Image | None, int)  – komposit ter-clip + jumlah scene
    """
    roi_geom = ee.Geometry(_roi_json)

    def mask_clouds(img: ee.Image) -> ee.Image:
        qa = img.select("QA60")
        mask = (qa.bitwiseAnd(1 << 10).eq(0)
                 .And(qa.bitwiseAnd(1 << 11).eq(0)))
        return (img.updateMask(mask)
                   .divide(10000)
                   .copyProperties(img, ["system:time_start"]))

    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi_geom)
        .filterDate(str(start), str(end))
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
        .map(mask_clouds)
    )
    count = col.size().getInfo()
    if count == 0:
        return None, 0
    return col.median().clip(roi_geom), count


def add_indices(img: ee.Image) -> ee.Image:
    """Tambahkan band NDVI, NDWI, dan NDBI ke image Sentinel-2."""
    return img.addBands([
        img.normalizedDifference(["B8", "B4"]).rename("NDVI"),
        img.normalizedDifference(["B3", "B8"]).rename("NDWI"),
        img.normalizedDifference(["B11", "B8"]).rename("NDBI"),
    ])
