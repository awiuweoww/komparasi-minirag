# Dokumentasi Komparasi MiniRAG UU 45 Tahun 2009

## Gemma 3:12B (Baseline M. Arjun Dewana) vs Gemma 4:12B (Chandra Supriatna)

**Cluster:** BRIN MAHAMERU-AI (NVIDIA DGX A100)

---

## 1. Struktur Folder

```text
pengujian-komparasi-minirag/
├── README.md                                # Dokumentasi panduan eksekusi komprehensif
├── LOG_VERSION.md                           # Log riwayat pembaruan antar versi (V1 -> V2 -> V3)
├── ANALISA_PERCOBAAN_1_DAN_2.md             # Analisis mendalam komparasi stabilitas Percobaan 1 vs 2
├── check_env.sh                             # Skrip otomatis pengecekan tools & environment
├── extract_mineru_hpc.py                    # Ekstraksi MinerU v4 & chunker pasal
├── run_mineru_extract.sbatch                # SLURM script ekstraksi MinerU di DGX A100
├── pull_models.sh                           # Skrip pengunduhan model gemma4 & bge-m3
├── 1_dokumen_sumber/                        # Naskah resmi & data ekstraksi MinerU otentik
│   ├── UU Nomor 45 Tahun 2009.pdf           # Naskah PDF sumber
│   ├── chunks_uu_45_2009.json               # Hasil chunk awal berbasis pasal
│   ├── chunks_uu_45_2009_512.json           # Chunk standar 512 token + 100 overlap
│   └── UU_Nomor_45_Tahun_2009/              # Hasil parsing MinerU v4 otentik
│       ├── content_list.json                # Metadata visual DLA & bounding box
│       ├── output.md                        # Konversi Markdown utuh
│       └── origin.pdf                       # Berkas PDF asli
├── 2_minirag_mjundewana/                    # Baseline M. Arjun Dewana (Gemma 3:12B)
│   └── UU Nomor 45 Tahun 2009/
│       ├── graph_chunk_entity_relation.graphml
│       ├── kv_store_text_chunks.json
│       ├── vdb_entities.json
│       ├── vdb_entities_name.json
│       └── vdb_relationships.json
├── 3_minirag_chandra/                       # Indexing Gemma 4:12B - Versi 1 (Baseline Awal: 218 Node / 428 Edge)
│   ├── proses_indexing/
│   │   ├── index_gemma4_fast.py             # Script indexing V1
│   │   ├── run_indexing.sbatch              # SLURM batch V1
│   │   ├── data/chunks_uu_45_2009.json      # Chunk pasal MinerU
│   │   └── minirag/prompt_id_revisi.py      # Prompt revisi V1
│   └── hasil_indexing/
│       └── storage_gemma4_uu45/             # Hasil V1 (218 Node / 428 Edge)
├── 4_minirag_chandra_v2/                    # Indexing Gemma 4:12B - Versi 2 (Tuned: 595 Node / 817 Edge)
│   ├── proses_indexing/
│   │   ├── rechunk_512.py                   # Re-chunking 512 token boundary-aware & legal header
│   │   ├── normalisasi_entitas.py           # Modul kanonikalisasi ALIASES & dedup_graph resmi BRIN
│   │   ├── index_gemma4_fast.py             # Script indexing V2 (Prompt v2.2.0, balanced parser, hierarchical anchoring)
│   │   ├── run_indexing.sbatch              # SLURM batch V2 (dynamic port anti-collision, 4 parallel slot A100)
│   │   ├── data/chunks_uu_45_2009.json      # 60 chunk token standar ber-header kanonik
│   │   └── minirag/prompt_id_revisi.py      # Prompt Indexing Resmi BRIN v2.2.0
│   └── hasil_indexing/
│       └── storage_gemma4_uu45/             # Hasil V2 (595 Node / 817 Edge, 0 Isolates, 0 Junk, 10 Duplikat)
└── 5_minirag_chandra_v2.1/                  # Indexing Gemma 4:12B - Versi 2.1 (Strict MinerU JSON AST Mode)
    ├── proses_indexing/
    │   ├── universal_legal_chunker.py       # Engine chunking yuridis universal (Strict JSON AST & Zero-Tolerance Guard)
    │   ├── normalisasi_entitas.py           # Modul kanonikalisasi ALIASES & dedup_graph resmi BRIN
    │   ├── index_gemma4_fast.py             # Script indexing V2.1
    │   ├── run_indexing.sbatch              # SLURM batch V2.1
    │   ├── evaluate_mentor_metrics.py       # Audit 11 parameter metrik mentor (V2.1, V2, V1, Arjun)
    │   └── data/chunks_uu_45_2009.json      # 60 chunk hasil ekstraksi layout-aware MinerU AST
    └── hasil_indexing/
        └── storage_gemma4_uu45/             # Target output graf V2.1
```

