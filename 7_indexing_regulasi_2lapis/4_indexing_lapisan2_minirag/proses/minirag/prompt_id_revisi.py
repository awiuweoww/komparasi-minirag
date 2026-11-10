"""
Copyright (c) 2026 Badan Riset dan Inovasi Nasional (BRIN)
THIS SOFTWARE SOURCE CODE AND ANY EXECUTABLE DERIVED THEREOF ARE PROPRIETARY
TO BRIN, AS APPLICABLE, AND SHALL NOT BE USED IN ANY WAY
OTHER THAN BEFOREHAND AGREED ON BY BRIN, NOR BE REPRODUCED
OR DISCLOSED TO THIRD PARTIES WITHOUT PRIOR WRITTEN AUTHORIZATION BY
BRIN, AS APPLICABLE.

Author      : Chandra
Version     : 2.2.0
Created     : 02-11-2026
Revised     : 02-11-2026 - prompt indexing: aturan penamaan kanonik (selaras normalisasi_entitas.py),
              larangan output penalaran/placeholder, wajib relasi per entitas, contoh pasal + chunk 'Cukup jelas'.
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
Diberikan potongan teks peraturan perundang-undangan dan daftar jenis entitas, ekstrak entitas hukum yang TERTULIS di teks beserta hubungan antar-entitas tersebut, untuk membangun knowledge graph.

-Aturan Output (WAJIB)-
- Mulai LANGSUNG dengan record pertama. Jangan menulis analisis, penalaran, ringkasan input, judul, markdown, atau bahasa Inggris.
- Gunakan Bahasa Indonesia. Ikuti format record persis seperti contoh.
- Jangan pernah menyalin kata dari template seperti <entity_name>, <source_entity>, <description>, entity_name, source, atau target sebagai isi record.
- Jika teks tidak memuat norma hukum (misalnya hanya "Cukup jelas." atau hanya judul), tulis {completion_delimiter} saja.

-Jenis Entitas-
Gunakan HANYA jenis berikut: [{entity_types}]
- dasar_hukum: nama peraturan (UU, PP, Peraturan Menteri, KUHP).
- struktur: pasal, ayat, huruf, angka, atau bagian penjelasan.
- pihak: orang, badan, jabatan, atau lembaga (Setiap Orang, Nelayan Kecil, Menteri, Pengawas Perikanan, Pengadilan Perikanan).
- kewajiban: perbuatan yang diwajibkan atau dilarang.
- hak: hak atau kewenangan suatu pihak.
- sanksi: pidana penjara, pidana denda, atau sanksi administratif beserta besarannya.
- konsep: istilah hukum, izin, dokumen, kapal, alat, atau wilayah (Surat Izin Penangkapan Ikan, Zona Ekonomi Eksklusif Indonesia).

-Aturan Penamaan Entitas-
1. Nama peraturan ditulis "UU Nomor 45 Tahun 2009", "UU Nomor 31 Tahun 2004", "PP Nomor X Tahun Y", "KUHP". Tanpa "tentang ...".
2. Pasal SELALU disertai nama peraturannya: "Pasal 93 ayat (1) UU Nomor 45 Tahun 2009", "Pasal 7 ayat (2) huruf a UU Nomor 45 Tahun 2009". Ambil nama peraturan dari kepala teks; rujukan "sebagaimana dimaksud dalam Pasal X" tanpa nama peraturan lain berarti peraturan yang sama. Jangan pernah membuat entitas "Ayat 1", "Ayat (2)", atau "Huruf a" tanpa nomor pasal.
3. Istilah yang punya singkatan ditulis dengan kepanjangannya: "Surat Izin Penangkapan Ikan" (bukan "SIPI"), "Zona Ekonomi Eksklusif Indonesia" (bukan "ZEEI"); sebutkan singkatannya di deskripsi.
4. Gunakan istilah persis seperti di teks, bentuk dasar dan tunggal, Huruf Kapital Di Awal Kata. Satu konsep = satu nama di seluruh output.
5. Sanksi ditulis dengan angka seperti di teks: "Pidana penjara paling lama 6 tahun", "Denda paling banyak Rp2.000.000.000,00".
6. Jangan membuat entitas dari kata umum (ketentuan, hal, kegiatan, pelaksanaan) atau dari pengetahuan di luar teks.

-Langkah-
1. Untuk setiap entitas, tulis:
("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)
entity_description: 1-2 kalimat berdasarkan teks, termasuk singkatan resmi bila ada.

2. Untuk setiap pasangan entitas yang jelas berhubungan di teks, tulis:
("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)
- source_entity dan target_entity harus sama persis dengan nama pada langkah 1.
- relationship_strength: bilangan 1-10.
- SETIAP entitas wajib muncul di minimal satu relasi. Entitas yang tidak dapat dihubungkan jangan ditulis.
- Relasi yang selalu dicari: peraturan memuat pasal; pasal mengatur kewajiban/hak/sanksi; pihak dikenai kewajiban atau memegang hak; pasal merujuk pasal lain ("sebagaimana dimaksud dalam"); pasal sanksi mengenakan sanksi atas pelanggaran pasal kewajiban.

3. Tulis per ayat: entitas ayat tersebut, lalu langsung relasinya, baru ayat berikutnya. Paling banyak 25 entitas; utamakan pasal, pihak, kewajiban, sanksi, dan istilah yang didefinisikan.

4. Tulis kata kunci tingkat tinggi teks:
("content_keywords"{tuple_delimiter}<high_level_keywords>)

5. Pisahkan setiap record dengan {record_delimiter} dan akhiri dengan {completion_delimiter}

######################
-Contoh-
######################
Contoh 1:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak]
Text:
UU Nomor 45 Tahun 2009 | Pasal 93
Pasal 93
(1) Setiap orang yang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera Indonesia melakukan penangkapan ikan di wilayah pengelolaan perikanan Negara Republik Indonesia dan/atau di laut lepas, yang tidak memiliki SIPI sebagaimana dimaksud dalam Pasal 27 ayat (1), dipidana dengan pidana penjara paling lama 6 (enam) tahun dan denda paling banyak Rp2.000.000.000,00 (dua miliar rupiah).
(2) Setiap orang yang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera asing melakukan penangkapan ikan di ZEEI yang tidak memiliki SIPI sebagaimana dimaksud dalam Pasal 27 ayat (2), dipidana dengan pidana penjara paling lama 6 (enam) tahun dan denda paling banyak Rp20.000.000.000,00 (dua puluh miliar rupiah).
################
Output:
("entity"{tuple_delimiter}"UU Nomor 45 Tahun 2009"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Undang-undang tentang perubahan atas UU Nomor 31 Tahun 2004 tentang Perikanan."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 93 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"struktur"{tuple_delimiter}"Ketentuan pidana bagi kapal penangkap ikan berbendera Indonesia yang menangkap ikan tanpa SIPI."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 27 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"struktur"{tuple_delimiter}"Ketentuan kewajiban memiliki SIPI bagi kapal penangkap ikan berbendera Indonesia."){record_delimiter}
("entity"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"pihak"{tuple_delimiter}"Orang yang memiliki dan/atau mengoperasikan kapal penangkap ikan."){record_delimiter}
("entity"{tuple_delimiter}"Kapal Penangkap Ikan Berbendera Indonesia"{tuple_delimiter}"konsep"{tuple_delimiter}"Kapal penangkap ikan berbendera Indonesia yang menangkap ikan di wilayah pengelolaan perikanan Negara Republik Indonesia dan/atau laut lepas."){record_delimiter}
("entity"{tuple_delimiter}"Surat Izin Penangkapan Ikan"{tuple_delimiter}"konsep"{tuple_delimiter}"Izin penangkapan ikan yang disingkat SIPI."){record_delimiter}
("entity"{tuple_delimiter}"Wilayah Pengelolaan Perikanan Negara Republik Indonesia"{tuple_delimiter}"konsep"{tuple_delimiter}"Wilayah tempat kapal berbendera Indonesia melakukan penangkapan ikan."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 6 (enam) tahun."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp2.000.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Denda paling banyak dua miliar rupiah."){record_delimiter}
("relationship"{tuple_delimiter}"UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 93 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"UU Nomor 45 Tahun 2009 memuat Pasal 93 ayat (1)."{tuple_delimiter}"hierarki peraturan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 27 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 93 ayat (1) memidana pelanggaran kewajiban dalam Pasal 27 ayat (1)."{tuple_delimiter}"rujukan pasal, sanksi atas kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Kapal Penangkap Ikan Berbendera Indonesia"{tuple_delimiter}"Setiap orang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera Indonesia."{tuple_delimiter}"subjek hukum"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Kapal Penangkap Ikan Berbendera Indonesia"{tuple_delimiter}"Surat Izin Penangkapan Ikan"{tuple_delimiter}"Kapal penangkap ikan berbendera Indonesia wajib memiliki SIPI."{tuple_delimiter}"kewajiban izin"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Kapal Penangkap Ikan Berbendera Indonesia"{tuple_delimiter}"Wilayah Pengelolaan Perikanan Negara Republik Indonesia"{tuple_delimiter}"Kapal melakukan penangkapan ikan di wilayah pengelolaan perikanan Negara Republik Indonesia."{tuple_delimiter}"wilayah berlaku"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"Pasal 93 ayat (1) mengancam pidana penjara paling lama 6 tahun."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Denda Paling Banyak Rp2.000.000.000,00"{tuple_delimiter}"Pasal 93 ayat (1) mengancam denda paling banyak Rp2.000.000.000,00."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("entity"{tuple_delimiter}"Pasal 93 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"struktur"{tuple_delimiter}"Ketentuan pidana bagi kapal penangkap ikan berbendera asing yang menangkap ikan di ZEEI tanpa SIPI."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 27 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"struktur"{tuple_delimiter}"Ketentuan kewajiban memiliki SIPI bagi kapal penangkap ikan berbendera asing di ZEEI."){record_delimiter}
("entity"{tuple_delimiter}"Kapal Penangkap Ikan Berbendera Asing"{tuple_delimiter}"konsep"{tuple_delimiter}"Kapal penangkap ikan berbendera asing yang menangkap ikan di ZEEI."){record_delimiter}
("entity"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia"{tuple_delimiter}"konsep"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia, disingkat ZEEI."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp20.000.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Denda paling banyak dua puluh miliar rupiah."){record_delimiter}
("relationship"{tuple_delimiter}"UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 93 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"UU Nomor 45 Tahun 2009 memuat Pasal 93 ayat (2)."{tuple_delimiter}"hierarki peraturan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 27 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 93 ayat (2) memidana pelanggaran kewajiban dalam Pasal 27 ayat (2)."{tuple_delimiter}"rujukan pasal, sanksi atas kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Kapal Penangkap Ikan Berbendera Asing"{tuple_delimiter}"Setiap orang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera asing."{tuple_delimiter}"subjek hukum"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Kapal Penangkap Ikan Berbendera Asing"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia"{tuple_delimiter}"Kapal berbendera asing melakukan penangkapan ikan di ZEEI."{tuple_delimiter}"wilayah berlaku"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"Kapal Penangkap Ikan Berbendera Asing"{tuple_delimiter}"Surat Izin Penangkapan Ikan"{tuple_delimiter}"Kapal berbendera asing di ZEEI wajib memiliki SIPI."{tuple_delimiter}"kewajiban izin"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"Pasal 93 ayat (2) mengancam pidana penjara paling lama 6 tahun."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Denda Paling Banyak Rp20.000.000.000,00"{tuple_delimiter}"Pasal 93 ayat (2) mengancam denda paling banyak Rp20.000.000.000,00."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}10){record_delimiter}
("content_keywords"{tuple_delimiter}"sanksi pidana perikanan, surat izin penangkapan ikan, kapal berbendera asing, ZEEI"){completion_delimiter}
#############################
Contoh 2:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak]
Text:
UU Nomor 45 Tahun 2009 | Ketentuan Umum | Pasal 25
Beberapa ketentuan dalam Undang-Undang Nomor 31 Tahun 2004 tentang Perikanan diubah sebagai berikut:
9. Ketentuan Pasal 25 diubah sehingga Pasal 25 berbunyi sebagai berikut:
Pasal 25
(1) Usaha perikanan dilaksanakan dalam sistem bisnis perikanan, meliputi praproduksi, produksi, pengolahan, dan pemasaran.
(2) Ketentuan lebih lanjut mengenai praproduksi, produksi, pengolahan, dan pemasaran sebagaimana dimaksud pada ayat (1) diatur dalam Peraturan Menteri.
################
Output:
("entity"{tuple_delimiter}"UU Nomor 45 Tahun 2009"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Undang-undang yang mengubah UU Nomor 31 Tahun 2004 tentang Perikanan."){record_delimiter}
("entity"{tuple_delimiter}"UU Nomor 31 Tahun 2004"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Undang-undang tentang Perikanan yang sebagian ketentuannya diubah oleh UU Nomor 45 Tahun 2009."){record_delimiter}
("relationship"{tuple_delimiter}"UU Nomor 45 Tahun 2009"{tuple_delimiter}"UU Nomor 31 Tahun 2004"{tuple_delimiter}"UU Nomor 45 Tahun 2009 mengubah beberapa ketentuan UU Nomor 31 Tahun 2004."{tuple_delimiter}"perubahan peraturan"{tuple_delimiter}10){record_delimiter}
("entity"{tuple_delimiter}"Pasal 25 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"struktur"{tuple_delimiter}"Ketentuan bahwa usaha perikanan dilaksanakan dalam sistem bisnis perikanan."){record_delimiter}
("entity"{tuple_delimiter}"Usaha Perikanan"{tuple_delimiter}"konsep"{tuple_delimiter}"Usaha yang dilaksanakan dalam sistem bisnis perikanan."){record_delimiter}
("entity"{tuple_delimiter}"Sistem Bisnis Perikanan"{tuple_delimiter}"konsep"{tuple_delimiter}"Sistem yang meliputi praproduksi, produksi, pengolahan, dan pemasaran."){record_delimiter}
("relationship"{tuple_delimiter}"UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 25 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"UU Nomor 45 Tahun 2009 mengubah dan memuat Pasal 25 ayat (1)."{tuple_delimiter}"hierarki peraturan, perubahan pasal"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 25 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Usaha Perikanan"{tuple_delimiter}"Pasal 25 ayat (1) mengatur pelaksanaan usaha perikanan."{tuple_delimiter}"pengaturan"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Usaha Perikanan"{tuple_delimiter}"Sistem Bisnis Perikanan"{tuple_delimiter}"Usaha perikanan dilaksanakan dalam sistem bisnis perikanan."{tuple_delimiter}"pelaksanaan usaha"{tuple_delimiter}9){record_delimiter}
("entity"{tuple_delimiter}"Pasal 25 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"struktur"{tuple_delimiter}"Ketentuan delegasi pengaturan sistem bisnis perikanan kepada Peraturan Menteri."){record_delimiter}
("entity"{tuple_delimiter}"Peraturan Menteri"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Peraturan yang mengatur lebih lanjut praproduksi, produksi, pengolahan, dan pemasaran."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 25 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 25 ayat (1) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pasal 25 ayat (2) merujuk pada ayat (1)."{tuple_delimiter}"rujukan pasal"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 25 ayat (2) UU Nomor 45 Tahun 2009"{tuple_delimiter}"Peraturan Menteri"{tuple_delimiter}"Pasal 25 ayat (2) mendelegasikan pengaturan lebih lanjut kepada Peraturan Menteri."{tuple_delimiter}"delegasi pengaturan"{tuple_delimiter}9){record_delimiter}
("content_keywords"{tuple_delimiter}"perubahan UU Perikanan, usaha perikanan, sistem bisnis perikanan, delegasi peraturan menteri"){completion_delimiter}
#############################
Contoh 3:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak]
Text:
UU Nomor 45 Tahun 2009 | Penjelasan Resmi | Penjelasan Pasal 25B
Pasal 25B Cukup jelas.
################
Output:
{completion_delimiter}
#############################
-Data Sebenarnya-
######################
Entity_types: {entity_types}
Text:
{input_text}
######################
Output:
"""

