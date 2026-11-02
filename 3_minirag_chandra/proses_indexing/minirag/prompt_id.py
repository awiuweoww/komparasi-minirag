# Indonesian prompt templates for MiniRAG (prompt_id.py)
# This file provides localized prompt strings used by minirag/operate.py.

GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Jenis entitas default yang cocok untuk dokumen hukum
PROMPTS["DEFAULT_ENTITY_TYPES"] = [
    "Peraturan",
    "Pasal",
    "Lembaga/Jabatan",
    "Konsep Hukum",
    "Tindakan Hukum",
    "Lokasi",
    "Objek",
    "Sanksi",
]

PROMPTS["entity_extraction"] = (
  "-Tujuan-\n"
  "Diberikan sebuah teks dokumen yang relevan dan daftar jenis entitas, identifikasi semua entitas dari jenis-jenis tersebut dan semua hubungan di antara entitas yang diidentifikasi.\n\n"
  "-Langkah-\n"
  "1. Identifikasi semua entitas. Untuk setiap entitas yang ditemukan, ekstrak informasi berikut:\n"
  "- nama_entitas: Nama entitas sesuai bahasa teks input.\n"
  "- jenis_entitas: Salah satu jenis berikut: [{entity_types}]\n"
  "- deskripsi_entitas: Deskripsi komprehensif mengenai atribut atau peran entitas dalam konteks teks.\n"
  "Format tiap entitas: (\"entity\"{tuple_delimiter}<nama_entitas>{tuple_delimiter}<jenis_entitas>{tuple_delimiter}<deskripsi_entitas>)\n\n"
  "2. Dari entitas yang diidentifikasi, tentukan semua pasangan (entitas_sumber, entitas_target) yang jelas berhubungan satu sama lain. Untuk setiap pasangan, ekstrak:\n"
  "- entitas_sumber: nama entitas sumber seperti di langkah 1\n"
  "- entitas_target: nama entitas target seperti di langkah 1\n"
  "- deskripsi_hubungan: Jelaskan mengapa kedua entitas berhubungan\n"
  "- kata_kunci_hubungan: Satu atau beberapa kata kunci yang merangkum sifat hubungan\n"
  "- kekuatan_hubungan: Skor numerik 1-10 yang merefleksikan kekuatan atau kepastian hubungan\n"
  "Format tiap hubungan: (\"relationship\"{tuple_delimiter}<entitas_sumber>{tuple_delimiter}<entitas_target>{tuple_delimiter}<deskripsi_hubungan>{tuple_delimiter}<kata_kunci_hubungan>{tuple_delimiter}<kekuatan_hubungan>)\n\n"
  "3. Identifikasi kata kunci tingkat tinggi yang merangkum topik utama teks dan keluarkan sebagai (\"content_keywords\"{tuple_delimiter}<kata_kunci_utama>)\n\n"
  "4. Kembalikan semua entitas dan hubungan sebagai satu daftar tunggal, gunakan **{record_delimiter}** sebagai pemisah antar rekaman.\n\n"
  "5. Setelah selesai, keluarkan {completion_delimiter}\n"
)

PROMPTS["summarize_entity_descriptions"] = (
    "Anda adalah asisten yang menyusun ringkasan komprehensif dari beberapa deskripsi entitas yang terkait. "
    "Gabungkan deskripsi menjadi satu deskripsi yang koheren dalam bahasa Indonesia, tuliskan dalam orang ketiga.\n\n"
    "Data:\nEntities: {entity_name}\nDescription List: {description_list}\nOutput:"
)

PROMPTS["entiti_continue_extraction"] = (
    "Beberapa entitas mungkin terlewat. Tambahkan entitas yang terlewat menggunakan format yang sama seperti sebelumnya."
)

PROMPTS["entiti_continue_extraction_mini"] = (
    "Beberapa entitas hukum terlewatkan. Bandingkan hasil ekstraksi sebelumnya dengan teks asli dan tambahkan entitas yang hilang. Jenis entitas yang direkomendasikan: {entity_types}."
)

PROMPTS["minirag_query2kwd"] = (
  "---Peran---\nAnda adalah asisten yang bertugas mengidentifikasi jenis jawaban dan kata kunci dari kueri pengguna.\n\n"
  "---Tujuan---\nDiberikan sebuah kueri, keluarkan JSON yang berisi 'answer_type_keywords' dan 'entities_from_query'.\n\n"
  "Instruksi: Pilih maksimal 3 kata kunci jenis jawaban yang paling relevan dan ekstrak entitas spesifik dari kueri.\n\n"
  "Kueri: {query}\nOutput:"
)

PROMPTS["entiti_if_loop_extraction"] = (
  "Tampaknya beberapa entitas mungkin masih terlewat. Jawab YA atau TIDAK apakah masih ada entitas yang perlu ditambahkan."
)

PROMPTS["fail_response"] = "Maaf, saya tidak dapat memberikan jawaban atas pertanyaan terkait dokumen hukum ini."

PROMPTS["rag_response"] = (
  "---Peran---\nAnda adalah asisten AI yang merespons pertanyaan berdasarkan dokumen hukum yang disediakan sebagai konteks.\n\n"
  "---Tujuan---\nHasilkan jawaban yang singkat, tepat, dan berbasis bukti dalam bahasa Indonesia. Jika informasi tidak ada dalam konteks, nyatakan 'Tidak tersedia dalam sumber.' Jangan mengarang fakta.\n\n"
  "---Panjang dan format respons target---\n{response_type}\n\n"
  "---Tabel data (Kutipan Dokumen Hukum)---\n{context_data}\n\n"
  "Susun respons dalam format markdown. Sertakan rujukan pasal atau fragmen bukti jika tersedia dalam konteks."
)

