"""
buat_metadata.py — Membangkitkan 9 teks metadata skema (3 skema x 3 level)
untuk disisipkan ke prompt LLM.

  M0 = nama tabel + nama kolom + tipe data
  M1 = M0 + PRIMARY KEY / FOREIGN KEY + label peran tabel
  M2 = M1 + deskripsi & sinonim Bahasa Indonesia per tabel/kolom
          + format nilai + glosarium istilah bisnis

Prinsip: konsep yang sama diberi deskripsi yang SAMA di ketiga skema,
sehingga perbedaan hasil hanya berasal dari struktur skema.

Keluaran: metadata/<skema>_<level>.sql  (9 file)
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metadata")

# ------------------------------------------------------------------
# Deskripsi kolom bersama (dipakai lintas skema bila konsepnya sama)
# ------------------------------------------------------------------
D = {
    "order_id": "ID pesanan (satu pesanan bisa berisi beberapa item)",
    "order_item_id": "nomor urut item di dalam pesanan (1, 2, 3, ...); satu baris = satu unit barang",
    "price": "harga barang per item (BRL), TANPA ongkos kirim; sinonim: nilai barang, harga jual",
    "freight_value": "ongkos kirim per item (BRL); sinonim: ongkir, biaya pengiriman",
    "total_value": "price + freight_value (BRL); sinonim: omzet, nilai penjualan, pendapatan kotor",
    "customer_id": "ID pelanggan PER PESANAN (setiap pesanan punya customer_id baru); JANGAN dipakai untuk menghitung jumlah pelanggan",
    "customer_unique_id": "ID unik orang/pelanggan sebenarnya; pakai COUNT(DISTINCT customer_unique_id) untuk jumlah pelanggan",
    "zip_code_prefix": "5 digit awal kode pos",
    "city": "nama kota, huruf kecil tanpa aksen (mis. 'sao paulo', 'rio de janeiro')",
    "state": "kode negara bagian Brasil 2 huruf kapital (mis. 'SP' = Sao Paulo); sinonim: provinsi, wilayah",
    "seller_id": "ID penjual; sinonim: seller, toko, merchant, mitra",
    "product_id": "ID produk",
    "category_en": "nama kategori produk Bahasa Inggris, huruf kecil dengan garis bawah (mis. 'health_beauty'); lihat daftar kategori di glosarium",
    "category_pt": "nama kategori produk Bahasa Portugis (mis. 'beleza_saude')",
    "name_length": "jumlah karakter nama produk",
    "description_length": "jumlah karakter deskripsi produk",
    "photos_qty": "jumlah foto produk",
    "weight_g": "berat produk (gram)",
    "length_cm": "panjang produk (cm)",
    "height_cm": "tinggi produk (cm)",
    "width_cm": "lebar produk (cm)",
    "order_status": "status pesanan: approved, canceled, delivered, invoiced, processing, shipped (lihat glosarium)",
    "purchase": "tanggal pembelian/pemesanan oleh pelanggan; tanggal DEFAULT untuk 'tanggal transaksi/penjualan'",
    "approved": "tanggal pembayaran disetujui (NULL bila belum)",
    "delivered_carrier": "tanggal barang diserahkan ke kurir (NULL bila belum)",
    "delivered_customer": "tanggal barang diterima pelanggan (NULL bila belum diterima)",
    "estimated_delivery": "tanggal estimasi barang sampai yang dijanjikan ke pelanggan",
    "shipping_limit": "batas waktu penjual menyerahkan barang ke kurir",
    "date_key": "kunci tanggal format YYYYMMDD (integer), mis. 20180315",
    "full_date": "tanggal kalender (DATE)",
    "day_of_month": "tanggal dalam bulan (1-31)",
    "day_of_week": "hari dalam minggu ISO: 1=Senin ... 7=Minggu",
    "day_name": "nama hari Bahasa Inggris: Monday ... Sunday",
    "is_weekend": "TRUE bila Sabtu/Minggu (akhir pekan)",
    "week_of_year": "minggu ke- dalam tahun (ISO)",
    "month": "bulan (1-12)",
    "month_name": "nama bulan Bahasa Inggris: January ... December",
    "quarter": "kuartal/triwulan (1-4)",
    "year": "tahun (data penjualan 2017-01-05 s.d. 2018-08-29)",
    "month_key": "kunci bulan format YYYYMM (integer), mis. 201803",
}

# ------------------------------------------------------------------
# Definisi skema: list tabel -> (nama, peran, deskripsi tabel, kolom)
# kolom: (nama, tipe, deskripsi, pk?, fk_ref)
# ------------------------------------------------------------------
def c(n, t, d, pk=False, fk=None):
    return (n, t, d, pk, fk)


ROLE_ID = {"fact": "tabel fakta", "dim": "tabel dimensi", "sub": "tabel sub-dimensi (normalisasi)",
           "trx": "tabel transaksi", "master": "tabel master", "ref": "tabel referensi"}

DATE_ROLES = [("purchase", "purchase"), ("approved", "approved"), ("delivered_carrier", "delivered_carrier"),
              ("delivered_customer", "delivered_customer"), ("estimated_delivery", "estimated_delivery"),
              ("shipping_limit", "shipping_limit")]


def fact_sales(dim_date_ref):
    cols = [c("order_id", "text", D["order_id"], pk=True),
            c("order_item_id", "integer", D["order_item_id"], pk=True)]
    for col, k in DATE_ROLES:
        cols.append(c(f"{col}_date_key", "integer", D[k] + " -> dim_date", fk=dim_date_ref))
    cols += [c("customer_key", "integer", "pelanggan pemesan", fk="dim_customer(customer_key)"),
             c("product_key", "integer", "produk yang dibeli", fk="dim_product(product_key)"),
             c("seller_key", "integer", "penjual yang menjual item", fk="dim_seller(seller_key)"),
             c("order_status_key", "integer", "status pesanan", fk="dim_order_status(order_status_key)"),
             c("price", "numeric(10,2)", D["price"]),
             c("freight_value", "numeric(10,2)", D["freight_value"]),
             c("total_value", "numeric(10,2)", D["total_value"])]
    return ("fact_sales", "fact",
            "fakta penjualan; GRAIN: satu baris = satu item (unit) dalam satu pesanan. "
            "Jumlah pesanan = COUNT(DISTINCT order_id); jumlah item/unit terjual = COUNT(*).", cols)


DIM_PRODUCT_ATTR = [c("name_length", "integer", D["name_length"]),
                    c("description_length", "integer", D["description_length"]),
                    c("photos_qty", "integer", D["photos_qty"]),
                    c("weight_g", "integer", D["weight_g"]),
                    c("length_cm", "integer", D["length_cm"]),
                    c("height_cm", "integer", D["height_cm"]),
                    c("width_cm", "integer", D["width_cm"])]

STATUS_DIM = ("dim_order_status", "dim", "dimensi status pesanan",
              [c("order_status_key", "integer", "kunci surrogate", pk=True),
               c("order_status", "text", D["order_status"])])

STAR = [
    fact_sales("dim_date(date_key)"),
    ("dim_date", "dim", "dimensi tanggal (kalender); dipakai untuk semua peran tanggal di fact_sales",
     [c("date_key", "integer", D["date_key"], pk=True), c("full_date", "date", D["full_date"]),
      c("day_of_month", "smallint", D["day_of_month"]), c("day_of_week", "smallint", D["day_of_week"]),
      c("day_name", "text", D["day_name"]), c("is_weekend", "boolean", D["is_weekend"]),
      c("week_of_year", "smallint", D["week_of_year"]), c("month", "smallint", D["month"]),
      c("month_name", "text", D["month_name"]), c("quarter", "smallint", D["quarter"]),
      c("year", "smallint", D["year"])]),
    ("dim_customer", "dim", "dimensi pelanggan beserta lokasinya; sinonim: pembeli, konsumen",
     [c("customer_key", "integer", "kunci surrogate", pk=True), c("customer_id", "text", D["customer_id"]),
      c("customer_unique_id", "text", D["customer_unique_id"]),
      c("zip_code_prefix", "text", D["zip_code_prefix"]), c("city", "text", "kota pelanggan; " + D["city"]),
      c("state", "char(2)", "negara bagian pelanggan; " + D["state"])]),
    ("dim_product", "dim", "dimensi produk beserta kategorinya; sinonim: barang",
     [c("product_key", "integer", "kunci surrogate", pk=True), c("product_id", "text", D["product_id"]),
      c("category_name", "text", D["category_en"]),
      c("category_name_portuguese", "text", D["category_pt"])] + DIM_PRODUCT_ATTR),
    ("dim_seller", "dim", "dimensi penjual beserta lokasinya; sinonim: seller, toko, merchant",
     [c("seller_key", "integer", "kunci surrogate", pk=True), c("seller_id", "text", D["seller_id"]),
      c("zip_code_prefix", "text", D["zip_code_prefix"]), c("city", "text", "kota penjual; " + D["city"]),
      c("state", "char(2)", "negara bagian penjual; " + D["state"])]),
    STATUS_DIM,
]

SNOWFLAKE = [
    fact_sales("dim_date(date_key)"),
    ("dim_date", "dim", "dimensi tanggal; atribut bulan/tahun ada di dim_month dan dim_year",
     [c("date_key", "integer", D["date_key"], pk=True), c("full_date", "date", D["full_date"]),
      c("month_key", "integer", "bulan dari tanggal ini -> dim_month", fk="dim_month(month_key)"),
      c("day_of_month", "smallint", D["day_of_month"]), c("day_of_week", "smallint", D["day_of_week"]),
      c("day_name", "text", D["day_name"]), c("is_weekend", "boolean", D["is_weekend"]),
      c("week_of_year", "smallint", D["week_of_year"])]),
    ("dim_month", "sub", "sub-dimensi bulan",
     [c("month_key", "integer", D["month_key"], pk=True),
      c("year_key", "smallint", "tahun -> dim_year", fk="dim_year(year_key)"),
      c("month", "smallint", D["month"]), c("month_name", "text", D["month_name"]),
      c("quarter", "smallint", D["quarter"])]),
    ("dim_year", "sub", "sub-dimensi tahun",
     [c("year_key", "smallint", "tahun, mis. 2018 (" + D["year"] + ")", pk=True)]),
    ("dim_customer", "dim", "dimensi pelanggan; lokasi lewat dim_city -> dim_state; sinonim: pembeli, konsumen",
     [c("customer_key", "integer", "kunci surrogate", pk=True), c("customer_id", "text", D["customer_id"]),
      c("customer_unique_id", "text", D["customer_unique_id"]),
      c("zip_code_prefix", "text", D["zip_code_prefix"]),
      c("city_key", "integer", "kota pelanggan -> dim_city", fk="dim_city(city_key)")]),
    ("dim_seller", "dim", "dimensi penjual; lokasi lewat dim_city -> dim_state; sinonim: seller, toko, merchant",
     [c("seller_key", "integer", "kunci surrogate", pk=True), c("seller_id", "text", D["seller_id"]),
      c("zip_code_prefix", "text", D["zip_code_prefix"]),
      c("city_key", "integer", "kota penjual -> dim_city", fk="dim_city(city_key)")]),
    ("dim_city", "sub", "sub-dimensi kota (dipakai bersama oleh pelanggan dan penjual)",
     [c("city_key", "integer", "kunci surrogate", pk=True), c("city_name", "text", D["city"]),
      c("state_key", "integer", "negara bagian -> dim_state", fk="dim_state(state_key)")]),
    ("dim_state", "sub", "sub-dimensi negara bagian",
     [c("state_key", "integer", "kunci surrogate", pk=True), c("state_code", "char(2)", D["state"])]),
    ("dim_product", "dim", "dimensi produk; kategori lewat dim_category; sinonim: barang",
     [c("product_key", "integer", "kunci surrogate", pk=True), c("product_id", "text", D["product_id"]),
      c("category_key", "integer", "kategori -> dim_category", fk="dim_category(category_key)")]
     + DIM_PRODUCT_ATTR),
    ("dim_category", "sub", "sub-dimensi kategori produk",
     [c("category_key", "integer", "kunci surrogate", pk=True), c("category_name", "text", D["category_en"]),
      c("category_name_portuguese", "text", D["category_pt"])]),
    STATUS_DIM,
]

TS = "timestamp"
OLTP = [
    ("order_items", "trx",
     "item pesanan; GRAIN: satu baris = satu item (unit) dalam satu pesanan. Tidak ada kolom total: "
     "omzet = price + freight_value. Jumlah item/unit terjual = COUNT(*).",
     [c("order_id", "text", D["order_id"], pk=True, fk="orders(order_id)"),
      c("order_item_id", "integer", D["order_item_id"], pk=True),
      c("product_id", "text", D["product_id"], fk="products(product_id)"),
      c("seller_id", "text", D["seller_id"], fk="sellers(seller_id)"),
      c("shipping_limit_date", TS, D["shipping_limit"]),
      c("price", "numeric(10,2)", D["price"]),
      c("freight_value", "numeric(10,2)", D["freight_value"])]),
    ("orders", "trx",
     "header pesanan (satu baris = satu pesanan). Jumlah pesanan = COUNT(DISTINCT order_id).",
     [c("order_id", "text", D["order_id"], pk=True),
      c("customer_id", "text", D["customer_id"], fk="customers(customer_id)"),
      c("order_status", "text", D["order_status"]),
      c("order_purchase_timestamp", TS, D["purchase"]),
      c("order_approved_at", TS, D["approved"]),
      c("order_delivered_carrier_date", TS, D["delivered_carrier"]),
      c("order_delivered_customer_date", TS, D["delivered_customer"]),
      c("order_estimated_delivery_date", TS, D["estimated_delivery"])]),
    ("customers", "master", "data pelanggan beserta lokasinya; sinonim: pembeli, konsumen",
     [c("customer_id", "text", D["customer_id"], pk=True),
      c("customer_unique_id", "text", D["customer_unique_id"]),
      c("customer_zip_code_prefix", "text", D["zip_code_prefix"]),
      c("customer_city", "text", "kota pelanggan; " + D["city"]),
      c("customer_state", "char(2)", "negara bagian pelanggan; " + D["state"])]),
    ("sellers", "master", "data penjual beserta lokasinya; sinonim: seller, toko, merchant",
     [c("seller_id", "text", D["seller_id"], pk=True),
      c("seller_zip_code_prefix", "text", D["zip_code_prefix"]),
      c("seller_city", "text", "kota penjual; " + D["city"]),
      c("seller_state", "char(2)", "negara bagian penjual; " + D["state"])]),
    ("products", "master", "data produk; sinonim: barang. Nama kategori di sini Bahasa Portugis",
     [c("product_id", "text", D["product_id"], pk=True),
      c("product_category_name", "text",
        D["category_pt"] + "; nama Inggris ada di product_category_name_translation",
        fk="product_category_name_translation(product_category_name)"),
      c("product_name_lenght", "integer", D["name_length"] + " (ejaan 'lenght' sesuai data asli)"),
      c("product_description_lenght", "integer", D["description_length"] + " (ejaan 'lenght' sesuai data asli)"),
      c("product_photos_qty", "integer", D["photos_qty"]),
      c("product_weight_g", "integer", D["weight_g"]),
      c("product_length_cm", "integer", D["length_cm"]),
      c("product_height_cm", "integer", D["height_cm"]),
      c("product_width_cm", "integer", D["width_cm"])]),
    ("product_category_name_translation", "ref", "terjemahan nama kategori Portugis -> Inggris",
     [c("product_category_name", "text", D["category_pt"], pk=True),
      c("product_category_name_english", "text", D["category_en"])]),
]

# ------------------------------------------------------------------
# Glosarium (hanya M2) — sama untuk ketiga skema
# ------------------------------------------------------------------
STATES = ("AC=Acre, AL=Alagoas, AM=Amazonas, AP=Amapa, BA=Bahia, CE=Ceara, DF=Distrito Federal (Brasilia), "
          "ES=Espirito Santo, GO=Goias, MA=Maranhao, MG=Minas Gerais, MS=Mato Grosso do Sul, MT=Mato Grosso, "
          "PA=Para, PB=Paraiba, PE=Pernambuco, PI=Piaui, PR=Parana, RJ=Rio de Janeiro, RN=Rio Grande do Norte, "
          "RO=Rondonia, RR=Roraima, RS=Rio Grande do Sul, SC=Santa Catarina, SE=Sergipe, SP=Sao Paulo, "
          "TO=Tocantins")

CATEGORIES = [
    ("agro_industry_and_commerce", "agroindustri & perdagangan"), ("air_conditioning", "pendingin ruangan/AC"),
    ("art", "seni"), ("arts_and_craftmanship", "seni & kerajinan"), ("audio", "audio"),
    ("auto", "otomotif"), ("baby", "bayi"), ("bed_bath_table", "perlengkapan tidur, mandi & meja"),
    ("books_general_interest", "buku umum"), ("books_imported", "buku impor"),
    ("books_technical", "buku teknik"), ("cds_dvds_musicals", "CD/DVD musik"),
    ("christmas_supplies", "perlengkapan Natal"), ("cine_photo", "film & foto"),
    ("computers", "komputer/PC"), ("computers_accessories", "aksesori komputer"),
    ("consoles_games", "konsol & gim"), ("construction_tools_construction", "alat konstruksi"),
    ("construction_tools_lights", "alat konstruksi - pencahayaan"),
    ("construction_tools_safety", "alat konstruksi - keselamatan"), ("cool_stuff", "barang unik/keren"),
    ("costruction_tools_garden", "alat konstruksi - taman"), ("costruction_tools_tools", "perkakas"),
    ("diapers_and_hygiene", "popok & kebersihan"), ("drinks", "minuman"), ("dvds_blu_ray", "DVD & Blu-ray"),
    ("electronics", "elektronik"), ("fashio_female_clothing", "pakaian wanita"),
    ("fashion_bags_accessories", "tas & aksesori fesyen"), ("fashion_childrens_clothes", "pakaian anak"),
    ("fashion_male_clothing", "pakaian pria"), ("fashion_shoes", "sepatu"),
    ("fashion_sport", "pakaian olahraga"), ("fashion_underwear_beach", "pakaian dalam & pantai"),
    ("fixed_telephony", "telepon rumah"), ("flowers", "bunga"), ("food", "makanan"),
    ("food_drink", "makanan & minuman"), ("furniture_bedroom", "furnitur kamar tidur"),
    ("furniture_decor", "furnitur & dekorasi"), ("furniture_living_room", "furnitur ruang tamu"),
    ("furniture_mattress_and_upholstery", "kasur & pelapis furnitur"), ("garden_tools", "alat taman"),
    ("health_beauty", "kesehatan & kecantikan"), ("home_appliances", "peralatan rumah tangga (besar)"),
    ("home_appliances_2", "peralatan rumah tangga 2"), ("home_comfort_2", "kenyamanan rumah 2"),
    ("home_confort", "kenyamanan rumah"), ("home_construction", "konstruksi rumah"),
    ("housewares", "perabot rumah tangga"), ("industry_commerce_and_business", "industri, niaga & bisnis"),
    ("kitchen_dining_laundry_garden_furniture", "furnitur dapur, makan, cuci & taman"),
    ("la_cuisine", "peralatan masak premium"), ("luggage_accessories", "koper & aksesori"),
    ("market_place", "marketplace/aneka"), ("music", "musik"), ("musical_instruments", "alat musik"),
    ("office_furniture", "furnitur kantor"), ("party_supplies", "perlengkapan pesta"),
    ("pc_gamer", "PC gaming"), ("perfumery", "parfum"), ("pet_shop", "perlengkapan hewan peliharaan"),
    ("portable_kitchen_and_food_preparers", "alat dapur portabel"), ("security_and_services", "asuransi & layanan"),
    ("signaling_and_security", "rambu & keamanan"), ("small_appliances", "peralatan elektronik kecil"),
    ("small_appliances_home_oven_and_coffee", "oven & mesin kopi"), ("sports_leisure", "olahraga & rekreasi"),
    ("stationery", "alat tulis"), ("tablets_printing_image", "tablet, cetak & gambar"),
    ("telephony", "telepon & ponsel"), ("toys", "mainan"), ("unknown", "tanpa kategori/tidak diketahui"),
    ("watches_gifts", "jam tangan & hadiah"),
]


def glosarium():
    g = ["-- ================= GLOSARIUM ISTILAH BISNIS =================",
         "-- Mata uang: Real Brasil (BRL). Periode transaksi: 5 Jan 2017 s.d. 29 Agu 2018.",
         "-- omzet / nilai penjualan / pendapatan kotor = price + freight_value (harga barang + ongkir)",
         "-- nilai barang / pendapatan produk (tanpa ongkir) = price",
         "-- ongkir / ongkos kirim / biaya pengiriman = freight_value",
         "-- jumlah pesanan / jumlah transaksi = COUNT(DISTINCT order_id)",
         "-- jumlah item / unit terjual / barang terjual = jumlah baris item (COUNT(*))",
         "-- jumlah pelanggan / pelanggan unik = COUNT(DISTINCT customer_unique_id)",
         "-- rata-rata nilai pesanan (AOV) = omzet / jumlah pesanan",
         "-- tanggal transaksi / penjualan (default) = tanggal pembelian (purchase)",
         "-- lama pengiriman (hari) = tanggal diterima pelanggan - tanggal pembelian",
         "-- terlambat = tanggal diterima pelanggan > tanggal estimasi",
         "-- akhir pekan = Sabtu & Minggu; kuartal/triwulan = 3 bulanan",
         "-- Status pesanan: approved=pembayaran disetujui, invoiced=faktur terbit/ditagih, processing=diproses,",
         "--   shipped=sedang dikirim, delivered=terkirim/diterima pelanggan, canceled=dibatalkan.",
         "--   Tanpa keterangan status, hitung SEMUA status.",
         f"-- Negara bagian (kode=nama): {STATES}.",
         "-- Kategori produk (nama di database = arti Bahasa Indonesia):"]
    line = "--   "
    for en, idn in CATEGORIES:
        item = f"{en}={idn}; "
        if len(line) + len(item) > 110:
            g.append(line.rstrip())
            line = "--   "
        line += item
    g.append(line.rstrip().rstrip(";"))
    return g


# ------------------------------------------------------------------
def render(tables, level, skema):
    out = ["-- Skema database PostgreSQL. Tulis nama tabel tanpa prefiks skema.", ""]
    for name, role, tdesc, cols in reversed(tables):  # tabel yang dirujuk didefinisikan lebih dulu
        if level >= 1:
            out.append(f"-- Peran: {ROLE_ID[role]}")
        if level >= 2:
            out.append(f"-- {name}: {tdesc}")
        out.append(f"CREATE TABLE {name} (")
        lines = []
        for n, t, d, pk, fk in cols:
            s = f"  {n} {t}"
            if level >= 1 and fk:
                s += f" REFERENCES {fk}"
            lines.append((s, d))
        pks = [n for n, _, _, pk, _ in cols if pk]
        if level >= 1 and pks:
            lines.append((f"  PRIMARY KEY ({', '.join(pks)})", None))
        for i, (s, d) in enumerate(lines):
            comma = "," if i < len(lines) - 1 else ""
            if level >= 2 and d:
                out.append(f"{s}{comma}  -- {d}")
            else:
                out.append(f"{s}{comma}")
        out.append(");")
        out.append("")
    if level >= 2:
        out += glosarium()
    return "\n".join(out).rstrip() + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    for skema, tables in (("oltp", OLTP), ("star", STAR), ("snowflake", SNOWFLAKE)):
        for level in (0, 1, 2):
            p = os.path.join(OUT, f"{skema}_M{level}.sql")
            with open(p, "w", encoding="utf-8") as f:
                f.write(render(tables, level, skema))
            print(p)


if __name__ == "__main__":
    main()
