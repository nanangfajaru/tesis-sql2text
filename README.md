# Tesis Text-to-SQL pada Data Warehouse (Olist)

Penelitian tesis Magister — Universitas Esa Unggul.

**Topik:** pengaruh model skema data warehouse (OLTP / star / snowflake) dan kelengkapan metadata
(M1 / M2 / M3) terhadap akurasi LLM dalam menerjemahkan pertanyaan bisnis **Bahasa Indonesia** menjadi SQL.
Desain eksperimen faktorial 3 × 3, metrik utama *Execution Accuracy*.

- Dataset: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (CC BY-NC-SA 4.0) — **tidak disertakan** di repo ini, unduh dari Kaggle.
- DBMS: PostgreSQL 16+.
- LLM: model open-weight via OpenRouter, zero-shot (model final ditentukan lewat pilot).

## Struktur repo

| Path | Isi |
|---|---|
| `PANDUAN.md` | Panduan membangun database di Windows |
| `sql/00_jalankan_semua.sql` … `05_validasi.sql` | Build DW: staging → OLTP → star → snowflake + 6 uji kesetaraan antar-varian |
| `sql/06_user_readonly.sql` | User `llm_reader` (read-only, timeout 30 dtk) untuk menjalankan SQL buatan LLM |
| `metadata/<skema>_M{0,1,2}.sql` | 9 teks metadata skema yang disisipkan ke prompt |
| `buat_metadata.py` | Generator ke-9 file metadata (satu kamus deskripsi untuk semua skema) |
| `docs/pedoman-metadata-soal.md` | Definisi M1/M2/M3, template prompt, pedoman 100 soal, aturan penilaian EX |
| `soal/` | 100 soal + 300 SQL kunci + validasi otomatis (lihat `soal/README.md`) |
| `contoh/contoh_soal.sql` | 4 contoh soal (L1–L4) dengan SQL kunci di 3 skema |
| `eksperimen/jalankan.py` | Skrip pilot & eksperimen penuh (lihat `eksperimen/README.md`) |
| `cek_koneksi.py` | Cek kesiapan: `.env`, API key OpenRouter, koneksi DB read-only, 1 panggilan model |
| `profil_dataset.py` | Profil/audit CSV dataset (DuckDB) |
| `.env.example` | Contoh isi `.env` (file `.env` asli **tidak** di-commit) |

## Langkah singkat

```bash
# 1. Build database (lihat PANDUAN.md); di Git Bash gunakan psql.exe
cd /c/tesis/olist
psql.exe -U postgres -d tesis_dw -f /c/tesis/sql/00_jalankan_semua.sql > /c/tesis/hasil_build.txt 2>&1

# 2. User read-only
psql.exe -U postgres -d tesis_dw -v pw='PASSWORD_READER' -f /c/tesis/sql/06_user_readonly.sql

# 3. Isi .env (salin dari .env.example), lalu cek
python -m pip install "psycopg[binary]" python-dotenv
python cek_koneksi.py --uji-model

# 4. (Re)generate metadata
python buat_metadata.py
```

## Status

- [x] Build DW + 6/6 uji kesetaraan lulus
- [x] User read-only + koneksi OpenRouter
- [x] Metadata M1/M2/M3 (disetujui 18 Nov 2026)
- [x] 100 soal + 300 SQL kunci (lolos validasi 100/100)
- [x] Skrip pilot & eksperimen (`eksperimen/jalankan.py`, dry-run 900/900)
- [ ] Pilot 2 kandidat model
- [ ] Analisis statistik
