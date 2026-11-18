"""
soal_def.py — Definisi 100 soal (Bahasa Indonesia) + template SQL kunci.

Kolom tiap soal:
  id, tingkat (L1-L4), topik, glos (butuh_glosarium), q (pertanyaan),
  sql (template; lihat sqlgen.py), urut (urutan baris penting?)

Topik: waktu, produk, pelanggan, penjual, pengiriman, status.
Aturan glosarium: glos=True bila jawaban bergantung pada definisi/pemetaan yang
hanya ada di metadata M2: omzet/nilai penjualan, pelanggan unik, AOV, lama
pengiriman, terlambat, pelanggan baru, nama kategori Bahasa Indonesia, nama
lengkap negara bagian, format nama kota.
"""

S = []


def q(id, tingkat, topik, glos, teks, sql, urut=False):
    S.append(dict(id=id, tingkat=tingkat, topik=topik, glos=glos, q=teks, sql=sql.strip(), urut=urut))


# =====================================================================
# L1 — MUDAH: 1 ukuran agregat, <=1 dimensi, <=1 filter
# =====================================================================
q("Q001", "L1", "status", False,
  "Berapa jumlah pesanan yang dibatalkan?",
  "SELECT COUNT(DISTINCT {order}) FROM {FROM} WHERE {status} = 'canceled'")
q("Q002", "L1", "pengiriman,waktu", False,
  "Berapa total ongkos kirim seluruh item yang dibeli pada tahun 2017?",
  "SELECT ROUND(SUM({freight}), 2) FROM {FROM} WHERE {year} = 2017")
q("Q003", "L1", "waktu", False,
  "Berapa jumlah item yang terjual pada bulan Desember 2017?",
  "SELECT COUNT(*) FROM {FROM} WHERE {year} = 2017 AND {month} = 12")
q("Q004", "L1", "waktu", True,
  "Berapa omzet total pada tahun 2018?",
  "SELECT ROUND(SUM({total}), 2) FROM {FROM} WHERE {year} = 2018")
q("Q005", "L1", "produk", False,
  "Berapa harga barang tertinggi untuk satu item yang pernah terjual?",
  "SELECT MAX({price}) FROM {FROM}")
q("Q006", "L1", "pengiriman", False,
  "Berapa rata-rata ongkos kirim per item?",
  "SELECT ROUND(AVG({freight}), 2) FROM {FROM}")
q("Q007", "L1", "pelanggan,waktu", True,
  "Berapa jumlah pelanggan unik yang berbelanja pada tahun 2017?",
  "SELECT COUNT(DISTINCT {cust}) FROM {FROM} WHERE {year} = 2017")
q("Q008", "L1", "penjual", False,
  "Ada berapa penjual berbeda yang pernah menjual barang?",
  "SELECT COUNT(DISTINCT {seller}) FROM {FROM}")
q("Q009", "L1", "produk,waktu", False,
  "Berapa jumlah produk berbeda yang terjual pada kuartal kedua tahun 2018?",
  "SELECT COUNT(DISTINCT {product}) FROM {FROM} WHERE {year} = 2018 AND {quarter} = 2")
q("Q010", "L1", "pelanggan", False,
  "Berapa jumlah pesanan yang dibuat oleh pelanggan dari negara bagian RJ?",
  "SELECT COUNT(DISTINCT {order}) FROM {FROM} WHERE {cstate} = 'RJ'")
q("Q011", "L1", "penjual", True,
  "Berapa jumlah penjual yang berlokasi di negara bagian Parana?",
  "SELECT COUNT(DISTINCT {seller}) FROM {FROM} WHERE {sstate} = 'PR'")
q("Q012", "L1", "produk", True,
  "Berapa total nilai barang, tanpa ongkos kirim, dari kategori kesehatan dan kecantikan?",
  "SELECT ROUND(SUM({price}), 2) FROM {FROM} WHERE {cat} = 'health_beauty'")
q("Q013", "L1", "waktu", False,
  "Berapa jumlah item yang dibeli pada hari Minggu?",
  "SELECT COUNT(*) FROM {FROM} WHERE {dow} = 7")
q("Q014", "L1", "waktu", False,
  "Berapa jumlah pesanan yang dibuat pada akhir pekan selama tahun 2017?",
  "SELECT COUNT(DISTINCT {order}) FROM {FROM} WHERE {weekend} AND {year} = 2017")
q("Q015", "L1", "status", False,
  "Berapa jumlah pesanan yang statusnya masih dalam pengiriman?",
  "SELECT COUNT(DISTINCT {order}) FROM {FROM} WHERE {status} = 'shipped'")
q("Q016", "L1", "produk", False,
  "Berapa rata-rata berat produk dalam gram per item yang terjual?",
  "SELECT ROUND(AVG({weight}), 2) FROM {FROM}")
q("Q017", "L1", "produk,waktu", True,
  "Berapa jumlah item kategori mainan yang terjual pada tahun 2018?",
  "SELECT COUNT(*) FROM {FROM} WHERE {cat} = 'toys' AND {year} = 2018")
q("Q018", "L1", "pelanggan", True,
  "Berapa jumlah pelanggan unik yang tinggal di kota Curitiba?",
  "SELECT COUNT(DISTINCT {cust}) FROM {FROM} WHERE {ccity} = 'curitiba'")
q("Q019", "L1", "pengiriman", False,
  "Berapa ongkos kirim paling mahal untuk satu item?",
  "SELECT MAX({freight}) FROM {FROM}")