---

## 2. Pengecekan Kesiapan Tools & Environment

Sebelum menjalankan proses ekstraksi atau indexing, pastikan seluruh dependensi sudah terpasang dengan benar di login node (`mahoni01`).

### A. Pengecekan Otomatis (1 Perintah)

```bash
cd ~/projek-legal-rag
bash check_env.sh
```

Skrip akan memeriksa Miniconda, Python 3.10, modul-modul library, biner Ollama, serta ketersediaan model AI.

---

### B. Panduan Instalasi Jika Komponen Belum Lengkap

#### 1. Pasang Miniconda & Buat Environment `minirag` (Jika Belum Ada)

```bash
# 1. Pasang Miniconda
curl -sLO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
rm -f Miniconda3-latest-Linux-x86_64.sh

# 2. Buat Environment minirag dengan Python 3.10
$HOME/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
$HOME/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
$HOME/miniconda3/bin/conda create -n minirag --override-channels -c conda-forge python=3.10 pip numpy networkx httpx tqdm -y

# 3. Pasang Modul Pendukung Termasuk MinerU
$HOME/miniconda3/envs/minirag/bin/pip install tiktoken nano-vectordb ollama tenacity python-dotenv json-repair pipmaster "mineru[core]>=4.0.0" pymupdf
```

#### 2. Pasang Biner Ollama v0.40.13 Portabel (Jika Belum Ada)

```bash
mkdir -p ~/projek-legal-rag/bin
curl -sL https://github.com/ollama/ollama/releases/download/v0.40.13/ollama-linux-amd64.tar.zst -o /tmp/ollama.tar.zst
/bin/zstd -d -c /tmp/ollama.tar.zst | tar -xf - -C ~/projek-legal-rag/bin/
chmod +x ~/projek-legal-rag/bin/ollama
rm -f /tmp/ollama.tar.zst
```

#### 3. Unduh Model AI ke Folder `models` Proyek (Jika Belum Ada)

_Catatan: Dijalankan di Login Node (`mahoni01`)._

```bash
cd ~/projek-legal-rag
bash pull_models.sh
```

Skrip ini secara otomatis mengunduh:

- **`gemma4:12b`** (~7.4 GB)
- **`bge-m3:latest`** (~1.2 GB)
  langsung ke folder `~/projek-legal-rag/models` pada port terisolasi 11500.

---

## 3. Manajemen Job SLURM

### Membatalkan / Menghentikan Job yang Sedang Berjalan

```bash
# Batalkan job berdasarkan Job ID tertentu
scancel <JOB_ID>

# Atau batalkan seluruh job aktif milik user
scancel -u $USER

# Pastikan job sudah berhenti (tabel antrean harus kosong)
squeue -u $USER
```

### Menghentikan Proses Ollama Background (Jika Masih Berjalan)

```bash
pkill -f ollama
```

---

## 4. Alur Lengkap Eksekusi Pengujian

### Tahap 1: Ekstraksi Dokumen MinerU v4 di HPC

Menjalankan ekstraksi otentik MinerU v4 pada PDF naskah resmi menggunakan GPU NVIDIA A100. Menghasilkan `content_list.json`, `output.md`, `origin.pdf`, dan chunk pasal.

**Di Terminal HPC (`csupriatna@mahoni01`):**

```bash
cd ~/projek-legal-rag
sbatch run_mineru_extract.sbatch
```

Pantau progresnya:

```bash
tail -f mineru_*.log
```

---

### Tahap 2: Menyimpan Hasil Ekstraksi ke Laptop Anda

Setelah job ekstraksi MinerU selesai di HPC, jalankan perintah sinkronisasi berikut **dari terminal laptop (WSL)** Anda:

