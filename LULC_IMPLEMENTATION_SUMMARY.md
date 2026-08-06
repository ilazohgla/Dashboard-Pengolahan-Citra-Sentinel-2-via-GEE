# 🗺️ Implementasi Klasifikasi LULC – Summary

## Tanggal Update
**May 29, 2026**

---

## 📋 Fitur Baru yang Ditambahkan

### ✅ Tab 3: Klasifikasi LULC (Land Use Land Cover)

Dashboard sekarang memiliki **tab baru untuk klasifikasi LULC dengan 4 metode machine learning**.

#### Metode Klasifikasi

1. **K-Means Unsupervised** (Cepat, otomatis)
   - Tidak perlu training data
   - Hasil bervariasi, akurasi sedang

2. **KNN Supervised** (Akurat, fleksibel)
   - Parameter: Nilai K (default 5)
   - Cocok untuk batas kelas yang jelas

3. **Random Forest Supervised** (Akurat, robust)
   - Parameter: Jumlah trees (default 100), bag fraction
   - Ideal untuk klasifikasi multivariabel

4. **⭐ KNN + RF Ensemble** (Paling Akurat!)
   - Kombinasi voting majority KNN & RF
   - Akurasi tertinggi, paling robust
   - **REKOMENDASI UNTUK ANALISIS PRESISI TINGGI**

#### 7 Kelas LULC

```
1 = 🏢 Built-up (Area Terbangun)
2 = 🌾 Cropland (Lahan Pertanian)
3 = 🌳 Forest (Hutan)
4 = 💧 Water (Perairan)
5 = 🪨 Bare Land (Lahan Terbuka)
6 = 🌱 Shrub & Grassland (Semak/Padang Rumput)
7 = 🏞️ Wetland (Lahan Basah)
```

#### Feature Engineering (13 Fitur)

Setiap piksel dianalisis dengan:
- **6 Band Reflektansi** (B2, B3, B4, B5, B6, B7)
- **7 Indeks Spektral**:
  - NDVI (Normalized Difference Vegetation Index)
  - NDWI (Normalized Difference Water Index)
  - NDBI (Normalized Difference Built-up Index)
  - MNDWI (Modified Normalized Difference Water Index)
  - EVI (Enhanced Vegetation Index)
  - SAVI (Soil-Adjusted Vegetation Index)
  - BSI (Bare Soil Index)

---

## 📁 File Baru yang Ditambahkan

### 1. `utils/classification_utils.py` (520 lines)

**Fungsi utama:**

- `build_feature_image()` – Bangun image multivariabel dengan 13 fitur
- `create_auto_training_samples()` – Generate training data otomatis dari heuristik spektral
- `classify_kmeans()` – K-Means unsupervised classification
- `classify_supervised()` – KNN, RF, atau Ensemble classification
- `calculate_area_per_class()` – Hitung luas per kelas LULC
- `export_lulc_to_drive()` – Export hasil ke Google Drive

**Fitur khusus:**

- Training data otomatis berbasis threshold spektral (tidak perlu manual labeling)
- Confusion matrix & akurasi otomatis untuk supervised methods
- Variable importance untuk Random Forest
- Support untuk Landsat 8/9 dan Sentinel-2

### 2. `pages/tab_lulc_classification.py` (280 lines)

**UI & interaktivitas:**

- Dropdown pemilihan metode klasifikasi
- Slider untuk parameter tuning (k, num_trees, bag_fraction, samples_per_class)
- Checkbox untuk tampilkan akurasi & variable importance
- Live peta hasil LULC dengan legenda
- Tabel & chart luas per kelas
- Tombol export ke Google Drive

### 3. File yang Di-Update

#### `app.py`
- Tambah import `render_tab_lulc`
- Update `st.tabs()` dari 2 menjadi 3 tab
- Tambah `with tab3:` block untuk LULC rendering

#### `requirements.txt`
- Tambah: `pandas>=2.0.0`
- Tambah: `scikit-learn>=1.3.0`
- Tambah: `numpy>=1.24.0`

#### `README.md`
- Tambah section "Tab 3: Klasifikasi LULC"
- Dokumentasi lengkap metode & parameter
- Tips optimal untuk classification

---

## 🔧 Konfigurasi & Parameter

### Untuk K-Means (Unsupervised)

```
Metode: K-Means
Parameter: Otomatis (7 klaster)
Kebutuhan: Cepat, tanpa GPU
Waktu: ~1 menit
```

### Untuk Supervised (KNN, RF, Ensemble)