q("Q020", "L1", "waktu", False,
  "Berapa jumlah pesanan pada bulan Januari 2018?",
  "SELECT COUNT(DISTINCT {order}) FROM {FROM} WHERE {year} = 2018 AND {month} = 1")
q("Q021", "L1", "penjual,waktu", False,
  "Berapa total harga barang yang dijual oleh penjual dari negara bagian SP pada tahun 2018?",
  "SELECT ROUND(SUM({price}), 2) FROM {FROM} WHERE {sstate} = 'SP' AND {year} = 2018")
q("Q022", "L1", "pengiriman", False,
  "Berapa jumlah item yang belum diterima oleh pelanggan (tanggal diterima masih kosong)?",
  "SELECT COUNT(*) FROM {FROM} WHERE {ddate} IS NULL")
q("Q023", "L1", "status", True,
  "Berapa omzet dari pesanan yang dibatalkan?",
  "SELECT ROUND(SUM({total}), 2) FROM {FROM} WHERE {status} = 'canceled'")
q("Q024", "L1", "produk", True,
  "Berapa jumlah produk berbeda dalam kategori parfum yang pernah terjual?",
  "SELECT COUNT(DISTINCT {product}) FROM {FROM} WHERE {cat} = 'perfumery'")
q("Q025", "L1", "produk,waktu", False,
  "Berapa rata-rata harga barang per item pada kuartal keempat tahun 2017?",
  "SELECT ROUND(AVG({price}), 2) FROM {FROM} WHERE {year} = 2017 AND {quarter} = 4")

# =====================================================================
# L2 — SEDANG: GROUP BY + ORDER BY/LIMIT, 1-2 dimensi, filter waktu
# =====================================================================
q("Q026", "L2", "waktu", False,
  "Tampilkan nomor bulan dan jumlah pesanan untuk setiap bulan pada tahun 2017, urutkan dari Januari.",
  "SELECT {month}, COUNT(DISTINCT {order}) FROM {FROM} WHERE {year} = 2017 GROUP BY 1 ORDER BY 1", urut=True)
q("Q027", "L2", "pelanggan,waktu", True,
  "Sebutkan 5 negara bagian pelanggan dengan omzet terbesar pada tahun 2017 beserta omzetnya.",
  "SELECT {cstate}, ROUND(SUM({total}), 2) AS omzet FROM {FROM} WHERE {year} = 2017 "
  "GROUP BY 1 ORDER BY omzet DESC LIMIT 5", urut=True)
q("Q028", "L2", "produk", False,
  "Sebutkan 10 kategori produk dengan jumlah item terjual terbanyak beserta jumlah itemnya.",
  "SELECT {cat}, COUNT(*) AS n FROM {FROM} GROUP BY 1 ORDER BY n DESC LIMIT 10", urut=True)
q("Q029", "L2", "pengiriman,waktu", False,
  "Tampilkan nomor kuartal dan total ongkos kirim untuk setiap kuartal tahun 2018, urutkan per kuartal.",
  "SELECT {quarter}, ROUND(SUM({freight}), 2) FROM {FROM} WHERE {year} = 2018 GROUP BY 1 ORDER BY 1", urut=True)
q("Q030", "L2", "status", False,
  "Tampilkan setiap status pesanan beserta jumlah itemnya, urutkan dari yang terbanyak.",
  "SELECT {status}, COUNT(*) AS n FROM {FROM} GROUP BY 1 ORDER BY n DESC", urut=True)
q("Q031", "L2", "penjual,waktu", False,
  "Sebutkan 5 kota penjual dengan jumlah item terjual terbanyak pada tahun 2018 beserta jumlah itemnya.",
  "SELECT {scity}, COUNT(*) AS n FROM {FROM} WHERE {year} = 2018 GROUP BY 1 ORDER BY n DESC LIMIT 5", urut=True)
q("Q032", "L2", "waktu", False,
  "Untuk tahun 2017, tampilkan nomor hari dalam seminggu (1 = Senin sampai 7 = Minggu) dan jumlah pesanannya, urutkan dari Senin.",
  "SELECT {dow}, COUNT(DISTINCT {order}) FROM {FROM} WHERE {year} = 2017 GROUP BY 1 ORDER BY 1", urut=True)
q("Q033", "L2", "penjual,produk", False,
  "Sebutkan 5 negara bagian penjual dengan rata-rata harga barang per item tertinggi beserta rata-ratanya.",
  "SELECT {sstate}, ROUND(AVG({price}), 2) AS r FROM {FROM} GROUP BY 1 ORDER BY r DESC LIMIT 5", urut=True)
q("Q034", "L2", "produk,pengiriman,waktu", False,
  "Sebutkan 3 kategori produk dengan total ongkos kirim terbesar pada bulan November 2017 beserta totalnya.",
  "SELECT {cat}, ROUND(SUM({freight}), 2) AS x FROM {FROM} WHERE {year} = 2017 AND {month} = 11 "
  "GROUP BY 1 ORDER BY x DESC LIMIT 3", urut=True)
q("Q035", "L2", "pelanggan,waktu", True,
  "Tampilkan jumlah pelanggan unik untuk setiap tahun, urutkan per tahun.",
  "SELECT {year}, COUNT(DISTINCT {cust}) FROM {FROM} GROUP BY 1 ORDER BY 1", urut=True)
q("Q036", "L2", "pelanggan,waktu", False,
  "Sebutkan 5 negara bagian pelanggan dengan jumlah pesanan paling sedikit pada tahun 2018 beserta jumlah pesanannya, mulai dari yang paling sedikit.",
  "SELECT {cstate}, COUNT(DISTINCT {order}) AS n FROM {FROM} WHERE {year} = 2018 GROUP BY 1 ORDER BY n ASC LIMIT 5", urut=True)
