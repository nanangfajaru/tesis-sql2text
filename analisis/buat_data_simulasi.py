"""
buat_data_simulasi.py — Membuat CSV hasil eksperimen BUATAN (acak) dengan format
yang sama dengan eksperimen/jalankan.py, untuk mencoba analisis.py sebelum data
asli tersedia. JANGAN dipakai sebagai hasil penelitian.

  python analisis/buat_data_simulasi.py      -> hasil/simulasi.csv
"""
import csv
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(7)
SK = {"oltp": 0.0, "star": 0.6, "snowflake": 0.2}
MT = {"M1": 0.0, "M2": 0.4, "M3": 1.6}
LV = {"L1": 1.5, "L2": 0.3, "L3": -0.8, "L4": -2.2}

with open(os.path.join(ROOT, "soal", "soal.csv"), encoding="utf-8") as f:
    soal = list(csv.DictReader(f))
os.makedirs(os.path.join(ROOT, "hasil"), exist_ok=True)
with open(os.path.join(ROOT, "hasil", "simulasi.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["run", "id", "tingkat", "butuh_glosarium", "skema", "metadata", "status", "benar"])
    w.writeheader()
    for s in soal:
        d = LV[s["tingkat"]] + random.gauss(0, 0.8)
        for sk, es in SK.items():
            for m, em in MT.items():
                p = 1 / (1 + math.exp(-(d + es + em - 0.3)))
                b = int(random.random() < p)
                st = "benar" if b else random.choice(["hasil_salah"] * 4 + ["error_eksekusi"])
                w.writerow(dict(run="simulasi", id=s["id"], tingkat=s["tingkat"], butuh_glosarium=s["butuh_glosarium"],
                                skema=sk, metadata=m, status=st, benar=b))
print("hasil/simulasi.csv dibuat (DATA BUATAN)")
