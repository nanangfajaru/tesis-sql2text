# Metadata M0/M1/M2 & Pedoman 100 Soal (v1.0 — DISETUJUI 18 Nov 2026)

Status: **disetujui seluruhnya oleh Nanang, 18 Nov 2026 15:38.** Menjadi acuan penulisan soal dan eksperimen.
File pendukung: `metadata/` (9 file), `buat_metadata.py`, `contoh/contoh_soal.sql`.

---

## 1. Metadata skema (Faktor 2)

### 1.1 Format
Metadata ditulis sebagai **DDL `CREATE TABLE`** (representasi kode), mengikuti representasi skema berbentuk kode yang dikaji Gao dkk. (2024, PVLDB). Semua level memakai format yang sama; yang berbeda hanya isinya.

| Level | Isi | Ukuran (± token) OLTP / Star / Snowflake |
|---|---|---|
| **M0** | nama tabel, nama kolom, tipe data | 310 / 360 / 440 |
| **M1** | M0 + PRIMARY KEY + FOREIGN KEY (REFERENCES) + label peran tabel | 440 / 520 / 740 |
| **M2** | M1 + deskripsi & sinonim Bahasa Indonesia per tabel/kolom + format nilai + glosarium istilah bisnis | 2.300 / 2.400 / 2.700 |

Label peran tabel (M1):
- Star & snowflake: *tabel fakta*, *tabel dimensi*, *tabel sub-dimensi (normalisasi)*.
- OLTP (tidak punya konsep fakta/dimensi): *tabel transaksi* (orders, order_items), *tabel master* (customers, sellers, products), *tabel referensi* (product_category_name_translation).

### 1.2 Prinsip penyusunan
1. **Konsep sama → deskripsi sama** di ketiga skema (dibangkitkan dari satu kamus di `buat_metadata.py`), sehingga perbedaan hasil hanya berasal dari struktur skema.
2. **Netral:** prompt tidak menyebut nama "OLTP/star/snowflake".
3. **Diverifikasi otomatis:** ke-9 file lolos eksekusi sebagai DDL PostgreSQL, dan daftar kolomnya identik 100% dengan database asli.
4. Tabel yang dirujuk ditulis lebih dulu, tabel fakta/transaksi di akhir.

### 1.3 Isi M2 yang tidak bisa ditebak dari nama kolom
- `customer_id` = ID **per pesanan**; jumlah pelanggan harus memakai `customer_unique_id` (98.353 vs 95.121).
- Omzet = `price + freight_value`; di OLTP tidak ada kolom total.
- Grain: satu baris = satu item; jumlah pesanan = `COUNT(DISTINCT order_id)`.
- Kode negara bagian (`SP` = Sao Paulo, dst. 27 kode), kota huruf kecil tanpa aksen.
- 74 kategori: nama database (Inggris) ↔ arti Bahasa Indonesia; di OLTP nama Inggris ada di tabel terjemahan.
- Peran tanggal: tanggal transaksi default = tanggal pembelian; `date_key` format YYYYMMDD; `day_of_week` ISO 1=Senin.
- Status pesanan (6 nilai) dan artinya; tanpa keterangan status = semua status.

### 1.4 Catatan untuk Bab 3 (keterbatasan)
M2 ±5× lebih panjang dari M1. Efek M2 = efek *isi* + *panjang* prompt; ini disebut sebagai batasan.

---

## 2. Template prompt (sama untuk 9 kondisi)

**System:**
> Anda adalah analis data. Tulis SATU query SQL PostgreSQL yang menjawab pertanyaan pengguna berdasarkan skema database yang diberikan. Hanya gunakan SELECT (boleh WITH). Jangan memberi penjelasan. Tulis query di dalam blok ```sql ... ```.

**User:**
> ### Skema database
> {METADATA kondisi}
>
> ### Pertanyaan
> {SOAL}

Pengaturan: zero-shot (tanpa contoh soal), temperature 0, seed tetap, reasoning off. `search_path` diset ke skema kondisi oleh skrip.

---

## 3. Pedoman penulisan 100 soal

### 3.1 Komposisi tingkat kesulitan (25 soal per tingkat)
Diadaptasi dari kriteria kesulitan Spider (Yu dkk., 2018); tingkat ditetapkan berdasarkan **SQL kunci versi star**.