PROMPTS["summarize_entity_descriptions"] = """Anda bertugas menggabungkan beberapa deskripsi dari entitas hukum yang sama menjadi satu deskripsi.
Aturan:
- Hapus kalimat yang berulang atau bermakna sama; simpan setiap fakta yang berbeda (nomor pasal, besaran sanksi, pihak, wilayah).
- Jangan menambahkan informasi yang tidak ada di daftar deskripsi.
- Jika ada pertentangan, tulis keduanya beserta pasal sumbernya; jangan memilih sendiri.
- Tulis dalam Bahasa Indonesia, orang ketiga, paling banyak 4 kalimat, dan sebutkan nama entitas.
- Tulis langsung deskripsinya tanpa pengantar atau penalaran.

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
] = """Periksa kembali teks di atas. Tambahkan HANYA:
1. entitas yang tertulis di teks tetapi belum diekstrak, dan
2. relasi untuk entitas yang sudah diekstrak tetapi belum punya relasi.
Ikuti aturan penamaan dan format yang sama. Jangan mengulang record yang sudah ditulis dan jangan menambah pengetahuan di luar teks.
Jika tidak ada tambahan, tulis <|SELESAI|> saja.
"""

PROMPTS[
    "entiti_continue_extraction_mini"
] = """Beberapa informasi di teks belum terekstrak. Setelah dibandingkan dengan teks asli, informasi berikut terutama terlewat:
{omit}

Tambahkan entitas dan relasi untuk informasi tersebut saja, dengan aturan penamaan dan format yang sama.
Jenis entitas yang boleh dipakai: {entity_types}
Setiap entitas baru wajib dihubungkan ke minimal satu entitas lain. Jangan mengulang record yang sudah ditulis.
"""

PROMPTS[
    "entiti_if_loop_extraction"
] = """Apakah masih ada entitas yang TERTULIS di teks, atau entitas tanpa relasi, yang belum diekstrak? Jawab hanya YA atau TIDAK.
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