q("Q037", "L2", "waktu", True,
  "Tampilkan nomor bulan dan omzet setiap bulan dari Januari sampai Juni 2018.",
  "SELECT {month}, ROUND(SUM({total}), 2) FROM {FROM} WHERE {year} = 2018 AND {month} BETWEEN 1 AND 6 "
  "GROUP BY 1 ORDER BY 1", urut=True)
q("Q038", "L2", "waktu", False,
  "Pada tahun 2018, berapa jumlah item yang dibeli pada akhir pekan dan berapa yang dibeli pada hari kerja? Tampilkan penanda akhir pekan (benar/salah) dan jumlah itemnya.",
  "SELECT {weekend}, COUNT(*) FROM {FROM} WHERE {year} = 2018 GROUP BY 1")
q("Q039", "L2", "produk,waktu", False,
  "Sebutkan 5 kategori produk dengan rata-rata harga barang per item tertinggi pada tahun 2017 beserta rata-ratanya.",
  "SELECT {cat}, ROUND(AVG({price}), 2) AS r FROM {FROM} WHERE {year} = 2017 GROUP BY 1 ORDER BY r DESC LIMIT 5", urut=True)
q("Q040", "L2", "penjual,waktu", False,
  "Sebutkan ID 10 penjual dengan total harga barang terjual terbesar pada tahun 2017 beserta totalnya.",
  "SELECT {seller}, ROUND(SUM({price}), 2) AS x FROM {FROM} WHERE {year} = 2017 GROUP BY 1 ORDER BY x DESC LIMIT 10", urut=True)
q("Q041", "L2", "pelanggan,produk", True,
  "Untuk kategori jam tangan dan hadiah, sebutkan 5 negara bagian pelanggan dengan jumlah pesanan terbanyak beserta jumlah pesanannya.",
  "SELECT {cstate}, COUNT(DISTINCT {order}) AS n FROM {FROM} WHERE {cat} = 'watches_gifts' "
  "GROUP BY 1 ORDER BY n DESC LIMIT 5", urut=True)
q("Q042", "L2", "pelanggan,produk", True,
  "Untuk pelanggan dari negara bagian Minas Gerais, sebutkan 5 kategori produk dengan total nilai barang (tanpa ongkir) terbesar beserta totalnya.",
  "SELECT {cat}, ROUND(SUM({price}), 2) AS x FROM {FROM} WHERE {cstate} = 'MG' GROUP BY 1 ORDER BY x DESC LIMIT 5", urut=True)
q("Q043", "L2", "status,waktu", False,
  "Tampilkan nomor bulan dan jumlah pesanan yang dibatalkan untuk setiap bulan pada tahun 2018, urutkan per bulan.",
  "SELECT {month}, COUNT(DISTINCT {order}) FROM {FROM} WHERE {status} = 'canceled' AND {year} = 2018 "
  "GROUP BY 1 ORDER BY 1", urut=True)
q("Q044", "L2", "pelanggan", True,
  "Sebutkan 5 kota pelanggan di negara bagian RS dengan omzet terbesar beserta omzetnya.",
  "SELECT {ccity}, ROUND(SUM({total}), 2) AS x FROM {FROM} WHERE {cstate} = 'RS' GROUP BY 1 ORDER BY x DESC LIMIT 5", urut=True)
q("Q045", "L2", "pelanggan,pengiriman", False,
  "Sebutkan 5 negara bagian pelanggan dengan rata-rata ongkos kirim per item termahal beserta rata-ratanya.",
  "SELECT {cstate}, ROUND(AVG({freight}), 2) AS r FROM {FROM} GROUP BY 1 ORDER BY r DESC LIMIT 5", urut=True)
q("Q046", "L2", "produk,waktu", False,
  "Pada kuartal pertama 2018, sebutkan 10 kategori dengan jumlah produk berbeda yang terjual terbanyak beserta jumlah produknya.",
  "SELECT {cat}, COUNT(DISTINCT {product}) AS n FROM {FROM} WHERE {year} = 2018 AND {quarter} = 1 "
  "GROUP BY 1 ORDER BY n DESC LIMIT 10", urut=True)
q("Q047", "L2", "status,waktu", False,
  "Untuk item yang dibeli pada tahun 2018, tampilkan setiap status pesanan beserta jumlah itemnya.",
  "SELECT {status}, COUNT(*) FROM {FROM} WHERE {year} = 2018 GROUP BY 1")
q("Q048", "L2", "waktu", False,
  "Tampilkan tahun, nomor kuartal, dan total harga barang untuk setiap kuartal, urutkan secara kronologis.",
  "SELECT {year}, {quarter}, ROUND(SUM({price}), 2) FROM {FROM} GROUP BY 1, 2 ORDER BY 1, 2", urut=True)
q("Q049", "L2", "penjual,produk", True,
  "Untuk kategori furnitur dan dekorasi, sebutkan ID 5 penjual dengan jumlah pesanan terbanyak beserta jumlah pesanannya.",
  "SELECT {seller}, COUNT(DISTINCT {order}) AS n FROM {FROM} WHERE {cat} = 'furniture_decor' "
  "GROUP BY 1 ORDER BY n DESC LIMIT 5", urut=True)
