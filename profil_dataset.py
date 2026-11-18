"""
profil_dataset.py
Memeriksa (profiling) semua file CSV di satu folder dan menulis laporan
ringkas ke file 'profil_dataset.md'. Data tidak diubah sama sekali.

Cara pakai:
    python profil_dataset.py <folder_berisi_csv>

Contoh (Windows):
    python profil_dataset.py C:\\tesis\\data

Kebutuhan: Python 3.9+ dan paket duckdb & pandas  ->  pip install duckdb pandas
"""

import glob
import os
import sys
import time

import duckdb


def q(con, sql):
    return con.execute(sql).fetchall()


def esc(path):
    return path.replace("\\", "/").replace("'", "''")


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        print(f"Tidak ada file .csv di folder: {folder}")
        sys.exit(1)

    con = duckdb.connect()
    lines = ["# Profil Dataset", "", f"Folder: `{folder}`", f"Waktu: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    tables = []

    # 1. Muat setiap CSV sebagai view
    for f in files:
        t = os.path.splitext(os.path.basename(f))[0].replace("-", "_").replace(" ", "_").lower()
        size_mb = os.path.getsize(f) / 1024 / 1024
        con.execute(f"CREATE VIEW \"{t}\" AS SELECT * FROM read_csv_auto('{esc(f)}', sample_size=-1)")
        tables.append((t, os.path.basename(f), size_mb))
        print(f"Membaca {os.path.basename(f)} ...")

    lines += ["## Ringkasan file", "", "| Tabel | File | Ukuran (MB) | Jumlah baris | Jumlah kolom |", "|---|---|---|---|---|"]
    info = {}
    for t, fname, size_mb in tables:
        n = q(con, f'SELECT COUNT(*) FROM "{t}"')[0][0]
        cols = q(con, f'DESCRIBE "{t}"')
        info[t] = {"rows": n, "cols": [(c[0], c[1]) for c in cols]}
        lines.append(f"| {t} | {fname} | {size_mb:.1f} | {n:,} | {len(cols)} |")
    lines.append("")

    # 2. Detail per tabel
    for t, fname, _ in tables:
        print(f"Memprofil {t} ...")
        lines += [f"## Tabel `{t}` ({info[t]['rows']:,} baris)", "",
                  "| Kolom | Tipe | Null (%) | Nilai unik (perkiraan) | Min | Max |", "|---|---|---|---|---|---|"]
        summ = con.execute(f'SUMMARIZE "{t}"').fetchdf()
        for _, r in summ.iterrows():
            mn = str(r["min"])[:40] if r["min"] is not None else ""
            mx = str(r["max"])[:40] if r["max"] is not None else ""
            lines.append(f"| {r['column_name']} | {r['column_type']} | {r['null_percentage']} | "
                         f"{r['approx_unique']} | {mn} | {mx} |")
        lines += ["", "Contoh 3 baris:", "", "```"]
        sample = con.execute(f'SELECT * FROM "{t}" LIMIT 3').fetchdf()
        lines.append(sample.to_string(max_colwidth=40))
        lines += ["```", ""]

        # Nilai kategori untuk kolom teks dengan sedikit nilai unik
        for c, typ in info[t]["cols"]:
            if "VARCHAR" in typ.upper() and not c.lower().endswith("_id"):
                k = q(con, f'SELECT COUNT(DISTINCT "{c}") FROM "{t}"')[0][0]
                if 1 < k <= 30:
                    vals = q(con, f'SELECT "{c}", COUNT(*) FROM "{t}" GROUP BY 1 ORDER BY 2 DESC')
                    lines.append(f"- Nilai `{c}` ({k} kategori): " +
                                 ", ".join(f"{v} ({cnt:,})" for v, cnt in vals))
        lines.append("")

    # 3. Kandidat primary key & cek relasi (foreign key) untuk kolom *_id
    print("Memeriksa kunci dan relasi ...")
    lines += ["## Kandidat primary key (kolom *_id yang unik)", ""]
    pk = {}
    for t, _, _ in tables:
        for c, _ in info[t]["cols"]:
            if c.lower().endswith("_id") or c.lower() == "id":
                nn, nd = q(con, f'SELECT COUNT("{c}"), COUNT(DISTINCT "{c}") FROM "{t}"')[0]
                nulls = info[t]["rows"] - nn
                unique = (nn == nd and nulls == 0)
                if unique:
                    pk.setdefault(c, []).append(t)
                lines.append(f"- `{t}.{c}`: {nd:,} nilai unik dari {info[t]['rows']:,} baris, "
                             f"null {nulls:,} -> {'UNIK (kandidat PK)' if unique else 'tidak unik'}")
    lines.append("")

    lines += ["## Cek relasi (baris yatim = nilai yang tidak ditemukan di tabel induk)", "",
              "| Tabel anak.kolom | Tabel induk | Baris yatim |", "|---|---|---|"]
    for col, parents in pk.items():
        for parent in parents:
            for t, _, _ in tables:
                if t == parent:
                    continue
                if col in [c for c, _ in info[t]["cols"]]:
                    orphan = q(con, f'SELECT COUNT(*) FROM "{t}" a WHERE a."{col}" IS NOT NULL AND NOT EXISTS '
                                    f'(SELECT 1 FROM "{parent}" b WHERE b."{col}" = a."{col}")')[0][0]
                    lines.append(f"| {t}.{col} | {parent} | {orphan:,} |")
    lines.append("")

    out = os.path.join(os.getcwd(), "profil_dataset.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"\nSelesai. Laporan tersimpan di: {out}")
    print("Unggah file tersebut ke chat.")


if __name__ == "__main__":
    main()
