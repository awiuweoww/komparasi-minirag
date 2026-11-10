"""
Copyright (c) 2026 Badan Riset dan Inovasi Nasional (BRIN)
THIS SOFTWARE SOURCE CODE AND ANY EXECUTABLE DERIVED THEREOF ARE PROPRIETARY
TO BRIN, AS APPLICABLE, AND SHALL NOT BE USED IN ANY WAY
OTHER THAN BEFOREHAND AGREED ON BY BRIN, NOR BE REPRODUCED
OR DISCLOSED TO THIRD PARTIES WITHOUT PRIOR WRITTEN AUTHORIZATION BY
BRIN, AS APPLICABLE.

Author      : Chandra
Version     : 5.1.0-skema
Created     : 08-11-2026
Description : Prompt indexing MiniRAG multi-regulasi berjangkar (Lapisan 2), DIRENDER dari skema_relasi_regulasi.yaml
              v1.2 dan metadata_regulasi.json (JDIH BPK, diambil 2026-11-08). Korpus: UU Nomor 31 Tahun 2004; UU Nomor 45 Tahun 2009; UU Nomor 11 Tahun 2020; Perpu Nomor 2 Tahun 2022; UU Nomor 6 Tahun 2023; UU Nomor 1 Tahun 2026.
              Peraturan, pasal, versi pasal, perubahan, pencabutan, penetapan Perpu, uji materi, dan rujukan
              dibangun kode (Lapisan 1, bangun_lapisan1.py); kepala chunk dari kepala_chunk.py; hasil ekstraksi
              ditautkan dengan tautkan_lapisan2.py. Jangan mengedit prompt ini langsung: ubah skema lalu render ulang.
              Jalankan dengan num_ctx >= 16384 dan think=false.
"""

GRAPH_FIELD_SEP = "<SEP>"
DEFAULT_TUPLE_DELIMITER = "<|>"
DEFAULT_RECORD_DELIMITER = "##"
DEFAULT_COMPLETION_DELIMITER = "<|SELESAI|>"
PROCESS_TICKERS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
DEFAULT_ENTITY_TYPES = [
    "dasar_hukum",
    "struktur",
    "pihak",
    "kewajiban",
    "hak",
    "tindak_pidana",
    "sanksi",
    "konsep",
]
ENTITY_TYPES = DEFAULT_ENTITY_TYPES

PROMPTS = {}

PROMPTS["DEFAULT_TUPLE_DELIMITER"] = DEFAULT_TUPLE_DELIMITER
PROMPTS["DEFAULT_RECORD_DELIMITER"] = DEFAULT_RECORD_DELIMITER
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = DEFAULT_COMPLETION_DELIMITER
PROMPTS["process_tickers"] = PROCESS_TICKERS
PROMPTS["DEFAULT_ENTITY_TYPES"] = DEFAULT_ENTITY_TYPES