```bash
# Jalankan di terminal laptop (WSL):
rsync -avzP csupriatna@mahoni01:~/projek-legal-rag/1_dokumen_sumber/ /home/chandreu/brin-2026/pengujian-komparasi-minirag/1_dokumen_sumber/
rsync -avzP csupriatna@mahoni01:~/projek-legal-rag/3_minirag_chandra/proses_indexing/data/ /home/chandreu/brin-2026/pengujian-komparasi-minirag/3_minirag_chandra/proses_indexing/data/
```

Seluruh berkas otentik MinerU (`content_list.json`, `output.md`, `origin.pdf`) dan chunk JSON pasal akan tersimpan rapi di laptop Anda.

---

### Tahap 3: Re-Chunking Standar MiniRAG (512 Token + 100 Overlap)

Sebelum indexing, potong teks bersih `output.md` MinerU v4 menjadi blok 512 token:

```bash
# Di terminal HPC (mahoni01):
cd ~/projek-legal-rag/4_minirag_chandra_v2/proses_indexing
$HOME/miniconda3/envs/minirag/bin/python rechunk_512.py
```

_(Menghasilkan 58 chunk padat konteks, menghilangkan label buatan P/C, dan menjaga 26 definisi Pasal 1 serta 11 asas tetap utuh)._

---

### Tahap 4: Menjalankan Indexing MiniRAG (Gemma 4:12B)

**Di Terminal HPC (`csupriatna@mahoni01`):**

1. Masuk ke folder skrip indexing (Versi 2 - Rekomendasi Tuned):

   ```bash
   cd ~/projek-legal-rag/4_minirag_chandra_v2/proses_indexing
   ```

   _(Atau ke `3_minirag_chandra/proses_indexing` jika ingin menjalankan Versi 1 awal)._

2. Jalankan job batch SLURM (4 slot paralel A100, RAM 100G, NUM_PREDICT=3072, think: false):

   ```bash
   sbatch run_indexing.sbatch
   ```

3. Pantau progres indexing:
   ```bash
   tail -f indexing_*.log
   ```

---

### Tahap 5: Menyimpan Hasil Indexing MiniRAG ke Laptop Anda

Setelah proses indexing selesai (ditandai `INDEXING SELESAI SUKSES`), simpan seluruh artefak graf dan vektor ke laptop Anda dengan menjalankan perintah ini **dari terminal laptop (WSL)**:

```bash
# Unduh Hasil Versi 2 (Tuned):
rsync -avzP csupriatna@mahoni01:~/projek-legal-rag/4_minirag_chandra_v2/hasil_indexing/ /home/chandreu/brin-2026/pengujian-komparasi-minirag/4_minirag_chandra_v2/hasil_indexing/

# Unduh Hasil Versi 1 (Baseline Awal jika ada update):
rsync -avzP csupriatna@mahoni01:~/projek-legal-rag/3_minirag_chandra/hasil_indexing/ /home/chandreu/brin-2026/pengujian-komparasi-minirag/3_minirag_chandra/hasil_indexing/
```

---

### Tahap 6: Evaluasi Metrik Densitas & Konsistensi Graf

Jalankan script evaluasi komparatif (bisa dijalankan di HPC maupun langsung di laptop Anda):

```bash
# Evaluasi Lengkap 11 Parameter Mentor & Konsistensi Multi-Run (Run 1 vs Run 2 vs V1 vs Arjun):
$HOME/miniconda3/envs/minirag/bin/python evaluate_mentor_metrics.py

# Evaluasi Komparasi Densitas:
python3 evaluate_density.py
```

---

## 5. Tabel Hasil Komparasi Metrik Graf (Audit Mentor)

