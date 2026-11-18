# Soal eksperimen (100 soal × 3 SQL kunci)

| File | Isi |
|---|---|
| `soal.csv` | **Dataset soal final**: id, tingkat, topik, butuh_glosarium, pertanyaan, sql_oltp, sql_star, sql_snowflake, urutan_penting, jumlah_baris, catatan |
| `laporan_validasi.md` | Ringkasan validasi + daftar 100 soal beserta cuplikan jawaban — **baca ini untuk review** |
| `soal_def.py` | Sumber: teks soal + template SQL kunci (diedit di sini, bukan di CSV) |
| `sqlgen.py` | Menerjemahkan template ke SQL OLTP / star / snowflake |
| `validasi_soal.py` | Membangkitkan `soal.csv` dan menjalankan validasi V1–V5 |

Validasi (semua harus OK): V1 ketiga SQL dapat dieksekusi · V2 hasil ketiga skema identik ·
V3 tidak kosong & ≤100 baris · V4 tidak ada nilai seri pada kolom pengurut / batas top-N ·
V5 waktu eksekusi < 5 detik.

Hasil terakhir: **100/100 lulus**; 25 soal per tingkat; 40 soal `butuh_glosarium = ya`.

Menjalankan ulang (Git Bash, dari folder repo; pakai user `postgres`, bukan `llm_reader`):

```bash
PGUSER=postgres PGPASSWORD='...' python soal/validasi_soal.py
```

Catatan: Q053 sengaja `urutan_penting = tidak` karena dua negara bagian (PR, MG) seri pada 2 desimal;
himpunan 5 negara bagiannya tetap pasti.