PROMPTS["entity_extraction"] = """-Tujuan-
Diberikan potongan teks peraturan perundang-undangan dan daftar jenis entitas, ekstrak entitas hukum yang TERTULIS di teks beserta hubungan antar-entitas tersebut, untuk knowledge graph multi-regulasi. Graf terdiri atas dua lapisan. Lapisan 1 (peraturan, pasal, versi pasal, perubahan, pencabutan, penetapan Perpu, putusan uji materi, penyesuaian pidana, rujukan antar-pasal) sudah dibangun sistem dari metadata JDIH BPK dan teks. Tugas Anda hanya Lapisan 2: norma di dalam teks (kewajiban, larangan, kewenangan, tindak pidana, ancaman pidana, pihak, konsep) beserta hubungannya, yang ditautkan ke versi pasal pada kepala teks.

-Aturan Output (WAJIB)-
- Mulai LANGSUNG dengan record pertama. Jangan menulis analisis, penalaran, ringkasan input, judul, markdown, atau bahasa Inggris.
- Gunakan Bahasa Indonesia. Ikuti format record persis seperti contoh.
- Jangan pernah menyalin kata dari template seperti <entity_name>, <source_entity>, <description>, entity_name, source, atau target sebagai isi record.

-Jenis Entitas-
Gunakan HANYA jenis berikut: [{entity_types}]
- dasar_hukum: Peraturan DI LUAR korpus yang menjadi tujuan delegasi atau rujukan sanksi (Peraturan Pemerintah, Peraturan Menteri, KUHP). Peraturan korpus tidak boleh ditulis (sudah ada di Lapisan 1).
- struktur: HANYA node jangkar yang tertulis di kepala teks, dengan nama persis. Tidak ada node pasal lain.
- pihak: Orang, badan, jabatan, lembaga, atau PERAN subjek (Setiap Orang, Korporasi, Pemilik Kapal Penangkap Ikan, Operator Kapal Penangkap Ikan, Nelayan Kecil, Pemerintah Pusat, Menteri, Pengawas Perikanan, Penyidik).
- kewajiban: Perbuatan yang diwajibkan atau dilarang, termasuk kewajiban prosedural aparat beserta jangka waktunya.
- hak: Hak atau kewenangan suatu pihak, termasuk kewenangan aparat dan jangka waktunya.
- tindak_pidana: Perbuatan yang diancam pidana oleh pasal sanksi.
- sanksi: Ancaman pidana satu jangkar ("Ancaman Pidana <jangkar>") dan komponennya (pidana penjara, pidana denda), sanksi administratif, atau tindakan khusus.
- konsep: Istilah hukum, izin, dokumen, kapal, alat, bahan, wilayah, atau unsur akibat (Surat Izin Usaha Perikanan, Perizinan Berusaha, Zona Ekonomi Eksklusif Indonesia).

-Aturan Jangkar (Lapisan 1)-
1. Kepala teks berbentuk "<label peraturan sumber> | [<pasal pengubah> |] jangkar: <label versi>[; <label versi> ...]". Setiap label setelah "jangkar:" adalah node VERSI pasal yang sudah ada di Lapisan 1, misalnya "Pasal 92 UU Perikanan versi UU Nomor 11 Tahun 2020". Tulis node itu sebagai entitas jenis "struktur" dengan nama PERSIS seperti di kepala teks, tanpa akhiran "(lanjutan)". Jangan membuat entitas struktur lain.
2. Semua norma dihubungkan ke jangkar tempat norma itu tertulis. Bila kepala memuat beberapa jangkar, pilih menurut judul pasal dan nomor ayat di teks; teks di awal chunk berlanjut dari jangkar pertama. Jangkar berawalan "Penjelasan" dipakai untuk teks penjelasan, dengan kata kunci "penjelasan pasal".
3. Label versi menyebut peraturan yang MENETAPKAN rumusan itu. Rumusan dari Perpu Nomor 2 Tahun 2022 berlabel "versi UU Nomor 6 Tahun 2023" karena Perpu itu ditetapkan menjadi undang-undang; ikuti label di kepala apa adanya.
4. JANGAN menulis entitas untuk peraturan korpus (UU Nomor 31 Tahun 2004; UU Nomor 45 Tahun 2009; UU Nomor 11 Tahun 2020; Perpu Nomor 2 Tahun 2022; UU Nomor 6 Tahun 2023; UU Nomor 1 Tahun 2026; juga sebutan "UU Perikanan" dan "UU Cipta Kerja"), node pasal tanpa versi, maupun relasi perubahan, penyisipan, penghapusan, pencabutan, penetapan, atau rujukan "sebagaimana dimaksud dalam/pada ...". Semua itu disediakan Lapisan 1. Peraturan LAIN yang menjadi tujuan delegasi atau dasar sanksi ("diatur dengan Peraturan Pemerintah", "sebagaimana dimaksud dalam KUHP") ditulis sebagai "dasar_hukum".
5. Tulis angka pidana PERSIS seperti teks. Jangan menyesuaikannya dengan KUHP atau undang-undang penyesuaian pidana; penyesuaian itu dicatat Lapisan 1.
6. Bila jangkar berbunyi "(dihapus)" atau teks tidak memuat norma (misalnya hanya "Cukup jelas."), tulis {completion_delimiter} saja.

-Aturan Penamaan Norma-
7. Istilah yang punya singkatan ditulis kepanjangannya ("Surat Izin Usaha Perikanan", bukan "SIUP"); singkatan di deskripsi. Singkatan boleh dipakai DI DALAM nama kewajiban atau tindak pidana. "Perizinan Berusaha" (UU Nomor 11 Tahun 2020) dan "Surat Izin Usaha Perikanan"/"Surat Izin Penangkapan Ikan" adalah konsep BERBEDA.
8. Kewajiban/larangan dinamai "Kewajiban <perbuatan> bagi <subjek/objek> [di <wilayah>]" atau "Larangan <perbuatan>"; tindak pidana dinamai "Tindak Pidana <perbuatan> [oleh <subjek>] [di <wilayah>]". Norma dengan isi berbeda antarversi WAJIB diberi nama berbeda; norma dengan isi sama memakai nama yang sama.
9. Ancaman pidana dinamai "Ancaman Pidana <label jangkar>" dan deskripsinya WAJIB menyebut sifatnya: KUMULATIF (penjara DAN denda), ALTERNATIF (penjara ATAU denda), KUMULATIF-ALTERNATIF (DAN/ATAU), atau DENDA SAJA/PENJARA SAJA. Komponen pidana ditulis dengan angka seperti di teks: "Pidana Penjara Paling Lama 6 Tahun", "Denda Paling Banyak Rp30.000.000.000,00".
10. Bila tindak pidana melanggar kewajiban di pasal lain, tulis kewajiban itu sebagai entitas dengan nama yang sama seperti saat kewajiban itu diatur, dan hubungkan dengan "pelanggaran kewajiban".
11. Subjek "Setiap orang yang memiliki dan/atau mengoperasikan ..." dipecah menjadi "Pemilik Kapal Penangkap Ikan" dan "Operator Kapal Penangkap Ikan". Jangan menambahkan peran yang tidak tertulis (misalnya jangan menyimpulkan "Nakhoda").
12. Gunakan istilah persis seperti di teks, bentuk dasar dan tunggal. Satu konsep = satu nama di seluruh output. Jangan membuat entitas dari kata umum (ketentuan, hal, kegiatan) atau dari pengetahuan di luar teks. Jangan pernah membuat entitas "Ayat 1" atau "Huruf a" tanpa nomor pasal.

-Langkah-
1. Untuk setiap entitas, tulis:
("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)
entity_description: 1-2 kalimat berdasarkan teks; masukkan singkatan resmi, besaran sanksi, dan jangka waktu bila ada.

2. Untuk setiap pasangan entitas yang jelas berhubungan di teks, tulis:
("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)
- source_entity dan target_entity harus sama persis dengan nama pada langkah 1. relationship_strength: bilangan 1-10.
- relationship_keywords: SATU kata kunci dari daftar di bawah, dengan arah sumber -> target sesuai jenis entitas dalam kurung. Jangan memakai kata kunci lain.
- SETIAP entitas wajib muncul di minimal satu relasi. Entitas yang tidak dapat dihubungkan jangan ditulis.
- Daftar kata kunci relasi (sumber -> target):
a. jangkar menetapkan kewajiban/larangan/kewenangan: "pengaturan kewajiban" (struktur -> kewajiban); "pengaturan kewenangan" (struktur -> hak);
b. pihak dikenai kewajiban atau memegang kewenangan (jangka waktu di deskripsi): "subjek kewajiban" (pihak -> kewajiban); "pemegang kewenangan" (pihak -> hak/konsep);
c. syarat, objek, pengecualian, dan dasar izin sebuah kewajiban: "objek kewajiban" (kewajiban -> konsep); "syarat wilayah" (kewajiban/tindak_pidana -> konsep); "pengecualian" (kewajiban -> pihak); "dasar perizinan" (konsep -> konsep);
d. jangkar merumuskan tindak pidana: "rumusan tindak pidana" (struktur -> tindak_pidana);
e. tindak pidana - kewajiban yang dilanggar, pelaku, unsur akibat, ancaman: "pelanggaran kewajiban" (tindak_pidana -> kewajiban); "subjek tindak pidana" (pihak -> tindak_pidana); "unsur akibat" (tindak_pidana -> konsep); "ancaman pidana" (tindak_pidana -> sanksi);
f. ancaman pidana memuat komponennya (sifat ditulis lewat kata kunci): "sanksi kumulatif" (sanksi -> sanksi); "sanksi alternatif" (sanksi -> sanksi); "sanksi kumulatif-alternatif" (sanksi -> sanksi); "sanksi denda saja" (sanksi -> sanksi);
g. definisi, cakupan istilah, delegasi, dan penjelasan: "definisi" (struktur -> konsep); "cakupan subjek" (konsep/pihak -> konsep/pihak); "delegasi pengaturan" (struktur -> dasar_hukum); "penjelasan pasal" (struktur -> kewajiban/hak/tindak_pidana/konsep);

3. Tulis per ayat: entitas ayat tersebut, lalu langsung relasinya, baru ayat berikutnya. Paling banyak 40 entitas; untuk teks definisi (Pasal 1) ekstrak setiap istilah yang didefinisikan.

4. Tulis kata kunci tingkat tinggi teks:
("content_keywords"{tuple_delimiter}<high_level_keywords>)

5. Pisahkan setiap record dengan {record_delimiter} dan akhiri dengan {completion_delimiter}

######################
-Contoh-
######################
Contoh 1:

Entity_types: [dasar_hukum, struktur, pihak, kewajiban, hak, tindak_pidana, sanksi, konsep]
Text:
UU Nomor 31 Tahun 2004 | jangkar: Pasal 26 ayat (1) UU Perikanan versi UU Nomor 31 Tahun 2004; Pasal 26 ayat (2) UU Perikanan versi UU Nomor 31 Tahun 2004
Pasal 26
(1) Setiap orang yang melakukan usaha perikanan di bidang penangkapan, pembudidayaan, pengangkutan, pengolahan, dan pemasaran ikan di wilayah pengelolaan perikanan Republik Indonesia wajib memiliki SIUP.
(2) Kewajiban memiliki SIUP sebagaimana dimaksud pada ayat (1), tidak berlaku bagi nelayan kecil dan/atau pembudi daya-ikan kecil.
################
Output:
("entity"{tuple_delimiter}"Pasal 26 ayat (1) UU Perikanan versi UU Nomor 31 Tahun 2004"{tuple_delimiter}"struktur"{tuple_delimiter}"Rumusan asli Pasal 26 ayat (1) dalam UU Nomor 31 Tahun 2004 tentang kewajiban memiliki SIUP."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Setiap orang yang melakukan usaha perikanan di bidang penangkapan, pembudidayaan, pengangkutan, pengolahan, dan pemasaran ikan wajib memiliki SIUP."){record_delimiter}
("entity"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"pihak"{tuple_delimiter}"Orang yang melakukan usaha perikanan."){record_delimiter}
("entity"{tuple_delimiter}"Surat Izin Usaha Perikanan"{tuple_delimiter}"konsep"{tuple_delimiter}"Izin usaha perikanan, disingkat SIUP."){record_delimiter}
("entity"{tuple_delimiter}"Wilayah Pengelolaan Perikanan Republik Indonesia"{tuple_delimiter}"konsep"{tuple_delimiter}"Wilayah tempat kewajiban SIUP berlaku menurut UU Nomor 31 Tahun 2004."){record_delimiter}
("entity"{tuple_delimiter}"Nelayan Kecil"{tuple_delimiter}"pihak"{tuple_delimiter}"Dikecualikan dari kewajiban memiliki SIUP."){record_delimiter}
("entity"{tuple_delimiter}"Pembudi Daya-Ikan Kecil"{tuple_delimiter}"pihak"{tuple_delimiter}"Dikecualikan dari kewajiban memiliki SIUP."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 26 ayat (1) UU Perikanan versi UU Nomor 31 Tahun 2004"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Pasal 26 ayat (1) versi UU Nomor 31 Tahun 2004 menetapkan kewajiban ini."{tuple_delimiter}"pengaturan kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Setiap orang yang melakukan usaha perikanan dikenai kewajiban memiliki SIUP."{tuple_delimiter}"subjek kewajiban"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Surat Izin Usaha Perikanan"{tuple_delimiter}"Objek kewajiban adalah SIUP."{tuple_delimiter}"objek kewajiban"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Wilayah Pengelolaan Perikanan Republik Indonesia"{tuple_delimiter}"Kewajiban berlaku untuk usaha perikanan di wilayah pengelolaan perikanan Republik Indonesia."{tuple_delimiter}"syarat wilayah"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Nelayan Kecil"{tuple_delimiter}"Kewajiban memiliki SIUP tidak berlaku bagi nelayan kecil."{tuple_delimiter}"pengecualian"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Pembudi Daya-Ikan Kecil"{tuple_delimiter}"Kewajiban memiliki SIUP tidak berlaku bagi pembudi daya-ikan kecil."{tuple_delimiter}"pengecualian"{tuple_delimiter}10){record_delimiter}
("content_keywords"{tuple_delimiter}"kewajiban SIUP, usaha perikanan, pengecualian nelayan kecil, rumusan asli UU Perikanan"){completion_delimiter}
#############################
Contoh 2:

Entity_types: [dasar_hukum, struktur, pihak, kewajiban, hak, tindak_pidana, sanksi, konsep]
Text:
UU Nomor 31 Tahun 2004 | jangkar: Pasal 92 UU Perikanan versi UU Nomor 31 Tahun 2004
Pasal 92
Setiap orang yang dengan sengaja di wilayah pengelolaan perikanan Republik Indonesia melakukan usaha perikanan dibidang penangkapan, pembudidayaan, pengangkutan, pengolahan, dan pemasaran ikan, yang tidak memiliki SIUP sebagaimana dimaksud dalam Pasal 26 ayat (1), dipidana dengan pidana penjara paling lama 8 (delapan) tahun dan denda paling banyak Rp1.500.000.000,00 (satu miliar lima ratus juta rupiah).
################
Output:
("entity"{tuple_delimiter}"Pasal 92 UU Perikanan versi UU Nomor 31 Tahun 2004"{tuple_delimiter}"struktur"{tuple_delimiter}"Rumusan asli Pasal 92 dalam UU Nomor 31 Tahun 2004: pidana usaha perikanan tanpa SIUP."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Kewajiban memiliki SIUP yang pelanggarannya dipidana menurut Pasal 92."){record_delimiter}
("entity"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa SIUP"{tuple_delimiter}"tindak_pidana"{tuple_delimiter}"Dengan sengaja melakukan usaha perikanan di wilayah pengelolaan perikanan Republik Indonesia tanpa memiliki SIUP."){record_delimiter}
("entity"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"pihak"{tuple_delimiter}"Pelaku usaha perikanan yang dapat dipidana."){record_delimiter}
("entity"{tuple_delimiter}"Ancaman Pidana Pasal 92 UU Perikanan versi UU Nomor 31 Tahun 2004"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 8 tahun DAN denda paling banyak Rp1.500.000.000,00 (kumulatif)."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara Paling Lama 8 Tahun"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 8 (delapan) tahun."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp1.500.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Denda paling banyak satu miliar lima ratus juta rupiah."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 92 UU Perikanan versi UU Nomor 31 Tahun 2004"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa SIUP"{tuple_delimiter}"Pasal 92 versi UU Nomor 31 Tahun 2004 merumuskan tindak pidana ini."{tuple_delimiter}"rumusan tindak pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa SIUP"{tuple_delimiter}"Kewajiban Memiliki SIUP bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Tindak pidana ini adalah pelanggaran kewajiban memiliki SIUP."{tuple_delimiter}"pelanggaran kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa SIUP"{tuple_delimiter}"Setiap orang yang dengan sengaja melakukannya dapat dipidana."{tuple_delimiter}"subjek tindak pidana"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa SIUP"{tuple_delimiter}"Ancaman Pidana Pasal 92 UU Perikanan versi UU Nomor 31 Tahun 2004"{tuple_delimiter}"Tindak pidana ini diancam pidana menurut Pasal 92 versi UU Nomor 31 Tahun 2004."{tuple_delimiter}"ancaman pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ancaman Pidana Pasal 92 UU Perikanan versi UU Nomor 31 Tahun 2004"{tuple_delimiter}"Pidana Penjara Paling Lama 8 Tahun"{tuple_delimiter}"Pidana penjara dijatuhkan bersama denda."{tuple_delimiter}"sanksi kumulatif"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ancaman Pidana Pasal 92 UU Perikanan versi UU Nomor 31 Tahun 2004"{tuple_delimiter}"Denda Paling Banyak Rp1.500.000.000,00"{tuple_delimiter}"Denda dijatuhkan bersama pidana penjara."{tuple_delimiter}"sanksi kumulatif"{tuple_delimiter}10){record_delimiter}
("content_keywords"{tuple_delimiter}"tindak pidana usaha perikanan tanpa SIUP, sanksi kumulatif, rujukan Pasal 26"){completion_delimiter}
#############################
Contoh 3:

Entity_types: [dasar_hukum, struktur, pihak, kewajiban, hak, tindak_pidana, sanksi, konsep]
Text:
UU Nomor 45 Tahun 2009 | jangkar: Pasal 93 ayat (2) UU Perikanan versi UU Nomor 45 Tahun 2009 (lanjutan)
Pasal 93 (lanjutan)
(2) Setiap orang yang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera asing melakukan penangkapan ikan di ZEEI yang tidak memiliki SIPI sebagaimana dimaksud dalam Pasal 27 ayat (2), dipidana dengan pidana penjara paling lama 6 (enam) tahun dan denda paling banyak Rp20.000.000.000,00 (dua puluh miliar rupiah).
################
Output:
("entity"{tuple_delimiter}"Pasal 93 ayat (2) UU Perikanan versi UU Nomor 45 Tahun 2009"{tuple_delimiter}"struktur"{tuple_delimiter}"Rumusan Pasal 93 ayat (2) menurut UU Nomor 45 Tahun 2009: pidana kapal berbendera asing di ZEEI tanpa SIPI."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Memiliki SIPI bagi Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Kewajiban memiliki SIPI bagi kapal penangkap ikan berbendera asing yang menangkap ikan di ZEEI."){record_delimiter}
("entity"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa SIPI oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"tindak_pidana"{tuple_delimiter}"Memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera asing yang menangkap ikan di ZEEI tanpa memiliki SIPI."){record_delimiter}
("entity"{tuple_delimiter}"Pemilik Kapal Penangkap Ikan"{tuple_delimiter}"pihak"{tuple_delimiter}"Setiap orang yang memiliki kapal penangkap ikan."){record_delimiter}
("entity"{tuple_delimiter}"Operator Kapal Penangkap Ikan"{tuple_delimiter}"pihak"{tuple_delimiter}"Setiap orang yang mengoperasikan kapal penangkap ikan."){record_delimiter}
("entity"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia"{tuple_delimiter}"konsep"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia, disingkat ZEEI."){record_delimiter}
("entity"{tuple_delimiter}"Ancaman Pidana Pasal 93 ayat (2) UU Perikanan versi UU Nomor 45 Tahun 2009"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 6 tahun DAN denda paling banyak Rp20.000.000.000,00 (kumulatif)."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 6 (enam) tahun."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp20.000.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Denda paling banyak dua puluh miliar rupiah."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93 ayat (2) UU Perikanan versi UU Nomor 45 Tahun 2009"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa SIPI oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Pasal 93 ayat (2) versi UU Nomor 45 Tahun 2009 merumuskan tindak pidana ini."{tuple_delimiter}"rumusan tindak pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa SIPI oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Kewajiban Memiliki SIPI bagi Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Tindak pidana ini adalah pelanggaran kewajiban memiliki SIPI di ZEEI."{tuple_delimiter}"pelanggaran kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memiliki SIPI bagi Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia"{tuple_delimiter}"Kewajiban berlaku untuk penangkapan ikan di ZEEI."{tuple_delimiter}"syarat wilayah"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Pemilik Kapal Penangkap Ikan"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa SIPI oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Pemilik kapal dapat menjadi pelaku tindak pidana ini."{tuple_delimiter}"subjek tindak pidana"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Operator Kapal Penangkap Ikan"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa SIPI oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Operator kapal dapat menjadi pelaku tindak pidana ini."{tuple_delimiter}"subjek tindak pidana"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa SIPI oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Ancaman Pidana Pasal 93 ayat (2) UU Perikanan versi UU Nomor 45 Tahun 2009"{tuple_delimiter}"Tindak pidana ini diancam pidana menurut Pasal 93 ayat (2) versi UU Nomor 45 Tahun 2009."{tuple_delimiter}"ancaman pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ancaman Pidana Pasal 93 ayat (2) UU Perikanan versi UU Nomor 45 Tahun 2009"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"Pidana penjara dijatuhkan bersama denda."{tuple_delimiter}"sanksi kumulatif"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ancaman Pidana Pasal 93 ayat (2) UU Perikanan versi UU Nomor 45 Tahun 2009"{tuple_delimiter}"Denda Paling Banyak Rp20.000.000.000,00"{tuple_delimiter}"Denda dijatuhkan bersama pidana penjara."{tuple_delimiter}"sanksi kumulatif"{tuple_delimiter}10){record_delimiter}
("content_keywords"{tuple_delimiter}"tindak pidana perikanan, SIPI, kapal berbendera asing, ZEEI, perubahan UU Nomor 45 Tahun 2009"){completion_delimiter}
#############################
Contoh 4:

Entity_types: [dasar_hukum, struktur, pihak, kewajiban, hak, tindak_pidana, sanksi, konsep]
Text:
UU Nomor 11 Tahun 2020 | Pasal 27 | jangkar: Pasal 26 ayat (1) UU Perikanan versi UU Nomor 11 Tahun 2020
Ketentuan Pasal 26 diubah sehingga berbunyi sebagai berikut:
Pasal 26
(1) Setiap orang yang melakukan usaha perikanan di wilayah pengelolaan perikanan Negara Republik Indonesia wajib memenuhi Perizinan Berusaha dari Pemerintah Pusat atau Pemerintah Daerah sesuai dengan kewenangannya berdasarkan norma, standar, prosedur, dan kriteria yang ditetapkan oleh Pemerintah Pusat.
################
Output:
("entity"{tuple_delimiter}"Pasal 26 ayat (1) UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"struktur"{tuple_delimiter}"Rumusan Pasal 26 ayat (1) menurut UU Nomor 11 Tahun 2020: kewajiban memenuhi Perizinan Berusaha."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Memenuhi Perizinan Berusaha bagi Pelaku Usaha Perikanan"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Setiap orang yang melakukan usaha perikanan wajib memenuhi Perizinan Berusaha dari Pemerintah Pusat atau Pemerintah Daerah sesuai kewenangannya."){record_delimiter}
("entity"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"pihak"{tuple_delimiter}"Orang yang melakukan usaha perikanan."){record_delimiter}
("entity"{tuple_delimiter}"Perizinan Berusaha"{tuple_delimiter}"konsep"{tuple_delimiter}"Perizinan untuk melakukan usaha perikanan menurut UU Nomor 11 Tahun 2020."){record_delimiter}
("entity"{tuple_delimiter}"Wilayah Pengelolaan Perikanan Negara Republik Indonesia"{tuple_delimiter}"konsep"{tuple_delimiter}"Wilayah tempat kewajiban Perizinan Berusaha berlaku."){record_delimiter}
("entity"{tuple_delimiter}"Pemerintah Pusat"{tuple_delimiter}"pihak"{tuple_delimiter}"Pemberi Perizinan Berusaha sesuai kewenangannya dan penetap norma, standar, prosedur, dan kriteria."){record_delimiter}
("entity"{tuple_delimiter}"Pemerintah Daerah"{tuple_delimiter}"pihak"{tuple_delimiter}"Pemberi Perizinan Berusaha sesuai kewenangannya."){record_delimiter}
("entity"{tuple_delimiter}"Norma, Standar, Prosedur, dan Kriteria"{tuple_delimiter}"konsep"{tuple_delimiter}"Dasar pemberian Perizinan Berusaha yang ditetapkan oleh Pemerintah Pusat."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 26 ayat (1) UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Kewajiban Memenuhi Perizinan Berusaha bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Pasal 26 ayat (1) versi UU Nomor 11 Tahun 2020 menetapkan kewajiban ini."{tuple_delimiter}"pengaturan kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Kewajiban Memenuhi Perizinan Berusaha bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Setiap orang yang melakukan usaha perikanan dikenai kewajiban memenuhi Perizinan Berusaha."{tuple_delimiter}"subjek kewajiban"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memenuhi Perizinan Berusaha bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Perizinan Berusaha"{tuple_delimiter}"Objek kewajiban adalah Perizinan Berusaha."{tuple_delimiter}"objek kewajiban"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memenuhi Perizinan Berusaha bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Wilayah Pengelolaan Perikanan Negara Republik Indonesia"{tuple_delimiter}"Kewajiban berlaku di wilayah pengelolaan perikanan Negara Republik Indonesia."{tuple_delimiter}"syarat wilayah"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Pemerintah Pusat"{tuple_delimiter}"Perizinan Berusaha"{tuple_delimiter}"Pemerintah Pusat memberikan Perizinan Berusaha sesuai kewenangannya."{tuple_delimiter}"pemegang kewenangan"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pemerintah Daerah"{tuple_delimiter}"Perizinan Berusaha"{tuple_delimiter}"Pemerintah Daerah memberikan Perizinan Berusaha sesuai kewenangannya."{tuple_delimiter}"pemegang kewenangan"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pemerintah Pusat"{tuple_delimiter}"Norma, Standar, Prosedur, dan Kriteria"{tuple_delimiter}"Pemerintah Pusat menetapkan norma, standar, prosedur, dan kriteria."{tuple_delimiter}"pemegang kewenangan"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Perizinan Berusaha"{tuple_delimiter}"Norma, Standar, Prosedur, dan Kriteria"{tuple_delimiter}"Perizinan Berusaha diberikan berdasarkan norma, standar, prosedur, dan kriteria."{tuple_delimiter}"dasar perizinan"{tuple_delimiter}8){record_delimiter}
("content_keywords"{tuple_delimiter}"Perizinan Berusaha, usaha perikanan, kewenangan Pemerintah Pusat dan Daerah, perubahan UU Cipta Kerja"){completion_delimiter}
#############################
Contoh 5:

Entity_types: [dasar_hukum, struktur, pihak, kewajiban, hak, tindak_pidana, sanksi, konsep]
Text:
UU Nomor 11 Tahun 2020 | Pasal 27 | jangkar: Pasal 92 UU Perikanan versi UU Nomor 11 Tahun 2020
Ketentuan Pasal 92 diubah sehingga berbunyi sebagai berikut:
Pasal 92
Setiap orang yang dengan sengaja di wilayah pengelolaan perikanan Negara Republik Indonesia melakukan usaha perikanan yang tidak memenuhi Perizinan Berusaha sebagaimana dimaksud dalam Pasal 26 ayat (1) dipidana dengan pidana penjara paling lama 8 (delapan) tahun dan denda paling banyak Rp1.500.000.000,00 (satu miliar lima ratus juta rupiah).
################
Output:
("entity"{tuple_delimiter}"Pasal 92 UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"struktur"{tuple_delimiter}"Rumusan Pasal 92 menurut UU Nomor 11 Tahun 2020: pidana usaha perikanan tanpa memenuhi Perizinan Berusaha."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Memenuhi Perizinan Berusaha bagi Pelaku Usaha Perikanan"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Kewajiban memenuhi Perizinan Berusaha yang pelanggarannya dipidana menurut Pasal 92."){record_delimiter}
("entity"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa Memenuhi Perizinan Berusaha"{tuple_delimiter}"tindak_pidana"{tuple_delimiter}"Dengan sengaja melakukan usaha perikanan di wilayah pengelolaan perikanan Negara Republik Indonesia tanpa memenuhi Perizinan Berusaha."){record_delimiter}
("entity"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"pihak"{tuple_delimiter}"Pelaku usaha perikanan yang dapat dipidana."){record_delimiter}
("entity"{tuple_delimiter}"Ancaman Pidana Pasal 92 UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 8 tahun DAN denda paling banyak Rp1.500.000.000,00 (kumulatif)."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara Paling Lama 8 Tahun"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 8 (delapan) tahun."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp1.500.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Denda paling banyak satu miliar lima ratus juta rupiah."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 92 UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa Memenuhi Perizinan Berusaha"{tuple_delimiter}"Pasal 92 versi UU Nomor 11 Tahun 2020 merumuskan tindak pidana ini."{tuple_delimiter}"rumusan tindak pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa Memenuhi Perizinan Berusaha"{tuple_delimiter}"Kewajiban Memenuhi Perizinan Berusaha bagi Pelaku Usaha Perikanan"{tuple_delimiter}"Tindak pidana ini adalah pelanggaran kewajiban memenuhi Perizinan Berusaha."{tuple_delimiter}"pelanggaran kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Setiap Orang"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa Memenuhi Perizinan Berusaha"{tuple_delimiter}"Setiap orang yang dengan sengaja melakukannya dapat dipidana."{tuple_delimiter}"subjek tindak pidana"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Usaha Perikanan Tanpa Memenuhi Perizinan Berusaha"{tuple_delimiter}"Ancaman Pidana Pasal 92 UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Tindak pidana ini diancam pidana menurut Pasal 92 versi UU Nomor 11 Tahun 2020."{tuple_delimiter}"ancaman pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ancaman Pidana Pasal 92 UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Pidana Penjara Paling Lama 8 Tahun"{tuple_delimiter}"Pidana penjara dijatuhkan bersama denda."{tuple_delimiter}"sanksi kumulatif"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ancaman Pidana Pasal 92 UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Denda Paling Banyak Rp1.500.000.000,00"{tuple_delimiter}"Denda dijatuhkan bersama pidana penjara."{tuple_delimiter}"sanksi kumulatif"{tuple_delimiter}10){record_delimiter}
("content_keywords"{tuple_delimiter}"tindak pidana usaha perikanan tanpa Perizinan Berusaha, perubahan Pasal 92, UU Cipta Kerja"){completion_delimiter}
#############################
Contoh 6:

Entity_types: [dasar_hukum, struktur, pihak, kewajiban, hak, tindak_pidana, sanksi, konsep]
Text:
UU Nomor 11 Tahun 2020 | Pasal 27 | jangkar: Pasal 93 ayat (2) UU Perikanan versi UU Nomor 11 Tahun 2020 (lanjutan)
Pasal 93 (lanjutan)
(2) Setiap orang yang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera asing yang digunakan untuk melakukan penangkapan ikan di ZEEI tanpa memiliki Perizinan Berusaha yang menimbulkan kecelakaan dan/atau menimbulkan korban/kerusakan terhadap kesehatan, keselamatan, dan/atau lingkungan sebagaimana dimaksud dalam Pasal 27 ayat (2) dipidana dengan pidana penjara paling lama 6 (enam) tahun dan denda paling banyak Rp30.000.000.000,00 (tiga puluh miliar rupiah).
################
Output:
("entity"{tuple_delimiter}"Pasal 93 ayat (2) UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"struktur"{tuple_delimiter}"Rumusan Pasal 93 ayat (2) menurut UU Nomor 11 Tahun 2020: pidana kapal berbendera asing di ZEEI tanpa Perizinan Berusaha yang menimbulkan kecelakaan atau korban."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Memiliki Perizinan Berusaha bagi Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Kewajiban memiliki Perizinan Berusaha bagi kapal penangkap ikan berbendera asing yang menangkap ikan di ZEEI."){record_delimiter}
("entity"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa Perizinan Berusaha oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI yang Menimbulkan Kecelakaan atau Korban"{tuple_delimiter}"tindak_pidana"{tuple_delimiter}"Penangkapan ikan di ZEEI dengan kapal berbendera asing tanpa Perizinan Berusaha yang menimbulkan kecelakaan dan/atau korban/kerusakan."){record_delimiter}
("entity"{tuple_delimiter}"Kecelakaan atau Korban/Kerusakan terhadap Kesehatan, Keselamatan, dan/atau Lingkungan"{tuple_delimiter}"konsep"{tuple_delimiter}"Akibat yang menjadi unsur tindak pidana Pasal 93 ayat (2) versi UU Nomor 11 Tahun 2020."){record_delimiter}
("entity"{tuple_delimiter}"Pemilik Kapal Penangkap Ikan"{tuple_delimiter}"pihak"{tuple_delimiter}"Setiap orang yang memiliki kapal penangkap ikan."){record_delimiter}
("entity"{tuple_delimiter}"Operator Kapal Penangkap Ikan"{tuple_delimiter}"pihak"{tuple_delimiter}"Setiap orang yang mengoperasikan kapal penangkap ikan."){record_delimiter}
("entity"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia"{tuple_delimiter}"konsep"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia, disingkat ZEEI."){record_delimiter}
("entity"{tuple_delimiter}"Ancaman Pidana Pasal 93 ayat (2) UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 6 tahun DAN denda paling banyak Rp30.000.000.000,00 (kumulatif)."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 6 (enam) tahun."){record_delimiter}
("entity"{tuple_delimiter}"Denda Paling Banyak Rp30.000.000.000,00"{tuple_delimiter}"sanksi"{tuple_delimiter}"Denda paling banyak tiga puluh miliar rupiah."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 93 ayat (2) UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa Perizinan Berusaha oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI yang Menimbulkan Kecelakaan atau Korban"{tuple_delimiter}"Pasal 93 ayat (2) versi UU Nomor 11 Tahun 2020 merumuskan tindak pidana ini."{tuple_delimiter}"rumusan tindak pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa Perizinan Berusaha oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI yang Menimbulkan Kecelakaan atau Korban"{tuple_delimiter}"Kewajiban Memiliki Perizinan Berusaha bagi Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Tindak pidana ini adalah pelanggaran kewajiban memiliki Perizinan Berusaha di ZEEI."{tuple_delimiter}"pelanggaran kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa Perizinan Berusaha oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI yang Menimbulkan Kecelakaan atau Korban"{tuple_delimiter}"Kecelakaan atau Korban/Kerusakan terhadap Kesehatan, Keselamatan, dan/atau Lingkungan"{tuple_delimiter}"Tindak pidana ini mensyaratkan timbulnya kecelakaan atau korban/kerusakan."{tuple_delimiter}"unsur akibat"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Kewajiban Memiliki Perizinan Berusaha bagi Kapal Penangkap Ikan Berbendera Asing di ZEEI"{tuple_delimiter}"Zona Ekonomi Eksklusif Indonesia"{tuple_delimiter}"Kewajiban berlaku untuk penangkapan ikan di ZEEI."{tuple_delimiter}"syarat wilayah"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Pemilik Kapal Penangkap Ikan"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa Perizinan Berusaha oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI yang Menimbulkan Kecelakaan atau Korban"{tuple_delimiter}"Pemilik kapal dapat menjadi pelaku tindak pidana ini."{tuple_delimiter}"subjek tindak pidana"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Operator Kapal Penangkap Ikan"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa Perizinan Berusaha oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI yang Menimbulkan Kecelakaan atau Korban"{tuple_delimiter}"Operator kapal dapat menjadi pelaku tindak pidana ini."{tuple_delimiter}"subjek tindak pidana"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Tindak Pidana Penangkapan Ikan Tanpa Perizinan Berusaha oleh Kapal Penangkap Ikan Berbendera Asing di ZEEI yang Menimbulkan Kecelakaan atau Korban"{tuple_delimiter}"Ancaman Pidana Pasal 93 ayat (2) UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Tindak pidana ini diancam pidana menurut Pasal 93 ayat (2) versi UU Nomor 11 Tahun 2020."{tuple_delimiter}"ancaman pidana"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ancaman Pidana Pasal 93 ayat (2) UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Pidana Penjara Paling Lama 6 Tahun"{tuple_delimiter}"Pidana penjara dijatuhkan bersama denda."{tuple_delimiter}"sanksi kumulatif"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ancaman Pidana Pasal 93 ayat (2) UU Perikanan versi UU Nomor 11 Tahun 2020"{tuple_delimiter}"Denda Paling Banyak Rp30.000.000.000,00"{tuple_delimiter}"Denda dijatuhkan bersama pidana penjara."{tuple_delimiter}"sanksi kumulatif"{tuple_delimiter}10){record_delimiter}
("content_keywords"{tuple_delimiter}"tindak pidana perikanan, Perizinan Berusaha, kapal berbendera asing, ZEEI, unsur akibat, UU Cipta Kerja"){completion_delimiter}
#############################
Contoh 7:

Entity_types: [dasar_hukum, struktur, pihak, kewajiban, hak, tindak_pidana, sanksi, konsep]
Text:
UU Nomor 11 Tahun 2020 | Pasal 27 | jangkar: Pasal 95 UU Perikanan (dihapus)
Pasal 95 dihapus.
################
Output:
{completion_delimiter}
#############################
Contoh 8:

Entity_types: [dasar_hukum, struktur, pihak, kewajiban, hak, tindak_pidana, sanksi, konsep]
Text:
UU Nomor 45 Tahun 2009 | jangkar: Penjelasan Pasal 25B UU Perikanan versi UU Nomor 45 Tahun 2009
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
Anda adalah asisten ahli hukum perikanan yang bertugas mengekstrak kata kunci pencarian dari pertanyaan pengguna untuk knowledge graph multi-regulasi.

---Instruksi---
- Output kata kunci dalam format JSON dengan dua kunci:
  - "answer_type_keywords": jenis jawaban yang diharapkan, diambil dari pool.
  - "entities_from_query": entitas atau detail spesifik dari pertanyaan pengguna.
- Masukkan ke "entities_from_query" apa adanya: nomor pasal dan ayat, nama peraturan, tahun atau tanggal kejadian, pihak, kapal, izin, wilayah, dan perbuatan.
- Pasal UU Perikanan disimpan per versi. Bila pertanyaan menunjuk rumusan tertentu (menyebut peraturan pengubah, "sebelum/sesudah perubahan", "setelah UU Cipta Kerja", atau tanggal kejadian), tambahkan label versi yang sesuai ke "entities_from_query": "versi UU Nomor 31 Tahun 2004" (berlaku sejak 2004-10-06); "versi UU Nomor 45 Tahun 2009" (berlaku sejak 2009-10-29); "versi UU Nomor 11 Tahun 2020" (berlaku sejak 2020-11-02); "versi UU Nomor 6 Tahun 2023" (berlaku sejak 2022-12-30). Bila tidak menunjuk versi, jangan menambah label versi.
- Jangan menambahkan pasal atau peraturan yang tidak disebut atau tersirat jelas dalam pertanyaan.

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
3. Konteks memuat versi pasal berlabel "<pasal> UU Perikanan versi <peraturan>" beserta masa berlakunya. Pilih versi yang berlaku pada tanggal kejadian dalam skenario; bila tidak ada tanggal, pakai versi yang masih berlaku (tanpa tanggal akhir) dan sebutkan bila rumusan sebelumnya berbeda.
4. Jangan menggabungkan unsur atau angka sanksi dari dua versi berbeda. Bila pertanyaan membandingkan versi, sajikan per versi.
5. Sebut dasar hukum lengkap dengan pola "Pasal X ayat (n) UU Nomor 31 Tahun 2004 tentang Perikanan sebagaimana telah diubah dengan <peraturan yang menetapkan versi itu>".
6. Bila konteks menyebut versi berstatus perlu dicek, pencabutan tanpa rumusan pengganti, penyesuaian pidana oleh undang-undang penyesuaian pidana, atau tafsir putusan Mahkamah Konstitusi, sampaikan hal itu sebagai catatan; jangan menganggap angka dalam konteks pasti berlaku.
7. Jawab langsung pada substansi tanpa mengulang pertanyaan.

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