q("Q050", "L2", "penjual,waktu", False,
  "Untuk penjual di negara bagian SP, tampilkan nomor bulan dan jumlah item terjual setiap bulan selama tahun 2017, urutkan per bulan.",
  "SELECT {month}, COUNT(*) FROM {FROM} WHERE {sstate} = 'SP' AND {year} = 2017 GROUP BY 1 ORDER BY 1", urut=True)

# =====================================================================
# L3 — SULIT: >=2 dimensi atau HAVING, ukuran turunan, COUNT DISTINCT
# =====================================================================
q("Q051", "L3", "produk,waktu", True,
  "Tampilkan kategori produk yang omzetnya pada kuartal pertama 2018 lebih dari 100.000 BRL beserta omzetnya, urutkan dari yang terbesar.",
  "SELECT {cat}, ROUND(SUM({total}), 2) AS x FROM {FROM} WHERE {year} = 2018 AND {quarter} = 1 "
  "GROUP BY 1 HAVING SUM({total}) > 100000 ORDER BY x DESC", urut=True)
q("Q052", "L3", "pelanggan,waktu", True,
  "Pada tahun 2017, sebutkan 5 negara bagian pelanggan dengan rata-rata nilai pesanan (AOV) tertinggi beserta nilainya.",
  "SELECT {cstate}, ROUND(SUM({total}) / COUNT(DISTINCT {order}), 2) AS aov FROM {FROM} WHERE {year} = 2017 "
  "GROUP BY 1 ORDER BY aov DESC LIMIT 5", urut=True)
q("Q053", "L3", "pengiriman,pelanggan", True,
  "Untuk pesanan yang sudah diterima pelanggan, sebutkan 5 negara bagian pelanggan dengan rata-rata lama pengiriman tercepat (dalam hari) beserta rata-ratanya.",
  "SELECT st, ROUND(AVG(lama), 2) AS r FROM (SELECT DISTINCT {order} AS oid, {cstate} AS st, {ddate} - {pdate} AS lama "
  "FROM {FROM} WHERE {ddate} IS NOT NULL) x GROUP BY 1 ORDER BY r ASC LIMIT 5")
q("Q054", "L3", "pengiriman,waktu", True,
  "Untuk setiap tahun pembelian, berapa persen pesanan yang terlambat dari seluruh pesanan yang sudah diterima pelanggan? Tampilkan tahun dan persentasenya.",
  "SELECT yr, ROUND(100.0 * SUM(CASE WHEN tl THEN 1 ELSE 0 END) / COUNT(*), 2) FROM "
  "(SELECT DISTINCT {order} AS oid, {year} AS yr, ({ddate} > {edate}) AS tl FROM {FROM} WHERE {ddate} IS NOT NULL) x "
  "GROUP BY 1 ORDER BY 1", urut=True)
q("Q055", "L3", "pelanggan", True,
  "Negara bagian pelanggan mana saja yang memiliki lebih dari 5.000 pelanggan unik? Tampilkan kode negara bagian dan jumlah pelanggannya.",
  "SELECT {cstate}, COUNT(DISTINCT {cust}) FROM {FROM} GROUP BY 1 HAVING COUNT(DISTINCT {cust}) > 5000")
q("Q056", "L3", "produk,penjual", False,
  "Kategori produk mana saja yang dijual oleh lebih dari 200 penjual berbeda? Tampilkan kategori dan jumlah penjualnya, urutkan dari yang terbanyak.",
  "SELECT {cat}, COUNT(DISTINCT {seller}) AS n FROM {FROM} GROUP BY 1 HAVING COUNT(DISTINCT {seller}) > 200 "
  "ORDER BY n DESC", urut=True)
q("Q057", "L3", "waktu,pelanggan", True,
  "Untuk setiap kuartal tahun 2017, tampilkan nomor kuartal, jumlah pesanan, jumlah pelanggan unik, dan omzetnya.",
  "SELECT {quarter}, COUNT(DISTINCT {order}), COUNT(DISTINCT {cust}), ROUND(SUM({total}), 2) FROM {FROM} "
  "WHERE {year} = 2017 GROUP BY 1 ORDER BY 1", urut=True)
q("Q058", "L3", "penjual,pelanggan", False,
  "Sebutkan 5 pasangan negara bagian penjual dan negara bagian pelanggan dengan jumlah item terbanyak. Tampilkan negara bagian penjual, negara bagian pelanggan, dan jumlah itemnya.",
  "SELECT {sstate}, {cstate}, COUNT(*) AS n FROM {FROM} GROUP BY 1, 2 ORDER BY n DESC LIMIT 5", urut=True)
q("Q059", "L3", "pelanggan,waktu", False,
  "Kota pelanggan mana saja di negara bagian SP yang memiliki lebih dari 1.000 pesanan pada tahun 2018? Tampilkan nama kota dan jumlah pesanannya.",
  "SELECT {ccity}, COUNT(DISTINCT {order}) FROM {FROM} WHERE {cstate} = 'SP' AND {year} = 2018 "
  "GROUP BY 1 HAVING COUNT(DISTINCT {order}) > 1000")
q("Q060", "L3", "produk,pengiriman", False,
  "Untuk item dengan berat produk lebih dari 10.000 gram, dan hanya untuk kategori yang memiliki minimal 50 item seperti itu, sebutkan 10 kategori dengan rata-rata ongkos kirim termahal beserta rata-ratanya.",
  "SELECT {cat}, ROUND(AVG({freight}), 2) AS r FROM {FROM} WHERE {weight} > 10000 GROUP BY 1 "
  "HAVING COUNT(*) >= 50 ORDER BY r DESC LIMIT 10", urut=True)
