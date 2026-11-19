"""
jalankan.py — Menjalankan eksperimen Text-to-SQL (pilot maupun penuh).

Alur per pemanggilan: rakit prompt (template + metadata kondisi + soal) -> OpenRouter
-> ekstrak SQL -> eksekusi di PostgreSQL sebagai llm_reader (search_path = skema kondisi)
-> bandingkan dengan hasil SQL kunci (aturan EX pedoman v1.0) -> simpan.

Contoh (Git Bash, dari folder repo):
  # pilot: 10 soal x 3 skema x M1,M3 = 60 panggilan
  python eksperimen/jalankan.py --model qwen/qwen3-coder-30b-a3b-instruct --pilot
  python eksperimen/jalankan.py --model qwen/qwen3.8-27b --pilot

  # eksperimen penuh: 100 soal x 3 skema x 3 metadata = 900 panggilan
  python eksperimen/jalankan.py --model <id_model> --provider <nama_penyedia>

  # uji pipeline tanpa API (jawaban = SQL kunci, harus 100% benar)
  python eksperimen/jalankan.py --dry-run --pilot

Keluaran (folder hasil/ & log_mentah/ dibuat otomatis):
  hasil/<run>.csv              satu baris per pemanggilan
  log_mentah/<run>.jsonl       prompt & respons mentah lengkap
Run yang terputus bisa dilanjutkan: jalankan perintah yang sama (yang sudah selesai dilewati).
"""
import argparse
import csv
import itertools
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal

import psycopg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://openrouter.ai/api/v1/chat/completions"
SCHEMAS = ["oltp", "star", "snowflake"]
LEVELS = ["M1", "M2", "M3"]
PILOT = ["Q004", "Q010", "Q027", "Q031", "Q041", "Q052", "Q056", "Q066", "Q076", "Q086"]
SEED = 42
MAX_TOKENS = 1024
MAX_ROWS = 10000

SYSTEM = ("Anda adalah analis data. Tulis SATU query SQL PostgreSQL yang menjawab pertanyaan pengguna "
          "berdasarkan skema database yang diberikan. Hanya gunakan SELECT (boleh WITH). Jangan memberi "
          "penjelasan. Tulis query di dalam blok ```sql ... ```.")
USER = "### Skema database\n{meta}\n\n### Pertanyaan\n{soal}"


# ------------------------------------------------------------------ util
def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(ROOT, ".env"))
    except ImportError:
        pass


def load_soal():
    with open(os.path.join(ROOT, "soal", "soal.csv"), encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def load_meta():
    m = {}
    for sc in SCHEMAS:
        for lv in LEVELS:
            with open(os.path.join(ROOT, "metadata", f"{sc}_{lv}.sql"), encoding="utf-8") as f:
                m[(sc, lv)] = f.read().strip()
    return m


def extract_sql(text):
    if not text:
        return ""
    blocks = re.findall(r"```(?:sql|postgresql)?\s*\n?(.*?)```", text, re.S | re.I)
    sql = blocks[0] if blocks else text
    return sql.strip().rstrip(";").strip()


def is_select(sql):
    s = re.sub(r"--[^\n]*", "", sql).strip().lower()
    return s.startswith("select") or s.startswith("with")


def nv(v):
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float, Decimal)):
        return f"{round(float(v), 2):.2f}"
    return "NULL" if v is None else str(v)


def same_result(pred, gold, ordered):
    """Aturan EX: jumlah kolom sama; nama kolom diabaikan; urutan kolom boleh beda;
    angka dibulatkan 2 desimal; urutan baris dinilai hanya bila ordered."""
    if len(pred) != len(gold):
        return False
    if not gold:
        return not pred
    ncol = len(gold[0])
    if any(len(r) != ncol for r in pred):
        return False
    g = [tuple(nv(v) for v in r) for r in gold]
    p = [tuple(nv(v) for v in r) for r in pred]
    if not ordered:
        g = sorted(g)
    perms = itertools.permutations(range(ncol)) if ncol <= 6 else [tuple(range(ncol))]
    for perm in perms:
        pp = [tuple(r[i] for i in perm) for r in p]
        if (pp if ordered else sorted(pp)) == g:
            return True
    return False