PROMPTS["keywords_extraction"] = (
  "---Peran---\nAnda adalah asisten yang mengidentifikasi kata kunci tingkat tinggi dan rendah dari kueri pengguna terkait dokumen hukum.\n\n"
  "---Tujuan---\nBeri keluaran dalam format JSON dengan dua kunci: 'high_level_keywords' dan 'low_level_keywords'.\n\n"
  "Kueri: {query}\nOutput:"
)

PROMPTS["naive_rag_response"] = (
  "---Peran---\nAnda adalah asisten AI yang merespons pertanyaan berdasarkan dokumen yang diberikan.\n\n"
  "---Tujuan---\nBuat jawaban singkat dalam bahasa Indonesia yang hanya menggunakan informasi yang ada dalam dokumen. Jika tidak ada informasi yang relevan, katakan 'Tidak tersedia dalam sumber.'\n\n"
  "---Panjang dan format respons target---\n{response_type}\n\n---Dokumen---\n{content_data}\n\n"
  "Susun respons dalam format markdown."
)

# Tambahan: Pastikan semua kunci lain yang digunakan di operate.py ada juga dalam versi Bahasa Indonesia
PROMPTS["summarize_entity_descriptions"] = "Anda adalah asisten yang menyusun ringkasan komprehensif dari daftar deskripsi entitas. Gabungkan menjadi satu deskripsi koheren dalam bahasa Indonesia.\nData:\nEntities: {entity_name}\nDescription List: {description_list}\nOutput:"

PROMPTS["entiti_continue_extraction"] = "BANYAK entitas mungkin terlewatkan pada ekstraksi sebelumnya. Tambahkan entitas yang hilang menggunakan format yang sama."

PROMPTS["entiti_continue_extraction_mini"] = (
  "Beberapa entitas terlewat setelah ekstraksi sebelumnya. Bandingkan hasil ekstraksi dengan teks asli dan tambahkan informasi yang hilang: {omit}\n"
  "Jenis entitas yang direkomendasikan: {entity_types}\n"
  "Tambahkan entitas dan hubungan yang hilang di bawah ini menggunakan format yang sama."
)

PROMPTS["entiti_if_loop_extraction"] = "Tampaknya beberapa entitas mungkin masih terlewat. Jawab YA | TIDAK jika masih ada entitas yang perlu ditambahkan."

PROMPTS["minirag_query2kwd"] = (
  "---Peran---\nAnda adalah asisten yang mengidentifikasi kata kunci jenis-jawaban dan entitas dalam kueri.\n\n"
  "---Tujuan---\nKeluarkan JSON dengan kunci 'answer_type_keywords' dan 'entities_from_query'.\n"
  "Kueri: {query}\nOutput:"
)

PROMPTS["entiti_if_loop_extraction"] = "Tampaknya beberapa entitas hukum (mis. pasal, definisi, lembaga) mungkin masih terlewatkan. Jawab YA atau TIDAK."

PROMPTS["fail_response"] = "Maaf, saya tidak dapat memberikan jawaban atas pertanyaan ini."

PROMPTS["rag_response"] = (
  "---Peran---\nAnda adalah asisten AI yang membantu merespons pertanyaan berdasarkan informasi dari dokumen yang disediakan.\n\n"
  "---Tujuan---\nHasilkan jawaban yang akurat dan berbasis bukti dalam bahasa Indonesia. Jika informasi tidak ada dalam sumber, nyatakan 'Tidak tersedia dalam sumber.'\n\n"
  "---Panjang dan format respons target---\n{response_type}\n\n"
  "---Tabel data / Dokumen Konteks---\n{context_data}\n\n"
  "Susun respons dalam format markdown dan sertakan referensi pasal atau kutipan jika tersedia."
)

PROMPTS["keywords_extraction"] = (
  "---Peran---\nAnda adalah asisten yang mengidentifikasi kata kunci tingkat tinggi dan rendah dari kueri.\n\n"
  "---Tujuan---\nKeluarkan JSON dengan 'high_level_keywords' dan 'low_level_keywords'.\n"
  "Kueri: {query}\nOutput:"
)

PROMPTS["naive_rag_response"] = (
  "---Peran---\nAnda adalah asisten AI yang merespons pertanyaan berdasarkan dokumen yang diberikan.\n\n"
  "---Tujuan---\nBuat jawaban singkat dalam bahasa Indonesia yang hanya mengandalkan informasi yang tersedia dalam dokumen. Jika tidak ada, katakan demikian.\n\n"
  "---Panjang dan format respons target---\n{response_type}\n\n---Dokumen---\n{content_data}\n\n"
  "Susun respons dalam format markdown."
)

# End of file
# Bagian lain dari prompt.py tetap sama...

GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Jenis Entitas Default disesuaikan untuk konteks hukum
PROMPTS["DEFAULT_ENTITY_TYPES"] = ["Peraturan", "Pasal", "Lembaga/Jabatan", "Konsep Hukum", "Tindakan Hukum", "Lokasi", "Objek", "Sanksi"]


