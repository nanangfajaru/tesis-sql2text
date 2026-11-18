# Panduan Membangun Data Warehouse Olist (3 Varian)

Paket ini membangun satu database PostgreSQL bernama `tesis_dw` berisi tiga skema
dengan isi data yang identik:

| Skema | Varian | Tabel |
|---|---|---|
| `oltp` | OLTP (transaksional asli) | customers, orders, order_items, products, sellers, product_category_name_translation |
| `star` | Star schema | fact_sales + dim_date, dim_customer, dim_product, dim_seller, dim_order_status |
| `snowflake` | Snowflake schema | fact_sales + dim_date → dim_month → dim_year, dim_customer/dim_seller → dim_city → dim_state, dim_product → dim_category, dim_order_status |

Skema `staging` berisi salinan mentah CSV (tidak dipakai dalam eksperimen).

## Aturan ETL (berlaku untuk ketiga varian)

- E1. Periode pembelian: 1 Januari 2017 s.d. 31 Agustus 2018.
- E2. Pesanan tanpa item dibuang.
- E3. Produk tanpa kategori diberi kategori `unknown`; dua kategori tanpa terjemahan
  (`pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`) diterjemahkan manual.
- E4. Tabel pembayaran, ulasan, dan geolocation tidak dipakai (satu tabel fakta: penjualan).
- Granularitas waktu terkecil di star/snowflake adalah tanggal (jam tidak disimpan).

Hasil yang diharapkan: 98.353 pesanan, 112.279 item, total nilai penjualan
(harga + ongkos kirim) 15.786.203,57.

## Langkah-langkah (Windows)

### 1. Pasang PostgreSQL
1. Unduh installer PostgreSQL versi 16 atau 17 dari
   https://www.postgresql.org/download/windows/ (installer EDB).
2. Jalankan installer, pakai pilihan bawaan. Catat **password** untuk user `postgres`.
   Port biarkan `5432`.
3. Setelah selesai, buka **Command Prompt** dan cek:
   ```
   "C:\Program Files\PostgreSQL\16\bin\psql.exe" --version
   ```
   (ganti `16` dengan versi yang terpasang). Supaya cukup mengetik `psql`, tambahkan folder
   `C:\Program Files\PostgreSQL\16\bin` ke PATH Windows, atau pakai path lengkap di atas.

### 2. Siapkan folder
```
C:\tesis\olist\   <- ekstrak zip Olist dari Kaggle di sini (9 file .csv)
C:\tesis\sql\     <- ekstrak isi folder sql dari paket ini di sini
```

### 3. Buat database
```
psql -U postgres -c "CREATE DATABASE tesis_dw;"
```
Masukkan password `postgres` saat diminta.

### 4. Jalankan skrip
Perintah ini **harus dijalankan dari folder CSV Olist**:
```
cd C:\tesis\olist
psql -U postgres -d tesis_dw -f C:/tesis/sql/00_jalankan_semua.sql > C:\tesis\hasil_build.txt 2>&1
```
Proses memakan waktu sekitar 1–3 menit.

### 5. Periksa hasil
Buka `C:\tesis\hasil_build.txt`. Di bagian paling bawah harus ada tabel
"Uji kesetaraan antar-varian" dengan **6 baris berstatus OK**, lalu tulisan `SELESAI.`

Kirim file `hasil_build.txt` ke chat untuk dicek.

## Jika ada error
- `psql is not recognized` → pakai path lengkap `"C:\Program Files\PostgreSQL\16\bin\psql.exe"`.
- `could not open file "olist_...csv"` → perintah tidak dijalankan dari folder `C:\tesis\olist`.
- `password authentication failed` → password user `postgres` salah.
- Error lain → kirim screenshot atau isi `hasil_build.txt`.
