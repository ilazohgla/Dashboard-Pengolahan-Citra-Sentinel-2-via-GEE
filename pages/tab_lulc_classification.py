"""
pages/tab_lulc_classification.py
────────────────────────────────
Tab 3: LULC (Land Use Land Cover) Classification dengan berbagai metode.
Dipanggil dari app.py.
"""

import streamlit as st
import ee
import json
import pandas as pd
import plotly.graph_objects as go
import folium
import requests
from datetime import datetime
from streamlit_folium import st_folium
from utils.classification_utils import (
    LULC_CLASSES,
    LULC_PALETTE,
    build_feature_image,
    classify_kmeans,
    classify_supervised,
    calculate_area_per_class,
    export_lulc_to_drive,
)
from utils.map_utils import add_ee_layer, base_map, add_roi_layer, add_legend
from utils.geo_utils import get_centroid, utm_epsg_from_latlon
from utils.download_utils import get_download_url, get_geotiff_raw_url, fetch_geotiff_bytes


def render_tab_lulc(composite, roi, roi_json, satellite, center_lat, center_lon):
    """Render Tab 3: LULC Classification"""

    st.subheader("🗺️ Klasifikasi LULC (Land Use Land Cover)")

    st.info(
        "📊 **7 Kelas LULC:** Built-up, Cropland, Forest, Water, Bare Land, Shrub/Grassland, Wetland\n"
        "🔧 **Metode:** K-Means (Unsupervised), KNN, Random Forest, atau Ensemble KNN+RF (Supervised)",
        icon="ℹ️",
    )

    # ── Resolusi asli citra ──────────────────────────────────────────────
    # CATATAN PENTING: nominalScale() pada composite hasil median()+clip()
    # KADANG melaporkan grid EPSG:4326 (geografis) alih-alih proyeksi UTM
    # native — nilainya ~111319 m (= 1 derajat) untuk Sentinel-2 yang
    # seharusnya 10 m. Terima hanya nilai wajar 2–120 m; di luar itu fallback
    # ke resolusi native satelit yang diketahui (S2 = 10 m, Landsat = 30 m).
    try:
        raw_scale = float(composite.select("B2").projection().nominalScale().getInfo())
    except Exception:
        raw_scale = 0.0

    native_by_sat = {"S2": 10, "L8": 30, "L9": 30}
    classification_scale = native_by_sat.get(satellite, 10)
    if 2 <= raw_scale <= 120:
        classification_scale = int(round(raw_scale))

    st.info(f"📐 **Resolusi Asli Citra Terdeteksi:** {classification_scale} m/piksel (Menggunakan ukuran asli GEE tanpa modifikasi/resampling).")
    col1, col2, col3 = st.columns(3)

    with col1:
        method = st.selectbox(
            "Metode Klasifikasi",
            options=[
                "K-Means (Unsupervised)",
                "KNN Supervised",
                "Random Forest Supervised",
                "KNN + RF Ensemble ⭐",
            ],
            key="lulc_method",
        )

    with col2:
        if method == "KNN Supervised":
            k_value = st.slider("Nilai K", min_value=1, max_value=15, value=5, key="k_param")
        else:
            k_value = 5

    with col3:
        if "Random Forest" in method or "Ensemble" in method:
            num_trees = st.slider(
                "Jumlah Trees", min_value=10, max_value=500, value=100, step=10, key="num_trees"
            )
        else:
            num_trees = 100

    # ── Konfigurasi Supervised Learning ───────────────────────────────────
    if method != "K-Means (Unsupervised)":
        st.markdown("#### ⚙️ Konfigurasi Supervised Learning")

        col_sample, col_bag = st.columns(2)
        with col_sample:
            samples_per_class = st.slider(
                "Training Samples per Kelas",
                min_value=50,
                max_value=500,
                value=150,
                step=50,
                key="samples_per_class",
            )

        with col_bag:
            if "Random Forest" in method or "Ensemble" in method:
                bag_fraction = st.slider(
                    "Bag Fraction (RF)",
                    min_value=0.3,
                    max_value=0.9,
                    value=0.5,
                    step=0.1,
                    key="bag_fraction",
                )
            else:
                bag_fraction = 0.5

        show_accuracy = st.checkbox("📈 Tampilkan Confusion Matrix & Akurasi", value=True)
        show_variable_importance = st.checkbox(
            "📊 Tampilkan Variable Importance (RF)", value=False
        )

    else:
        samples_per_class = 150
        bag_fraction = 0.5
        show_accuracy = False
        show_variable_importance = False

    st.markdown("---")

    # ── Tombol Klasifikasi ────────────────────────────────────────────────
    run_classification = st.button(
        "🚀 Jalankan Klasifikasi LULC", type="primary", width="stretch"
    )

    # ════════════════════════════════════════════════════════════════════════
    # PROSES KLASIFIKASI
    # ════════════════════════════════════════════════════════════════════════

    if run_classification:
        with st.spinner("⏳ Memproses klasifikasi LULC...\n\n(Proses ini bisa memakan waktu 1-5 menit tergantung metode)"):

                # Cek composite tersedia
                if composite is None:
                    st.error("⚠️ Tampilkan RGB terlebih dahulu di tab sebelumnya.")
                    st.stop()

                try:
                    # ── K-Means ───────────────────────────────────────────
                    if method == "K-Means (Unsupervised)":
                        st.info("📊 K-Means: Klasifikasi unsupervised dengan 7 klaster...")
                        lulc_result = classify_kmeans(composite, roi, satellite, num_clusters=7)
                        accuracy = None

                        # Quick validation: pastikan hasil bukan image kosong
                        try:
                            test_vis = lulc_result.getMapId({"min": 0, "max": 6, "palette": LULC_PALETTE})
                            del test_vis
                        except Exception as viz_err:
                            st.error(f"❌ K-Means menghasilkan image yang tidak valid untuk rendering: {viz_err}")
                            st.stop()

                        st.success("✅ K-Means klasifikasi selesai.")

                    # ── Supervised Methods ────────────────────────────────
                    else:
                        # Build feature image
                        st.info("🔨 Membangun feature image multivariabel...")
                        feature_img = build_feature_image(composite, satellite, roi)

                        # Classify
                        if method == "KNN Supervised":
                            st.info(f"🔍 Training KNN (k={k_value}) dengan {samples_per_class} samples/kelas...")
                            lulc_result, accuracy, _ = classify_supervised(
                                feature_img,
                                roi,
                                satellite,
                                method="knn",
                                k=k_value,
                                samples_per_class=samples_per_class,
                            )

                        elif method == "Random Forest Supervised":
                            st.info(
                                f"🌲 Training Random Forest ({num_trees} trees) dengan {samples_per_class} samples/kelas..."
                            )
                            lulc_result, accuracy, _ = classify_supervised(
                                feature_img,
                                roi,
                                satellite,
                                method="randomforest",
                                num_trees=num_trees,
                                samples_per_class=samples_per_class,
                                bag_fraction=bag_fraction,
                            )

                        elif method == "KNN + RF Ensemble ⭐":
                            st.info(
                                f"⭐ Training Ensemble (KNN k={k_value} + RF {num_trees} trees) dengan {samples_per_class} samples/kelas..."
                            )
                            lulc_result, accuracy, _ = classify_supervised(
                                feature_img,
                                roi,
                                satellite,
                                method="ensemble",
                                k=k_value,
                                num_trees=num_trees,
                                samples_per_class=samples_per_class,
                                bag_fraction=bag_fraction,
                            )

                        st.success(f"✅ {method} klasifikasi selesai.")

                    # Quality guard: supervised classifier yang hanya menghasilkan
                    # satu kelas tidak layak dijadikan peta LULC. Coba fallback
                    # K-Means agar hasil tetap memiliki pemisahan spektral.
                    try:
                        result_hist = lulc_result.reduceRegion(
                            reducer=ee.Reducer.frequencyHistogram(),
                            geometry=roi,
                            scale=classification_scale,
                            maxPixels=1e9,
                            bestEffort=True,
                        ).getInfo() or {}
                        result_values = result_hist.get("LULC", result_hist)
                        unique_classes = result_values if isinstance(result_values, dict) else {}
                    except Exception:
                        unique_classes = {}

                    if method != "K-Means (Unsupervised)" and len(unique_classes) <= 1:
                        st.warning(
                            "⚠️ Model supervised menghasilkan satu kelas saja. "
                            "Menjalankan K-Means fallback agar variasi spektral tetap terlihat."
                        )
                        lulc_result = classify_kmeans(composite, roi, satellite, num_clusters=7)
                        method = "K-Means (Fallback dari supervised)"
                        accuracy = None

                    # ── Hitung area per kelas ──────────────────────────────
                    with st.spinner("📊 Menghitung luas per kelas..."):
                        areas = calculate_area_per_class(lulc_result, roi)

                    # Store result untuk display
                    st.session_state["lulc_result"] = lulc_result
                    # Simpan AOI dan parameter yang benar-benar dipakai saat
                    # klasifikasi. Hasil tidak boleh berpindah jika AOI global
                    # berubah setelah proses selesai.
                    st.session_state["lulc_roi"] = roi
                    st.session_state["lulc_roi_json"] = roi_json
                    st.session_state["lulc_classification_scale"] = classification_scale
                    st.session_state["classification_result_method"] = method
                    st.session_state["lulc_accuracy"] = accuracy
                    st.session_state["lulc_areas"] = areas
                    st.session_state["show_accuracy"] = show_accuracy
                    st.session_state.pop("lulc_geotiff_data", None)
                    st.session_state.pop("lulc_geotiff_filename", None)

                except Exception as e:
                    st.error(f"❌ Error saat klasifikasi: {str(e)}")
                    st.write(e)
                    st.stop()

    # ════════════════════════════════════════════════════════════════════════
    # TAMPILKAN HASIL DARI SESSION STATE
    # ════════════════════════════════════════════════════════════════════════

    if "lulc_result" in st.session_state:
        lulc_result = st.session_state["lulc_result"]
        # Semua visualisasi dan export memakai AOI snapshot saat klasifikasi,
        # bukan AOI global yang mungkin sudah berubah.
        result_roi = st.session_state.get("lulc_roi", roi)
        result_roi_json = st.session_state.get("lulc_roi_json", roi_json)
        classification_scale = st.session_state.get("lulc_classification_scale", classification_scale)
        method = st.session_state["classification_result_method"]
        accuracy = st.session_state["lulc_accuracy"]
        areas = st.session_state["lulc_areas"]

        # Tampilkan peta
        st.subheader("🗺️ Hasil Klasifikasi LULC")
        result_center_lat, result_center_lon = get_centroid(result_roi_json)
        Map = base_map(result_center_lat, result_center_lon, zoom=12)
        try:
            # vis eksplisit: band "LULC" + palette 7 kelas, NoData transparan
            # (hasil klasifikasi kini tidak di-unmask(0), jadi area kosong tidak
            # menimpa basemap dengan warna kelas 0).
            add_ee_layer(
                Map,
                lulc_result,
                {"bands": ["LULC"], "min": 0, "max": 6, "palette": LULC_PALETTE},
                f"LULC - {method}",
                show=True,
            )
            add_roi_layer(Map, result_roi, "Batas AOI", "yellow")
            folium.LayerControl().add_to(Map)
            st_folium(Map, height=640, width="stretch", key="lulc_map_result")
        except Exception as map_error:
            st.error(
                "❌ Hasil klasifikasi tidak dapat dirender oleh Earth Engine. "
                "Jalankan klasifikasi ulang setelah memastikan AOI dan periode valid."
            )
            st.caption(f"Detail: {map_error}")
            # Jangan return — tabel luas dan download tetap harus tampil.
        
        # Tampilkan legenda di bawah peta
        st.subheader("🎨 Legenda LULC (7 Kelas)")
        legend_cols = st.columns(4)
        for idx in range(7):
            with legend_cols[idx % 4]:
                st.markdown(f"<span style='background-color: {LULC_PALETTE[idx]}; width: 20px; height: 20px; display: inline-block; border-radius: 3px; border: 1px solid #333; margin-right: 8px;'></span> {LULC_CLASSES[idx].split(' (')[0]}", unsafe_allow_html=True)

        # Tampilkan akurasi jika ada
        if accuracy and st.session_state.get("show_accuracy", False):
            st.subheader("📈 Akurasi Klasifikasi")

            if accuracy["method"] == "ensemble":
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "OA - KNN",
                        f"{float(accuracy['oa_knn'].getInfo()) * 100:.2f}%",
                    )
                with col2:
                    st.metric(
                        "Kappa - KNN",
                        f"{float(accuracy['kappa_knn'].getInfo()):.4f}",
                    )
                with col3:
                    st.metric(
                        "OA - RF",
                        f"{float(accuracy['oa_rf'].getInfo()) * 100:.2f}%",
                    )
                with col4:
                    st.metric(
                        "Kappa - RF",
                        f"{float(accuracy['kappa_rf'].getInfo()):.4f}",
                    )
                st.info("🏆 Ensemble menggunakan majority vote KNN & RF.")

            else:
                oa = float(accuracy["oa"].getInfo()) * 100
                kappa = float(accuracy["kappa"].getInfo())

                col_oa, col_kappa = st.columns(2)
                with col_oa:
                    st.metric("Overall Accuracy", f"{oa:.2f}%")
                with col_kappa:
                    st.metric("Kappa Coefficient", f"{kappa:.4f}")

                st.success(
                    f"✅ Akurasi {'baik' if oa > 75 else 'sedang' if oa > 60 else 'rendah'}."
                )

        # ── Tampilkan area per kelas ──────────────────────────────────
        st.subheader("📐 Luas Penggunaan Lahan per Kelas")

        # Buat dataframe
        area_data = []
        area_values_for_chart = []
        for class_id in range(7):
            area_val = areas[class_id]
            try:
                raw = area_val.getInfo() if area_val else 0
                area_float = float(raw or 0)
            except Exception:
                area_float = 0.0
            if area_val is None or area_float <= 0:
                continue
            area_data.append(
                {
                    "Kelas": LULC_CLASSES[class_id],
                    "Luas (km²)": f"{area_float:.3f}",
                }
            )
            area_values_for_chart.append({"class_id": class_id, "luas": area_float})

        # Tabs untuk tampilan berbeda
        tab_table, tab_bar, tab_pie = st.tabs(["📋 Tabel", "📊 Diagram Batang", "🥧 Diagram Lingkaran"])
        
        with tab_table:
            df_area = pd.DataFrame(area_data)
            st.dataframe(df_area, width="stretch")
        
        # Bar chart dengan warna LULC
        with tab_bar:
            if area_values_for_chart:
                df_chart = pd.DataFrame(
                    [
                        {
                            "Kelas": LULC_CLASSES[item["class_id"]].split(" (")[0],
                            "Luas": item["luas"],
                        }
                        for item in area_values_for_chart
                    ]
                )
                
                fig_bar = go.Figure()
                for idx, row in df_chart.iterrows():
                    fig_bar.add_trace(go.Bar(
                        x=[row["Kelas"]],
                        y=[row["Luas"]],
                        marker_color=LULC_PALETTE[area_values_for_chart[idx]["class_id"]],
                        showlegend=False,
                        hovertemplate="%{x}<br>Luas: %{y:.2f} km²<extra></extra>"
                    ))
                fig_bar.update_layout(
                    xaxis_title="Kelas LULC",
                    yaxis_title="Luas (km²)",
                    height=500,
                    showlegend=False,
                    hovermode="x unified"
                )
                st.plotly_chart(fig_bar, width="stretch")
        
        # Pie chart dengan warna LULC
        with tab_pie:
            if area_values_for_chart:
                df_pie = pd.DataFrame(area_values_for_chart)
                colors = [LULC_PALETTE[cid] for cid in df_pie["class_id"]]
                labels = [LULC_CLASSES[cid].split(" (")[0] for cid in df_pie["class_id"]]
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=df_pie["luas"],
                    marker=dict(colors=colors),
                    hovertemplate="%{label}<br>Luas: %{value:.2f} km²<br>Persen: %{percent}<extra></extra>"
                )])
                fig_pie.update_layout(height=500)
                st.plotly_chart(fig_pie, width="stretch")

    # ── Download & Export GeoTIFF ─────────────────────────────────────────────
    if "lulc_result" in st.session_state:
        result_roi = st.session_state.get("lulc_roi", roi)
        result_roi_json = st.session_state.get("lulc_roi_json", roi_json)
        result_center_lat, result_center_lon = get_centroid(result_roi_json)
        st.markdown("---")
        st.subheader("💾 Ekspor & Unduh GeoTIFF LULC")
        st.info("Pilih metode ekspor di bawah ini. File hasil unduhan adalah data raster mentah (*integer/float*) dengan nilai piksel 0-6 sesuai kelas LULC.")
        
        col_dl, col_drv = st.columns(2)
        
        with col_dl:
            download_geotiff = st.button("⬇️ Download Langsung ke PC", width="stretch", key="btn_dl_geotiff")
        with col_drv:
            export_drive = st.button("📤 Export ke Google Drive (Tanpa Batas Ukuran)", width="stretch", key="btn_drv_geotiff")

        # 1. Proses Download Langsung
        if download_geotiff:
            with st.spinner("⏳ Menyiapkan file GeoTIFF mentah..."):
                lulc_result = st.session_state["lulc_result"]
                try:
                    # Pastikan hasil klasifikasi benar-benar memiliki piksel valid
                    # pada snapshot AOI sebelum membentuk file export.
                    valid_pixel_count = lulc_result.reduceRegion(
                        reducer=ee.Reducer.count(),
                        geometry=result_roi,
                        scale=30,
                        maxPixels=1e9,
                        bestEffort=True,
                    ).getInfo()
                    if not valid_pixel_count:
                        st.error("❌ Hasil klasifikasi tidak memiliki piksel valid pada AOI ini. Jalankan klasifikasi ulang.")
                        st.stop()
                    valid_pixels = int(sum(valid_pixel_count.values()))
                    roi_area_m2 = float(result_roi.area(maxError=1).getInfo() or 0)
                    estimated_pixels_native = max(1, int(roi_area_m2 / (classification_scale * classification_scale)))
                    st.caption(
                        f"Piksel valid LULC: {valid_pixels:,} · "
                        f"Luas AOI: {roi_area_m2 / 1e6:.4f} km² · "
                        f"Estimasi piksel {classification_scale} m: {estimated_pixels_native:,}"
                    )
                    if valid_pixels < 4:
                        st.error(
                            "❌ AOI terlalu kecil untuk menghasilkan raster yang bermakna "
                            f"({valid_pixels} piksel valid). Perbesar AOI minimal sekitar 300×300 m "
                            "atau gunakan Export ke Google Drive."
                        )
                        st.stop()

                    # Verifikasi kelas yang benar-benar ada pada hasil klasifikasi.
                    class_histogram = lulc_result.reduceRegion(
                        reducer=ee.Reducer.frequencyHistogram(),
                        geometry=result_roi,
                        scale=classification_scale,
                        maxPixels=1e9,
                        bestEffort=True,
                    ).getInfo() or {}
                    st.caption(f"Distribusi kelas: {class_histogram}")
                    class_values = class_histogram.get("LULC", class_histogram)
                    if isinstance(class_values, dict) and len(class_values) == 1:
                        only_class = next(iter(class_values))
                        st.warning(
                            f"⚠️ Seluruh piksel AOI masuk satu kelas (kelas {only_class}). "
                            "GeoTIFF kategorikal seperti ini memang dapat berukuran sangat kecil karena nilainya konstan. "
                            "Perbesar/geser AOI atau gunakan periode lain untuk variasi kelas."
                        )

                    # Satu band integer: 0-6 = kelas LULC, 255 = NoData.
                    # Clip eksplisit ke snapshot AOI agar raster tidak kembali ke
                    # footprint komposit/default projection.
                    if composite is None:
                        st.error("❌ Composite Sentinel-2 tidak tersedia untuk menentukan grid export.")
                        st.stop()
                    # Pakai grid resolusi asli citra (10 m utk Sentinel-2) dan
                    # proyeksi native composite supaya hasil identik dgn basemap.
                    # Sebelumnya hardcoded 30 m + EPSG:4326 → file kecil & grid
                    # bergeser, tidak cocok dengan tampilan di peta.
                    native_proj = composite.select("B2").projection()
                    export_scale = classification_scale  # mis. 10 utk S2
                    lulc_export = (
                        lulc_result.clip(result_roi)
                        .select([0])
                        .rename("LULC_class")
                        .toUint8()
                        .setDefaultProjection(native_proj)
                        .unmask(255)
                    )
                    geotiff_data = None
                    download_error = ""
                    # ── Estimasi piksel pada resolusi asli ────────────────
                    # getDownloadURL GEE dibatasi ~32 MB / ~1e8 piksel.
                    # Pada 10 m, limit itu ≈ 100 km². Jika AOI melewatinya,
                    # 10 m TIDAK mungkin via download langsung — langsung
                    # arahkan ke Export Drive (scale 10 m, tanpa batas),
                    # jangan diam-diam turun ke 30 m yang grid-nya beda.
                    roi_area_m2 = float(result_roi.area(maxError=1).getInfo() or 0)
                    est_px_10m = roi_area_m2 / (export_scale * export_scale)
                    DOWNLOAD_PX_LIMIT = 1e8  # batas aman getDownloadURL
                    if est_px_10m > DOWNLOAD_PX_LIMIT:
                        st.warning(
                            f"⚠️ AOI terlalu luas untuk download langsung pada {export_scale} m "
                            f"(estimasi {est_px_10m / 1e6:.1f} juta piksel > batas GEE ±100 juta). "
                            "Gunakan **Export ke Google Drive** — tetap resolusi asli, tanpa batas ukuran."
                        )
                        download_error = "AOI melebihi batas getDownloadURL pada resolusi asli."
                    else:
                        # Coba resolusi asli; fallback 30 m hanya jika GEE menolak.
                        for scale in (export_scale, 30):
                            download_url = get_geotiff_raw_url(
                                lulc_export, band_name=None, roi_geom=result_roi,
                                scale=scale, crs=None, format_name="GEO_TIFF"
                            )
                            if not download_url:
                                continue
                            geotiff_data, download_error = fetch_geotiff_bytes(download_url)
                            if geotiff_data:
                                st.success(
                                    f"✅ GeoTIFF valid siap diunduh pada resolusi {scale} m "
                                    f"({len(geotiff_data) / 1024:.1f} KB)."
                                )
                                break
                            if scale == export_scale:
                                st.warning("⚠️ Download resolusi asli gagal atau terlalu besar; mencoba fallback 30 m...")

                    if geotiff_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.session_state["lulc_geotiff_data"] = geotiff_data
                        st.session_state["lulc_geotiff_filename"] = f"LULC_classification_{timestamp}.tif"
                    else:
                        st.error(download_error or "Earth Engine tidak menghasilkan GeoTIFF yang valid.")
                        st.error("❌ Download langsung gagal. Gunakan Export ke Google Drive untuk AOI besar.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        # Payload disimpan di session state agar tidak hilang saat download
        # memicu rerun Streamlit.
        if st.session_state.get("lulc_geotiff_data"):
            st.download_button(
                label="📥 Simpan GeoTIFF ke PC",
                data=st.session_state["lulc_geotiff_data"],
                file_name=st.session_state.get("lulc_geotiff_filename", "LULC_classification.tif"),
                mime="image/tiff",
                width="stretch",
                key="download_lulc_geotiff",
            )

        # 2. Proses Export ke Google Drive
        if export_drive:
            with st.spinner("📤 Mengirim tugas ekspor ke Google Earth Engine..."):
                lulc_result = st.session_state["lulc_result"]
                try:
                    # Pastikan proyeksi diset menggunakan grid composite.
                    try:
                        if composite is None:
                            raise ValueError("Composite Sentinel-2 tidak tersedia")
                        # Samakan grid Drive export dengan composite klasifikasi.
                        native_proj = composite.select("B2").projection()
                        lulc_result = lulc_result.setDefaultProjection(native_proj)
                    except Exception:
                        pass
                        
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    task_id = export_lulc_to_drive(
                        lulc_result,
                        result_roi,
                        description=f"LULC_classification_10m_{timestamp}",
                        scale=10,
                        crs=utm_epsg_from_latlon(result_center_lat, result_center_lon),
                    )
                    st.success(f"🚀 Tugas Ekspor berhasil dikirim ke GEE!")
                    st.info(
                        f"📂 **Nama File:** `LULC_classification_10m_{timestamp}.tif`\n"
                        f"📍 **Folder Google Drive:** `GEE_LULC_Export`\n"
                        f"🆔 **ID Tugas:** `{task_id}`\n\n"
                        "Proses ini berjalan di latar belakang server Google. Silakan cek Google Drive Anda dalam beberapa menit!"
                    )
                except Exception as e:
                    st.error(f"❌ Gagal mengirim tugas ekspor: {str(e)}")