PROMPTS["entity_extraction"] = """-Tujuan-
Diberikan sebuah dokumen hukum (misalnya Undang-Undang) dan daftar jenis entitas yang relevan dengan hukum, identifikasi semua entitas dari jenis tersebut dari teks dan semua hubungan di antara entitas yang diidentifikasi.

-Jenis Entitas yang Relevan untuk Dokumen Hukum-
Fokus pada jenis entitas berikut: [{entity_types}] atau jenis lain yang relevan secara spesifik dalam konteks hukum seperti:
- Peraturan: Nama atau nomor spesifik dari sebuah Undang-Undang, Peraturan Pemerintah, Keputusan Menteri, dll.
- Pasal: Referensi spesifik ke bagian/pasal/ayat dalam sebuah peraturan.
- Lembaga/Jabatan: Institusi pemerintah atau jabatan resmi yang disebut (misal: Pemerintah, Menteri, Syahbandar, Otoritas Pelabuhan, Tim Ahli Cagar Budaya).
- Konsep Hukum: Terminologi hukum atau definisi kunci (misal: Cagar Budaya, Pelayaran, Kelaiklautan Kapal, Hipotek Kapal, Kompensasi, Izin).
- Tindakan Hukum: Proses atau aktivitas yang diatur oleh hukum (misal: Pelestarian, Pendaftaran, Penetapan, Pengawasan, Penyidikan, Pemanduan, Penyelamatan).
- Lokasi: Tempat geografis yang relevan secara hukum (misal: Perairan Indonesia, Pelabuhan, Situs Cagar Budaya, Kawasan Cagar Budaya, Zona Inti).
- Objek: Benda fisik yang menjadi subjek hukum (misal: Kapal, Benda Cagar Budaya, Bangunan Cagar Budaya, Kerangka Kapal, Sertifikat).
- Peran: Pihak atau subjek hukum (misal: Nakhoda, Awak Kapal, Pemilik Kapal, Setiap Orang, Badan Usaha).
- Sanksi: Konsekuensi hukum atas pelanggaran (misal: Pidana Penjara, Denda Administratif, Pencabutan Izin).

-Langkah-langkah-
1. Identifikasi semua entitas yang relevan. Untuk setiap entitas yang diidentifikasi, ekstrak informasi berikut:
- nama_entitas: Nama entitas sebagaimana tertulis dalam teks (misal: "Cagar Budaya", "Pasal 5", "Menteri", "Pelestarian"). Gunakan bahasa asli teks.
- jenis_entitas: Salah satu jenis entitas relevan yang tercantum di atas.
- deskripsi_entitas: Deskripsi singkat tentang entitas tersebut berdasarkan konteks dalam teks.
Format setiap entitas sebagai ("entity"{tuple_delimiter}<nama_entitas>{tuple_delimiter}<jenis_entitas>{tuple_delimiter}<deskripsi_entitas>)

2. Dari entitas yang diidentifikasi di langkah 1, identifikasi semua pasangan (entitas_sumber, entitas_target) yang *jelas memiliki hubungan hukum* satu sama lain (misalnya, definisi, kewajiban, kewenangan, larangan, kriteria, sanksi).
Untuk setiap pasangan entitas terkait, ekstrak informasi berikut:
- entitas_sumber: nama entitas sumber, seperti yang diidentifikasi di langkah 1.
- entitas_target: nama entitas target, seperti yang diidentifikasi di langkah 1.
- deskripsi_hubungan: penjelasan mengenai sifat hubungan hukum antar entitas (misal: "mendefinisikan", "mewajibkan", "melarang", "memberi wewenang kepada", "merupakan kriteria untuk", "dikenakan sanksi berupa").
- kekuatan_hubungan: skor numerik (1-10) yang menunjukkan kekuatan atau kepastian hubungan hukum tersebut.
- kata_kunci_hubungan: satu atau lebih kata kunci yang merangkum sifat hubungan (misal: "definisi", "kewajiban", "larangan", "kewenangan", "kriteria", "sanksi").
Format setiap hubungan sebagai ("relationship"{tuple_delimiter}<entitas_sumber>{tuple_delimiter}<entitas_target>{tuple_delimiter}<deskripsi_hubungan>{tuple_delimiter}<kata_kunci_hubungan>{tuple_delimiter}<kekuatan_hubungan>)

3. Identifikasi kata kunci utama yang merangkum topik atau konsep hukum utama dari keseluruhan teks yang dianalisis.
Format kata kunci konten sebagai ("content_keywords"{tuple_delimiter}<kata_kunci_utama>)

4. Kembalikan keluaran sebagai satu daftar tunggal berisi semua entitas dan hubungan yang diidentifikasi. Gunakan **{record_delimiter}** sebagai pemisah antar rekaman (entity atau relationship).

5. Setelah selesai, keluarkan {completion_delimiter}.

######################
-Contoh-contoh dari Undang-Undang Indonesia-
######################
Contoh 1 (Dari UU No. 11 Tahun 2010 tentang Cagar Budaya):

Jenis_Entitas: [Peraturan, Pasal, Konsep Hukum, Tindakan Hukum, Lembaga/Jabatan, Lokasi]
Teks:
Pasal 1
Dalam Undang-Undang ini yang dimaksud dengan:
1. Cagar Budaya adalah warisan budaya bersifat kebendaan berupa Benda Cagar Budaya, Bangunan Cagar Budaya, Struktur Cagar Budaya, Situs Cagar Budaya, dan Kawasan Cagar Budaya di darat dan/atau di air yang perlu dilestarikan keberadaannya karena memiliki nilai penting bagi sejarah, ilmu pengetahuan, pendidikan, agama, dan/atau kebudayaan melalui proses penetapan.
...
22. Pelestarian adalah upaya dinamis untuk mempertahankan keberadaan Cagar Budaya dan nilainya dengan cara melindungi, mengembangkan, dan memanfaatkannya.
23. Pelindungan adalah upaya mencegah dan menanggulangi dari kerusakan, kehancuran, atau kemusnahan dengan cara Penyelamatan, Pengamanan, Zonasi, Pemeliharaan, dan Pemugaran Cagar Budaya.
################
Keluaran:
("entity"{tuple_delimiter}"Pasal 1"{tuple_delimiter}"Pasal"{tuple_delimiter}"Berisi definisi istilah-istilah kunci dalam UU Cagar Budaya."){record_delimiter}
("entity"{tuple_delimiter}"Undang-Undang ini"{tuple_delimiter}"Peraturan"{tuple_delimiter}"Merujuk pada UU No. 11 Tahun 2010 tentang Cagar Budaya."){record_delimiter}
("entity"{tuple_delimiter}"Cagar Budaya"{tuple_delimiter}"Konsep Hukum"{tuple_delimiter}"Warisan budaya kebendaan (Benda, Bangunan, Struktur, Situs, Kawasan) yang perlu dilestarikan melalui penetapan karena nilai pentingnya."){record_delimiter}
("entity"{tuple_delimiter}"Pelestarian"{tuple_delimiter}"Tindakan Hukum"{tuple_delimiter}"Upaya dinamis mempertahankan Cagar Budaya dan nilainya melalui pelindungan, pengembangan, dan pemanfaatan."){record_delimiter}
("entity"{tuple_delimiter}"Pelindungan"{tuple_delimiter}"Tindakan Hukum"{tuple_delimiter}"Upaya mencegah dan menanggulangi kerusakan Cagar Budaya melalui Penyelamatan, Pengamanan, Zonasi, Pemeliharaan, dan Pemugaran."){record_delimiter}
("entity"{tuple_delimiter}"Penetapan"{tuple_delimiter}"Tindakan Hukum"{tuple_delimiter}"Proses pemberian status Cagar Budaya."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 1"{tuple_delimiter}"Cagar Budaya"{tuple_delimiter}"Pasal 1 mendefinisikan istilah Cagar Budaya."{tuple_delimiter}"definisi"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 1"{tuple_delimiter}"Pelestarian"{tuple_delimiter}"Pasal 1 mendefinisikan istilah Pelestarian."{tuple_delimiter}"definisi"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 1"{tuple_delimiter}"Pelindungan"{tuple_delimiter}"Pasal 1 mendefinisikan istilah Pelindungan."{tuple_delimiter}"definisi"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Cagar Budaya"{tuple_delimiter}"Penetapan"{tuple_delimiter}"Status Cagar Budaya diperoleh melalui proses Penetapan."{tuple_delimiter}"proses hukum"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Pelestarian"{tuple_delimiter}"Pelindungan"{tuple_delimiter}"Pelindungan adalah salah satu cara melakukan Pelestarian Cagar Budaya."{tuple_delimiter}"komponen"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"Definisi, Cagar Budaya, Pelestarian, Pelindungan"){completion_delimiter}
#############################
Contoh 2 (Dari UU No. 11 Tahun 2010 tentang Cagar Budaya):

Jenis_Entitas: [Pasal, Objek, Konsep Hukum, Kriteria]
Teks:
Pasal 5
Benda, bangunan, atau struktur dapat diusulkan sebagai Benda Cagar Budaya, Bangunan Cagar Budaya, atau Struktur Cagar Budaya apabila memenuhi kriteria:
a. berusia 50 (lima puluh) tahun atau lebih;
b. mewakili masa gaya paling singkat berusia 50 (lima puluh) tahun;
c. memiliki arti khusus bagi sejarah, ilmu pengetahuan, pendidikan, agama, dan/atau kebudayaan; dan
d. memiliki nilai budaya bagi penguatan kepribadian bangsa.
################
Keluaran:
("entity"{tuple_delimiter}"Pasal 5"{tuple_delimiter}"Pasal"{tuple_delimiter}"Menetapkan kriteria untuk Benda, Bangunan, atau Struktur Cagar Budaya."){record_delimiter}
("entity"{tuple_delimiter}"Benda Cagar Budaya"{tuple_delimiter}"Objek"{tuple_delimiter}"Objek yang dapat diusulkan sebagai Cagar Budaya jika memenuhi kriteria Pasal 5."){record_delimiter}
("entity"{tuple_delimiter}"Bangunan Cagar Budaya"{tuple_delimiter}"Objek"{tuple_delimiter}"Objek yang dapat diusulkan sebagai Cagar Budaya jika memenuhi kriteria Pasal 5."){record_delimiter}
("entity"{tuple_delimiter}"Struktur Cagar Budaya"{tuple_delimiter}"Objek"{tuple_delimiter}"Objek yang dapat diusulkan sebagai Cagar Budaya jika memenuhi kriteria Pasal 5."){record_delimiter}
("entity"{tuple_delimiter}"Berusia 50 tahun atau lebih"{tuple_delimiter}"Kriteria"{tuple_delimiter}"Salah satu kriteria kelayakan sebagai Cagar Budaya (Benda, Bangunan, Struktur)."){record_delimiter}
("entity"{tuple_delimiter}"Mewakili masa gaya 50 tahun"{tuple_delimiter}"Kriteria"{tuple_delimiter}"Salah satu kriteria kelayakan sebagai Cagar Budaya (Benda, Bangunan, Struktur)."){record_delimiter}
("entity"{tuple_delimiter}"Memiliki arti khusus"{tuple_delimiter}"Kriteria"{tuple_delimiter}"Salah satu kriteria kelayakan (sejarah, ilmu pengetahuan, pendidikan, agama, kebudayaan) sebagai Cagar Budaya (Benda, Bangunan, Struktur)."){record_delimiter}
("entity"{tuple_delimiter}"Memiliki nilai budaya"{tuple_delimiter}"Kriteria"{tuple_delimiter}"Salah satu kriteria kelayakan (penguatan kepribadian bangsa) sebagai Cagar Budaya (Benda, Bangunan, Struktur)."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 5"{tuple_delimiter}"Benda Cagar Budaya"{tuple_delimiter}"Pasal 5 menetapkan kriteria kelayakan untuk Benda Cagar Budaya."{tuple_delimiter}"kriteria"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Benda Cagar Budaya"{tuple_delimiter}"Berusia 50 tahun atau lebih"{tuple_delimiter}"Usia minimal 50 tahun adalah kriteria untuk Benda Cagar Budaya."{tuple_delimiter}"persyaratan"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Bangunan Cagar Budaya"{tuple_delimiter}"Memiliki arti khusus"{tuple_delimiter}"Memiliki arti khusus adalah kriteria untuk Bangunan Cagar Budaya."{tuple_delimiter}"persyaratan"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Struktur Cagar Budaya"{tuple_delimiter}"Memiliki nilai budaya"{tuple_delimiter}"Memiliki nilai budaya adalah kriteria untuk Struktur Cagar Budaya."{tuple_delimiter}"persyaratan"{tuple_delimiter}8){record_delimiter}
("content_keywords"{tuple_delimiter}"Kriteria Cagar Budaya, Usia, Nilai Sejarah, Nilai Budaya"){completion_delimiter}
#############################
Contoh 3 (Dari UU No. 17 Tahun 2008 tentang Pelayaran):

Jenis_Entitas: [Pasal, Objek, Konsep Hukum, Lembaga/Jabatan, Tindakan Hukum]
Teks:
Pasal 60
(1) Kapal yang telah didaftarkan dalam Daftar Kapal Indonesia dapat dijadikan jaminan utang dengan pembebanan hipotek atas kapal.
(2) Pembebanan hipotek atas kapal dilakukan dengan pembuatan akta hipotek oleh Pejabat Pendaftar dan Pencatat Balik Nama Kapal di tempat kapal didaftarkan dan dicatat dalam Daftar Induk Pendaftaran Kapal.
(3) Setiap akta hipotek diterbitkan 1 (satu) Grosse Akta Hipotek yang diberikan kepada penerima hipotek.
################
Keluaran:
("entity"{tuple_delimiter}"Pasal 60"{tuple_delimiter}"Pasal"{tuple_delimiter}"Mengatur tentang pembebanan hipotek atas kapal yang terdaftar."){record_delimiter}
("entity"{tuple_delimiter}"Kapal"{tuple_delimiter}"Objek"{tuple_delimiter}"Kendaraan air yang dapat dijadikan jaminan utang melalui hipotek jika terdaftar."){record_delimiter}
("entity"{tuple_delimiter}"Daftar Kapal Indonesia"{tuple_delimiter}"Objek"{tuple_delimiter}"Register resmi tempat kapal didaftarkan di Indonesia."){record_delimiter}
("entity"{tuple_delimiter}"Hipotek atas kapal"{tuple_delimiter}"Konsep Hukum"{tuple_delimiter}"Hak agunan kebendaan atas kapal terdaftar untuk menjamin pelunasan utang."){record_delimiter}
("entity"{tuple_delimiter}"Pembebanan hipotek"{tuple_delimiter}"Tindakan Hukum"{tuple_delimiter}"Proses menjadikan kapal sebagai jaminan utang melalui hipotek."){record_delimiter}
("entity"{tuple_delimiter}"Akta hipotek"{tuple_delimiter}"Objek"{tuple_delimiter}"Dokumen hukum yang dibuat untuk pembebanan hipotek kapal."){record_delimiter}
("entity"{tuple_delimiter}"Pejabat Pendaftar dan Pencatat Balik Nama Kapal"{tuple_delimiter}"Lembaga/Jabatan"{tuple_delimiter}"Pejabat yang berwenang membuat akta hipotek kapal."){record_delimiter}
("entity"{tuple_delimiter}"Grosse Akta Hipotek"{tuple_delimiter}"Objek"{tuple_delimiter}"Salinan resmi akta hipotek yang diberikan kepada penerima hipotek."){record_delimiter}
("entity"{tuple_delimiter}"Penerima hipotek"{tuple_delimiter}"Peran"{tuple_delimiter}"Pihak yang menerima kapal sebagai jaminan utang (kreditor)."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 60"{tuple_delimiter}"Hipotek atas kapal"{tuple_delimiter}"Pasal 60 ayat (1) memungkinkan Kapal terdaftar dibebani Hipotek atas kapal."{tuple_delimiter}"pengaturan"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pembebanan hipotek"{tuple_delimiter}"Akta hipotek"{tuple_delimiter}"Pembebanan hipotek dilakukan dengan pembuatan Akta hipotek."{tuple_delimiter}"proses hukum"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Akta hipotek"{tuple_delimiter}"Pejabat Pendaftar dan Pencatat Balik Nama Kapal"{tuple_delimiter}"Akta hipotek dibuat oleh Pejabat Pendaftar dan Pencatat Balik Nama Kapal."{tuple_delimiter}"kewenangan"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Akta hipotek"{tuple_delimiter}"Grosse Akta Hipotek"{tuple_delimiter}"Setiap Akta hipotek diterbitkan satu Grosse Akta Hipotek."{tuple_delimiter}"hasil proses"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Grosse Akta Hipotek"{tuple_delimiter}"Penerima hipotek"{tuple_delimiter}"Grosse Akta Hipotek diberikan kepada Penerima hipotek."{tuple_delimiter}"pemberian hak"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"Hipotek Kapal, Jaminan Utang, Pendaftaran Kapal, Akta Hipotek"){completion_delimiter}
#############################
Contoh 4 (Dari UU No. 17 Tahun 2008 tentang Pelayaran):

Jenis_Entitas: [Pasal, Lembaga/Jabatan, Tindakan Hukum, Konsep Hukum, Lokasi]
Teks:
Pasal 208
(1) Dalam melaksanakan fungsi keselamatan dan keamanan sebagaimana dimaksud dalam Pasal 207 ayat (1) Syahbandar mempunyai tugas:
a. mengawasi kelaiklautan kapal, keselamatan, keamanan dan ketertiban di pelabuhan;
b. mengawasi tertib lalu lintas kapal di perairan pelabuhan dan alur-pelayaran;
...
n. mengawasi pelaksanaan perlindungan lingkungan maritim.
################
Keluaran:
("entity"{tuple_delimiter}"Pasal 208"{tuple_delimiter}"Pasal"{tuple_delimiter}"Menjelaskan tugas Syahbandar terkait fungsi keselamatan dan keamanan pelayaran."){record_delimiter}
("entity"{tuple_delimiter}"Syahbandar"{tuple_delimiter}"Lembaga/Jabatan"{tuple_delimiter}"Pejabat pemerintah di pelabuhan dengan kewenangan tertinggi terkait keselamatan dan keamanan pelayaran."){record_delimiter}
("entity"{tuple_delimiter}"Keselamatan dan Keamanan Pelayaran"{tuple_delimiter}"Konsep Hukum"{tuple_delimiter}"Fungsi yang dilaksanakan oleh Syahbandar."){record_delimiter}
("entity"{tuple_delimiter}"Mengawasi kelaiklautan kapal"{tuple_delimiter}"Tindakan Hukum"{tuple_delimiter}"Salah satu tugas Syahbandar."){record_delimiter}
("entity"{tuple_delimiter}"Mengawasi tertib lalu lintas kapal"{tuple_delimiter}"Tindakan Hukum"{tuple_delimiter}"Salah satu tugas Syahbandar."){record_delimiter}
("entity"{tuple_delimiter}"Mengawasi perlindungan lingkungan maritim"{tuple_delimiter}"Tindakan Hukum"{tuple_delimiter}"Salah satu tugas Syahbandar."){record_delimiter}
("entity"{tuple_delimiter}"Pelabuhan"{tuple_delimiter}"Lokasi"{tuple_delimiter}"Lokasi di mana Syahbandar bertugas mengawasi keselamatan, keamanan, dan ketertiban."){record_delimiter}
("entity"{tuple_delimiter}"Perairan pelabuhan"{tuple_delimiter}"Lokasi"{tuple_delimiter}"Lokasi di mana Syahbandar bertugas mengawasi lalu lintas kapal."){record_delimiter}
("entity"{tuple_delimiter}"Alur-pelayaran"{tuple_delimiter}"Lokasi"{tuple_delimiter}"Lokasi di mana Syahbandar bertugas mengawasi lalu lintas kapal."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 208"{tuple_delimiter}"Syahbandar"{tuple_delimiter}"Pasal 208 ayat (1) merinci tugas-tugas Syahbandar."{tuple_delimiter}"tugas"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Syahbandar"{tuple_delimiter}"Mengawasi kelaiklautan kapal"{tuple_delimiter}"Mengawasi kelaiklautan kapal adalah tugas Syahbandar."{tuple_delimiter}"tugas"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Syahbandar"{tuple_delimiter}"Mengawasi tertib lalu lintas kapal"{tuple_delimiter}"Mengawasi tertib lalu lintas kapal adalah tugas Syahbandar."{tuple_delimiter}"tugas"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Syahbandar"{tuple_delimiter}"Pelabuhan"{tuple_delimiter}"Syahbandar bertugas mengawasi ketertiban di Pelabuhan."{tuple_delimiter}"lokasi tugas"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"Mengawasi tertib lalu lintas kapal"{tuple_delimiter}"Perairan pelabuhan"{tuple_delimiter}"Pengawasan lalu lintas kapal oleh Syahbandar dilakukan di Perairan pelabuhan."{tuple_delimiter}"lokasi tindakan"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"Mengawasi tertib lalu lintas kapal"{tuple_delimiter}"Alur-pelayaran"{tuple_delimiter}"Pengawasan lalu lintas kapal oleh Syahbandar dilakukan di Alur-pelayaran."{tuple_delimiter}"lokasi tindakan"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"Tugas Syahbandar, Pengawasan Pelayaran, Kelaiklautan Kapal, Lalu Lintas Kapal, Keselamatan Pelayaran"){completion_delimiter}
#############################
-Data Sebenarnya (Dokumen Hukum)-
######################
Jenis_Entitas: {entity_types}
Teks: {input_text}
######################
Keluaran:
"""

