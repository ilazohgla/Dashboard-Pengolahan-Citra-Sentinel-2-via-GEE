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
import io
import zipfile
import requests
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

    except Exception as e:
        print(f"DEBUG: Error generating URL: {e}")
        return None


def get_geotiff_raw_url(
    ee_image: ee.Image,
    band_name: str | None,
    roi_geom: ee.Geometry,
    scale: int = DEFAULT_SCALE,
    crs: str | None = None,
    format_name: str = "GEO_TIFF",
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
    crs        : str | None      – sistem koordinat proyeksi (misal 'EPSG:32648' / 'EPSG:4326')

    Returns
    -------
    str | None  – URL download, atau None jika gagal
    """
    try:
        # Pakai geometri AOI asli agar hasil tidak bergeser ke bounding box.
        # Jika geometry terlalu besar, EE akan mengembalikan error dan UI memberi
        # fallback/anjuran Export ke Drive, bukan membuat file kosong.
        region_info = roi_geom.getInfo()
        # getDownloadURL accepts a geometry object; preserve the exact AOI.
        region = region_info
        img_to_dl = ee_image if band_name is None else ee_image.select(band_name)

        # Gunakan format ini untuk stabilitas lebih baik
        params = {
            "region": region,
            "scale":  scale,
            "format": format_name,
            "filePerBand": False,
        }
        # crs=None → jangan paksa EPSG:4326; biarkan GEE memakai projection
        # default image (setDefaultProjection dari native composite) supaya
        # grid GeoTIFF identik dengan tampilan basemap, bukan bergeser/resample.
        if crs is not None:
            params["crs"] = crs
        return img_to_dl.getDownloadURL(params)
    except Exception as e:
        print(f"DEBUG: Error generating URL: {e}")
        return None


def fetch_geotiff_bytes(download_url: str, timeout: int = 180) -> tuple[bytes | None, str]:
    """Fetch one valid GeoTIFF from an Earth Engine download URL.

    Accepts direct TIFF or ZIP-wrapped TIFF and rejects tiny metadata-only files.
    """
    try:
        response = requests.get(download_url, timeout=timeout)
        response.raise_for_status()
        payload = response.content
    except requests.RequestException as exc:
        return None, f"Request ke Earth Engine gagal: {exc}"

    if zipfile.is_zipfile(io.BytesIO(payload)):
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                tif_names = [
                    name for name in archive.namelist()
                    if name.lower().endswith((".tif", ".tiff"))
                ]
                if not tif_names:
                    return None, "Respons Earth Engine berupa ZIP tetapi tidak berisi GeoTIFF."
                name = max(tif_names, key=lambda item: archive.getinfo(item).file_size)
                payload = archive.read(name)
        except (zipfile.BadZipFile, KeyError) as exc:
            return None, f"ZIP GeoTIFF tidak valid: {exc}"

    is_tiff = payload[:4] in (b"II*\x00", b"MM\x00*")
    if not is_tiff:
        detail = payload[:300].decode("utf-8", errors="replace").strip()
        return None, f"Earth Engine mengembalikan respons non-TIFF: {detail}"
    # GeoTIFF kategorikal (mis. LULC satu kelas konstan) bisa sangat kecil
    # dan tetap valid. Hanya tolak jika lebih kecil dari header TIFF minimal
    # (8 byte), bukan 512 byte — threshold lama menolak file bagus.
    if len(payload) < 8:
        return None, f"GeoTIFF tidak valid ({len(payload)} byte), kemungkinan respons tidak lengkap."
    return payload, ""

