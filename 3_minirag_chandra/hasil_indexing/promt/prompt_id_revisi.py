"""
Copyright (c) 2026 Badan Riset dan Inovasi Nasional (BRIN)
THIS SOFTWARE SOURCE CODE AND ANY EXECUTABLE DERIVED THEREOF ARE PROPRIETARY
TO BRIN, AS APPLICABLE, AND SHALL NOT BE USED IN ANY WAY
OTHER THAN BEFOREHAND AGREED ON BY BRIN, NOR BE REPRODUCED
OR DISCLOSED TO THIRD PARTIES WITHOUT PRIOR WRITTEN AUTHORIZATION BY
BRIN, AS APPLICABLE.

Author      : Chandra
Version     : 2.1.0
Created     : 02-11-2026
Description : Prompt template resmi MiniRAG untuk Domain Hukum Kelautan, Perikanan, dan Pelayaran.
              Menggunakan 3 Contoh Few-Shot Kemaritiman Nyata:
              1. UU Nomor 45 Tahun 2009 (Perizinan Kapal Penangkap Ikan SIPI & Sanksi WPP-NRI)
              2. UU Nomor 17 Tahun 2008 (Kelaiklautan Kapal, Wewenang Syahbandar & SPB)
              3. UU Perikanan (Larangan Destructive Fishing / Bahan Peledak & Perlindungan Nelayan Kecil)
"""

GRAPH_FIELD_SEP = "<SEP>"
DEFAULT_TUPLE_DELIMITER = "<|>"
DEFAULT_RECORD_DELIMITER = "##"
DEFAULT_COMPLETION_DELIMITER = "<|SELESAI|>"
PROCESS_TICKERS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
DEFAULT_ENTITY_TYPES = [
    "dasar_hukum",
    "struktur",
    "konsep",
    "sanksi",
    "pihak",
    "kewajiban",
    "hak",
]
ENTITY_TYPES = DEFAULT_ENTITY_TYPES

PROMPTS = {}

PROMPTS["DEFAULT_TUPLE_DELIMITER"] = DEFAULT_TUPLE_DELIMITER
PROMPTS["DEFAULT_RECORD_DELIMITER"] = DEFAULT_RECORD_DELIMITER
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = DEFAULT_COMPLETION_DELIMITER
PROMPTS["process_tickers"] = PROCESS_TICKERS
PROMPTS["DEFAULT_ENTITY_TYPES"] = DEFAULT_ENTITY_TYPES