def call_llm(key, model, provider, prompt_user, dry_sql=None):
    if dry_sql is not None:
        return {"content": f"```sql\n{dry_sql}\n```", "provider": "dry-run", "model": "dry-run",
                "usage": {}, "latency": 0.0, "raw": None}
    body = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt_user}],
        "temperature": 0, "seed": SEED, "max_tokens": MAX_TOKENS,
        "reasoning": {"enabled": False, "exclude": True},
        "usage": {"include": True},
    }
    if provider:
        body["provider"] = {"order": [provider], "allow_fallbacks": False}
    data = json.dumps(body).encode()
    last = None
    for attempt in range(4):
        req = urllib.request.Request(URL, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {key}")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Title", "tesis-text2sql")
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = json.loads(r.read().decode())
            if "error" in raw:
                raise RuntimeError(json.dumps(raw["error"])[:300])
            msg = raw["choices"][0]["message"]
            return {"content": msg.get("content") or "", "provider": raw.get("provider"),
                    "model": raw.get("model"), "usage": raw.get("usage") or {},
                    "latency": time.time() - t0, "raw": raw}
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:300]}"
            if e.code not in (408, 429, 500, 502, 503, 504):
                break
        except Exception as e:  # jaringan / format
            last = str(e)[:300]
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(last)


def run_sql(conn, schema, sql):
    with conn.cursor() as cur:
        cur.execute(f"SET search_path = {schema}")
        cur.execute(sql)
        return cur.fetchmany(MAX_ROWS + 1)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen/qwen3-coder-30b-a3b-instruct")
    ap.add_argument("--provider", default=None,
                    help="kunci ke satu penyedia (mis. 'Amazon Bedrock'); bila kosong, penyedia "
                         "pertama yang menjawab dikunci untuk sisa run")
    ap.add_argument("--pilot", action="store_true", help="10 soal pilot, metadata M1 & M3")
    ap.add_argument("--soal", default=None, help="daftar id dipisah koma (opsional)")
    ap.add_argument("--metadata", default=None, help="mis. M1,M3 (default: semua / pilot M1,M3)")
    ap.add_argument("--run", default=None, help="nama run (default otomatis)")
    ap.add_argument("--dry-run", action="store_true", help="tanpa API: jawaban = SQL kunci")
    a = ap.parse_args()

    load_env()
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not a.dry_run and not key.startswith("sk-or-"):
        sys.exit("OPENROUTER_API_KEY tidak ada di .env")

    soal = load_soal()
    meta = load_meta()
    ids = a.soal.split(",") if a.soal else (PILOT if a.pilot else list(soal))
    levels = a.metadata.split(",") if a.metadata else (["M1", "M3"] if a.pilot else LEVELS)
    tag = "dryrun" if a.dry_run else re.sub(r"[^a-z0-9]+", "-", a.model.lower()).strip("-")
    run = a.run or f"{'pilot' if a.pilot else 'penuh'}_{tag}"

    os.makedirs(os.path.join(ROOT, "hasil"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "log_mentah"), exist_ok=True)
    out_csv = os.path.join(ROOT, "hasil", f"{run}.csv")
    out_log = os.path.join(ROOT, "log_mentah", f"{run}.jsonl")

    fields = ["run", "waktu_utc", "id", "tingkat", "butuh_glosarium", "skema", "metadata", "model",
              "penyedia", "sql_model", "status", "benar", "pesan_error", "baris_model", "baris_kunci",
              "token_masuk", "token_keluar", "token_reasoning", "biaya_usd", "latensi_dtk"]
    done = set()
    if os.path.exists(out_csv):
        with open(out_csv, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["status"] != "api_error":
                    done.add((r["id"], r["skema"], r["metadata"]))
    new_file = not os.path.exists(out_csv)
    fcsv = open(out_csv, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fcsv, fieldnames=fields)
    if new_file:
        w.writeheader()
    flog = open(out_log, "a", encoding="utf-8")

    conn = psycopg.connect(autocommit=True)  # PG* dari .env -> llm_reader
    gold_cache = {}
    provider = a.provider
    jobs = [(i, sc, lv) for i in ids for sc in SCHEMAS for lv in levels]
    todo = [j for j in jobs if j not in done]
    print(f"Run {run}: {len(jobs)} kondisi, {len(jobs) - len(todo)} sudah selesai, {len(todo)} dikerjakan.")
    total_cost = 0.0

    for n, (i, sc, lv) in enumerate(todo, 1):
        s = soal[i]
        ordered = s["urutan_penting"] == "ya"
        gkey = (i, sc)
        if gkey not in gold_cache:
            gold_cache[gkey] = run_sql(conn, sc, s[f"sql_{sc}"])
        gold = gold_cache[gkey]
        prompt = USER.format(meta=meta[(sc, lv)], soal=s["pertanyaan"])
        row = dict(run=run, waktu_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), id=i,
                   tingkat=s["tingkat"], butuh_glosarium=s["butuh_glosarium"], skema=sc, metadata=lv,
                   model=a.model if not a.dry_run else "dry-run", baris_kunci=len(gold))
        resp = None
        try:
            resp = call_llm(key, a.model, provider, prompt, dry_sql=s[f"sql_{sc}"] if a.dry_run else None)
        except Exception as e:
            row.update(status="api_error", benar=0, pesan_error=str(e)[:300])
        if resp is not None:
            if provider is None and not a.dry_run and resp["provider"]:
                provider = resp["provider"]
                print(f"  -> penyedia dikunci ke: {provider}")
            u = resp["usage"]
            rt = ((u.get("completion_tokens_details") or {}).get("reasoning_tokens")) or 0
            total_cost += float(u.get("cost") or 0)
            sql = extract_sql(resp["content"])
            row.update(penyedia=resp["provider"], sql_model=sql, token_masuk=u.get("prompt_tokens"),
                       token_keluar=u.get("completion_tokens"), token_reasoning=rt, biaya_usd=u.get("cost"),
                       latensi_dtk=round(resp["latency"], 2))
            if not sql:
                row.update(status="tanpa_sql", benar=0)
            elif not is_select(sql):
                row.update(status="bukan_select", benar=0)
            else:
                try:
                    pred = run_sql(conn, sc, sql)
                    ok = len(pred) <= MAX_ROWS and same_result(pred, gold, ordered)
                    row.update(status="benar" if ok else "hasil_salah", benar=int(ok), baris_model=len(pred))
                except psycopg.errors.QueryCanceled:
                    row.update(status="timeout", benar=0, pesan_error="statement_timeout 30 dtk")
                except psycopg.Error as e:
                    row.update(status="error_eksekusi", benar=0, pesan_error=str(e).splitlines()[0][:300])
            flog.write(json.dumps({"run": run, "id": i, "skema": sc, "metadata": lv, "system": SYSTEM,
                                   "user": prompt, "respons": resp["raw"], "konten": resp["content"],
                                   "waktu_utc": row["waktu_utc"]}, ensure_ascii=False, default=str) + "\n")
            flog.flush()
            if rt:
                print(f"  !! PERINGATAN: {rt} token reasoning terdeteksi ({i} {sc} {lv})")
        w.writerow(row)
        fcsv.flush()
        print(f"[{n}/{len(todo)}] {i} {sc:9s} {lv} -> {row['status']}"
              + (f" ({row.get('pesan_error', '')[:60]})" if row.get("pesan_error") else ""))

    fcsv.close()
    flog.close()
    ringkas(out_csv, total_cost)


