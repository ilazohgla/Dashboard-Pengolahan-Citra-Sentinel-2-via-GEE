"""
utils/download_utils.py
────────────────────────
Fungsi untuk menghasilkan URL download citra dari Google Earth Engine:
  - get_download_url()      : PNG / JPG preview  atau  GeoTIFF visualisasi RGB
  - get_geotiff_raw_url()   : GeoTIFF nilai mentah float (band asli)

Batasan GEE:
  • getThumbURL  → maks ~1024px, cocok untuk preview cepat
  • getDownloadURL → maks ±32 MB / ±100 km²; untuk area lebih besar
    gunakan Export.image.toDrive di GEE Code Editor.
"""

import ee
from config import DEFAULT_SCALE, MAX_THUMB_DIM


def get_download_url(
    ee_image: ee.Image,
    vis_params: dict,
    roi_geom: ee.Geometry,
    scale: int = DEFAULT_SCALE,
    fmt: str = "png",
) -> str | None:
    """
    Hasilkan URL download dari EE Image.

    Parameters
    ----------
    ee_image   : ee.Image   – citra yang akan diunduh
    vis_params : dict       – parameter visualisasi (bands, min, max, palette…)
    roi_geom   : ee.Geometry – batas area of interest
    scale      : int        – resolusi spasial dalam meter/piksel (khusus GeoTIFF)
    fmt        : str        – 'png' | 'jpg' | 'geotiff'

    Returns
    -------
    str | None  – URL download, atau None jika gagal
    """
    try:
        region = roi_geom.bounds().getInfo()["coordinates"]

        if fmt == "geotiff":
            # Render sebagai RGB uint8 terlebih dahulu agar warna sesuai tampilan
            bands = vis_params.get("bands", None)
            if bands:
                img_to_dl = ee_image.select(bands).visualize(**vis_params)
            else:
                img_to_dl = ee_image.visualize(**vis_params)

            return img_to_dl.getDownloadURL({
                "region": region,
                "scale":  scale,
                "format": "GEO_TIFF",
                "crs":    "EPSG:4326",
            })
        else:
            # PNG / JPG preview via getThumbURL
            return ee_image.getThumbURL({
                **vis_params,
                "region":     region,
                "dimensions": MAX_THUMB_DIM,
                "format":     fmt,
            })

    except Exception:
        return None


def get_geotiff_raw_url(
    ee_image: ee.Image,
    band_name: str | None,
    roi_geom: ee.Geometry,
    scale: int = DEFAULT_SCALE,
) -> str | None:
    """
    Hasilkan URL download GeoTIFF dengan nilai mentah float/int.
    Cocok untuk analisis lanjut di QGIS / Python (rasterio, GDAL).

    Parameters
    ----------
    ee_image   : ee.Image        – citra sumber
    band_name  : str | None      – nama band yang ingin diunduh;
                                   None = unduh semua band yang ada
    roi_geom   : ee.Geometry     – batas area of interest
    scale      : int             – resolusi spasial dalam meter/piksel

    Returns
    -------
    str | None  – URL download, atau None jika gagal
    """
    try:
        region = roi_geom.bounds().getInfo()["coordinates"]
        img_to_dl = ee_image if band_name is None else ee_image.select(band_name)
        return img_to_dl.getDownloadURL({
            "region": region,
            "scale":  scale,
            "format": "GEO_TIFF",
            "crs":    "EPSG:4326",
        })
    except Exception:
        return None