q("Q061", "L3", "status", False,
  "Untuk setiap status pesanan selain terkirim (delivered), tampilkan status, jumlah pesanan, dan total harga barangnya.",
  "SELECT {status}, COUNT(DISTINCT {order}), ROUND(SUM({price}), 2) FROM {FROM} WHERE {status} <> 'delivered' GROUP BY 1")
q("Q062", "L3", "penjual,waktu", False,
  "Penjual mana saja yang menjual lebih dari 1.000 item pada tahun 2017? Tampilkan ID penjual dan jumlah itemnya.",
  "SELECT {seller}, COUNT(*) FROM {FROM} WHERE {year} = 2017 GROUP BY 1 HAVING COUNT(*) > 1000")
q("Q063", "L3", "waktu", False,
  "Untuk setiap bulan pada tahun 2018, tampilkan nomor bulan, jumlah pesanan yang dibuat pada akhir pekan, dan jumlah pesanan yang dibuat pada hari kerja.",
  "SELECT {month}, COUNT(DISTINCT CASE WHEN {weekend} THEN {order} END), "
  "COUNT(DISTINCT CASE WHEN NOT {weekend} THEN {order} END) FROM {FROM} WHERE {year} = 2018 GROUP BY 1 ORDER BY 1", urut=True)
q("Q064", "L3", "produk", False,
  "Di antara kategori yang memiliki minimal 1.000 item terjual, sebutkan 5 kategori dengan rata-rata harga barang per item termurah beserta rata-ratanya.",
  "SELECT {cat}, ROUND(AVG({price}), 2) AS r FROM {FROM} GROUP BY 1 HAVING COUNT(*) >= 1000 ORDER BY r ASC LIMIT 5", urut=True)
q("Q065", "L3", "pelanggan,pengiriman", False,
  "Negara bagian pelanggan mana saja yang rata-rata ongkos kirim per itemnya di atas 30 BRL? Tampilkan kode negara bagian dan rata-ratanya, urutkan dari termahal.",
  "SELECT {cstate}, ROUND(AVG({freight}), 2) AS r FROM {FROM} GROUP BY 1 HAVING AVG({freight}) > 30 ORDER BY r DESC", urut=True)
q("Q066", "L3", "pengiriman,pelanggan", True,
  "Sebutkan 5 negara bagian pelanggan dengan jumlah pesanan yang lama pengirimannya lebih dari 30 hari terbanyak, beserta jumlah pesanannya.",
  "SELECT {cstate}, COUNT(DISTINCT {order}) AS n FROM {FROM} WHERE {ddate} - {pdate} > 30 "
  "GROUP BY 1 ORDER BY n DESC LIMIT 5", urut=True)
q("Q067", "L3", "pelanggan,produk", True,
  "Untuk kategori elektronik, sebutkan 5 negara bagian pelanggan dengan jumlah pelanggan unik terbanyak beserta jumlah pelanggannya.",
  "SELECT {cstate}, COUNT(DISTINCT {cust}) AS n FROM {FROM} WHERE {cat} = 'electronics' "
  "GROUP BY 1 ORDER BY n DESC LIMIT 5", urut=True)
q("Q068", "L3", "produk,pengiriman", False,
  "Di antara kategori yang memiliki minimal 500 item terjual, sebutkan 5 kategori dengan persentase total ongkos kirim terhadap total harga barang tertinggi beserta persentasenya.",
  "SELECT {cat}, ROUND(100 * SUM({freight}) / SUM({price}), 2) AS pct FROM {FROM} GROUP BY 1 "
  "HAVING COUNT(*) >= 500 ORDER BY pct DESC LIMIT 5", urut=True)
q("Q069", "L3", "waktu", False,
  "Untuk setiap tahun, berapa jumlah pesanan yang berisi lebih dari satu item? Tampilkan tahun dan jumlah pesanannya.",
  "SELECT yr, COUNT(*) FROM (SELECT {order}, {year} AS yr FROM {FROM} GROUP BY 1, 2 HAVING COUNT(*) > 1) x "
  "GROUP BY 1 ORDER BY 1", urut=True)
q("Q070", "L3", "penjual", True,
  "Penjual dari luar negara bagian SP mana saja yang omzetnya lebih dari 50.000 BRL? Tampilkan ID penjual, negara bagiannya, dan omzetnya.",
  "SELECT {seller}, {sstate}, ROUND(SUM({total}), 2) FROM {FROM} WHERE {sstate} <> 'SP' GROUP BY 1, 2 "
  "HAVING SUM({total}) > 50000")
q("Q071", "L3", "pengiriman,waktu", True,
  "Untuk pesanan yang dibeli pada Januari sampai Agustus 2018 dan sudah diterima, tampilkan nomor bulan pembelian dan rata-rata lama pengirimannya dalam hari.",
  "SELECT mo, ROUND(AVG(lama), 2) FROM (SELECT DISTINCT {order} AS oid, {month} AS mo, {ddate} - {pdate} AS lama "
  "FROM {FROM} WHERE {year} = 2018 AND {ddate} IS NOT NULL) x GROUP BY 1 ORDER BY 1", urut=True)
q("Q072", "L3", "penjual", False,
  "Kota penjual mana saja yang memiliki minimal 50 penjual berbeda? Tampilkan nama kota dan jumlah penjualnya, urutkan dari terbanyak.",
  "SELECT {scity}, COUNT(DISTINCT {seller}) AS n FROM {FROM} GROUP BY 1 HAVING COUNT(DISTINCT {seller}) >= 50 "
  "ORDER BY n DESC", urut=True)
