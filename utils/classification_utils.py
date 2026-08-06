"""
utils/classification_utils.py
──────────────────────────────
Fungsi untuk klasifikasi LULC (Land Use Land Cover) dengan berbagai metode:
  - K-Means Unsupervised
  - KNN Supervised
  - Random Forest Supervised
  - KNN + RF Ensemble

Feature engineering: Band reflektansi + 7 indeks spektral (NDVI, NDWI, NDBI, MNDWI, EVI, SAVI, BSI)
Training data otomatis dari heuristik spektral.
"""

import ee
import numpy as np
import streamlit as st
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, cohen_kappa_score
import pandas as pd


# ── KONFIGURASI LULC ──────────────────────────────────────────────────────
LULC_CLASSES = {
    0: "Built-up (Area Terbangun)",
    1: "Cropland (Lahan Pertanian)",
    2: "Forest (Hutan)",
    3: "Water (Perairan)",
    4: "Bare Land (Lahan Terbuka)",
    5: "Shrub & Grassland (Semak/Padang Rumput)",
    6: "Wetland (Lahan Basah)",
}

LULC_PALETTE = ["#e53935", "#f4b400", "#2e7d32", "#1e88e5", "#9e9d24", "#6d4c41", "#26a69a"]
LULC_COLORS = {i: LULC_PALETTE[i] for i in range(7)}


# ═════════════════════════════════════════════════════════════════════════════
# 1. FEATURE ENGINEERING
# ═════════════════════════════════════════════════════════════════════════════

def build_feature_image(composite: ee.Image, satellite: str, roi: ee.Geometry):
    """
    Bangun image multivariabel dengan:
      - Band reflektansi dasar
      - NDVI, NDWI, NDBI, MNDWI, EVI, SAVI, BSI

    Parameters
    ----------
    composite : ee.Image     – Citra komposit median yang sudah di-clip
    satellite : str          – 'L8' | 'L9' | 'S2'
    roi       : ee.Geometry  – Area of Interest

    Returns
    -------
    ee.Image  – Image multivariabel dengan semua fitur
    """
    is_landsat = satellite in ["L8", "L9"]

    # Pilih band dasar
    if is_landsat:
        bands = composite.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"])
    else:
        bands = composite.select(["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B11", "B12"])

    # === Indeks Spektral ===
    if is_landsat:
        ndvi = composite.normalizedDifference(["SR_B5", "SR_B4"])
        ndwi = composite.normalizedDifference(["SR_B3", "SR_B5"])
        ndbi = composite.normalizedDifference(["SR_B6", "SR_B5"])
        mndwi = composite.normalizedDifference(["SR_B3", "SR_B6"])

        # EVI = 2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))
        evi = composite.expression(
            "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
            {
                "NIR": composite.select("SR_B5"),
                "RED": composite.select("SR_B4"),
                "BLUE": composite.select("SR_B2"),
            },
        )

        # SAVI = ((NIR - RED) / (NIR + RED + 0.5)) * 1.5
        savi = composite.expression(
            "((NIR - RED) / (NIR + RED + 0.5)) * 1.5",
            {"NIR": composite.select("SR_B5"), "RED": composite.select("SR_B4")},
        )

        # BSI = ((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE))
        bsi = composite.expression(
            "((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE))",
            {
                "SWIR": composite.select("SR_B6"),
                "RED": composite.select("SR_B4"),
                "NIR": composite.select("SR_B5"),
                "BLUE": composite.select("SR_B2"),
            },
        )
    else:  # Sentinel-2
        ndvi = composite.normalizedDifference(["B8", "B4"])
        ndwi = composite.normalizedDifference(["B3", "B11"])
        ndbi = composite.normalizedDifference(["B11", "B8"])
        mndwi = composite.normalizedDifference(["B3", "B11"])

        evi = composite.expression(
            "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
            {"NIR": composite.select("B8"), "RED": composite.select("B4"), "BLUE": composite.select("B2")},
        )

        savi = composite.expression(
            "((NIR - RED) / (NIR + RED + 0.5)) * 1.5",
            {"NIR": composite.select("B8"), "RED": composite.select("B4")},
        )

        bsi = composite.expression(
            "((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE))",
            {
                "SWIR": composite.select("B11"),
                "RED": composite.select("B4"),
                "NIR": composite.select("B8"),
                "BLUE": composite.select("B2"),
            },
        )

    # Gabungkan semua fitur
    feature_image = (
        bands.addBands(ndvi.rename("NDVI"))
        .addBands(ndwi.rename("NDWI"))
        .addBands(ndbi.rename("NDBI"))
        .addBands(mndwi.rename("MNDWI"))
        .addBands(evi.rename("EVI"))
        .addBands(savi.rename("SAVI"))
        .addBands(bsi.rename("BSI"))
        .clip(roi)
    )

    return feature_image


# ═════════════════════════════════════════════════════════════════════════════
# 2. AUTO TRAINING DATA (Heuristik Spektral)
# ═════════════════════════════════════════════════════════════════════════════