# Bagian lain dari prompt.py tetap sama...
PROMPTS[
    "summarize_entity_descriptions"
] = """Anda adalah asisten yang membantu yang bertanggung jawab untuk menghasilkan ringkasan komprehensif dari data yang disediakan di bawah ini.
Diberikan satu atau dua entitas, dan daftar deskripsi, semuanya terkait dengan entitas atau kelompok entitas yang sama (misalnya, definisi sebuah istilah hukum dari beberapa pasal).
Harap gabungkan semua ini menjadi satu deskripsi tunggal yang komprehensif dan akurat sesuai konteks hukum. Pastikan untuk menyertakan informasi yang dikumpulkan dari semua deskripsi.
Jika deskripsi yang diberikan kontradiktif, coba cari penjelasan dalam teks sumber atau nyatakan adanya kontradiksi jika tidak dapat diselesaikan.
Pastikan itu ditulis dalam sudut pandang orang ketiga, dan sertakan nama entitas sehingga kami memiliki konteks penuh.

#######
-Data-
Entitas: {entity_name}
Daftar Deskripsi: {description_list}
#######
Keluaran:
"""

PROMPTS[
    "entiti_continue_extraction"
] = """BANYAK entitas (misalnya, definisi, pasal, lembaga, sanksi) terlewatkan pada ekstraksi terakhir. Tambahkan di bawah ini menggunakan format yang sama:
"""