```
Parameter Default:
- K Value (KNN): 5
- Num Trees (RF): 100
- Bag Fraction (RF): 0.5
- Samples per Class: 150
- Train/Test Split: 80:20

Rekomendasi untuk Akurasi Tinggi:
- Samples per Class: ≥ 150
- AOI Size: ≥ 300 km²
- Metode: Ensemble KNN+RF
- Waktu: ~2-3 menit (tergantung AOI size)
```

---

## 📊 Output & Hasil

### Peta LULC
- **Format**: GeoTIFF (30m resolution, 7 kelas)
- **CRS**: EPSG:4326 (WGS84)
- **Download**: Otomatis di Google Drive

### Evaluasi Akurasi (Supervised)
- **Overall Accuracy (OA)**: Persentase piksel yang benar
- **Kappa Coefficient**: Ukuran agreement beyond chance
- **Confusion Matrix**: Detail per-kelas accuracy

### Area Report
- **Luas per Kelas**: Dalam km²
- **Persentase**: % dari total AOI
- **Chart**: Visualisasi bar chart untuk perbandingan

---

## 🚀 Cara Menggunakan

### Setup Pertama

```bash
# 1. Update requirements
pip install -r requirements.txt

# 2. Jalankan app
streamlit run app.py
```

### Workflow Klasifikasi LULC

```
1. Tab 1: Tampilkan Citra RGB → OK
2. Tab 1: Hitung NDVI (opsional)
3. Tab 3: Buka Klasifikasi LULC
4. Pilih Metode (rekomendasi: Ensemble ⭐)
5. Atur parameter (gunakan default atau custom)
6. Klik "Jalankan Klasifikasi LULC"
7. Tunggu 1-3 menit
8. Lihat hasil + akurasi + luas per kelas
9. Export ke Drive (opsional)
```

---

## ⚡ Performance Tips

| Aksi | Waktu | Tips |
|---|---|---|
| K-Means | ~1 min | Cepat, untuk eksplorasi |
| KNN (k=5) | ~1.5 min | Sedang, cocok offline |
| Random Forest (100 trees) | ~2 min | Baik, GPU optional |
| **Ensemble (recommended)** | ~3 min | Terbaik, tunggu sebentar |

**Untuk AOI besar (>1000 km²):**
- Kurangi samples_per_class (dari 150 → 100)
- Atau reduce jumlah trees (dari 100 → 50)

---

## 🔒 Security & Privacy

- ✅ Semua file `.env` **tetap protected** (tidak ter-push)
- ✅ Training data dibuat **otomatis** dari spektral heuristic
- ✅ **Tidak perlu manual labeling** atau training samples upload
- ✅ Hasil export langsung ke personal **Google Drive** (private)

---

## 📝 Next Steps / Future Enhancements

Fitur yang bisa ditambahkan di masa depan:

1. **Manual Training Data Upload** – Upload shapefile dengan training polygons
2. **Post-processing** – Morphological filtering, smoothing
3. **Change Detection** – Bandingkan LULC antar periode
4. **Probability Map** – Confidence/probability per kelas
5. **Custom Classes** – Biarkan user define kelas sesuai kebutuhan
6. **Export ke Formats Lain** – GeoJSON, NetCDF, COG

---

## 📞 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'sklearn'"
```bash
pip install scikit-learn>=1.3.0
```

### Error: "Training samples terlalu sedikit"
- Perlebar AOI (draw polygon yang lebih besar)
- Atau naikkan `samples_per_class` slider

### Hasil Classification Jelek
- Gunakan Ensemble method (akurasi lebih baik)
- Naikkan `samples_per_class` (dari 150 → 200+)
- Pastikan AOI ≥ 300 km²

### Export ke Drive Gagal
- Pastikan authenticated dengan Google Account
- Check tab **Tasks** di GEE untuk status
- Lihat error message di GEE Console

---

## 📚 References

- **NDVI**: Rouse et al. (1973) – Vegetation monitoring
- **NDWI**: McFeeters (1996) – Water detection
- **NDBI**: Zha et al. (2003) – Built-up area detection
- **EVI**: Huete et al. (2002) – Enhanced vegetation index
- **Random Forest**: Breiman (2001) – Machine learning
- **KNN Ensemble**: Combining classifiers for better accuracy

---

## ✅ Checklist Sebelum Push ke GitHub

- [x] File `.env` tidak ter-push (protected by .gitignore)
- [x] Requirements.txt updated
- [x] README.md dengan dokumentasi lengkap
- [x] Code commented & readable
- [x] Test di local machine berhasil
- [x] Ready untuk push ke GitHub!

---

**Version**: v3.1 (Dengan LULC Classification)
**Last Updated**: May 29, 2026
**Status**: ✅ Production Ready