PROMPTS["entity_extraction"] = """-Tujuan-
Diberikan dokumen teks hukum yang relevan dan daftar jenis entitas, identifikasi semua entitas dari jenis tersebut beserta semua hubungan antar entitas yang teridentifikasi.

-Langkah-
1. Identifikasi semua entitas. Untuk setiap entitas yang teridentifikasi, ekstrak informasi berikut:
- entity_name: Nama entitas, gunakan bahasa Indonesia
- entity_type: Salah satu dari jenis berikut: [{entity_types}]
- entity_description: Deskripsi komprehensif tentang atribut dan aktivitas entitas
Format setiap entitas sebagai ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. Dari entitas yang diidentifikasi pada langkah 1, identifikasi semua pasangan (source_entity, target_entity) yang *jelas berhubungan* satu sama lain.
Untuk setiap pasangan entitas yang berhubungan, ekstrak informasi berikut:
- source_entity: nama entitas sumber, seperti yang diidentifikasi pada langkah 1
- target_entity: nama entitas target, seperti yang diidentifikasi pada langkah 1
- relationship_description: penjelasan mengapa entitas sumber dan entitas target saling berhubungan
- relationship_strength: skor numerik 1-10 yang menunjukkan kekuatan hubungan antara entitas sumber dan entitas target
- relationship_keywords: satu atau lebih kata kunci tingkat tinggi yang merangkum sifat menyeluruh dari hubungan, fokus pada konsep atau tema daripada detail spesifik
Format setiap hubungan sebagai ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identifikasi kata kunci tingkat tinggi yang merangkum konsep utama, tema, atau topik dari keseluruhan teks. Ini harus menangkap ide-ide menyeluruh yang ada dalam dokumen.
Format kata kunci tingkat konten sebagai ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Kembalikan output dalam Bahasa Indonesia sebagai satu daftar dari semua entitas dan hubungan yang diidentifikasi pada langkah 1 dan 2. Gunakan **{record_delimiter}** sebagai pembatas daftar.

5. Setelah selesai, output {completion_delimiter}

######################
-Contoh-
######################
Contoh 1:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak]
Text:
Pasal 27 ayat (1) Undang-Undang Nomor 45 Tahun 2009 tentang Perikanan menyatakan bahwa setiap orang yang mengoperasikan kapal penangkap ikan berbendera Indonesia di wilayah pengelolaan perikanan Republik Indonesia wajib memiliki Surat Izin Penangkapan Ikan (SIPI). Berdasarkan ketentuan Pasal 93 ayat (1), pengoperasian kapal penangkap ikan tanpa memiliki SIPI dipidana dengan pidana penjara paling lama 6 (enam) tahun dan denda paling banyak Rp2.000.000.000,00 (dua miliar rupiah). Menteri Kelautan dan Perikanan berwenang menetapkan alokasi penangkapan ikan dan menerbitkan izin usaha perikanan.

################
Output:
("entity"{tuple_delimiter}"UU Nomor 45 Tahun 2009"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Undang-Undang tentang Perubahan atas Undang-Undang Nomor 31 Tahun 2004 tentang Perikanan yang mengatur tata kelola perikanan nasional."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 27"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal yang mengatur norma kewajiban kepemilikan Surat Izin Penangkapan Ikan bagi setiap kapal perikanan."){record_delimiter}
("entity"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"struktur"{tuple_delimiter}"Ayat pertama dari Pasal 27 yang memuat rumusan imperatif kewajiban memiliki SIPI."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 93"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal ketentuan pidana yang mengatur ancaman sanksi atas pengoperasian kapal tanpa izin."){record_delimiter}
("entity"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"pihak"{tuple_delimiter}"Subjek hukum perorangan atau korporasi yang mengoperasikan kapal penangkap ikan."){record_delimiter}
("entity"{tuple_delimiter}"Menteri Kelautan dan Perikanan"{tuple_delimiter}"pihak"{tuple_delimiter}"Pejabat pemerintah yang berwenang menetapkan alokasi penangkapan ikan dan menerbitkan izin usaha perikanan."){record_delimiter}
("entity"{tuple_delimiter}"Surat Izin Penangkapan Ikan"{tuple_delimiter}"konsep"{tuple_delimiter}"Izin tertulis resmi bagi kapal perikanan untuk melakukan kegiatan penangkapan ikan di perairan Indonesia."){record_delimiter}
("entity"{tuple_delimiter}"Kapal Penangkap Ikan"{tuple_delimiter}"konsep"{tuple_delimiter}"Kapal bermotor yang dipergunakan khusus untuk kegiatan menangkap dan mendinginkan hasil tangkapan."){record_delimiter}
("entity"{tuple_delimiter}"Wilayah Pengelolaan Perikanan Republik Indonesia"{tuple_delimiter}"konsep"{tuple_delimiter}"Wilayah perairan Indonesia dan ZEEI tempat dilakukannya tata kelola perikanan."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Memiliki SIPI"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Kewajiban hukum imperatif bagi operator kapal penangkap ikan untuk mengantongi izin resmi sebelum melaut."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"sanksi"{tuple_delimiter}"Sanksi pidana kurungan badan paling lama 6 tahun atas pengoperasian kapal tanpa izin tangkap."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp2.000.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Sanksi kumulatif denda finansial maksimal dua miliar rupiah atas pelanggaran Pasal 27."){record_delimiter}
("relationship"{tuple_delimiter}"UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 27"{tuple_delimiter}"UU Nomor 45 Tahun 2009 memuat Pasal 27 sebagai ketentuan regulasi izin tangkap perikanan."{tuple_delimiter}"hierarki peraturan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 27"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"Pasal 27 memuat Ayat 1 sebagai rumusan norma kewajiban izin operasional kapal."{tuple_delimiter}"hierarki struktur"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Ayat 1 menetapkan Setiap Orang sebagai subjek hukum yang dikenai kewajiban perizinan."{tuple_delimiter}"subjek hukum"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Kewajiban Memiliki SIPI"{tuple_delimiter}"Setiap orang yang mengoperasikan kapal penangkap ikan memikul kewajiban memiliki SIPI."{tuple_delimiter}"subjek kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memiliki SIPI"{tuple_delimiter}"Surat Izin Penangkapan Ikan"{tuple_delimiter}"Kewajiban hukum diwujudkan dalam bentuk kepemilikan dokumen resmi SIPI."{tuple_delimiter}"objek kewajiban"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Surat Izin Penangkapan Ikan"{tuple_delimiter}"Wilayah Pengelolaan Perikanan Republik Indonesia"{tuple_delimiter}"SIPI berlaku sah untuk kegiatan tangkap di wilayah perairan Indonesia."{tuple_delimiter}"wilayah keberlakuan"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Menteri Kelautan dan Perikanan"{tuple_delimiter}"Surat Izin Penangkapan Ikan"{tuple_delimiter}"Menteri berwenang menyelenggarakan tata kelola dan menerbitkan izin penangkapan ikan."{tuple_delimiter}"kewenangan penerbitan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 27"{tuple_delimiter}"Pasal 93"{tuple_delimiter}"Pasal 27 menetapkan norma kewajiban perizinan sedangkan Pasal 93 menetapkan ancaman sanksi pidananya."{tuple_delimiter}"rujukan sanksi pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"Pasal 93 ayat 1 mengancamkan pidana penjara paling lama 6 tahun bagi pelanggar izin tangkap."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93"{tuple_delimiter}"Denda Paling Banyak Rp2.000.000.000,00"{tuple_delimiter}"Pasal 93 ayat 1 memuat sanksi denda finansial maksimal dua miliar rupiah."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("content_keywords"{tuple_delimiter}"perizinan perikanan, surat izin penangkapan ikan, kapal penangkap ikan, sanksi pidana perikanan, menteri kelautan"){completion_delimiter}
#############################
Contoh 2:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak]
Text:
Pasal 219 ayat (1) Undang-Undang Nomor 17 Tahun 2008 tentang Pelayaran mengatur bahwa setiap kapal yang berlayar di perairan Indonesia wajib memiliki Surat Persetujuan Berlayar (SPB) yang dikeluarkan oleh Syahbandar setelah kapal memenuhi persyaratan kelaiklautan kapal. Nahkoda yang melayarkan kapal tanpa memiliki Surat Persetujuan Berlayar dari Syahbandar sebagaimana dimaksud dalam Pasal 323 ayat (1) dipidana dengan pidana penjara paling lama 5 (lima) tahun dan denda paling banyak Rp600.000.000,00 (enam ratus juta rupiah). Setiap kapal berhak memperoleh pelayanan kepelabuhanan secara tertib dan adil.

################
Output:
("entity"{tuple_delimiter}"UU Nomor 17 Tahun 2008 tentang Pelayaran"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Undang-Undang yang mengatur keselamatan pelayaran, kepelabuhanan, dan angkutan perairan di Indonesia."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 219"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal yang mengatur kewajiban kepemilikan Surat Persetujuan Berlayar bagi seluruh kapal."){record_delimiter}
("entity"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"struktur"{tuple_delimiter}"Ayat pertama dari Pasal 219 yang memuat norma keharusan memiliki SPB sebelum berlayar."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 323"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal ketentuan pidana yang mengatur sanksi bagi nahkoda yang melayarkan kapal tanpa izin resmi."){record_delimiter}
("entity"{tuple_delimiter}"Syahbandar"{tuple_delimiter}"pihak"{tuple_delimiter}"Pejabat pemerintah di pelabuhan yang memiliki otoritas tertinggi memeriksa kelaiklautan dan menerbitkan SPB."){record_delimiter}
("entity"{tuple_delimiter}"Nahkoda"{tuple_delimiter}"pihak"{tuple_delimiter}"Pemimpin kapal yang bertanggung jawab penuh atas kelaiklautan, keselamatan, dan kepatuhan navigasi kapal."){record_delimiter}
("entity"{tuple_delimiter}"Surat Persetujuan Berlayar"{tuple_delimiter}"konsep"{tuple_delimiter}"Dokumen izin resmi negara yang menyatakan kapal telah memenuhi syarat kelaiklautan dan diizinkan berlayar."){record_delimiter}
("entity"{tuple_delimiter}"Kelaiklautan Kapal"{tuple_delimiter}"konsep"{tuple_delimiter}"Keadaan kapal yang memenuhi persyaratan keselamatan pengawakan, muatan, dan navigasi pelayaran."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Memiliki SPB"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Kewajiban hukum mutlak bagi nahkoda untuk mengantongi persetujuan syahbandar sebelum kapal bertolak."){record_delimiter}
("entity"{tuple_delimiter}"Hak Pelayanan Kepelabuhanan"{tuple_delimiter}"hak"{tuple_delimiter}"Hak hukum pengguna jasa kapal untuk mendapatkan fasilitas pelayanan kepelabuhanan yang tertib dan adil."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara Paling Lama 5 Tahun"{tuple_delimiter}"sanksi"{tuple_delimiter}"Ancaman hukuman kurungan badan maksimal 5 tahun bagi nahkoda yang melayarkan kapal tanpa SPB."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp600.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Ancaman denda pidana maksimal enam ratus juta rupiah atas pelanggaran Pasal 219 ayat 1."){record_delimiter}
("relationship"{tuple_delimiter}"UU Nomor 17 Tahun 2008 tentang Pelayaran"{tuple_delimiter}"Pasal 219"{tuple_delimiter}"UU Pelayaran memuat Pasal 219 dalam bab keselamatan dan keamanan pelayaran."{tuple_delimiter}"hierarki peraturan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 219"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"Pasal 219 memuat Ayat 1 sebagai rumusan norma imperatif izin berlayar kapal."{tuple_delimiter}"hierarki struktur"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"Nahkoda"{tuple_delimiter}"Ayat 1 mewajibkan Nahkoda untuk memastikan terpenuhinya persetujuan berlayar sebelum kapal bertolak."{tuple_delimiter}"subjek kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Nahkoda"{tuple_delimiter}"Kewajiban Memiliki SPB"{tuple_delimiter}"Nahkoda memikul tanggung jawab pidana atas kewajiban kepemilikan SPB sebelum melaut."{tuple_delimiter}"penanggung jawab kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Syahbandar"{tuple_delimiter}"Surat Persetujuan Berlayar"{tuple_delimiter}"Syahbandar memegang kewenangan eksklusif memeriksa kelaiklautan dan menerbitkan SPB."{tuple_delimiter}"kewenangan penerbitan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Surat Persetujuan Berlayar"{tuple_delimiter}"Kelaiklautan Kapal"{tuple_delimiter}"Penerbitan SPB mensyaratkan pemenuhan standar kelaiklautan kapal secara menyeluruh."{tuple_delimiter}"prasyarat kelaikan"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 219"{tuple_delimiter}"Pasal 323"{tuple_delimiter}"Pasal 219 menetapkan norma kewajiban SPB sedangkan Pasal 323 menetapkan ancaman sanksi pidananya."{tuple_delimiter}"rujukan sanksi pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 323"{tuple_delimiter}"Pidana Penjara Paling Lama 5 Tahun"{tuple_delimiter}"Pasal 323 ayat 1 menetapkan ancaman penjara maksimal 5 tahun bagi nahkoda tanpa SPB."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 323"{tuple_delimiter}"Denda Paling Banyak Rp600.000.000,00"{tuple_delimiter}"Pasal 323 ayat 1 memuat sanksi kumulatif denda maksimal enam ratus juta rupiah."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Nahkoda"{tuple_delimiter}"Hak Pelayanan Kepelabuhanan"{tuple_delimiter}"Kapal dan nahkoda berhak menerima pelayanan kepelabuhanan yang tertib dan adil."{tuple_delimiter}"penerima hak"{tuple_delimiter}8){record_delimiter}
("content_keywords"{tuple_delimiter}"keselamatan pelayaran, syahbandar, surat persetujuan berlayar, nahkoda, sanksi kelaiklautan"){completion_delimiter}
#############################
Contoh 3:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak]
Text:
Pasal 8 ayat (1) Undang-Undang Perikanan melarang setiap orang melakukan penangkapan ikan dengan menggunakan bahan kimia, bahan biologis, bahan peledak, racun, dan/atau alat penangkapan ikan yang merusak kelestarian sumber daya ikan di wilayah perairan Indonesia. Pelanggaran terhadap larangan penangkapan ikan yang merusak ini sebagaimana diatur dalam Pasal 84 ayat (1) dipidana dengan pidana penjara paling lama 6 (enam) tahun dan denda paling banyak Rp1.200.000.000,00 (satu miliar dua ratus juta rupiah). Pemerintah berkewajiban melindungi dan memberdayakan Nelayan Kecil melalui penyediaan sarana penangkapan ikan ramah lingkungan.

################
Output:
("entity"{tuple_delimiter}"Undang-Undang Perikanan"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Undang-Undang pokok perikanan Indonesia yang mengatur perlindungan sumber daya hayati laut."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 8"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal yang mengatur norma larangan penggunaan bahan berbahaya dan alat tangkap perusak lingkungan."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 84"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal penjatuhan sanksi pidana atas perbuatan destructive fishing di perairan Indonesia."){record_delimiter}
("entity"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"pihak"{tuple_delimiter}"Subjek hukum yang dilarang menggunakan alat perusak dalam penangkapan ikan."){record_delimiter}
("entity"{tuple_delimiter}"Pemerintah"{tuple_delimiter}"pihak"{tuple_delimiter}"Penyelenggara negara yang berkewajiban membina dan melindungi kegiatan perikanan rakyat."){record_delimiter}
("entity"{tuple_delimiter}"Nelayan Kecil"{tuple_delimiter}"pihak"{tuple_delimiter}"Masyarakat yang mata pencahariannya menangkap ikan secara tradisional dengan perahu kecil."){record_delimiter}
("entity"{tuple_delimiter}"Bahan Peledak"{tuple_delimiter}"konsep"{tuple_delimiter}"Bahan peledak destruktif yang dilarang keras untuk digunakan dalam aktivitas penangkapan ikan."){record_delimiter}
("entity"{tuple_delimiter}"Kelestarian Sumber Daya Ikan"{tuple_delimiter}"konsep"{tuple_delimiter}"Kondisi terjaganya daya dukung dan populasi biota perairan secara berkelanjutan."){record_delimiter}
("entity"{tuple_delimiter}"Larangan Penangkapan Ikan Merusak"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Norma larangan negatif untuk tidak merusak lingkungan perairan dengan bahan peledak atau racun."){record_delimiter}
("entity"{tuple_delimiter}"Hak Pemberdayaan Nelayan Kecil"{tuple_delimiter}"hak"{tuple_delimiter}"Hak hukum nelayan kecil untuk mendapatkan pembinaan dan bantuan sarana tangkap ramah lingkungan."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"sanksi"{tuple_delimiter}"Sanksi pidana penjara maksimal 6 tahun atas perbuatan penangkapan ikan destruktif."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp1.200.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Sanksi finansial denda maksimal 1,2 miliar rupiah atas pelanggaran Pasal 8."){record_delimiter}
("relationship"{tuple_delimiter}"Undang-Undang Perikanan"{tuple_delimiter}"Pasal 8"{tuple_delimiter}"Undang-Undang Perikanan memuat Pasal 8 dalam kerangka pelestarian ekosistem laut."{tuple_delimiter}"hierarki peraturan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 8"{tuple_delimiter}"Larangan Penangkapan Ikan Merusak"{tuple_delimiter}"Pasal 8 merumuskan larangan keras pemanfaatan bahan kimia dan peledak penangkapan ikan."{tuple_delimiter}"pengaturan larangan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Larangan Penangkapan Ikan Merusak"{tuple_delimiter}"Setiap orang terikat secara hukum pada larangan melakukan penangkapan ikan destruktif."{tuple_delimiter}"subjek larangan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Bahan Peledak"{tuple_delimiter}"Kelestarian Sumber Daya Ikan"{tuple_delimiter}"Penggunaan bahan peledak secara langsung merusak dan menghancurkan kelestarian sumber daya ikan."{tuple_delimiter}"dampak perusakan ekosistem"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 8"{tuple_delimiter}"Pasal 84"{tuple_delimiter}"Pasal 8 merupakan pasal larangan norma yang ancaman sanksi pidananya dirumuskan pada Pasal 84."{tuple_delimiter}"rujukan sanksi pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 84"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"Pasal 84 ayat 1 menjatuhkan pidana penjara maksimal 6 tahun bagi pelaku perusakan."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 84"{tuple_delimiter}"Denda Paling Banyak Rp1.200.000.000,00"{tuple_delimiter}"Pasal 84 ayat 1 memuat sanksi denda kumulatif maksimal 1,2 miliar rupiah."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pemerintah"{tuple_delimiter}"Nelayan Kecil"{tuple_delimiter}"Pemerintah berkewajiban melindungi dan memberdayakan nelayan kecil dengan alat ramah lingkungan."{tuple_delimiter}"kewajiban pembinaan"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Nelayan Kecil"{tuple_delimiter}"Hak Pemberdayaan Nelayan Kecil"{tuple_delimiter}"Nelayan kecil berhak memperoleh pembinaan dan bantuan sarana penangkapan ikan ramah lingkungan."{tuple_delimiter}"penerima hak"{tuple_delimiter}9){record_delimiter}
("content_keywords"{tuple_delimiter}"destructive fishing, bahan peledak perikanan, sanksi perusakan biota laut, perlindungan nelayan kecil"){completion_delimiter}
#############################
-Data Sebenarnya-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""

PROMPTS["summarize_entity_descriptions"] = """Anda adalah asisten yang bertanggung jawab menghasilkan ringkasan komprehensif dari data yang diberikan di bawah ini.
Diberikan satu atau dua entitas, dan daftar deskripsi, semuanya terkait dengan entitas yang sama atau kelompok entitas.
Silakan gabungkan semua ini menjadi satu deskripsi komprehensif. Pastikan untuk menyertakan informasi yang dikumpulkan dari semua deskripsi.
Jika deskripsi yang diberikan bertentangan, silakan selesaikan kontradiksi tersebut dan berikan ringkasan tunggal yang koheren.
Pastikan ditulis dalam orang ketiga, dan sertakan nama entitas sehingga kita memiliki konteks lengkap.

