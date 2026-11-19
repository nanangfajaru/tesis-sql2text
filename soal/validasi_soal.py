"""
validasi_soal.py — Membangkitkan soal.csv (100 soal x 3 SQL kunci) dan memvalidasinya.

Pemeriksaan per soal:
  V1 ketiga SQL kunci (OLTP, star, snowflake) bisa dieksekusi
  V2 hasil ketiganya IDENTIK (setelah normalisasi: angka dibulatkan 2 desimal)
  V3 hasil tidak kosong dan <= 100 baris
  V4 tidak ada nilai seri pada kolom pengurut (batas top-N / urutan) -> jawaban pasti
  V5 waktu eksekusi tiap SQL < 5 detik

Pakai (dari folder repo):
  python soal/validasi_soal.py            # koneksi dari .env (PG*), sebaiknya user postgres/pemilik
Keluaran:
  soal/soal.csv, soal/laporan_validasi.md
"""
import csv
import os
import re
import sys
import time
from collections import Counter
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psycopg  # noqa: E402
from sqlgen import render  # noqa: E402
from soal_def import S  # noqa: E402

SCHEMAS = ["oltp", "star", "snowflake"]
HERE = os.path.dirname(os.path.abspath(__file__))
TIE_COL = {"Q092": 1, "Q058": 2, "Q031": 2, "Q072": 2}       # indeks kolom pengurut bila bukan kolom terakhir
RANK_ROWS = {"Q077": 3, "Q086": 9}      # soal ranking per grup: jumlah baris yang diharapkan


def norm_val(v):
    if isinstance(v, (Decimal, float)):
        return f"{round(float(v), 2):.2f}"
    if isinstance(v, int) and not isinstance(v, bool):
        return f"{float(v):.2f}"
    return "NULL" if v is None else str(v)


def norm(rows, ordered):
    r = [tuple(norm_val(v) for v in row) for row in rows]
    return r if ordered else sorted(r)


def run(conn, schema, sql):
    with conn.cursor() as cur:
        cur.execute(f"SET search_path = {schema}")
        t = time.time()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows, time.time() - t


def connect():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(HERE, "..", ".env"))
    except ImportError:
        pass
    return psycopg.connect(autocommit=True)


def main():
    conn = connect()
    hasil, out_rows = [], []
    for s in S:
        sqls = {sc: render(s["sql"], sc) for sc in SCHEMAS}
        msg, res, waktu = [], {}, {}
        for sc in SCHEMAS:
            try:
                res[sc], waktu[sc] = run(conn, sc, sqls[sc])
            except Exception as e:
                msg.append(f"V1 gagal di {sc}: {str(e).splitlines()[0]}")
        if len(res) == 3:
            n = {sc: norm(res[sc], s["urut"]) for sc in SCHEMAS}
            if not (n["oltp"] == n["star"] == n["snowflake"]):
                msg.append("V2 hasil berbeda antar-skema")
            rows = res["star"]
            if not rows:
                msg.append("V3 hasil kosong")
            if len(rows) > 100:
                msg.append(f"V3 {len(rows)} baris (>100)")
            if len(rows) == 1 and all(v is None for v in rows[0]):
                msg.append("V3 hasil NULL")
            # V4 seri
            col = TIE_COL.get(s["id"], -1)
            sql_star = sqls["star"]
            m = re.search(r"LIMIT (\d+)\s*$", sql_star)
            if m:
                k = int(m.group(1))
                more, _ = run(conn, "star", sql_star[:m.start()] + f"LIMIT {k + 1}")
                if len(more) > k and norm_val(more[k - 1][col]) == norm_val(more[k][col]):
                    msg.append(f"V4 seri di batas top-{k}: {more[k - 1][col]}")
            if s["urut"] and re.search(r"ORDER BY \w+ (DESC|ASC)", sql_star):
                vals = [norm_val(r[col]) for r in rows]
                if any(a == b for a, b in zip(vals, vals[1:])):
                    msg.append("V4 seri pada urutan")
            if s["id"] in RANK_ROWS and len(rows) != RANK_ROWS[s["id"]]:
                msg.append(f"V4 ranking seri: {len(rows)} baris (harap {RANK_ROWS[s['id']]})")
            slow = [f"{sc} {w:.1f}s" for sc, w in waktu.items() if w >= 5]
            if slow:
                msg.append("V5 lambat: " + ", ".join(slow))
        status = "OK" if not msg else "GAGAL"
        hasil.append((s, status, msg, res.get("star"), waktu))
        out_rows.append({
            "id": s["id"], "tingkat": s["tingkat"], "topik": s["topik"],
            "butuh_glosarium": "ya" if s["glos"] else "tidak", "pertanyaan": s["q"],
            "sql_oltp": sqls["oltp"], "sql_star": sqls["star"], "sql_snowflake": sqls["snowflake"],
            "urutan_penting": "ya" if s["urut"] else "tidak",
            "jumlah_baris": len(res["star"]) if "star" in res else "",
            "catatan": "; ".join(msg),
        })
        print(f"{s['id']} {s['tingkat']} {status} {'; '.join(msg)}")

    with open(os.path.join(HERE, "soal.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)

    # ---------- laporan ----------
    ok = sum(1 for h in hasil if h[1] == "OK")
    tk = Counter(s["tingkat"] for s in S)
    gl = Counter((s["tingkat"], s["glos"]) for s in S)
    tp = Counter(t for s in S for t in s["topik"].split(","))
    L = ["# Laporan Validasi Soal", "",
         f"Lulus semua pemeriksaan (V1–V5): **{ok}/{len(S)}**", "",
         "| Tingkat | Jumlah | butuh_glosarium = ya |", "|---|---|---|"]
    for t in sorted(tk):
        L.append(f"| {t} | {tk[t]} | {gl[(t, True)]} |")
    L.append(f"| **Total** | **{len(S)}** | **{sum(s['glos'] for s in S)}** |")
    L += ["", "Cakupan topik (satu soal bisa >1 topik): " + ", ".join(f"{k} {v}" for k, v in sorted(tp.items())), "",
          "| ID | Tingkat | Glosarium | Baris | Waktu maks (dtk) | Status | Pertanyaan | Cuplikan jawaban (star) |",
          "|---|---|---|---|---|---|---|---|"]
    for s, st, msg, rows, waktu in hasil:
        cup = "" if rows is None else "; ".join(" | ".join(norm_val(v) for v in r) for r in rows[:3])
        if rows and len(rows) > 3:
            cup += " …"
        wm = f"{max(waktu.values()):.2f}" if waktu else "-"
        L.append(f"| {s['id']} | {s['tingkat']} | {'ya' if s['glos'] else 'tidak'} | "
                 f"{len(rows) if rows is not None else '-'} | {wm} | {st}{(' — ' + '; '.join(msg)) if msg else ''} | "
                 f"{s['q']} | {cup} |")
    with open(os.path.join(HERE, "laporan_validasi.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"\nLULUS {ok}/{len(S)}")


if __name__ == "__main__":
    main()
