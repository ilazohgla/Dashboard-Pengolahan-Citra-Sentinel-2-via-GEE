# 🛰️ GEE Geospatial Dashboard (Sentinel-2)

> **Dashboard pengolahan citra Sentinel-2 berbasis Google Earth Engine (GEE).**
> Visualisasikan komposit median, hitung indeks spektral, bandingkan antar-periode, dan klasifikasikan tutupan lahan (LULC) — semuanya dari browser.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![GEE](https://img.shields.io/badge/Google%20Earth%20Engine-4285F4?logo=google&logoColor=white)](https://earthengine.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📑 Daftar Isi

- [Tentang Proyek](#-tentang-proyek)
- [Fitur Utama](#-fitur-utama)
- [Cara Menggunakan](#-cara-menggunakan)
- [Klasifikasi LULC](#-klasifikasi-lulc)
- [Download Citra](#-download-citra)
- [Instalasi Lokal](#-instalasi--menjalankan-secara-lokal)
- [Autentikasi Google Earth Engine](#-autentikasi-google-earth-engine)
- [Deploy ke Streamlit Cloud](#-deploy-ke-streamlit-cloud)
- [Struktur Proyek](#-struktur-proyek)
- [Kustomisasi](#-kustomisasi)
- [Dependensi](#-dependensi)
- [Keamanan](#-keamanan)
- [Lisensi](#-lisensi)

---

## 📌 Tentang Proyek

**GEE Geospatial Dashboard** adalah aplikasi web open-source untuk analisis citra **Sentinel-2 Surface Reflectance (SR)** menggunakan komputasi cloud **Google Earth Engine**. Aplikasi ini dirancang untuk membantu:

| Pengguna | Kegunaan |
|---------|----------|
| 🛰️ **Analis penginderaan jauh** | Memantau kondisi tutupan lahan & vegetasi |
| 🌾 **Praktisi perkebunan/pertanian** | Evaluasi kesehatan vegetasi (NDVI) & kelembaban (NDWI) |
| 🏙️ **Perencana wilayah** | Deteksi area terbangun (NDBI), klasifikasi LULC |
| 🎓 **Mahasiswa & akademisi** | Eksplorasi citra satelit tanpa infrastruktur sendiri |

Tanpa perlu mengunduh data atau memiliki mesin khusus — cukup browser dan koneksi internet.

---

## ✨ Fitur Utama

| Fitur | Keterangan |
|-------|-----------|
| 🗺️ **Peta Interaktif** | Basemap Google Satellite + OpenStreetMap, Layer Control, fullscreen, measure tool |
| ✏️ **Draw AOI** | Gambar polygon / rectangle langsung di peta, konfirmasi sekali klik |
| 📂 **Upload Shapefile** | Muat AOI dari `.shp` + `.shx` + `.dbf` (opsional, butuh geopandas) |
| ☁️ **Cloud Masking** | Filter awan otomatis (QA60) pada Sentinel-2 SR |
| 🌿 **Indeks Spektral** | NDVI · NDWI · NDBI dengan palet warna & legenda |
| ↔️ **Split-Panel Temporal** | Bandingkan dua periode dengan zoom/pan tersinkron |
| 🧠 **Klasifikasi LULC** | K-Means, KNN, Random Forest, Ensemble KNN+RF — 7 kelas tutupan lahan |
| ⬇️ **Download** | PNG preview · GeoTIFF RGB · GeoTIFF nilai mentah float (grid asli 10 m) |
| 🎨 **UI Modern** | Tema dark flat presisi — aksen cyan, Space Grotesk + JetBrains Mono |

---

## 🚀 Cara Menggunakan

### Alur kerja 5 langkah

1. **Tentukan AOI** — gambar polygon di peta, atau upload shapefile (sidebar kiri).
2. **Atur periode & filter awan** — rentang tanggal komposit + batas tutupan awan.
3. **Lihat hasil** — komposit median otomatis dimuat dengan layer True Color, False Color, NDVI, NDWI, NDBI.
4. **Bandingkan antar-periode** — buka tab **Split-Panel** untuk perbandingan temporal.
5. **Download / Klasifikasi** — unduh PNG/GeoTIFF, atau jalankan klasifikasi LULC di tab ketiga.

> ⚠️ Komposit & indeks dihitung ulang otomatis saat AOI, tanggal, atau filter awan berubah.

---

## 🧠 Klasifikasi LULC

Dashboard mendukung **klasifikasi tutupan lahan (Land Use Land Cover)** dengan **7 kelas** menggunakan 4 metode machine learning:

| Metode | Tipe | Waktu* | Cocok Untuk |
|--------|------|--------|-------------|
| **K-Means** | Unsupervised | ~1 menit | Eksplorasi cepat |
| **KNN** | Supervised | ~1.5 menit | Batas kelas yang jelas |
| **Random Forest** | Supervised | ~2 menit | Klasifikasi presisi |
| **KNN + RF Ensemble ⭐** | Supervised | ~3 menit | **Rekomendasi — akurasi tertinggi** |

*\*Estimasi, tergantung ukuran AOI.*

### 7 Kelas Tutupan Lahan

```
1 = 🏢 Built-up         2 = 🌾 Cropland        3 = 🌳 Forest
4 = 💧 Water            5 = 🪨 Bare Land      6 = 🌱 Shrub & Grassland
7 = 🏞️ Wetland
```

### Feature Engineering (13 Fitur)

Setiap piksel dianalisis dengan **6 band reflektansi** (B2–B7 Sentinel-2 / SR_B2–SR_B7 Landsat 8/9) + **7 indeks spektral**:

| Indeks | Nama Lengkap | Kegunaan |
|--------|--------------|----------|
| NDVI | Normalized Difference Vegetation Index | Kesehatan vegetasi |
| NDWI | Normalized Difference Water Index | Deteksi air |
| NDBI | Normalized Difference Built-up Index | Deteksi area terbangun |
| MNDWI | Modified NDWI | Deteksi air lebih akurat |
| EVI | Enhanced Vegetation Index | Vegetasi tahan atmosfer |
| SAVI | Soil-Adjusted Vegetation Index | Vegetasi pada tanah terbuka |
| BSI | Bare Soil Index | Deteksi lahan terbuka |

**Cara pakai LULC:**
1. Buka tab **🗺️ Klasifikasi LULC**.
2. Pilih metode — untuk akurasi tertinggi gunakan **Ensemble KNN+RF ⭐**.
3. Atur parameter (K, jumlah trees, training samples per kelas — default 150).
4. Klik **🚀 Jalankan Klasifikasi LULC** → tunggu 1–3 menit.
5. Lihat peta hasil + confusion matrix + OA/Kappa + luas per kelas (km²).
6. **Download GeoTIFF** (resolusi asli citra) atau **Export ke Google Drive** untuk AOI besar.

**Tips akurasi:**
- Training samples ≥ 150/kelas
- AOI ≥ 300 km² agar semua kelas terwakili
- Gunakan **Ensemble** untuk analisis presisi tinggi

---

## ⬇️ Download Citra

| Format | Keterangan | Kegunaan |
|--------|-----------|----------|
| **PNG (preview)** | Gambar 1024 px, cepat | Presentasi, laporan |
| **GeoTIFF – Visualisasi RGB** | `.tif` bergeoreferensi sesuai tampilan peta | QGIS/ArcGIS (visualisasi) |
| **GeoTIFF – Nilai Mentah (Float)** | `.tif` nilai piksel asli | Analisis kuantitatif |

- Resolusi default mengikuti **grid asli citra (10 m Sentinel-2)** agar hasil download identik dengan tampilan di peta.
- Untuk **GeoTIFF LULC**: nilai piksel `1–7` = kelas, `0` = NoData.
- > **Batas GEE:** `getDownloadURL` dibatasi ±32 MB / ±100 km². Untuk area lebih besar gunakan **Export ke Google Drive**.

### 🎨 Style Warna LULC

File style untuk menampilkan GeoTIFF LULC (1 band, nilai 1–7) dengan warna persis dashboard:

| File | Untuk | Cara pakai |
|------|-------|-----------|
| `lulc_7_kelas.qml` | **QGIS** (raster) | Layer Properties → Symbology → Style → Load Style → "QGIS Layer Style File" |
| `lulc_7_kelas.sld` | **GeoServer** / WMS server-side | Upload via GeoServer REST/UI sebagai style raster |

> ⚠️ **QGIS TIDAK mendukung load SLD untuk layer raster** (error *"Layer type 1 not supported"* — parser SLD QGIS hanya untuk layer vektor). Untuk raster di QGIS selalu pakai `.qml`. SLD diperuntukkan GeoServer (nilai 0 otomatis transparan di kedua format).

---

## 🛠️ Instalasi & Menjalankan Secara Lokal

### Prasyarat

- Python **3.10+**
- Akun **Google** dengan akses [Google Earth Engine](https://earthengine.google.com)
- **GEE Project ID** (buat di [Google Cloud Console](https://console.cloud.google.com/))

### Langkah

```bash
# 1. Clone repositori
git clone https://github.com/ilazohgla/Dashboard-Pengolahan-Citra-Sentinel-2-via-GEE.git
cd Dashboard-Pengolahan-Citra-Sentinel-2-via-GEE

# 2. Virtual environment (disarankan)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependensi
pip install -r requirements.txt

# 4. Konfigurasi GEE (lihat bagian Autentikasi)
cp .env.example .env             # isi GEE_PROJECT

# 5. Jalankan
streamlit run app.py
```

Browser otomatis terbuka di `http://localhost:8501`. 🎉

---

## 🔐 Autentikasi Google Earth Engine

### Lokal (user account)

```bash
earthengine authenticate
```

### Service Account (untuk Streamlit Cloud / CI)

Dashboard mendukung **3 format** (dibaca dari Streamlit Secrets atau `.env`):

**1. JSON lengkap:**
```toml
GEE_SERVICE_ACCOUNT = '{ "type": "service_account", "project_id": "...", "private_key": "...", "client_email": "..." }'
```

**2. Email + private key terpisah:**
```toml
GEE_SERVICE_ACCOUNT = "sa-name@project.iam.gserviceaccount.com"
GEE_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\n..."
GEE_PROJECT_ID = "my-gee-project"
```

**3. Token lokal** — `ee.Initialize(project=GEE_PROJECT)` langsung (fallback).

Panduan lengkap: [GEE Service Account](https://developers.google.com/earth-engine/guides/service_account)

---

## ☁️ Deploy ke Streamlit Cloud

1. Push repositori ke GitHub (pastikan `.env` **tidak** ikut ter-push).
2. Buka [share.streamlit.io](https://share.streamlit.io) → hubungkan GitHub → pilih repo → main file `app.py`.
3. Di **Advanced settings → Secrets**, tambahkan kredensial service account (format di atas).

---

## 📁 Struktur Proyek

```
gee-dashboard/
├── app.py                        # Entry point
├── config.py                     # Konfigurasi terpusat (vis params, GEE_PROJECT)
├── requirements.txt              # Dependensi
├── .env.example                  # Template environment variable
│
├── utils/
│   ├── gee_utils.py              # GEE auth, komposit Sentinel-2, cloud mask, indeks
│   ├── geo_utils.py              # GeoJSON / shapefile helpers
│   ├── map_utils.py              # Folium map builder + ROI layer + legend
│   ├── download_utils.py         # URL download PNG/GeoTIFF + fetch bytes
│   └── classification_utils.py   # K-Means / KNN / RF / Ensemble LULC
│
└── pages/
    ├── tab_main_map.py           # Tab 1: Peta Utama & Download
    ├── tab_split_panel.py        # Tab 2: Split-Panel Temporal
    └── tab_lulc_classification.py# Tab 3: Klasifikasi LULC
```

---

## 🔧 Kustomisasi

### Mengubah vis params / menambah layer

Edit `config.py`:

```python
LAYER_CONFIG["EVI"] = {
    "vis": {"min": 0, "max": 1, "palette": ["white", "green"]},
    "band": "EVI",
    "icon": "🌱",
}
```

Lalu tambahkan kalkulasi band di `add_indices()` pada `utils/gee_utils.py`.

### Tema UI

- Tokens warna & font: CSS custom properties `:root` di `app.py` (palet flat, aksen `#22d3ee`).
- Konfigurasi tema: `.streamlit/config.toml`.

---

## 📦 Dependensi

| Paket | Versi Min | Keterangan |
|-------|-----------|------------|
| streamlit | 1.35.0 | Framework dashboard |
| earthengine-api | 0.1.400 | Klien Python GEE |
| folium | 0.17.0 | Peta interaktif (Leaflet) |
| streamlit-folium | 0.20.0 | Integrasi Folium ke Streamlit |
| python-dotenv | 1.0.0 | Baca `.env` |
| pandas / numpy | 2.0.0 / 1.24.0 | Dataframe & numerik (LULC) |
| scikit-learn | 1.3.0 | Metrik evaluasi (confusion matrix) |
| plotly | 5.0.0 | Chart luas per kelas |
| geopandas *(opsional)* | 0.14.0 | Upload shapefile |
| shapely *(opsional)* | 2.0.0 | Operasi geometri |

---

## 🛡️ Keamanan

- `.env` & `*.env` sudah di-`.gitignore` — **jangan pernah commit** kredensial GEE.
- Untuk cloud, gunakan **Streamlit Secrets** / environment variables, bukan hardcode.
- Service account key JSON jangan ditaruh di repositori (`service_account*.json` di-ignore).

---

## 🤝 Kontribusi

Pull request dan issue sangat disambut! Silakan fork repositori ini, buat branch baru, lalu ajukan PR.

---

## 📄 Lisensi

Proyek ini menggunakan lisensi **MIT**. Lihat file `LICENSE` untuk detail.

---

## 🙏 Acknowledgements

- [Google Earth Engine](https://earthengine.google.com/) — komputasi geospasial cloud
- [Streamlit](https://streamlit.io/) — framework web Python
- [Folium](https://python-visualization.github.io/folium/) — peta Leaflet di Python
- [Copernicus / ESA](https://www.esa.int/) — data Sentinel-2
