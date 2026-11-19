"""
analisis.py — Analisis hasil eksperimen untuk Bab 4.

Metode (disepakati 19 Nov 2026):
  * Deskriptif : Execution Accuracy (EX, %) per 9 kombinasi skema x metadata.
  * Inferensial: regresi logistik dengan koreksi pengelompokan per soal (GEE,
    korelasi exchangeable), karena 100 soal yang sama dipakai di 9 kondisi.
      RM1  pengaruh model skema    -> uji Wald faktor skema (model efek utama)
      RM2  pengaruh metadata       -> uji Wald faktor metadata (model efek utama)
      RM3  interaksi skema x meta  -> uji Wald suku interaksi (model interaksi)
    Odds ratio (OR) + selang kepercayaan 95% untuk setiap pasangan level;
    p dan selang pasangan dikoreksi Bonferroni (3 pasangan per faktor), sehingga
    "selang tidak memuat 1" <=> "p terkoreksi < 0,05" (selalu konsisten).
    Aturan baca: p < 0,05 -> terbukti; OR > 1 -> peluang benar naik.

Pakai:
  python analisis/analisis.py hasil/penuh_<model>.csv
Keluaran (folder analisis/output/):
  laporan.md, tabel_*.csv, gambar_4_1_interaksi.png, gambar_4_2_odds_ratio.png
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

warnings.filterwarnings("ignore")
SKEMA = ["oltp", "star", "snowflake"]
NAMA_SKEMA = {"oltp": "S1 OLTP", "star": "S2 Star", "snowflake": "S3 Snowflake"}
META = ["M1", "M2", "M3"]
TINGKAT = ["L1", "L2", "L3", "L4"]
ALPHA = 0.05
Z_BONF = float(stats.norm.ppf(1 - ALPHA / 2 / 3))  # 2,394


def zb(k):
    return float(stats.norm.ppf(1 - ALPHA / 2 / k))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def fmt(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def fp(p):
    return "< 0,001" if p < 0.001 else fmt(p, 3)


def holm(ps):  # tidak dipakai lagi; disimpan sebagai cadangan
    ps = np.asarray(ps, float)
    order = np.argsort(ps)
    adj = np.empty_like(ps)
    run = 0.0
    for k, i in enumerate(order):
        run = max(run, (len(ps) - k) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def load(path):
    df = pd.read_csv(path)
    df = df[df["status"] != "api_error"].copy()
    df["benar"] = df["benar"].astype(int)
    df["skema"] = pd.Categorical(df["skema"], SKEMA)
    global META
    META = [m for m in ["M1", "M2", "M3"] if m in set(df["metadata"])]
    df["meta"] = pd.Categorical(df["metadata"], META)
    df["soal"] = df["id"]
    n = df.groupby(["skema", "meta"], observed=False).size()
    if (n == 0).any():
        print("PERINGATAN: ada kombinasi tanpa data:\n", n[n == 0])
    return df


def gee(formula, df):
    return smf.gee(formula, groups="soal", data=df, family=sm.families.Binomial(),
                   cov_struct=sm.cov_struct.Exchangeable()).fit()


def wald(res, key):
    names = [n for n in res.params.index if key(n)]
    R = np.zeros((len(names), len(res.params)))
    for k, n in enumerate(names):
        R[k, list(res.params.index).index(n)] = 1
    w = res.wald_test(R, scalar=True)
    return float(w.statistic), int(len(names)), float(w.pvalue)


def contrast(res, a, b):
    """log-OR level a vs level b (nama parameter; None = level acuan)."""
    idx = list(res.params.index)
    c = np.zeros(len(idx))
    if a:
        c[idx.index(a)] += 1
    if b:
        c[idx.index(b)] -= 1
    est = float(c @ res.params.values)
    se = float(np.sqrt(c @ res.cov_params().values @ c))
    z = est / se
    p = 2 * stats.norm.sf(abs(z))
    return est, se, p


def main():
    global META
    if len(sys.argv) < 2:
        sys.exit("Pakai: python analisis/analisis.py hasil/<file>.csv")
    os.makedirs(OUT, exist_ok=True)
    df = load(sys.argv[1])
    L = ["# Hasil Analisis (dibangkitkan otomatis)", "",
         f"Sumber: `{sys.argv[1]}` — {len(df)} jawaban, {df['soal'].nunique()} soal.", ""]

    # ---------------- 1. Deskriptif ----------------
    ex = df.pivot_table(index="skema", columns="meta", values="benar", aggfunc="mean", observed=False) * 100
    ex["Rata-rata skema"] = df.groupby("skema", observed=False)["benar"].mean() * 100
    ex.loc["Rata-rata metadata"] = list(df.groupby("meta", observed=False)["benar"].mean() * 100) + [df["benar"].mean() * 100]
    ex.index = [NAMA_SKEMA.get(i, i) for i in ex.index]
    ex.round(1).to_csv(os.path.join(OUT, "tabel_akurasi.csv"))
    L += ["## Tabel 4.1 Akurasi eksekusi (%) per kombinasi", "",
          "| Model skema | " + " | ".join(META) + " | Rata-rata skema |", "|---" * (len(META) + 2) + "|"]
    for i, r in ex.iterrows():
        L.append(f"| {i} | " + " | ".join(fmt(v, 1) for v in r.values) + " |")
    cell = df.groupby(["skema", "meta"], observed=False)["benar"].mean()
    ekstrem = [f"{NAMA_SKEMA[a]}+{b} = {v * 100:.0f}%" for (a, b), v in cell.items() if v in (0.0, 1.0)]
    best = cell.idxmax()
    L += ["", f"Kombinasi terbaik: {NAMA_SKEMA[best[0]]} + {best[1]}.", ""]

    # ---------------- 2. Regresi logistik ----------------
    m_main = gee("benar ~ C(skema) + C(meta)", df)
    m_int = gee("benar ~ C(skema) * C(meta)", df)
    w_s = wald(m_main, lambda n: n.startswith("C(skema)"))
    w_m = wald(m_main, lambda n: n.startswith("C(meta)"))
    w_i = wald(m_int, lambda n: ":" in n)
    uji = [("RM1 Model skema", *w_s), ("RM2 Kelengkapan metadata", *w_m), ("RM3 Interaksi skema × metadata", *w_i)]
    pd.DataFrame(uji, columns=["faktor", "chi2", "df", "p"]).to_csv(os.path.join(OUT, "tabel_uji_faktor.csv"), index=False)
    if ekstrem:
        L += ["> **PERINGATAN:** ada kombinasi dengan akurasi 0% atau 100% (" + "; ".join(ekstrem) + "). "
              "Regresi logistik tidak dapat menaksir pengaruh dengan wajar pada sel seperti ini "
              "(*ceiling/floor effect*), sehingga nilai χ² dan OR yang melibatkan sel tersebut tidak dapat dipercaya.", ""]
    L += ["## Tabel 4.2 Uji pengaruh keseluruhan (regresi logistik GEE, uji Wald)", "",
          "| Faktor | χ² | df | p | Kesimpulan |", "|---|---|---|---|---|"]
    for f, c, d, p in uji:
        L.append(f"| {f} | {fmt(c)} | {d} | {fp(p)} | {'**Terbukti**' if p < ALPHA else 'Belum terbukti'} |")

    # pasangan (model efek utama), koreksi Holm per faktor
    ps = {"oltp": None, "star": "C(skema)[T.star]", "snowflake": "C(skema)[T.snowflake]"}
    pm = {m: (None if m == META[0] else f"C(meta)[T.{m}]") for m in META}
    pairs = [("RM1", NAMA_SKEMA[a], NAMA_SKEMA[b], ps[a], ps[b]) for a, b in
             [("star", "oltp"), ("snowflake", "oltp"), ("star", "snowflake")]]
    pairs += [("RM2", a, b, pm[a], pm[b]) for a, b in [("M2", "M1"), ("M3", "M1"), ("M3", "M2")]
              if a in pm and b in pm]
    rows = []
    for grp in ("RM1", "RM2"):
        sub = [p for p in pairs if p[0] == grp]
        res = [contrast(m_main, p[3], p[4]) for p in sub]
        adj = [min(1.0, len(sub) * r[2]) for r in res]
        for p, r, pa in zip(sub, res, adj):
            est, se, _ = r
            rows.append(dict(rm=grp, banding=f"{p[1]} vs {p[2]}", OR=np.exp(est),
                             lo=np.exp(est - zb(len(sub)) * se), hi=np.exp(est + zb(len(sub)) * se), p_terkoreksi=pa))
    orr = pd.DataFrame(rows)
    orr.to_csv(os.path.join(OUT, "tabel_odds_ratio.csv"), index=False)
    L += ["", "## Tabel 4.3 Odds ratio per pasangan (p dan selang dikoreksi Bonferroni)", "",
          "| RM | Perbandingan | OR | Selang 95% | p terkoreksi | Kesimpulan |", "|---|---|---|---|---|---|"]
    for _, r in orr.iterrows():
        sig_faktor = (w_s if r.rm == "RM1" else w_m)[2] < ALPHA
        ket = "**Terbukti**" if (r.p_terkoreksi < ALPHA and sig_faktor) else (
            "Kecenderungan (faktor keseluruhan tidak signifikan)" if r.p_terkoreksi < ALPHA else "Belum terbukti")
        L.append(f"| {r.rm} | {r.banding} | {fmt(r.OR)} | {fmt(r.lo)}–{fmt(r.hi)} | {fp(r.p_terkoreksi)} | {ket} |")
    L += ["", "Aturan baca: lihat Tabel 4.2 dulu; pasangan hanya disimpulkan bila faktornya terbukti. "
          "OR > 1 berarti peluang menjawab benar lebih besar pada kondisi pertama.", ""]

    # RM3 deskriptif: kenaikan M1 -> M3 per skema
    L += ["## Tabel 4.4 Kenaikan akurasi M1 → M3 per skema (pendukung RM3)", "",
          "| Model skema | M1 | M3 | Kenaikan (poin) | Tertolong | Terganggu |", "|---|---|---|---|---|---|"]
    w = df.pivot_table(index=["soal", "skema"], columns="meta", values="benar", observed=False).reset_index()
    lo_m, hi_m = META[0], META[-1]
    for s in SKEMA:
        x = w[w["skema"] == s]
        a, b = x[lo_m].mean() * 100, x[hi_m].mean() * 100
        tol = int(((x[lo_m] == 0) & (x[hi_m] == 1)).sum())
        gg = int(((x[lo_m] == 1) & (x[hi_m] == 0)).sum())
        L.append(f"| {NAMA_SKEMA[s]} | {fmt(a, 1)} | {fmt(b, 1)} | {fmt(b - a, 1)} | {tol} | {gg} |")

    # ---------------- 3. Temuan pendukung ----------------
    if "tingkat" in df:
        t = df.pivot_table(index="tingkat", columns="meta", values="benar", aggfunc="mean", observed=False) * 100
        L += ["", "## Tabel 4.5 Akurasi (%) per tingkat kesulitan", "", "| Tingkat | " + " | ".join(META) + " |", "|---" * (len(META) + 1) + "|"]
        for i, r in t.reindex([x for x in TINGKAT if x in t.index]).iterrows():
            L.append(f"| {i} | " + " | ".join(fmt(v, 1) for v in r.values) + " |")
    if "butuh_glosarium" in df:
        g = df.pivot_table(index="butuh_glosarium", columns="meta", values="benar", aggfunc="mean", observed=False) * 100
        L += ["", "## Tabel 4.6 Akurasi (%) menurut pemakaian istilah bisnis", "",
              "| Butuh glosarium | " + " | ".join(META) + " |", "|---" * (len(META) + 1) + "|"]
        for i, r in g.iterrows():
            L.append(f"| {i} | " + " | ".join(fmt(v, 1) for v in r.values) + " |")
    st = df.pivot_table(index="status", columns="skema", values="benar", aggfunc="size", fill_value=0, observed=False)
    L += ["", "## Tabel 4.7 Status jawaban per skema (jumlah)", "",
          "| Status | " + " | ".join(NAMA_SKEMA[s] for s in SKEMA) + " |", "|---|---|---|---|"]
    for i, r in st.iterrows():
        L.append(f"| {i} | " + " | ".join(str(int(r.get(s, 0))) for s in SKEMA) + " |")

    # ---------------- 4. Gambar ----------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        sty = {"oltp": ("-", "o"), "star": ("--", "s"), "snowflake": (":", "^")}
        for s in SKEMA:
            y = [df[(df.skema == s) & (df.meta == m)]["benar"].mean() * 100 for m in META]
            ax.plot(META, y, linestyle=sty[s][0], marker=sty[s][1], color="black", label=NAMA_SKEMA[s])
        ax.set_ylabel("Execution Accuracy (%)")
        ax.set_xlabel("Kelengkapan metadata")
        ax.legend(frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "gambar_4_1_interaksi.png"))
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 3.2), dpi=150)
        yy = range(len(orr))[::-1]
        ax.errorbar(orr["OR"], list(yy), xerr=[orr["OR"] - orr["lo"], orr["hi"] - orr["OR"]],
                    fmt="o", color="black", capsize=3)
        ax.axvline(1, linestyle="--", color="gray")
        ax.set_xscale("log")
        from matplotlib.ticker import FixedLocator, NullLocator
        tk = [0.5, 0.75, 1, 1.5, 2, 3, 4, 6]
        tk = [t for t in tk if orr["lo"].min() / 1.2 <= t <= orr["hi"].max() * 1.2] or [1]
        ax.xaxis.set_major_locator(FixedLocator(tk))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([str(t).replace(".", ",") for t in tk])
        ax.set_yticks(list(yy))
        ax.set_yticklabels(orr["banding"])
        ax.set_xlabel("Odds ratio (skala log), garis putus = 1")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "gambar_4_2_odds_ratio.png"))
        plt.close(fig)
        L += ["", "Gambar: `gambar_4_1_interaksi.png`, `gambar_4_2_odds_ratio.png`."]
    except ImportError:
        L += ["", "(matplotlib tidak terpasang: gambar tidak dibuat)"]

    # ---------------- 5. Kesimpulan otomatis ----------------
    kal = []
    for (f, c, d, p), nama in zip(uji, ["model skema", "kelengkapan metadata", "interaksi model skema dan metadata"]):
        kal.append(f"- {'Terbukti' if p < ALPHA else 'Belum terbukti'} bahwa {nama} berpengaruh terhadap akurasi "
                   f"(χ²({d}) = {fmt(c)}; p {fp(p) if p < 0.001 else '= ' + fp(p)}).")
    L += ["", "## Ringkasan untuk Bab 5", ""] + kal
    with open(os.path.join(OUT, "laporan.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nTersimpan di {OUT}")


if __name__ == "__main__":
    main()