q("Q073", "L3", "produk,status", False,
  "Kategori produk mana saja yang memiliki lebih dari 20 item dari pesanan yang dibatalkan? Tampilkan kategori dan jumlah itemnya.",
  "SELECT {cat}, COUNT(*) FROM {FROM} WHERE {status} = 'canceled' GROUP BY 1 HAVING COUNT(*) > 20")
q("Q074", "L3", "pelanggan,waktu", True,
  "Untuk pelanggan dari negara bagian Bahia, tampilkan tahun, jumlah pesanan, dan omzet per tahun.",
  "SELECT {year}, COUNT(DISTINCT {order}), ROUND(SUM({total}), 2) FROM {FROM} WHERE {cstate} = 'BA' "
  "GROUP BY 1 ORDER BY 1", urut=True)
q("Q075", "L3", "produk", False,
  "Di antara kategori yang memiliki minimal 100 item terjual, sebutkan 5 kategori dengan rata-rata berat produk per item terberat beserta rata-ratanya dalam gram.",
  "SELECT {cat}, ROUND(AVG({weight}), 2) AS r FROM {FROM} GROUP BY 1 HAVING COUNT(*) >= 100 ORDER BY r DESC LIMIT 5", urut=True)

# =====================================================================
# L4 — SANGAT SULIT: CTE/subquery, window, antar-periode, ranking per grup
# =====================================================================
q("Q076", "L4", "waktu", True,
  "Untuk setiap bulan Januari sampai Agustus 2018, berapa persen pertumbuhan omzet dibanding bulan yang sama tahun 2017? Tampilkan nomor bulan dan persentase pertumbuhannya.",
  "WITH b AS (SELECT {year} AS yr, {month} AS mo, SUM({total}) AS x FROM {FROM} GROUP BY 1, 2) "
  "SELECT b18.mo, ROUND(100 * (b18.x - b17.x) / b17.x, 2) FROM b b18 JOIN b b17 ON b17.mo = b18.mo AND b17.yr = 2017 "
  "WHERE b18.yr = 2018 ORDER BY 1", urut=True)
q("Q077", "L4", "pelanggan,produk", False,
  "Untuk masing-masing negara bagian pelanggan SP, RJ, dan MG, kategori produk apa yang jumlah item terjualnya paling banyak? Tampilkan negara bagian, kategori, dan jumlah itemnya.",
  "WITH x AS (SELECT {cstate} AS st, {cat} AS kat, COUNT(*) AS n FROM {FROM} WHERE {cstate} IN ('SP', 'RJ', 'MG') "
  "GROUP BY 1, 2), r AS (SELECT *, RANK() OVER (PARTITION BY st ORDER BY n DESC) AS rk FROM x) "
  "SELECT st, kat, n FROM r WHERE rk = 1")
q("Q078", "L4", "produk,waktu", True,
  "Sebutkan 5 kategori produk dengan kontribusi omzet terbesar pada tahun 2017, beserta persentase kontribusinya terhadap total omzet tahun 2017.",
  "SELECT {cat}, ROUND(100 * SUM({total}) / SUM(SUM({total})) OVER (), 2) AS pct FROM {FROM} WHERE {year} = 2017 "
  "GROUP BY 1 ORDER BY pct DESC LIMIT 5", urut=True)
q("Q079", "L4", "waktu", True,
  "Tampilkan nomor bulan dan omzet kumulatif (berjalan) dari awal tahun sampai bulan tersebut untuk setiap bulan pada tahun 2017.",
  "SELECT mo, ROUND(SUM(x) OVER (ORDER BY mo), 2) FROM (SELECT {month} AS mo, SUM({total}) AS x FROM {FROM} "
  "WHERE {year} = 2017 GROUP BY 1) b ORDER BY 1", urut=True)
q("Q080", "L4", "pengiriman,waktu", True,
  "Bandingkan rata-rata lama pengiriman (hari) antara pesanan yang dibeli pada akhir pekan dan pada hari kerja, untuk pesanan yang sudah diterima. Tampilkan penanda akhir pekan (benar/salah) dan rata-ratanya.",
  "SELECT wk, ROUND(AVG(lama), 2) FROM (SELECT DISTINCT {order} AS oid, {weekend} AS wk, {ddate} - {pdate} AS lama "
  "FROM {FROM} WHERE {ddate} IS NOT NULL) x GROUP BY 1")
q("Q081", "L4", "penjual,waktu", False,
  "Berapa jumlah penjual yang menjual barang pada tahun 2017 dan 2018, dan total harga barang yang dijualnya pada tahun 2018 lebih besar daripada pada tahun 2017?",
  "WITH s AS (SELECT {seller} AS sid, SUM(CASE WHEN {year} = 2017 THEN {price} ELSE 0 END) AS a, "
  "SUM(CASE WHEN {year} = 2018 THEN {price} ELSE 0 END) AS b, COUNT(DISTINCT {year}) AS ny FROM {FROM} GROUP BY 1) "
  "SELECT COUNT(*) FROM s WHERE ny = 2 AND b > a")
q("Q082", "L4", "pelanggan", True,
  "Berapa jumlah pelanggan unik yang pernah melakukan lebih dari satu pesanan?",
  "SELECT COUNT(*) FROM (SELECT {cust} FROM {FROM} GROUP BY 1 HAVING COUNT(DISTINCT {order}) > 1) x")