PROMPTS[
    "entiti_continue_extraction_mini"
] = """BANYAK entitas hukum terlewatkan pada ekstraksi terakhir.
Setelah meringkas dengan semua informasi yang diekstraksi sebelumnya, dibandingkan dengan teks asli, terlihat bahwa informasi berikut (misalnya definisi, kewajiban, larangan, sanksi) sebagian besar dihilangkan:
{omit}

Jenis entitas yang perlu ditambahkan dapat diperoleh dari Jenis_Entitas yang disarankan (Peraturan, Pasal, Lembaga/Jabatan, Konsep Hukum, Tindakan Hukum, Lokasi, Objek, Peran, Sanksi),
atau Anda dapat menambahkannya sendiri jika relevan secara hukum.

Jenis_Entitas: {entity_types}


Tambahkan entitas dan hubungan yang terlewat di bawah ini menggunakan format yang sama:
"""

# Prompt lainnya (minirag_query2kwd, entiti_if_loop_extraction, fail_response, rag_response, keywords_extraction, naive_rag_response)
# Dapat disesuaikan lebih lanjut jika diperlukan, tetapi perubahan utama ada di entity_extraction.
# Misalnya, untuk keywords_extraction, contohnya bisa disesuaikan dengan query terkait hukum.
# Untuk rag_response, instruksinya bisa ditekankan untuk menjawab berdasarkan konteks hukum yang diberikan.