#######
-Data-
Entitas: {entity_name}
Daftar Deskripsi: {description_list}
#######
Output:
"""

PROMPTS["minirag_query2kwd"] = """---Peran---
Anda adalah asisten ahli hukum kelautan, perikanan, dan pelayaran yang bertugas mengekstrak kata kunci pencarian dari pertanyaan pengguna.

---Instruksi---
- Output kata kunci dalam format JSON.
- JSON harus memiliki dua kunci:
  - "answer_type_keywords": jenis jawaban yang diharapkan dari pool.
  - "entities_from_query": entitas atau detail spesifik dari pertanyaan pengguna.

-Data Sebenarnya-
######################
Query: {query}
Answer type pool: {TYPE_POOL}
######################
Output:
"""

PROMPTS["rag_response"] = """---Konteks---

{context_data}

---Peran---

Anda adalah SinkronAIR, asisten hukum maritim BRIN yang menjawab pertanyaan berbasis skenario kasus HANYA menggunakan informasi dari konteks pasal regulasi yang diberikan.

---Instruksi---

1. Jawab dalam Bahasa Indonesia yang baku, tegas, dan berbobot yuridis.
2. Dasarkan jawaban HANYA pada konteks yang diberikan. Jika informasi tidak ditemukan dalam konteks, nyatakan secara jujur bahwa informasi tidak tersedia -- JANGAN mengarang pasal.
3. Sebutkan dasar hukum secara eksplisit (nama regulasi, pasal, dan ayat).
4. Jawab langsung pada substansi tanpa mengulang pertanyaan.

