"""
utils/gee_utils.py
──────────────────
Fungsi utilitas Google Earth Engine:
  - initialize_gee()    : autentikasi & inisialisasi
  - get_s2_composite()  : komposit median Sentinel-2 dengan cloud masking
  - add_indices()       : tambahkan band NDVI, NDWI, NDBI
"""

import os
import json
import ee
import streamlit as st
from config import GEE_PROJECT


@st.cache_resource(show_spinner="Menghubungkan ke Google Earth Engine...")
def initialize_gee() -> bool:
    """
    Inisialisasi GEE. Urutan percobaan:
    1. Service Account JSON penuh (GEE_SERVICE_ACCOUNT = {...})
    2. Service Account terpisah (GEE_SERVICE_ACCOUNT=email + GEE_PRIVATE_KEY + GEE_PROJECT_ID)
    3. ee.Initialize langsung (token lokal)
    4. ee.Authenticate() → fallback
    """
    # Baca dari st.secrets dulu (Streamlit Cloud), fallback ke os.getenv (lokal)
    secrets = getattr(st, "secrets", {})

    sa_json = secrets.get("GEE_SERVICE_ACCOUNT") or os.getenv("GEE_SERVICE_ACCOUNT")
    sa_key  = secrets.get("GEE_PRIVATE_KEY") or os.getenv("GEE_PRIVATE_KEY")
    project_id = secrets.get("GEE_PROJECT_ID") or secrets.get("GEE_PROJECT") or os.getenv("GEE_PROJECT_ID") or GEE_PROJECT

    # Format 1: JSON penuh
    if sa_json and sa_json.strip().startswith("{"):
        try:
            credentials = ee.ServiceAccountCredentials(email=None, key_data=sa_json)
            ee.Initialize(credentials, project=project_id)
            return True
        except Exception as e:
            st.warning(f"GEE JSON auth failed: {e}")

    # Format 2: email + private key terpisah
    sa_email = secrets.get("GEE_SERVICE_ACCOUNT") or os.getenv("GEE_SERVICE_ACCOUNT")
    if sa_email and sa_key and not sa_email.strip().startswith("{"):
        try:
            credentials = ee.ServiceAccountCredentials(email=sa_email, key_data=sa_key)
            ee.Initialize(credentials, project=project_id)
            return True
        except Exception as e:
            st.warning(f"GEE split auth failed: {e}")

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
def get_s2_composite(roi_json: dict, start, end, cloud_pct: int):
    """
    Buat komposit median Sentinel-2 SR yang sudah di-cloud-mask.

    Parameters
    ----------
    roi_json   : dict  – GeoJSON geometry (ikut menjadi cache key)
    start      : date  – tanggal mulai
    end        : date  – tanggal selesai
    cloud_pct  : int   – batas maksimum tutupan awan (%)

    Returns
    -------
    (ee.Image | None, int)  – komposit ter-clip + jumlah scene
    """
    roi_geom = ee.Geometry(roi_json)

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