| Parameter Metrik | Chandra V2 (Run 1) | Chandra V2 (Run 2) | Chandra V1 (Awal) | Arjun (Baseline) |
| :--- | :---: | :---: | :---: | :---: |
| **Jumlah node / edge** | **595 / 817** | **619 / 850** | 218 / 428 | 6.876 / 1.451 |
| **Chunk teks** | **60 chunks** | **60 chunks** | 144 chunks | 53 / 53 |
| **Pasal yang diubah (~55)** | **47 dari ~55** | **47 dari ~55** | 49 dari ~55 | 50 dari ~55 |
| **26 definisi di Pasal 1** | **20 persis, 0 seb** | **20 persis, 0 seb** | 2 persis, 5 seb | 21 / 26 |
| **11 asas perikanan** | **10 / 11** | **10 / 11** | 0 / 11 | 10 / 11 |
| **SIUP / SIPI / SIKPI / ZEEI / PNBP** | **5 / 5** | **5 / 5** | 2 / 5 | 5 / 5 |
| **Nama node muncul di teks UU (%)** | **64.7%** | **64.8%** | 36.7% | 21.4% |
| **Node terisolasi** | **0 (19 komp)** | **0 (19 komp)** | 0 (4 komp) | 5.773 (84.0%) |
| **Kelompok nama hampir duplikat** | **10** | **13** | 50 | 765 |
| **Node sampah / placeholder** | **0 node** | **0 node** | 18 node | 18 node |

> [!NOTE]
> - Analisis mendalam mengenai faktor penyebab selisih (+24 node, +33 edge) antara Run 1 dan Run 2 terdokumentasi lengkap di [**`ANALISA_PERCOBAAN_1_DAN_2.md`**](ANALISA_PERCOBAAN_1_DAN_2.md).
> - Rincian teknis kode diff dan riwayat pembaruan antar-versi terdokumentasi lengkap di [**`LOG_VERSION.md`**](LOG_VERSION.md).

---

## 6. Catatan Teknis & Solusi Kendala (Troubleshooting)

1. **Error `412: The model requires a newer version of Ollama` saat pull model:**
   - _Penyebab:_ Port default `11434` di login node menjalankan server Ollama bawaan sistem lama (v0.11.10).
   - _Solusi:_ Gunakan skrip `bash pull_models.sh` yang secara otomatis menjalankan Ollama v0.40.13 di port terisolasi `11500`.

2. **Error `TypeError: 'type' object is not subscriptable` saat eksekusi Python:**
   - _Penyebab:_ Shell terminal menggunakan Python sistem CentOS 7 (Python 3.6).
   - _Solusi:_ Jalankan skrip menggunakan Python conda: `$HOME/miniconda3/envs/minirag/bin/python <script.py>` (skrip `extract_mineru_hpc.py` juga sudah dilengkapi fitur auto re-exec ke Python conda).

3. **Error `sbatch: error: QOSMaxMemoryPerJob`:**
   - _Penyebab:_ Menghilangkan parameter `--mem` membuat SLURM meminta seluruh RAM node fisik (1 TB+) dan ditolak oleh kuota QOS cluster Mahameru.
   - _Solusi:_ Selalu cantumkan `--mem=100G` (maksimal 120G sesuai kuota QOS) dan `--cpus-per-task=4` pada file `.sbatch`.

---

## 7. Mekanisme Distribusi Skrip via Base64 & GitHub Gist

Teknik ini digunakan untuk mendistribusikan atau memperbarui kumpulan skrip ke server HPC secara instan tanpa perlu SCP bertingkat dan tanpa meninggalkan file arsip sementara di server.

### A. Cara Membuat Bundle (Di Laptop / PC Lokal)

Bungkus seluruh folder proyek atau skrip tertentu menjadi arsip biner `tar.gz`, lalu ubah menjadi teks Base64:

```bash
# Di terminal laptop:
cd /home/chandreu/brin-2026/pengujian-komparasi-minirag
tar --exclude='*.log' --exclude='storage_*' -czf - . | base64 > pengujian_bundle.b64
```

### B. Upload ke GitHub Gist