{response_type}
"""

PROMPTS["keywords_extraction"] = """---Peran---
Anda adalah asisten yang bertugas mengidentifikasi kata kunci tingkat tinggi dan tingkat rendah dalam pertanyaan pengguna mengenai regulasi hukum kemaritiman.

---Instruksi---
- Output kata kunci dalam format JSON dengan dua kunci: "high_level_keywords" dan "low_level_keywords".
"""

PROMPTS[
    "entiti_continue_extraction"
] = """BANYAK entitas yang terlewat dalam ekstraksi terakhir. Tambahkan di bawah ini menggunakan format yang sama:
"""

PROMPTS[
    "entiti_continue_extraction_mini"
] = """BANYAK entitas yang terlewat dalam ekstraksi terakhir.
Setelah merangkum semua informasi yang sebelumnya diekstrak, dibandingkan dengan teks asli, terlihat bahwa informasi berikut terutama dihilangkan:
{omit}

Jenis entitas yang perlu ditambahkan dapat diperoleh dari Entity_types,
atau Anda dapat menambahkannya sendiri.

Entity_types: {entity_types}


Tambahkan di bawah ini menggunakan format yang sama:
"""

PROMPTS[
    "entiti_if_loop_extraction"
] = """Sepertinya beberapa entitas mungkin masih terlewat. Jawab YA | TIDAK jika masih ada entitas yang perlu ditambahkan.
"""

PROMPTS["fail_response"] = "Maaf, saya tidak dapat memberikan jawaban untuk pertanyaan tersebut."

PROMPTS["naive_rag_response"] = """---Peran---

Anda adalah asisten yang menjawab pertanyaan dengan sangat singkat, padat, dan langsung pada intinya.

---Tujuan---

Jawab pertanyaan pengguna berdasarkan dokumen yang diberikan.
PENTING:
1. Jawaban HARUS sangat singkat (maksimal 3 kalimat).
2. Langsung ke inti jawaban. Jangan gunakan kata pengantar.
3. Jangan mencoba merangkum semua dokumen. Ambil saja poin utamanya.

---Panjang dan format respons target---

{response_type}

---Dokumen---

{content_data}
"""

PROMPTS["entity_extraction_noDes"] = PROMPTS["entity_extraction"]

__all__ = [
    "GRAPH_FIELD_SEP",
    "PROMPTS",
    "DEFAULT_TUPLE_DELIMITER",
    "DEFAULT_RECORD_DELIMITER",
    "DEFAULT_COMPLETION_DELIMITER",
    "PROCESS_TICKERS",
    "ENTITY_TYPES",
    "DEFAULT_ENTITY_TYPES",
]