def ringkas(path, cost=0.0):
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["status"] != "api_error"]
    if not rows:
        return
    print("\n=== Execution Accuracy (%) ===")
    lv = sorted({r["metadata"] for r in rows})
    print("skema      " + "  ".join(f"{x:>6s}" for x in lv))
    for sc in SCHEMAS:
        cells = []
        for m in lv:
            sel = [int(r["benar"]) for r in rows if r["skema"] == sc and r["metadata"] == m]
            cells.append(f"{100 * sum(sel) / len(sel):6.1f}" if sel else "     -")
        print(f"{sc:10s} " + "  ".join(cells))
    tot = [int(r["benar"]) for r in rows]
    print(f"Total: {100 * sum(tot) / len(tot):.1f}% dari {len(tot)} panggilan")
    st = {}
    for r in rows:
        st[r["status"]] = st.get(r["status"], 0) + 1
    print("Status:", ", ".join(f"{k} {v}" for k, v in sorted(st.items())))
    rt = sum(int(r["token_reasoning"] or 0) for r in rows)
    print(f"Token reasoning total: {rt} (harus 0)")
    pv = sorted({r["penyedia"] for r in rows if r["penyedia"]})
    print(f"Penyedia: {', '.join(pv)} (harus satu)")
    if cost:
        print(f"Biaya run ini: ${cost:.4f}")


if __name__ == "__main__":
    main()