1. Buka [gist.github.com](https://gist.github.com).
2. Buat file baru bernama `pengujian_bundle.b64`, lalu paste seluruh isi teksnya.
3. Klik **Create Public Gist**.
4. Klik tombol **"Raw"** untuk memperoleh tautan langsung teks tersebut:
   `https://gist.githubusercontent.com/<username>/<id_gist>/raw/pengujian_bundle.b64`

### C. Ekstrak Langsung di Server HPC (1 Baris Perintah)

Di terminal HPC (`mahoni01`), jalankan perintah pipeline streaming berikut:

```bash
cd ~/projek-legal-rag
curl -sL "https://gist.githubusercontent.com/awiuweoww/0e14fe0cebfb1c48e503e7115db5d4ad/raw/pengujian_bundle.b64?t=$(date +%s)" | base64 -d | tar -xzf -
```

**Penjelasan Alur Perintah (_Piping_):**

- `curl -sL "<URL>"`: Mengunduh teks dari Gist dan langsung mengalirkannya ke _stdout_ memori (tanpa menulis file sementara ke harddisk).
- `?t=$(date +%s)`: _Cache buster_ (stempel waktu unix) agar CDN GitHub selalu mengirim versi teranyar tanpa terkena cache.
- `| base64 -d`: Membaca stream teks dari _stdin_ dan memulihkannya kembali menjadi data biner `tar.gz`.
- `| tar -xzf -`: Menangkap data biner dari _stdin_ (`-`) dan langsung mengekstrak seluruh file ke folder saat itu tanpa meninggalkan file arsip sisa.

---

## 8. Panduan Sinkronisasi Langsung (WSL / Lokal ke HPC via `rsync`)

Metode sinkronisasi langsung menggunakan `rsync` melalui SSH ProxyJump adalah cara tercepat untuk mengirim folder atau file hasil modifikasi dari laptop/WSL lokal langsung ke server HPC tanpa perlu melakukan commit & push ke Git terlebih dahulu.

### A. Pola Perintah Universal

```bash
# Pola Umum:
rsync -avz <path_atau_nama_folder_lokal> <host_hpc>:<path_tujuan_di_hpc>/
```

### B. Kasus Penggunaan Universal

#### 1. Sinkronisasi Folder Pipeline Tertentu (Lokal ke HPC)
Untuk menyinkronkan satu folder pipeline lengkap (misalnya versi pengujian baru):
```bash
rsync -avz /home/chandreu/brin-2026/pengujian-komparasi-minirag/<nama_folder> mahoni01:~/projek-legal-rag/
```
*Contoh konkret:*
```bash
rsync -avz /home/chandreu/brin-2026/pengujian-komparasi-minirag/5_minirag_chandra_v2.1 mahoni01:~/projek-legal-rag/
```

#### 2. Sinkronisasi File Tertentu Saja (Lokal ke HPC)
Untuk memperbarui satu file skrip tertentu ke dalam subfolder HPC:
```bash
rsync -avz /home/chandreu/brin-2026/pengujian-komparasi-minirag/<path_subfolder>/<nama_file> mahoni01:~/projek-legal-rag/<path_subfolder>/
```
*Contoh konkret:*
```bash
rsync -avz /home/chandreu/brin-2026/pengujian-komparasi-minirag/5_minirag_chandra_v2.1/proses_indexing/universal_legal_chunker.py mahoni01:~/projek-legal-rag/5_minirag_chandra_v2.1/proses_indexing/
```

#### 3. Mengambil Hasil Indexing / Artefak (HPC ke Lokal)
Untuk menarik hasil graf (`storage_*`), log indexing, atau metrik evaluasi dari HPC kembali ke laptop lokal:
```bash
rsync -avz mahoni01:~/projek-legal-rag/<path_folder_di_hpc> <path_tujuan_lokal>/
```
*Contoh konkret:*
```bash
rsync -avz mahoni01:~/projek-legal-rag/5_minirag_chandra_v2.1/hasil_indexing/storage_gemma4_uu45 /home/chandreu/brin-2026/pengujian-komparasi-minirag/5_minirag_chandra_v2.1/hasil_indexing/
```

### C. Penjelasan Parameter `rsync`:
- `-a` (*archive*): Menyalin secara rekursif serta mempertahankan hak akses (*permissions*), kepemilikan, dan stempel waktu (*timestamps*).
- `-v` (*verbose*): Menampilkan detail file yang sedang ditransfer secara real-time.
- `-z` (*compress*): Mengompresi data saat transfer jaringan untuk menghemat bandwidth dan mempercepat transfer file besar (seperti chunks JSON dan GraphML).
- `--progress` *(opsional)*: Menampilkan progress bar dan kecepatan transfer per file.
- `--exclude='*.log'` *(opsional)*: Mengabaikan file log besar agar tidak membebani transfer.

# komparasi-minirag