q("Q083", "L4", "waktu", True,
  "Untuk setiap tahun, bulan apa yang memiliki omzet tertinggi? Tampilkan tahun, nomor bulan, dan omzetnya.",
  "WITH b AS (SELECT {year} AS yr, {month} AS mo, SUM({total}) AS x FROM {FROM} GROUP BY 1, 2), "
  "r AS (SELECT *, RANK() OVER (PARTITION BY yr ORDER BY x DESC) AS rk FROM b) "
  "SELECT yr, mo, ROUND(x, 2) FROM r WHERE rk = 1 ORDER BY yr", urut=True)
q("Q084", "L4", "produk,waktu", False,
  "Di antara kategori yang menjual minimal 100 item pada kuartal pertama 2017, sebutkan 5 kategori dengan pertumbuhan jumlah item terbesar dari kuartal pertama 2017 ke kuartal pertama 2018, beserta persentase pertumbuhannya.",
  "WITH b AS (SELECT {cat} AS kat, SUM(CASE WHEN {year} = 2017 AND {quarter} = 1 THEN 1 ELSE 0 END) AS a, "
  "SUM(CASE WHEN {year} = 2018 AND {quarter} = 1 THEN 1 ELSE 0 END) AS b FROM {FROM} GROUP BY 1) "
  "SELECT kat, ROUND(100.0 * (b - a) / a, 2) AS g FROM b WHERE a >= 100 ORDER BY g DESC LIMIT 5", urut=True)
q("Q085", "L4", "pengiriman,pelanggan", True,
  "Di antara negara bagian pelanggan yang memiliki minimal 1.000 pesanan yang sudah diterima, sebutkan 5 negara bagian dengan persentase pesanan terlambat tertinggi beserta persentasenya.",
  "SELECT st, ROUND(100.0 * SUM(CASE WHEN tl THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct FROM "
  "(SELECT DISTINCT {order} AS oid, {cstate} AS st, ({ddate} > {edate}) AS tl FROM {FROM} WHERE {ddate} IS NOT NULL) x "
  "GROUP BY 1 HAVING COUNT(*) >= 1000 ORDER BY pct DESC LIMIT 5", urut=True)
q("Q086", "L4", "penjual,waktu", False,
  "Untuk masing-masing negara bagian penjual SP, RJ, dan MG, sebutkan 3 penjual dengan jumlah item terjual terbanyak pada tahun 2018. Tampilkan negara bagian, ID penjual, dan jumlah itemnya.",
  "WITH x AS (SELECT {sstate} AS st, {seller} AS sid, COUNT(*) AS n FROM {FROM} WHERE {year} = 2018 "
  "AND {sstate} IN ('SP', 'RJ', 'MG') GROUP BY 1, 2), r AS (SELECT *, RANK() OVER (PARTITION BY st ORDER BY n DESC) AS rk FROM x) "
  "SELECT st, sid, n FROM r WHERE rk <= 3")
q("Q087", "L4", "pengiriman,waktu", False,
  "Untuk pesanan yang dibeli pada tahun 2018 dan sudah disetujui serta sudah diserahkan ke kurir, tampilkan nomor bulan pembelian dan rata-rata selisih hari antara tanggal persetujuan pembayaran dan tanggal penyerahan ke kurir.",
  "SELECT mo, ROUND(AVG(sel), 2) FROM (SELECT DISTINCT {order} AS oid, {month} AS mo, {cdate} - {adate} AS sel "
  "FROM {FROM} WHERE {year} = 2018 AND {adate} IS NOT NULL AND {cdate} IS NOT NULL) x GROUP BY 1 ORDER BY 1", urut=True)
q("Q088", "L4", "pengiriman,waktu", False,
  "Untuk pesanan yang sudah diterima, rata-rata berapa hari lebih cepat barang tiba dibanding tanggal estimasinya, untuk setiap tahun pembelian? Tampilkan tahun dan rata-rata selisih harinya (estimasi dikurangi tanggal diterima).",
  "SELECT yr, ROUND(AVG(sel), 2) FROM (SELECT DISTINCT {order} AS oid, {year} AS yr, {edate} - {ddate} AS sel "
  "FROM {FROM} WHERE {ddate} IS NOT NULL) x GROUP BY 1 ORDER BY 1", urut=True)
q("Q089", "L4", "pelanggan,penjual,waktu", True,
  "Untuk setiap tahun, berapa persen omzet yang berasal dari item yang negara bagian pelanggannya berbeda dengan negara bagian penjualnya? Tampilkan tahun dan persentasenya.",
  "SELECT {year}, ROUND(100 * SUM(CASE WHEN {cstate} <> {sstate} THEN {total} ELSE 0 END) / SUM({total}), 2) "
  "FROM {FROM} GROUP BY 1 ORDER BY 1", urut=True)
q("Q090", "L4", "waktu", False,
  "Pada tahun 2017, hari apa dalam seminggu yang memiliki rata-rata jumlah pesanan harian tertinggi? Tampilkan nomor hari (1 = Senin sampai 7 = Minggu) dan rata-rata jumlah pesanan hariannya.",
  "SELECT dw, ROUND(AVG(n), 2) AS r FROM (SELECT {pdate} AS tgl, {dow} AS dw, COUNT(DISTINCT {order}) AS n FROM {FROM} "
  "WHERE {year} = 2017 GROUP BY 1, 2) x GROUP BY 1 ORDER BY r DESC LIMIT 1", urut=True)
