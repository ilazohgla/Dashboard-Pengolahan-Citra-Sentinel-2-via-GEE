# 🌍 GEE Geospatial Dashboard

Dashboard interaktif berbasis **Streamlit** untuk memvisualisasikan dan mengunduh citra **Sentinel-2** menggunakan **Google Earth Engine (GEE)**. Mendukung pembuatan Area of Interest (AOI) langsung di peta, upload Shapefile, perbandingan temporal, serta download dalam format **PNG** maupun **GeoTIFF**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?logo=streamlit)
![GEE](https://img.shields.io/badge/Google%20Earth%20Engine-API-green?logo=google)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Fitur Utama

| Fitur | Keterangan |
|---|---|
| 🗺️ Peta interaktif | Basemap Satellite + OpenStreetMap, Layer Control |
| ✏️ Draw AOI | Gambar polygon / rectangle langsung di peta |
| 📂 Upload Shapefile | Muat AOI dari file `.shp` (butuh geopandas) |
| ☁️ Cloud masking | Filter awan otomatis pada Sentinel-2 SR |
| 🌿 Indeks spektral | NDVI · NDWI · NDBI dengan palet warna |
| ↔️ Split-panel | Perbandingan dua periode dengan zoom tersinkron |
| ⬇️ Download | PNG preview · GeoTIFF RGB · GeoTIFF nilai mentah float |

---

## 📁 Struktur Proyek

```
gee-dashboard/
├── app.py                   # Entry point – jalankan file ini
├── config.py                # Konfigurasi terpusat (baca dari .env)
├── requirements.txt         # Dependensi Python
├── .env.example             # Template environment variable
├── .gitignore               # Melindungi .env & file sensitif
│
├── utils/
│   ├── gee_utils.py         # GEE auth, komposit Sentinel-2, indeks
│   ├── geo_utils.py         # GeoJSON / Shapefile helpers
│   ├── map_utils.py         # Folium map builder
│   └── download_utils.py   # URL download PNG / GeoTIFF
│
└── pages/
    ├── tab_main_map.py      # Tab 1: Peta Utama & Download
    └── tab_split_panel.py  # Tab 2: Split-Panel Temporal
```

---

## 🚀 Panduan Instalasi (dari Nol)

### Prasyarat

- Python **3.10** atau lebih baru
- Akun **Google** dengan akses [Google Earth Engine](https://earthengine.google.com)
- **GEE Project ID** (bisa dibuat di [Google Cloud Console](https://console.cloud.google.com/))

---

### Langkah 1 – Clone Repositori

```bash
git clone https://github.com/USERNAME/gee-dashboard.git
cd gee-dashboard
```

---

### Langkah 2 – Buat Virtual Environment

Disarankan menggunakan virtual environment agar dependensi tidak tercampur dengan proyek lain.

```bash
# Buat virtual environment
python -m venv .venv

# Aktifkan (Linux / macOS)
source .venv/bin/activate

# Aktifkan (Windows)
.venv\Scripts\activate
```

---

### Langkah 3 – Install Dependensi

```bash
pip install -r requirements.txt
```

> **Catatan:** Paket `geopandas` bersifat opsional. Hanya dibutuhkan jika ingin menggunakan fitur Upload Shapefile. Jika instalasi `geopandas` gagal, dashboard tetap berjalan tanpa fitur tersebut.

---

### Langkah 4 – Konfigurasi Google Earth Engine

#### 4a. Daftar & Aktifkan GEE

1. Buka [https://earthengine.google.com](https://earthengine.google.com) dan daftar dengan akun Google Anda.
2. Tunggu email persetujuan (biasanya beberapa jam hingga 1–2 hari).

#### 4b. Buat GEE Project di Google Cloud

1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Klik **"Select a project" → "New Project"**.
3. Beri nama proyek, lalu catat **Project ID**-nya (contoh: `my-gee-project-123`).
4. Di menu navigasi, cari dan aktifkan **"Earth Engine API"**.

#### 4c. Autentikasi Lokal

Jalankan perintah berikut di terminal (hanya perlu sekali):

```bash
earthengine authenticate
```

Browser akan terbuka. Login dengan akun Google yang sama, lalu salin kode autentikasi kembali ke terminal.

---

### Langkah 5 – Buat File `.env`

Salin template `.env.example` menjadi `.env`:

```bash
cp .env.example .env
```

Buka `.env` dengan editor teks, lalu isi `GEE_PROJECT` dengan Project ID milik Anda:

```env
GEE_PROJECT=my-gee-project-123

# Opsional: ubah koordinat default (saat ini Bandung, Indonesia)
DEFAULT_LAT=-6.9175
DEFAULT_LON=107.6191
DEFAULT_ZOOM=11
```

> ⚠️ **PENTING:** File `.env` sudah terdaftar di `.gitignore`. **Jangan pernah commit file ini** ke repositori publik karena berisi data sensitif proyek Anda.

---

### Langkah 6 – Jalankan Dashboard

```bash
streamlit run app.py
```

Browser akan otomatis terbuka di `http://localhost:8501`. 🎉

---

## 🗺️ Cara Penggunaan

### Tab 3: Klasifikasi LULC (Land Use Land Cover)

Dashboard sekarang mendukung **klasifikasi LULC dengan 7 kelas** menggunakan berbagai metode machine learning:

#### Metode Klasifikasi

| Metode | Tipe | Keunggulan | Kelemahan |
|---|---|---|---|
| **K-Means** | Unsupervised | Otomatis, cepat, tanpa training data | Akurasi sedang, hasil bisa bervariasi |
| **KNN** | Supervised | Akurasi baik untuk batas kelas jelas | Sensitif terhadap noise, lambat |
| **Random Forest** | Supervised | Akurasi tinggi, robust | Training data perlu tersedia |
| **KNN + RF Ensemble ⭐** | Supervised | **Akurasi tertinggi**, robust, optimal | Lebih lambat, butuh resources lebih besar |

#### 7 Kelas LULC

1. 🏢 **Built-up** (Area Terbangun) – Bangunan, infrastruktur
2. 🌾 **Cropland** (Lahan Pertanian) – Sawah, ladang, perkebunan
3. 🌳 **Forest** (Hutan) – Vegetasi lebat, hutan
4. 💧 **Water** (Perairan) – Sungai, danau, tambak
5. 🪨 **Bare Land** (Lahan Terbuka) – Tanah kosong, pasir
6. 🌱 **Shrub & Grassland** (Semak/Padang Rumput) – Vegetasi rendah
7. 🏞️ **Wetland** (Lahan Basah) – Rawa, wetland

#### Fitur Engineering

Setiap piksel dianalisis menggunakan:
- **6 Band Reflektansi** dasar (B2-B7 Sentinel-2 / SR_B2-SR_B7 Landsat)
- **7 Indeks Spektral**:
  - **NDVI** – Normalized Difference Vegetation Index
  - **NDWI** – Normalized Difference Water Index
  - **NDBI** – Normalized Difference Built-up Index
  - **MNDWI** – Modified Normalized Difference Water Index
  - **EVI** – Enhanced Vegetation Index
  - **SAVI** – Soil-Adjusted Vegetation Index
  - **BSI** – Bare Soil Index

#### Cara Penggunaan LULC

1. **Buka Tab 3** – "🗺️ Klasifikasi LULC"
2. **Pilih Metode Klasifikasi**:
   - Untuk eksplorasi awal → K-Means (cepat)
   - Untuk akurasi tinggi → Ensemble KNN+RF ⭐
3. **Atur Parameter** (untuk Supervised):
   - **K Value** (KNN): Jumlah tetangga terdekat (default 5)
   - **Jumlah Trees** (RF): Jumlah decision trees (default 100)
   - **Training Samples**: Sampel per kelas untuk training (default 150)
4. **Jalankan Klasifikasi** → tunggu 1-3 menit
5. **Lihat Hasil**:
   - Peta LULC dengan warna berbeda per kelas
   - Confusion Matrix & akurasi (jika Supervised)
   - Luas penggunaan lahan per kelas (km²)
6. **Export ke Drive** – Simpan hasil untuk analisis lanjutan

#### Tips Optimal

- **Sample Size ≥ 150/kelas** untuk akurasi baik
- **AOI ≥ 300 km²** untuk hasil yang representative
- **Gunakan Ensemble** jika perlu akurasi tertinggi
- **K-Means** cocok untuk eksplorasi cepat area luas

#### Output LULC

- 📊 **GeoTIFF** – Raster 30m resolution, 7 kelas, georeferenced
- 📈 **Confusion Matrix** – Akurasi per kelas (untuk Supervised)
- 📐 **Area Report** – Luas per kelas dalam km² (untuk perencanaan)

---



Dashboard menyediakan dua cara untuk menentukan AOI:

**Opsi A – Gambar Langsung di Peta**
1. Di sidebar, pilih **"✏️ Gambar Polygon"**.
2. Di Tab **🗺️ Peta Utama**, gunakan toolbar di sisi kiri peta untuk menggambar polygon atau rectangle.
3. Setelah selesai menggambar, klik tombol **"✅ Konfirmasi AOI"** yang muncul di bawah peta.
4. Dashboard akan memuat ulang dengan AOI yang baru.

**Opsi B – Upload Shapefile**
1. Di sidebar, pilih **"📂 Upload Shapefile"**.
2. Klik **"Browse files"** dan upload berkas `.shp`, `.shx`, dan `.dbf` secara bersamaan.
3. Jika CRS bukan EPSG:4326, akan dikonversi otomatis.

### Mengatur Parameter

Di sidebar, atur:
- **Rentang Waktu** – periode komposit median yang diinginkan.
- **Filter Awan** – persentase tutupan awan maksimum (5–50%).

### Download Citra

Di bagian **"⬇️ Download Citra per Layer"**, pilih format yang diinginkan:

| Format | Keterangan | Kegunaan |
|---|---|---|
| **PNG (preview)** | Gambar 1024px, cepat | Presentasi, laporan |
| **GeoTIFF – Visualisasi RGB** | File `.tif` bergeoreferensi, warna seperti tampilan peta | QGIS/ArcGIS, tapi hanya visualisasi |
| **GeoTIFF – Nilai Mentah (Float)** | File `.tif` dengan nilai piksel asli | Analisis kuantitatif, klasifikasi |

Pilih juga **Resolusi (m/px)** — semakin kecil nilainya, semakin detail hasilnya (namun file lebih besar).

> **Batas GEE:** `getDownloadURL` dibatasi sekitar **32 MB / ±100 km²**. Untuk area lebih besar, gunakan `Export.image.toDrive` di [GEE Code Editor](https://code.earthengine.google.com/).

### Perbandingan Temporal (Tab ↔️ Split-Panel)

1. Buka tab **"↔️ Split-Panel"**.
2. Atur periode **Baseline** (kiri) dan **Perbandingan** (kanan).
3. Pilih layer yang ingin dibandingkan.
4. Klik **"🔄 Render Split-Panel Sinkron"**.
5. Zoom/pan di salah satu peta akan otomatis sinkron ke peta lainnya.

---

## ☁️ Deploy ke Streamlit Cloud (Opsional)

Agar bisa diakses online tanpa menjalankan secara lokal:

1. Push repositori ke GitHub (pastikan `.env` **tidak** ikut ter-push).
2. Buka [share.streamlit.io](https://share.streamlit.io) dan hubungkan akun GitHub Anda.
3. Pilih repositori dan set **Main file path** ke `app.py`.
4. Di menu **"Advanced settings → Secrets"**, tambahkan:

```toml
GEE_PROJECT = "my-gee-project-123"
DEFAULT_LAT  = "-6.9175"
DEFAULT_LON  = "107.6191"
```

5. Untuk autentikasi GEE di cloud, Anda perlu menggunakan **Service Account**. Ikuti panduan [GEE Service Account](https://developers.google.com/earth-engine/guides/service_account) dan tambahkan kredensial JSON-nya ke Streamlit Secrets.

---

## 🔧 Kustomisasi

### Mengubah Vis Params

Edit `config.py` untuk menyesuaikan rentang warna atau palette indeks:

```python
VIS_NDVI = {
    "min": -0.2,
    "max": 0.8,
    "palette": ["d73027", "fc8d59", "fee08b", "ffffbf", "91cf60", "1a9850"]
}
```

### Menambahkan Layer Baru

Di `config.py`, tambahkan entri baru ke `LAYER_CONFIG`:

```python
LAYER_CONFIG["EVI"] = {
    "vis": {"min": 0, "max": 1, "palette": ["white", "green"]},
    "band": "EVI",
    "icon": "🌱",
}
```

Lalu tambahkan kalkulasi band di `utils/gee_utils.py` dalam fungsi `add_indices()`.

---

## 📦 Dependensi

| Paket | Versi Min | Keterangan |
|---|---|---|
| streamlit | 1.35.0 | Framework dashboard web |
| earthengine-api | 0.1.400 | Klien Python GEE |
| folium | 0.17.0 | Peta interaktif berbasis Leaflet |
| streamlit-folium | 0.20.0 | Integrasi Folium ke Streamlit |
| python-dotenv | 1.0.0 | Baca file `.env` |
| geopandas *(opsional)* | 0.14.0 | Baca Shapefile |
| shapely *(opsional)* | 2.0.0 | Operasi geometri |

---

## 🛡️ Keamanan

- File `.env` (berisi `GEE_PROJECT`) **tidak akan pernah** ikut ter-push ke GitHub karena sudah ada di `.gitignore`.
- Jangan pernah hardcode Project ID atau kredensial langsung di kode sumber.
- Untuk deployment cloud, gunakan **Streamlit Secrets** atau **Environment Variables** dari platform hosting Anda.

---

## 🤝 Kontribusi

Pull request dan issue sangat disambut! Silakan fork repositori ini, buat branch baru, lalu ajukan PR.

---

## 📄 Lisensi

Proyek ini menggunakan lisensi **MIT**. Lihat file `LICENSE` untuk detail.

---

## 🙏 Acknowledgements

- [Google Earth Engine](https://earthengine.google.com/) – Platform komputasi geospasial
- [Streamlit](https://streamlit.io/) – Framework web Python
- [Folium](https://python-visualization.github.io/folium/) – Peta Leaflet di Python
- [Copernicus / ESA](https://www.esa.int/) – Data Sentinel-2
