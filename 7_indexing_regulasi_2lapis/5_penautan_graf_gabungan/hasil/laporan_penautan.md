# Laporan Penautan Graf Lapisan 2 ke Lapisan 1

## 1. Ringkasan Topologi Graf Gabungan
- **Node MiniRAG (Lapisan 2):** 569
- **Relasi MiniRAG (Lapisan 2):** 644
- **Format Nama Huruf Kecil:** `False`
- **Total Graf Gabungan Akhir:** **869 node**, **1820 edge**

## 2. Metrik Keberhasilan Penautan (Anchoring Metrics)
- **Struktur Cocok Jangkar:** `161/161 (100%)`
- **Struktur Karangan (Dipindah ke Jangkar Chunk):** 0
- **Struktur Tanpa Jangkar Chunk:** 0
- **Peraturan Korpus Ditulis LLM (Dilebur ke Lapisan 1):** 0
- **Kata Kunci Relasi Sesuai Skema:** `644/644 (100%)`
- **Arah & Jenis Relasi Sah:** `505/644 (78%)`
- **Versi Norma Terhubung Lewat Graf:** 397
- **Versi Cadangan Chunk:** 11
- **Norma Tanpa Versi:** 0
- **Norma Yatim (Tanpa Relasi):** 9
- **Turunan Relasi Mengancamkan:** 11

## 3. Rincian Galat & Anomali (Contoh, Maks 15 per Jenis)
### jenis entitas melanggar arah skema (Total: 139)
- `'definisi': Pasal 1 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Nelayan [pihak]`
- `'definisi': Pasal 1 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Pembudi Daya Ikan [pihak]`
- `'definisi': Pasal 1 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Setiap Orang [pihak]`
- `'definisi': Pasal 1 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Korporasi [pihak]`
- `'definisi': Pasal 1 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Pembudi Daya-Ikan Kecil [pihak]`
- `'definisi': Pasal 1 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Pemerintah [pihak]`
- `'definisi': Pasal 1 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Pemerintah Daerah [pihak]`
- `'definisi': Pasal 1 angka 11 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Nelayan Kecil [pihak]`
- `'subjek kewajiban': Kapal Perikanan [konsep] -- Kewajiban Memiliki Surat Persetujuan Berlayar bagi Kapal Perikanan [kewajiban]`
- `'pengaturan kewajiban': Kapal Perikanan [konsep] -- Pasal 66B ayat (1) UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur]`
- `'objek kewajiban': Kapal Perikanan [konsep] -- Kewenangan Pengawas Perikanan dalam Pelaksanaan Tugas [hak]`
- `'objek kewajiban': Nelayan [pihak] -- Kewajiban Membina Terselenggaranya Kebersamaan dan Kemitraan yang Sehat bagi Pemerintah [kewajiban]`
- `'objek kewajiban': Surat Izin Penangkapan Ikan [konsep] -- Kewenangan Pengawas Perikanan dalam Pelaksanaan Tugas [hak]`
- `'definisi': Pasal 1 angka 24 UU Perikanan versi UU Nomor 45 Tahun 2009 [struktur] -- Menteri [pihak]`
- `'objek kewajiban': Surat Izin Kapal Pengangkut Ikan [konsep] -- Kewenangan Pengawas Perikanan dalam Pelaksanaan Tugas [hak]`
