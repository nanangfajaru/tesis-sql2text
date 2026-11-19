-- Skema database PostgreSQL. Tulis nama tabel tanpa prefiks skema.

-- Peran: tabel referensi
-- product_category_name_translation: terjemahan nama kategori Portugis -> Inggris
CREATE TABLE product_category_name_translation (
  product_category_name text,  -- nama kategori produk Bahasa Portugis (mis. 'beleza_saude')
  product_category_name_english text,  -- nama kategori produk Bahasa Inggris, huruf kecil dengan garis bawah (mis. 'health_beauty'); lihat daftar kategori di glosarium
  PRIMARY KEY (product_category_name)
);

-- Peran: tabel master
-- products: data produk; sinonim: barang. Nama kategori di sini Bahasa Portugis
CREATE TABLE products (
  product_id text,  -- ID produk
  product_category_name text REFERENCES product_category_name_translation(product_category_name),  -- nama kategori produk Bahasa Portugis (mis. 'beleza_saude'); nama Inggris ada di product_category_name_translation
  product_name_lenght integer,  -- jumlah karakter nama produk (ejaan 'lenght' sesuai data asli)
  product_description_lenght integer,  -- jumlah karakter deskripsi produk (ejaan 'lenght' sesuai data asli)
  product_photos_qty integer,  -- jumlah foto produk
  product_weight_g integer,  -- berat produk (gram)
  product_length_cm integer,  -- panjang produk (cm)
  product_height_cm integer,  -- tinggi produk (cm)
  product_width_cm integer,  -- lebar produk (cm)
  PRIMARY KEY (product_id)
);

-- Peran: tabel master
-- sellers: data penjual beserta lokasinya; sinonim: seller, toko, merchant
CREATE TABLE sellers (
  seller_id text,  -- ID penjual; sinonim: seller, toko, merchant, mitra
  seller_zip_code_prefix text,  -- 5 digit awal kode pos
  seller_city text,  -- kota penjual; nama kota, huruf kecil tanpa aksen (mis. 'sao paulo', 'rio de janeiro')
  seller_state char(2),  -- negara bagian penjual; kode negara bagian Brasil 2 huruf kapital (mis. 'SP' = Sao Paulo); sinonim: provinsi, wilayah
  PRIMARY KEY (seller_id)
);

-- Peran: tabel master
-- customers: data pelanggan beserta lokasinya; sinonim: pembeli, konsumen
CREATE TABLE customers (
  customer_id text,  -- ID pelanggan PER PESANAN (setiap pesanan punya customer_id baru); JANGAN dipakai untuk menghitung jumlah pelanggan
  customer_unique_id text,  -- ID unik orang/pelanggan sebenarnya; pakai COUNT(DISTINCT customer_unique_id) untuk jumlah pelanggan
  customer_zip_code_prefix text,  -- 5 digit awal kode pos
  customer_city text,  -- kota pelanggan; nama kota, huruf kecil tanpa aksen (mis. 'sao paulo', 'rio de janeiro')
  customer_state char(2),  -- negara bagian pelanggan; kode negara bagian Brasil 2 huruf kapital (mis. 'SP' = Sao Paulo); sinonim: provinsi, wilayah
  PRIMARY KEY (customer_id)
);

-- Peran: tabel transaksi
-- orders: header pesanan (satu baris = satu pesanan). Jumlah pesanan = COUNT(DISTINCT order_id).
CREATE TABLE orders (
  order_id text,  -- ID pesanan (satu pesanan bisa berisi beberapa item)
  customer_id text REFERENCES customers(customer_id),  -- ID pelanggan PER PESANAN (setiap pesanan punya customer_id baru); JANGAN dipakai untuk menghitung jumlah pelanggan
  order_status text,  -- status pesanan: approved, canceled, delivered, invoiced, processing, shipped (lihat glosarium)
  order_purchase_timestamp timestamp,  -- tanggal pembelian/pemesanan oleh pelanggan; tanggal DEFAULT untuk 'tanggal transaksi/penjualan'
  order_approved_at timestamp,  -- tanggal pembayaran disetujui (NULL bila belum)
  order_delivered_carrier_date timestamp,  -- tanggal barang diserahkan ke kurir (NULL bila belum)
  order_delivered_customer_date timestamp,  -- tanggal barang diterima pelanggan (NULL bila belum diterima)
  order_estimated_delivery_date timestamp,  -- tanggal estimasi barang sampai yang dijanjikan ke pelanggan
  PRIMARY KEY (order_id)
);

-- Peran: tabel transaksi
-- order_items: item pesanan; GRAIN: satu baris = satu item (unit) dalam satu pesanan. Tidak ada kolom total: omzet = price + freight_value. Jumlah item/unit terjual = COUNT(*).
CREATE TABLE order_items (
  order_id text REFERENCES orders(order_id),  -- ID pesanan (satu pesanan bisa berisi beberapa item)
  order_item_id integer,  -- nomor urut item di dalam pesanan (1, 2, 3, ...); satu baris = satu unit barang
  product_id text REFERENCES products(product_id),  -- ID produk
  seller_id text REFERENCES sellers(seller_id),  -- ID penjual; sinonim: seller, toko, merchant, mitra
  shipping_limit_date timestamp,  -- batas waktu penjual menyerahkan barang ke kurir
  price numeric(10,2),  -- harga barang per item (BRL), TANPA ongkos kirim; sinonim: nilai barang, harga jual
  freight_value numeric(10,2),  -- ongkos kirim per item (BRL); sinonim: ongkir, biaya pengiriman
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
