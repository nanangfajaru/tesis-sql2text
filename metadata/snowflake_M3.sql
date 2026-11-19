-- Skema database PostgreSQL. Tulis nama tabel tanpa prefiks skema.

-- Peran: tabel dimensi
-- dim_order_status: dimensi status pesanan
CREATE TABLE dim_order_status (
  order_status_key integer,  -- kunci surrogate
  order_status text,  -- status pesanan: approved, canceled, delivered, invoiced, processing, shipped (lihat glosarium)
  PRIMARY KEY (order_status_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
-- dim_category: sub-dimensi kategori produk
CREATE TABLE dim_category (
  category_key integer,  -- kunci surrogate
  category_name text,  -- nama kategori produk Bahasa Inggris, huruf kecil dengan garis bawah (mis. 'health_beauty'); lihat daftar kategori di glosarium
  category_name_portuguese text,  -- nama kategori produk Bahasa Portugis (mis. 'beleza_saude')
  PRIMARY KEY (category_key)
);

-- Peran: tabel dimensi
-- dim_product: dimensi produk; kategori lewat dim_category; sinonim: barang
CREATE TABLE dim_product (
  product_key integer,  -- kunci surrogate
  product_id text,  -- ID produk
  category_key integer REFERENCES dim_category(category_key),  -- kategori -> dim_category
  name_length integer,  -- jumlah karakter nama produk
  description_length integer,  -- jumlah karakter deskripsi produk
  photos_qty integer,  -- jumlah foto produk
  weight_g integer,  -- berat produk (gram)
  length_cm integer,  -- panjang produk (cm)
  height_cm integer,  -- tinggi produk (cm)
  width_cm integer,  -- lebar produk (cm)
  PRIMARY KEY (product_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
-- dim_state: sub-dimensi negara bagian
CREATE TABLE dim_state (
  state_key integer,  -- kunci surrogate
  state_code char(2),  -- kode negara bagian Brasil 2 huruf kapital (mis. 'SP' = Sao Paulo); sinonim: provinsi, wilayah
  PRIMARY KEY (state_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
-- dim_city: sub-dimensi kota (dipakai bersama oleh pelanggan dan penjual)
CREATE TABLE dim_city (
  city_key integer,  -- kunci surrogate
  city_name text,  -- nama kota, huruf kecil tanpa aksen (mis. 'sao paulo', 'rio de janeiro')
  state_key integer REFERENCES dim_state(state_key),  -- negara bagian -> dim_state
  PRIMARY KEY (city_key)
);

-- Peran: tabel dimensi
-- dim_seller: dimensi penjual; lokasi lewat dim_city -> dim_state; sinonim: seller, toko, merchant
CREATE TABLE dim_seller (
  seller_key integer,  -- kunci surrogate
  seller_id text,  -- ID penjual; sinonim: seller, toko, merchant, mitra
  zip_code_prefix text,  -- 5 digit awal kode pos
  city_key integer REFERENCES dim_city(city_key),  -- kota penjual -> dim_city
  PRIMARY KEY (seller_key)
);

-- Peran: tabel dimensi
-- dim_customer: dimensi pelanggan; lokasi lewat dim_city -> dim_state; sinonim: pembeli, konsumen
CREATE TABLE dim_customer (
  customer_key integer,  -- kunci surrogate
  customer_id text,  -- ID pelanggan PER PESANAN (setiap pesanan punya customer_id baru); JANGAN dipakai untuk menghitung jumlah pelanggan
  customer_unique_id text,  -- ID unik orang/pelanggan sebenarnya; pakai COUNT(DISTINCT customer_unique_id) untuk jumlah pelanggan
  zip_code_prefix text,  -- 5 digit awal kode pos
  city_key integer REFERENCES dim_city(city_key),  -- kota pelanggan -> dim_city
  PRIMARY KEY (customer_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
-- dim_year: sub-dimensi tahun
CREATE TABLE dim_year (
  year_key smallint,  -- tahun, mis. 2018 (tahun (data penjualan 2017-01-05 s.d. 2018-08-29))
  PRIMARY KEY (year_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
-- dim_month: sub-dimensi bulan
CREATE TABLE dim_month (
  month_key integer,  -- kunci bulan format YYYYMM (integer), mis. 201803
  year_key smallint REFERENCES dim_year(year_key),  -- tahun -> dim_year
  month smallint,  -- bulan (1-12)
  month_name text,  -- nama bulan Bahasa Inggris: January ... December
  quarter smallint,  -- kuartal/triwulan (1-4)
  PRIMARY KEY (month_key)
);

-- Peran: tabel dimensi
-- dim_date: dimensi tanggal; atribut bulan/tahun ada di dim_month dan dim_year
CREATE TABLE dim_date (
  date_key integer,  -- kunci tanggal format YYYYMMDD (integer), mis. 20180315
  full_date date,  -- tanggal kalender (DATE)
  month_key integer REFERENCES dim_month(month_key),  -- bulan dari tanggal ini -> dim_month
  day_of_month smallint,  -- tanggal dalam bulan (1-31)
  day_of_week smallint,  -- hari dalam minggu ISO: 1=Senin ... 7=Minggu
  day_name text,  -- nama hari Bahasa Inggris: Monday ... Sunday
  is_weekend boolean,  -- TRUE bila Sabtu/Minggu (akhir pekan)
  week_of_year smallint,  -- minggu ke- dalam tahun (ISO)
  PRIMARY KEY (date_key)
);

-- Peran: tabel fakta
-- fact_sales: fakta penjualan; GRAIN: satu baris = satu item (unit) dalam satu pesanan. Jumlah pesanan = COUNT(DISTINCT order_id); jumlah item/unit terjual = COUNT(*).
CREATE TABLE fact_sales (
  order_id text,  -- ID pesanan (satu pesanan bisa berisi beberapa item)
  order_item_id integer,  -- nomor urut item di dalam pesanan (1, 2, 3, ...); satu baris = satu unit barang
  purchase_date_key integer REFERENCES dim_date(date_key),  -- tanggal pembelian/pemesanan oleh pelanggan; tanggal DEFAULT untuk 'tanggal transaksi/penjualan' -> dim_date
  approved_date_key integer REFERENCES dim_date(date_key),  -- tanggal pembayaran disetujui (NULL bila belum) -> dim_date
  delivered_carrier_date_key integer REFERENCES dim_date(date_key),  -- tanggal barang diserahkan ke kurir (NULL bila belum) -> dim_date
  delivered_customer_date_key integer REFERENCES dim_date(date_key),  -- tanggal barang diterima pelanggan (NULL bila belum diterima) -> dim_date
  estimated_delivery_date_key integer REFERENCES dim_date(date_key),  -- tanggal estimasi barang sampai yang dijanjikan ke pelanggan -> dim_date
  shipping_limit_date_key integer REFERENCES dim_date(date_key),  -- batas waktu penjual menyerahkan barang ke kurir -> dim_date
  customer_key integer REFERENCES dim_customer(customer_key),  -- pelanggan pemesan
  product_key integer REFERENCES dim_product(product_key),  -- produk yang dibeli
  seller_key integer REFERENCES dim_seller(seller_key),  -- penjual yang menjual item
  order_status_key integer REFERENCES dim_order_status(order_status_key),  -- status pesanan
  price numeric(10,2),  -- harga barang per item (BRL), TANPA ongkos kirim; sinonim: nilai barang, harga jual
  freight_value numeric(10,2),  -- ongkos kirim per item (BRL); sinonim: ongkir, biaya pengiriman
  total_value numeric(10,2),  -- price + freight_value (BRL); sinonim: omzet, nilai penjualan, pendapatan kotor
  PRIMARY KEY (order_id, order_item_id)
);

-- ================= GLOSARIUM ISTILAH BISNIS =================
-- Mata uang: Real Brasil (BRL). Periode transaksi: 5 Jan 2017 s.d. 29 Agu 2018.
-- omzet / nilai penjualan / pendapatan kotor = price + freight_value (harga barang + ongkir)
-- nilai barang / pendapatan produk (tanpa ongkir) = price
-- ongkir / ongkos kirim / biaya pengiriman = freight_value
-- jumlah pesanan / jumlah transaksi = COUNT(DISTINCT order_id)
-- jumlah item / unit terjual / barang terjual = jumlah baris item (COUNT(*))
-- jumlah pelanggan / pelanggan unik = COUNT(DISTINCT customer_unique_id)
-- rata-rata nilai pesanan (AOV) = omzet / jumlah pesanan
-- tanggal transaksi / penjualan (default) = tanggal pembelian (purchase)
-- lama pengiriman (hari) = tanggal diterima pelanggan - tanggal pembelian
-- terlambat = tanggal diterima pelanggan > tanggal estimasi
-- akhir pekan = Sabtu & Minggu; kuartal/triwulan = 3 bulanan
-- Status pesanan: approved=pembayaran disetujui, invoiced=faktur terbit/ditagih, processing=diproses,
--   shipped=sedang dikirim, delivered=terkirim/diterima pelanggan, canceled=dibatalkan.
--   Tanpa keterangan status, hitung SEMUA status.
-- Negara bagian (kode=nama): AC=Acre, AL=Alagoas, AM=Amazonas, AP=Amapa, BA=Bahia, CE=Ceara, DF=Distrito Federal (Brasilia), ES=Espirito Santo, GO=Goias, MA=Maranhao, MG=Minas Gerais, MS=Mato Grosso do Sul, MT=Mato Grosso, PA=Para, PB=Paraiba, PE=Pernambuco, PI=Piaui, PR=Parana, RJ=Rio de Janeiro, RN=Rio Grande do Norte, RO=Rondonia, RR=Roraima, RS=Rio Grande do Sul, SC=Santa Catarina, SE=Sergipe, SP=Sao Paulo, TO=Tocantins.
-- Kategori produk (nama di database = arti Bahasa Indonesia):
--   agro_industry_and_commerce=agroindustri & perdagangan; air_conditioning=pendingin ruangan/AC; art=seni;
--   arts_and_craftmanship=seni & kerajinan; audio=audio; auto=otomotif; baby=bayi;
--   bed_bath_table=perlengkapan tidur, mandi & meja; books_general_interest=buku umum;
--   books_imported=buku impor; books_technical=buku teknik; cds_dvds_musicals=CD/DVD musik;
--   christmas_supplies=perlengkapan Natal; cine_photo=film & foto; computers=komputer/PC;
--   computers_accessories=aksesori komputer; consoles_games=konsol & gim;
--   construction_tools_construction=alat konstruksi;
--   construction_tools_lights=alat konstruksi - pencahayaan;
--   construction_tools_safety=alat konstruksi - keselamatan; cool_stuff=barang unik/keren;
--   costruction_tools_garden=alat konstruksi - taman; costruction_tools_tools=perkakas;
--   diapers_and_hygiene=popok & kebersihan; drinks=minuman; dvds_blu_ray=DVD & Blu-ray;
--   electronics=elektronik; fashio_female_clothing=pakaian wanita;
--   fashion_bags_accessories=tas & aksesori fesyen; fashion_childrens_clothes=pakaian anak;
--   fashion_male_clothing=pakaian pria; fashion_shoes=sepatu; fashion_sport=pakaian olahraga;
--   fashion_underwear_beach=pakaian dalam & pantai; fixed_telephony=telepon rumah; flowers=bunga;
--   food=makanan; food_drink=makanan & minuman; furniture_bedroom=furnitur kamar tidur;
--   furniture_decor=furnitur & dekorasi; furniture_living_room=furnitur ruang tamu;
--   furniture_mattress_and_upholstery=kasur & pelapis furnitur; garden_tools=alat taman;
--   health_beauty=kesehatan & kecantikan; home_appliances=peralatan rumah tangga (besar);
--   home_appliances_2=peralatan rumah tangga 2; home_comfort_2=kenyamanan rumah 2;
--   home_confort=kenyamanan rumah; home_construction=konstruksi rumah; housewares=perabot rumah tangga;
--   industry_commerce_and_business=industri, niaga & bisnis;
--   kitchen_dining_laundry_garden_furniture=furnitur dapur, makan, cuci & taman;
--   la_cuisine=peralatan masak premium; luggage_accessories=koper & aksesori;
--   market_place=marketplace/aneka; music=musik; musical_instruments=alat musik;
--   office_furniture=furnitur kantor; party_supplies=perlengkapan pesta; pc_gamer=PC gaming;
--   perfumery=parfum; pet_shop=perlengkapan hewan peliharaan;
--   portable_kitchen_and_food_preparers=alat dapur portabel; security_and_services=asuransi & layanan;
--   signaling_and_security=rambu & keamanan; small_appliances=peralatan elektronik kecil;
--   small_appliances_home_oven_and_coffee=oven & mesin kopi; sports_leisure=olahraga & rekreasi;
--   stationery=alat tulis; tablets_printing_image=tablet, cetak & gambar; telephony=telepon & ponsel;
--   toys=mainan; unknown=tanpa kategori/tidak diketahui; watches_gifts=jam tangan & hadiah