PROMPTS["minirag_query2kwd"] = """---Peran---

Anda adalah asisten yang membantu yang bertugas mengidentifikasi kata kunci jenis-jawaban dan kata kunci entitas spesifik dalam kueri pengguna terkait dokumen hukum.

---Tujuan---

Diberikan kueri, daftarkan kata kunci jenis-jawaban dan kata kunci entitas spesifik.
kata_kunci_jenis_jawaban berfokus pada jenis informasi hukum yang dicari (misal: definisi, sanksi, prosedur, kewenangan), sedangkan kata_kunci_entitas_spesifik berfokus pada istilah hukum, pasal, atau lembaga yang disebutkan dalam kueri.
kata_kunci_jenis_jawaban harus dipilih dari kumpulan Jenis Jawaban yang mungkin relevan dengan konteks hukum.

---Instruksi---

- Keluarkan kata kunci dalam format JSON.
- JSON harus memiliki tiga kunci:
  - "answer_type_keywords": Daftar jenis jawaban hukum (maksimal 3, paling relevan di depan). Contoh: DEFINISI, SANKSI, PROSEDUR, KEWENANGAN, KEWAJIBAN, LARANGAN, KRITERIA.
  - "entities_from_query": Entitas hukum spesifik yang diekstrak dari kueri (istilah hukum, nomor pasal, nama lembaga).
######################
-Contoh-contoh Query Hukum-
######################
Contoh 1:

Kueri: "Apa definisi Cagar Budaya menurut UU No. 11 Tahun 2010?"
Kumpulan jenis jawaban: {{
 'DEFINISI': ['PENGERTIAN ISTILAH', 'ARTI KATA'],
 'SANKSI': ['HUKUMAN', 'DENDA', 'PIDANA'],
 'PROSEDUR': ['TATA CARA', 'LANGKAH-LANGKAH'],
 'KEWENANGAN': ['HAK', 'WEWENANG LEMBAGA'],
 'KEWAJIBAN': ['TANGGUNG JAWAB', 'HARUS DILAKUKAN'],
 'LARANGAN': ['TIDAK BOLEH', 'DILARANG'],
 'KRITERIA': ['SYARAT', 'KETENTUAN KELAYAKAN']
}}
################
Keluaran:
{{
  "answer_type_keywords": ["DEFINISI"],
  "entities_from_query": ["Cagar Budaya", "UU No. 11 Tahun 2010"]
}}
#############################
Contoh 2:

Kueri: "Sanksi apa jika merusak Cagar Budaya?"
Kumpulan jenis jawaban: {{
 'DEFINISI': ['PENGERTIAN ISTILAH', 'ARTI KATA'],
 'SANKSI': ['HUKUMAN', 'DENDA', 'PIDANA'],
 'PROSEDUR': ['TATA CARA', 'LANGKAH-LANGKAH'],
 'KEWENANGAN': ['HAK', 'WEWENANG LEMBAGA'],
 'KEWAJIBAN': ['TANGGUNG JAWAB', 'HARUS DILAKUKAN'],
 'LARANGAN': ['TIDAK BOLEH', 'DILARANG'],
 'KRITERIA': ['SYARAT', 'KETENTUAN KELAYAKAN']
}}
################
Keluaran:
{{
  "answer_type_keywords": ["SANKSI"],
  "entities_from_query": ["Merusak Cagar Budaya", "Cagar Budaya"]
}}
#############################
Contoh 3:

Kueri: "Bagaimana prosedur pembebanan hipotek kapal menurut UU Pelayaran?"
Kumpulan jenis jawaban: {{
 'DEFINISI': ['PENGERTIAN ISTILAH', 'ARTI KATA'],
 'SANKSI': ['HUKUMAN', 'DENDA', 'PIDANA'],
 'PROSEDUR': ['TATA CARA', 'LANGKAH-LANGKAH'],
 'KEWENANGAN': ['HAK', 'WEWENANG LEMBAGA'],
 'KEWAJIBAN': ['TANGGUNG JAWAB', 'HARUS DILAKUKAN'],
 'LARANGAN': ['TIDAK BOLEH', 'DILARANG'],
 'KRITERIA': ['SYARAT', 'KETENTUAN KELAYAKAN']
}}
################
Keluaran:
{{
  "answer_type_keywords": ["PROSEDUR"],
  "entities_from_query": ["Pembebanan hipotek kapal", "Hipotek kapal", "UU Pelayaran"]
}}
#############################

-Data Sebenarnya-
######################
Kueri: {query}
Kumpulan jenis jawaban:{TYPE_POOL}
######################
Keluaran:

"""


