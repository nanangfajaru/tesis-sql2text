# Analisis (Bab 4)

Metode (disepakati 19 Nov 2026): **akurasi eksekusi (EX, %)** sebagai deskripsi, dan
**regresi logistik dengan koreksi pengelompokan per soal (GEE)** sebagai uji.

| Rumusan masalah | Uji | Dibaca dari |
|---|---|---|
| RM1 pengaruh model skema | Uji Wald faktor skema | Tabel 4.2 |
| RM2 pengaruh metadata | Uji Wald faktor metadata | Tabel 4.2 |
| RM3 interaksi skema × metadata | Uji Wald suku interaksi | Tabel 4.2 (+ Tabel 4.4, Gambar 4.1) |
| Rincian per pasangan | Odds ratio + selang 95% (koreksi Bonferroni) | Tabel 4.3, Gambar 4.2 |

Aturan baca: **p < 0,05 → terbukti**. OR > 1 → peluang menjawab benar lebih besar.
Selang yang tidak memuat 1 selalu sama artinya dengan p terkoreksi < 0,05.
Lihat Tabel 4.2 dulu; rincian pasangan hanya disimpulkan bila faktornya terbukti.

```bash
python -m pip install pandas statsmodels matplotlib scipy
python analisis/buat_data_simulasi.py              # coba dengan DATA BUATAN
python analisis/analisis.py hasil/simulasi.csv     # -> analisis/output/laporan.md + gambar
python analisis/analisis.py hasil/penuh_<model>.csv   # data asli (setelah eksperimen penuh)
```