def create_auto_training_samples(
    feature_image: ee.Image,
    roi: ee.Geometry,
    samples_per_class: int = 150,
    seed: int = 42,
) -> ee.FeatureCollection:
    """
    Generate training samples otomatis berdasarkan threshold indeks spektral.

    Kelas:
      0 = Built-up   : NDBI > 0.05 & NDVI < 0.2
      1 = Cropland   : 0.35 ≤ NDVI ≤ 0.55 & SAVI > 0.1
      2 = Forest     : NDVI > 0.6 & EVI > 0.2
      3 = Water      : NDWI > 0.25 & MNDWI > 0.1
      4 = Bare Land  : BSI > 0.1 & NDVI < 0.1 & NDWI < 0.05
      5 = Shrub      : 0.15 ≤ NDVI < 0.35 & NDWI < 0.1
      6 = Wetland    : 0.05 ≤ NDWI ≤ 0.25 & NDVI < 0.2
    """
    ndvi = feature_image.select("NDVI")
    ndwi = feature_image.select("NDWI")
    ndbi = feature_image.select("NDBI")
    mndwi = feature_image.select("MNDWI")
    bsi = feature_image.select("BSI")
    evi = feature_image.select("EVI")
    savi = feature_image.select("SAVI")

    # Threshold dibuat sedikit overlap/toleran agar AOI kecil atau citra
    # homogen tetap memiliki sampel. Urutan kelas dipertahankan di bawah.
    # Threshold lama terlalu ketat dan sering menghasilkan FeatureCollection kosong.
    mask_buildup = ndbi.gt(0.0).And(ndvi.lt(0.3))
    mask_cropland = ndvi.gte(0.3).And(ndvi.lte(0.65)).And(savi.gt(0.05))
    mask_forest = ndvi.gt(0.5).And(evi.gt(0.15))
    mask_water = ndwi.gt(0.15).Or(mndwi.gt(0.1))
    mask_bare_land = bsi.gt(0.0).And(ndvi.lt(0.2))
    mask_shrub = ndvi.gte(0.1).And(ndvi.lt(0.45)).And(ndwi.lt(0.2))
    mask_wetland = ndwi.gte(0.0).And(ndwi.lte(0.3)).And(ndvi.lt(0.3))

    masks = [
        (mask_buildup, 0),
        (mask_cropland, 1),
        (mask_forest, 2),
        (mask_water, 3),
        (mask_bare_land, 4),
        (mask_shrub, 5),
        (mask_wetland, 6),
    ]

    def sample_class(mask, class_id):
        return (
            feature_image.updateMask(mask)
            .sample(
                region=roi,
                scale=30,
                numPixels=samples_per_class,
                seed=seed + class_id,
                geometries=True,
            )
            .map(lambda f: f.set("landcover", class_id))
        )

    samples = ee.FeatureCollection([sample_class(m, cid) for m, cid in masks]).flatten()

    # Fallback untuk AOI kecil/homogen atau komposit dengan banyak pixel masked.
    # Tanpa ini EE dapat menerima FeatureCollection kosong dan melempar
    # `No valid training data were found` saat classifier dilatih.
    fallback_samples = (
        feature_image.sample(
            region=roi,
            scale=10,
            numPixels=max(50, samples_per_class // 2),
            seed=seed + 999,
            dropNulls=True,
            geometries=True,
        )
        .map(lambda f: f.set("landcover", 5))
    )
    return samples.merge(fallback_samples)


# ═════════════════════════════════════════════════════════════════════════════
# 3. K-MEANS CLASSIFICATION
# ═════════════════════════════════════════════════════════════════════════════

def classify_kmeans(
    composite: ee.Image,
    roi: ee.Geometry,
    satellite: str,
    num_clusters: int = 7,
) -> ee.Image:
    """
    K-Means unsupervised classification dengan post-processing heuristik spektral.
    """
    is_landsat = satellite in ["L8", "L9"]

    # Select bands
    if is_landsat:
        bands = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
    else:
        bands = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B11", "B12"]

    input_img = composite.select(bands)

    # Sampling untuk training clusterer
    sample = input_img.sample(
        region=roi, scale=10, numPixels=8000, seed=1, geometries=False
    )

    # Validasi minimal training data
    sample_count = sample.size().getInfo()
    if not sample_count:
        st.error("❌ Tidak ada pixel valid untuk training K-Means di AOI ini. Perbesar AOI atau perluas rentang tanggal.")
        return ee.Image.constant(0).rename("LULC").clip(roi).toUint8()

    # K-Means clustering
    clusterer = ee.Clusterer.wekaKMeans(num_clusters).train(sample)
    clusters = input_img.cluster(clusterer).rename("cluster")

    # unmask isi pixel kosong dengan 0 supaya basemap + download tampil penuh
    return (
        clusters.rename("LULC")
        .clip(roi)
        .round()
        .toUint8()
        .unmask(0)
    )


# ═════════════════════════════════════════════════════════════════════════════
# 4. SUPERVISED CLASSIFICATION (KNN, RF, Ensemble)
# ═════════════════════════════════════════════════════════════════════════════

def classify_supervised(
    feature_image: ee.Image,
    roi: ee.Geometry,
    satellite: str,
    method: str = "knn",
    k: int = 5,
    num_trees: int = 100,
    samples_per_class: int = 150,
    bag_fraction: float = 0.5,
) -> tuple:
    """
    Klasifikasi supervised dengan KNN, Random Forest, atau Ensemble.
    Returns: (classified_image, accuracy_dict, feature_bands)
    """
    # Generate training data otomatis
    training_fc = create_auto_training_samples(feature_image, roi, samples_per_class)

    # Force a small server-side validation before training so Earth Engine
    # reports a useful error while the classifier is still recoverable.
    training_count = training_fc.size().getInfo()
    if not training_count:
        raise ee.EEException(
            "Tidak ada pixel valid untuk training pada AOI/periode ini. "
            "Perbesar AOI, perluas tanggal, atau naikkan batas awan."
        )

    # Get feature bands
    feature_bands = feature_image.bandNames()

    # Split 80:20
    training_with_rand = training_fc.randomColumn("random", 42)
    train_set = training_with_rand.filter(ee.Filter.lt("random", 0.8))
    test_set = training_with_rand.filter(ee.Filter.gte("random", 0.8))

    if method == "knn":
        classifier = ee.Classifier.smileKNN(k).train(
            features=train_set, classProperty="landcover", inputProperties=feature_bands
        )
        result_name = f"LULC_KNN_k{k}"

    elif method == "randomforest":
        classifier = ee.Classifier.smileRandomForest(
            numberOfTrees=num_trees, bagFraction=bag_fraction, seed=42
        ).train(features=train_set, classProperty="landcover", inputProperties=feature_bands)
        result_name = f"LULC_RF_{num_trees}trees"

    elif method == "ensemble":
        # Train kedua classifier
        clf_knn = ee.Classifier.smileKNN(k).train(
            features=train_set, classProperty="landcover", inputProperties=feature_bands
        )
        clf_rf = ee.Classifier.smileRandomForest(
            numberOfTrees=num_trees, bagFraction=bag_fraction, seed=42
        ).train(features=train_set, classProperty="landcover", inputProperties=feature_bands)

        # Klasifikasi dengan kedua model
        result_knn = feature_image.classify(clf_knn)
        result_rf = feature_image.classify(clf_rf)

        # Majority vote: jika sama pakai hasil, jika beda pakai RF
        classified = result_rf.where(result_knn.eq(result_rf), result_knn)
        classified = classified.clip(roi).rename("LULC").byte()

        # Evaluasi
        test_knn = test_set.classify(clf_knn)
        test_rf = test_set.classify(clf_rf)

        cm_knn = test_knn.errorMatrix("landcover", "classification")
        cm_rf = test_rf.errorMatrix("landcover", "classification")

        oa_knn = cm_knn.accuracy()
        oa_rf = cm_rf.accuracy()
        kappa_knn = cm_knn.kappa()
        kappa_rf = cm_rf.kappa()

        accuracy_dict = {
            "method": "ensemble",
            "oa_knn": oa_knn,
            "oa_rf": oa_rf,
            "kappa_knn": kappa_knn,
            "kappa_rf": kappa_rf,
            "k": k,
            "num_trees": num_trees,
        }

        return classified, accuracy_dict, feature_bands

    # Klasifikasi
    classified = feature_image.classify(classifier).clip(roi).rename("LULC").byte()

    # Evaluasi akurasi
    test_classified = test_set.classify(classifier)
    cm = test_classified.errorMatrix("landcover", "classification")

    oa = cm.accuracy()
    kappa = cm.kappa()

    accuracy_dict = {
        "method": method,
        "oa": oa,
        "kappa": kappa,
        "k": k if method == "knn" else None,
        "num_trees": num_trees if method in ["randomforest", "ensemble"] else None,
    }

    return classified, accuracy_dict, feature_bands


# ═════════════════════════════════════════════════════════════════════════════
# 5. AREA CALCULATION
# ═════════════════════════════════════════════════════════════════════════════

def calculate_area_per_class(
    lulc_image: ee.Image, roi: ee.Geometry
) -> dict:
    """
    Hitung luas per kelas LULC dalam km².
    """
    pixel_area = ee.Image.pixelArea().divide(1e6)  # Convert to km²

    areas = {}
    for class_id in range(7):
        area = (
            lulc_image.eq(class_id)
            .multiply(pixel_area)
            .reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=roi,
                scale=30,
                maxPixels=1e9,
            )
            .get("LULC")
        )
        areas[class_id] = area

    return areas


# ═════════════════════════════════════════════════════════════════════════════
# 6. EXPORT FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def export_lulc_to_drive(
    lulc_image: ee.Image,
    roi: ee.Geometry,
    description: str = "LULC_classification",
    scale: int = 10,
    crs: str = "EPSG:4326",
) -> str:
    """
    Export LULC classification ke Google Drive.
    """
    task = ee.batch.Export.image.toDrive(
        image=lulc_image,
        description=description,
        folder="GEE_LULC_Export",
        fileNamePrefix=description,
        region=roi,
        scale=scale,
        crs=crs,
        maxPixels=1e13,
    )
    task.start()
    return task.id
