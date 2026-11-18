"""
cek_koneksi.py — Cek kesiapan sebelum pilot eksperimen.

Yang dicek:
  1. File .env terbaca (API key TIDAK pernah dicetak utuh).
  2. API key OpenRouter valid + sisa kredit (gratis, tanpa memanggil model).
  3. Koneksi PostgreSQL sebagai llm_reader + benar-benar read-only.
  4. (opsional, --uji-model) satu panggilan kecil ke model (< $0,001).

Cara pakai (Git Bash, dari folder C:\\tesis):
  python cek_koneksi.py
  python cek_koneksi.py --uji-model
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
    import psycopg
except ImportError:
    sys.exit("Paket belum terpasang. Jalankan:  python -m pip install \"psycopg[binary]\" python-dotenv")

OPENROUTER = "https://openrouter.ai/api/v1"
MODEL_UJI = "qwen/qwen3-coder-30b-a3b-instruct"


def judul(teks):
    print(f"\n=== {teks} ===")


def ok(teks):
    print(f"  [OK]    {teks}")


def gagal(teks):
    print(f"  [GAGAL] {teks}")


def http_json(url, key, payload=None, timeout=60):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Title", "tesis-text2sql-cek")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def cek_env():
    judul("1. File .env")
    folder = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(folder, ".env")
    if not os.path.exists(path):
        gagal(f".env tidak ditemukan di {folder}")
        return None
    load_dotenv(path)
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key.startswith("sk-or-"):
        gagal("OPENROUTER_API_KEY kosong atau formatnya bukan 'sk-or-...'")
        return None
    ok(f"API key terbaca: {key[:8]}...{key[-4:]} (disamarkan)")
    for v in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"):
        if not os.getenv(v):
            gagal(f"{v} belum diisi di .env")
    return key


def cek_api(key):
    judul("2. API key OpenRouter")
    try:
        info = http_json(f"{OPENROUTER}/key", key).get("data", {})
    except urllib.error.HTTPError as e:
        gagal(f"HTTP {e.code} — key salah / dicabut? ({e.reason})")
        return False
    except Exception as e:
        gagal(f"Tidak bisa menghubungi OpenRouter: {e}")
        return False
    ok(f"Key valid. Label: {info.get('label')}")
    limit = info.get("limit")
    usage = info.get("usage", 0) or 0
    if limit is None:
        print("  [INFO]  Key TANPA batas kredit — disarankan set limit $5 di menu Keys.")
    else:
        ok(f"Batas kredit key: ${limit:.2f}, terpakai: ${usage:.4f}")
    return True


def cek_db():
    judul("3. PostgreSQL (user read-only)")
    try:
        conn = psycopg.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", "5432"),
            dbname=os.getenv("PGDATABASE", "tesis_dw"),
            user=os.getenv("PGUSER", "llm_reader"),
            password=os.getenv("PGPASSWORD"),
            connect_timeout=10,
        )
    except Exception as e:
        gagal(f"Tidak bisa konek: {e}")
        return False
    semua_ok = True
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT current_user, current_setting('statement_timeout'), "
                    "current_setting('default_transaction_read_only')")
        user, timeout, ro = cur.fetchone()
        ok(f"Login sebagai {user}, timeout {timeout}, read_only={ro}")
        for skema in ("oltp", "star", "snowflake"):
            tabel = "order_items" if skema == "oltp" else "fact_sales"
            cur.execute(f"SELECT count(*) FROM {skema}.{tabel}")
            n = cur.fetchone()[0]
            (ok if n == 112279 else gagal)(f"{skema}.{tabel} = {n:,} baris (harus 112,279)")
            semua_ok &= n == 112279
        conn.rollback()
        # Uji: user ini TIDAK boleh menulis
        try:
            cur.execute("CREATE TABLE star.uji_tulis(x int)")
            gagal("User masih bisa MENULIS — jalankan ulang 06_user_readonly.sql!")
            semua_ok = False
        except psycopg.Error:
            ok("Percobaan menulis DITOLAK (benar, user read-only)")
        conn.rollback()
        # Uji: staging tidak boleh terlihat
        try:
            cur.execute("SELECT 1 FROM staging.orders LIMIT 1")
            gagal("Skema staging masih bisa dibaca")
            semua_ok = False
        except psycopg.Error:
            ok("Skema staging tidak bisa diakses (benar)")
        conn.rollback()
    return semua_ok


def uji_model(key):
    judul(f"4. Uji 1 panggilan model ({MODEL_UJI})")
    payload = {
        "model": MODEL_UJI,
        "messages": [
            {"role": "system", "content": "Jawab hanya dengan satu query SQL PostgreSQL, tanpa penjelasan."},
            {"role": "user", "content": "Tabel: t(x int). Berapa jumlah baris tabel t?"},
        ],
        "temperature": 0,
        "seed": 42,
        "max_tokens": 50,
        "reasoning": {"enabled": False},
        "usage": {"include": True},
    }
    t0 = time.time()
    try:
        r = http_json(f"{OPENROUTER}/chat/completions", key, payload)
    except urllib.error.HTTPError as e:
        gagal(f"HTTP {e.code}: {e.read().decode()[:300]}")
        return False
    except Exception as e:
        gagal(f"Error: {e}")
        return False
    msg = r["choices"][0]["message"]
    usage = r.get("usage", {})
    ok(f"Jawaban: {msg.get('content', '').strip()!r}")
    ok(f"Penyedia: {r.get('provider')}, model: {r.get('model')}, {time.time() - t0:.1f} dtk")
    ok(f"Token: {usage.get('prompt_tokens')} masuk / {usage.get('completion_tokens')} keluar, "
       f"biaya: ${usage.get('cost', 0) or 0:.6f}")
    rt = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
    (ok if not rt and not msg.get("reasoning") else gagal)(f"Token reasoning: {rt} (harus 0)")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uji-model", action="store_true", help="lakukan 1 panggilan model (< $0,001)")
    a = ap.parse_args()

    key = cek_env()
    hasil = [key is not None]
    if key:
        hasil.append(cek_api(key))
    hasil.append(cek_db())
    if key and a.uji_model:
        hasil.append(uji_model(key))

    print("\n" + ("SEMUA SIAP." if all(hasil) else "ADA YANG PERLU DIPERBAIKI (lihat [GAGAL] di atas)."))


if __name__ == "__main__":
    main()