PROMPTS[
    "entiti_if_loop_extraction"
] = """Tampaknya beberapa entitas hukum (seperti pasal, definisi, lembaga, sanksi) mungkin masih terlewatkan. Jawab YA | TIDAK jika masih ada entitas yang perlu ditambahkan.
"""

PROMPTS["fail_response"] = "Maaf, saya tidak dapat memberikan jawaban atas pertanyaan terkait dokumen hukum ini."

PROMPTS["rag_response"] = """Berdasarkan konteks undang-undang berikut, jawab pertanyaan dengan tepat dan singkat.

{context_data}

INSTRUKSI:
1. Jawab berdasarkan HANYA informasi yang ada dalam konteks undang-undang di atas
2. Sebutkan pasal/ayat yang menjadi dasar jawaban jika memungkinkan
3. Jika informasi tidak tersedia dalam konteks, katakan \"Informasi tidak tersedia dalam konteks yang diberikan\"
4. Berikan jawaban yang singkat dan tepat

Jawaban:"""

PROMPTS["keywords_extraction"] = """---Peran---

Anda adalah asisten AI yang bertugas mengidentifikasi kata kunci tingkat tinggi (konsep umum) dan tingkat rendah (istilah spesifik) dalam kueri pengguna yang berkaitan dengan dokumen hukum.

---Tujuan---

Diberikan kueri, daftarkan kata kunci tingkat tinggi dan tingkat rendah. Kata kunci tingkat tinggi fokus pada konsep atau tema hukum umum, sementara kata kunci tingkat rendah fokus pada entitas hukum spesifik, pasal, detail, atau istilah konkret dalam kueri.

---Instruksi---

- Keluarkan kata kunci dalam format JSON.
- JSON harus memiliki dua kunci:
  - "high_level_keywords": untuk konsep atau tema hukum umum.
  - "low_level_keywords": untuk entitas atau detail hukum spesifik.

######################
-Contoh-contoh Query Hukum-
######################
Contoh 1:

Kueri: "Apa saja kriteria sebuah bangunan bisa ditetapkan sebagai Bangunan Cagar Budaya menurut UU 11/2010?"
################
Keluaran:
{{
  "high_level_keywords": ["Kriteria Cagar Budaya", "Penetapan Cagar Budaya", "Hukum Cagar Budaya"],
  "low_level_keywords": ["Bangunan Cagar Budaya", "Kriteria", "UU 11/2010"]
}}
#############################
Contoh 2:

Kueri: "Bagaimana tanggung jawab pengangkut jika terjadi keterlambatan angkutan penumpang menurut UU Pelayaran?"
################
Keluaran:
{{
  "high_level_keywords": ["Tanggung Jawab Pengangkut", "Hukum Pelayaran", "Hak Penumpang"],
  "low_level_keywords": ["Pengangkut", "Keterlambatan", "Angkutan penumpang", "UU Pelayaran"]
}}
#############################
Contoh 3:

Kueri: "Siapa yang berwenang menerbitkan Surat Persetujuan Berlayar?"
################
Keluaran:
{{
  "high_level_keywords": ["Keselamatan Pelayaran", "Perizinan Kapal", "Administrasi Pelabuhan"],
  "low_level_keywords": ["Surat Persetujuan Berlayar", "Kewenangan", "Penerbitan Izin"]
}}
#############################
-Data Sebenarnya-
######################
Kueri: {query}
######################
Keluaran:

"""

PROMPTS["naive_rag_response"] = """---Peran---

Anda adalah asisten AI yang membantu merespons pertanyaan berdasarkan informasi dari dokumen hukum (misalnya Undang-Undang, Peraturan Pemerintah) yang disediakan.


---Tujuan---

Hasilkan respons dengan panjang dan format target yang menjawab pertanyaan pengguna secara akurat berdasarkan data dalam dokumen hukum yang diberikan. Rangkum informasi yang relevan dari dokumen sesuai panjang dan format respons. Gunakan pengetahuan umum hanya jika diperlukan untuk memperjelas konteks hukum, namun utamakan informasi dari sumber.
Jika jawaban tidak ditemukan dalam dokumen yang diberikan, nyatakan demikian. Jangan mengarang informasi hukum.
Jangan sertakan informasi jika bukti pendukungnya tidak ada dalam dokumen hukum.

---Panjang dan format respons target---

{response_type}

---Dokumen Hukum---

{content_data}

Susun respons dalam format markdown. Jika memungkinkan, sertakan referensi ke pasal atau bagian relevan dari dokumen hukum yang digunakan.
"""