q("Q091", "L4", "produk,waktu", True,
  "Untuk 5 kategori produk dengan omzet terbesar sepanjang data, tampilkan kategori, omzet tahun 2017, dan omzet tahun 2018 secara berdampingan.",
  "WITH t AS (SELECT {cat} AS kat FROM {FROM} GROUP BY 1 ORDER BY SUM({total}) DESC LIMIT 5) "
  "SELECT {cat}, ROUND(SUM(CASE WHEN {year} = 2017 THEN {total} ELSE 0 END), 2), "
  "ROUND(SUM(CASE WHEN {year} = 2018 THEN {total} ELSE 0 END), 2) FROM {FROM} WHERE {cat} IN (SELECT kat FROM t) GROUP BY 1")
q("Q092", "L4", "pelanggan", True,
  "Sebutkan 5 pelanggan unik dengan total belanja (omzet) terbesar, beserta total belanja dan jumlah pesanannya.",
  "SELECT {cust}, ROUND(SUM({total}), 2) AS x, COUNT(DISTINCT {order}) FROM {FROM} GROUP BY 1 ORDER BY x DESC LIMIT 5", urut=True)
q("Q093", "L4", "produk", False,
  "Di antara kategori yang memiliki minimal 1.000 item terjual, sebutkan 5 kategori dengan median harga barang per item tertinggi beserta mediannya.",
  "SELECT {cat}, ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {price}))::numeric, 2) AS med FROM {FROM} "
  "GROUP BY 1 HAVING COUNT(*) >= 1000 ORDER BY med DESC LIMIT 5", urut=True)
q("Q094", "L4", "pelanggan", False,
  "Di antara negara bagian pelanggan yang memiliki minimal 500 pesanan, sebutkan 5 negara bagian dengan persentase pesanan berisi lebih dari satu item tertinggi beserta persentasenya.",
  "SELECT st, ROUND(100.0 * SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct FROM "
  "(SELECT {order} AS oid, {cstate} AS st, COUNT(*) AS n FROM {FROM} GROUP BY 1, 2) x "
  "GROUP BY 1 HAVING COUNT(*) >= 500 ORDER BY pct DESC LIMIT 5", urut=True)
q("Q095", "L4", "pelanggan,waktu", True,
  "Berapa jumlah pelanggan baru setiap bulan pada tahun 2018, yaitu pelanggan unik yang pembelian pertamanya terjadi pada bulan tersebut? Tampilkan nomor bulan dan jumlahnya.",
  "SELECT ym1 % 100 AS mo, COUNT(*) FROM (SELECT {cust} AS cid, MIN({ym}) AS ym1 FROM {FROM} GROUP BY 1) x "
  "WHERE ym1 / 100 = 2018 GROUP BY 1 ORDER BY 1", urut=True)
q("Q096", "L4", "produk,penjual", False,
  "Di antara kategori yang memiliki minimal 1.000 item terjual, sebutkan 5 kategori dengan persentase item dari penjual negara bagian SP tertinggi, beserta persentasenya.",
  "SELECT {cat}, ROUND(100.0 * SUM(CASE WHEN {sstate} = 'SP' THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct FROM {FROM} "
  "GROUP BY 1 HAVING COUNT(*) >= 1000 ORDER BY pct DESC LIMIT 5", urut=True)
q("Q097", "L4", "waktu", True,
  "Untuk setiap tahun, berapa jumlah pesanan yang nilai omzetnya di atas rata-rata omzet per pesanan seluruh data? Tampilkan tahun dan jumlah pesanannya.",
  "WITH o AS (SELECT {order} AS oid, {year} AS yr, SUM({total}) AS x FROM {FROM} GROUP BY 1, 2) "
  "SELECT yr, COUNT(*) FROM o WHERE x > (SELECT AVG(x) FROM o) GROUP BY 1 ORDER BY 1", urut=True)
q("Q098", "L4", "waktu", True,
  "Untuk setiap bulan pada tahun 2018, tampilkan nomor bulan, omzet bulan itu, dan selisihnya dibanding omzet bulan sebelumnya (untuk Januari 2018 dibanding Desember 2017).",
  "WITH b AS (SELECT {ym} AS ym, SUM({total}) AS x FROM {FROM} GROUP BY 1), "
  "l AS (SELECT ym, x, x - LAG(x) OVER (ORDER BY ym) AS d FROM b) "
  "SELECT ym % 100, ROUND(x, 2), ROUND(d, 2) FROM l WHERE ym / 100 = 2018 ORDER BY ym", urut=True)
q("Q099", "L4", "produk,pelanggan", False,
  "Kategori produk mana saja yang pernah dibeli oleh pelanggan dari seluruh negara bagian yang ada dalam data? Tampilkan nama kategorinya.",
  "SELECT {cat} FROM {FROM} GROUP BY 1 HAVING COUNT(DISTINCT {cstate}) = (SELECT COUNT(DISTINCT {cstate}) FROM {FROM})")
q("Q100", "L4", "pengiriman,pelanggan,penjual,waktu", True,
  "Untuk setiap tahun pembelian, bandingkan rata-rata lama pengiriman (hari) pesanan yang sudah diterima antara item yang penjual dan pelanggannya berada di negara bagian yang sama dan yang berbeda. Tampilkan tahun, penanda negara bagian sama (benar/salah), dan rata-ratanya.",
  "SELECT yr, sama, ROUND(AVG(lama), 2) FROM (SELECT {year} AS yr, ({cstate} = {sstate}) AS sama, {ddate} - {pdate} AS lama "
  "FROM {FROM} WHERE {ddate} IS NOT NULL) x GROUP BY 1, 2 ORDER BY 1, 2", urut=True)
