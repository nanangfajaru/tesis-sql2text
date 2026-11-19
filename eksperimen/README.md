# Eksperimen

`jalankan.py` dipakai untuk pilot dan eksperimen penuh.

| Mode | Perintah | Panggilan |
|---|---|---|
| Uji pipeline tanpa API (gratis, harus 100%) | `python eksperimen/jalankan.py --dry-run --pilot` | 0 |
| Pilot model A | `python eksperimen/jalankan.py --model qwen/qwen3-coder-30b-a3b-instruct --pilot` | 60 |
| Pilot model B | `python eksperimen/jalankan.py --model qwen/qwen3.8-27b --pilot` | 60 |
| Penuh | `python eksperimen/jalankan.py --model <id> --provider "<penyedia>"` | 900 |

Pilot = 10 soal (L1 2, L2 3, L3 3, L4 2) × 3 skema × metadata M1 & M3.

Pengaturan tetap: zero-shot, temperature 0, seed 42, max 1024 token, reasoning dimatikan,
penyedia dikunci (`allow_fallbacks = false`; bila `--provider` tidak diisi, penyedia pertama
yang menjawab dikunci untuk sisa run). SQL model dijalankan sebagai `llm_reader`
(read-only, timeout 30 dtk) dengan `search_path` = skema kondisi.

Status per pemanggilan: `benar`, `hasil_salah`, `error_eksekusi`, `timeout`, `bukan_select`,
`tanpa_sql`, `api_error` (api_error diulang otomatis saat run dijalankan lagi).

Keluaran:
- `hasil/<run>.csv` — ikut ke git (bahan analisis).
- `log_mentah/<run>.jsonl` — prompt & respons mentah lengkap; **tidak** ikut ke git (arsipkan terpisah).

Run yang terputus cukup dijalankan ulang dengan perintah yang sama.