| Tingkat | Ciri SQL kunci (versi star) | Contoh (sudah diuji di 3 skema, hasil identik) |
|---|---|---|
| **L1 Mudah** | 1 ukuran agregat, ≤1 dimensi, ≤1 filter | "Berapa jumlah pesanan yang dibatalkan?" → 448 |
| **L2 Sedang** | GROUP BY + ORDER BY/LIMIT, 1–2 dimensi, filter waktu | "Sebutkan 5 negara bagian pelanggan dengan omzet terbesar pada tahun 2017 beserta omzetnya." → SP, RJ, MG, RS, PR |
| **L3 Sulit** | ≥2 dimensi atau HAVING, ukuran turunan (rata-rata per pesanan, lama pengiriman), COUNT DISTINCT | "Tampilkan kategori produk dengan omzet kuartal 1 tahun 2018 di atas 100.000 BRL, urutkan dari terbesar." → 11 kategori |
| **L4 Sangat sulit** | CTE/subquery, window function, perbandingan antar-periode, ranking per grup, persentase dari total, dua peran tanggal sekaligus | "Untuk setiap bulan Januari–Agustus 2018, berapa persen pertumbuhan omzet dibanding bulan yang sama tahun 2017?" → 8 baris |

### 3.2 Cakupan topik (target, satu soal bisa >1 topik)
Waktu/tren (±20) · Produk & kategori (±20) · Pelanggan & lokasi (±20) · Penjual & lokasi (±15) · Pengiriman: lama, keterlambatan, ongkir (±15) · Status pesanan (±10).

### 3.3 Aturan bahasa & isi soal
1. Bahasa Indonesia natural; variasikan istilah (omzet / nilai penjualan; pelanggan / pembeli; penjual / toko).
2. **Jangan menyalin nama tabel, kolom, atau nilai database** (tulis "dibatalkan", bukan `canceled`; "kesehatan dan kecantikan", bukan `health_beauty`).
3. Sebut jelas kolom yang diminta tampil ("tampilkan nama kategori dan omzetnya").
4. Periode selalu eksplisit (tahun/bulan/kuartal dalam Jan 2017–Agu 2018); tidak ada "tahun ini".
5. **Tidak ada aturan tersembunyi:** semua istilah bisnis mengikuti glosarium M2; status tidak disebut = semua status.
6. Satu soal = satu jawaban pasti. Top-N tidak boleh seri di batas N (dicek otomatis).
7. Hasil tidak kosong dan ≤100 baris.

### 3.4 Kebijakan glosarium (DISETUJUI)
**Campuran.** Sekitar 35–40 soal sengaja memakai istilah bisnis yang definisinya ada di glosarium (omzet, pelanggan unik, lama pengiriman, terlambat, AOV, nama kategori/negara bagian dalam Bahasa Indonesia); sisanya bisa dijawab dari nama kolom saja. Setiap soal diberi tag `butuh_glosarium` (ya/tidak), sehingga analisis bisa memisahkan efek metadata pada dua jenis soal ini.

### 3.5 Format file `soal/soal.csv`
`id, tingkat, topik, butuh_glosarium, pertanyaan, sql_oltp, sql_star, sql_snowflake, urutan_penting, catatan`

### 3.6 SQL kunci & validasi
- Setiap soal punya **3 SQL kunci** (OLTP, star, snowflake).
- Skrip memvalidasi: ketiga hasil identik, tidak kosong, tidak seri di batas top-N, waktu eksekusi < 5 detik.
- Penulisan soal & SQL: Claude. Pemeriksaan keterbacaan & kewajaran bahasa: Nanang. Review ulang intra-rater setelah jeda ±2 minggu.

---

## 4. Aturan penilaian Execution Accuracy (EX)
- Benar bila hasil eksekusi SQL model **sama** dengan hasil SQL kunci pada skema yang sama.
- Baris dibandingkan sebagai multiset; urutan baris hanya diperhitungkan bila `urutan_penting = ya` (soal meminta urutan/top-N).
- Nama kolom diabaikan; urutan kolom boleh berbeda; jumlah kolom harus sama.
- Angka dibulatkan 2 desimal sebelum dibandingkan; NULL = NULL.
- SQL gagal dieksekusi, timeout 30 detik, atau bukan SELECT → salah (dicatat jenis kesalahannya).
