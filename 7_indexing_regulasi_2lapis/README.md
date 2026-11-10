# 7_INDEXING_REGULASI_2LAPIS (SinkronAIR MiniRAG V3)

Dokumentasi Arsitektur Monorepo Indexing Multi-Regulasi 2 Lapis Hirarki (Standar BRIN / ELI-FRBR).  
Setiap tahapan dipisahkan secara tegas antara folder **`proses/`** (skrip, konfigurasi, input data) dan folder **`hasil/`** (output artefak, graf, log) agar asal-usul setiap file hasil dapat dilacak dengan presisi 100%.

> 🚀 **Panduan Praktis HPC:** Untuk langkah-langkah dan sintaks CLI saat menjalankan di klaster HPC, buka:
> **[PANDUAN_EKSEKUSI_HPC.md](file:///home/chandreu/brin-2026/pengujian-komparasi-minirag/7_indexing_regulasi_2lapis/PANDUAN_EKSEKUSI_HPC.md)**
>
> 📋 **Rencana dan Tracking Task:** Buka **[PLAN_INDEXING_2_LAPIS_HIRARKI.md](file:///home/chandreu/brin-2026/pengujian-komparasi-minirag/7_indexing_regulasi_2lapis/PLAN_INDEXING_2_LAPIS_HIRARKI.md)**

---

## 1. Peta Struktur Monorepo (Proses vs Hasil)

```text
7_indexing_regulasi_2lapis/
│
├── PANDUAN_EKSEKUSI_HPC.md                  # Panduan lengkap sintaks CLI & SLURM di HPC
├── PLAN_INDEXING_2_LAPIS_HIRARKI.md         # Papan rencana tracking task langkah demi langkah
│
├── 1_parsing_metadata_jdih/
│   ├── proses/
│   │   ├── data_mentah_bpk/                 # Teks salinan browser dari halaman Details BPK
│   │   └── parsing_link_jdih.py             # Script parser HTML/teks halaman BPK
│   └── hasil/
│       └── metadata_regulasi.json           # File metadata resmi 6 UU hasil parsing
│
├── 2_graf_lapisan1_manual/
│   ├── 1_versi_asli_mentor/                 # Jalur Baseline: 100% Kode Asli Mentor Tanpa Modifikasi
│   │   ├── proses/
│   │   │   ├── skema_relasi_regulasi.yaml   # Ontologi acuan v1.2
│   │   │   ├── graf_relasi_uu_asli.py       # Builder Lapisan 1 Asli
│   │   │   └── teks_sumber_perubahan/
│   │   │       └── UU_Nomor_45_Tahun_2009.md
│   │   └── hasil/
│   │       ├── lapisan1.graphml             # Graf Lapisan 1 NetworkX
│   │       ├── lapisan1.json                # JSON silsilah Lapisan 1
│   │       ├── jangkar.json                 # Peta label versi <-> ID
│   │       └── laporan_validasi_lapisan1.md # Laporan audit validasi Lapisan 1
│   │
│   └── 2_versi_disempurnakan/               # Jalur Tuning: Staging Area Saat Menghadapi Case Problem
│       ├── proses/
│       │   ├── skema_relasi_regulasi.yaml
│       │   ├── graf_relasi_uu_tuned.py      # Builder Lapisan 1 Siap-Tuning
│       │   └── teks_sumber_perubahan/
│       │       └── UU_Nomor_45_Tahun_2009.md
│       └── hasil/
│
├── 3_persiapan_chunk_berjangkar/
│   ├── proses/
│   │   ├── kepala_chunk.py                  # Script injeksi header jangkar VersiPasal
│   │   └── data_input/
│   │       └── chunks_uu_45_2009.json       # 60 chunk teks bersih MinerU
│   └── hasil/
│       └── chunks_hasil_uu45_berjangkar.json # Chunk berjangkar siap diekstrak LLM
│
├── 4_indexing_lapisan2_minirag/
│   ├── proses/
│   │   ├── prompt_indexing_layer2_uu-V3.py  # Prompt resmi V3 (ekstraksi norma berjangkar)
│   │   ├── render_minirag_skema.py          # Compiler prompt otomatis dari skema YAML
│   │   ├── index_layer2_hpc.py              # Engine indexing async Gemma 4:12B + BGE-M3
│   │   └── run_indexing_hpc.sbatch          # Script job SLURM klaster HPC A100
│   └── hasil/
│       └── storage_lapisan2_gemma4/         # Output graf norma mentah Lapisan 2 (GraphML, KV)
│
├── 5_penautan_graf_gabungan/
│   ├── proses/
│   │   ├── skema_relasi_regulasi.yaml
│   │   └── tautkan_layer_hirarki.py         # Script linker perajut Lapisan 1 + Lapisan 2
│   └── hasil/
│       ├── gabungan.graphml                 # Knowledge Graph 2 Lapis Akhir (Final Graph)
│       ├── entitas_baru_embed.json          # Node Lapisan 1 untuk di-embed ke vektor DB
│       └── laporan_penautan.md              # Metrik keberhasilan penautan & zero isolates
│
└── 6_evaluasi_dan_laporan/
    ├── proses/
    │   └── evaluate_mentor_metrics.py       # Script audit 11 parameter mentor
    └── hasil/
        └── LAPORAN_KOMPARASI_V3.md          # Laporan evaluasi komprehensif
```

---

## 2. Hubungan Sebab-Akibat (*Traceability Matrix*)

| Tahapan | Folder `proses/` (Dijalankan dengan apa) | Folder `hasil/` (Menghasilkan apa) | Digunakan oleh Tahap Selanjutnya |
| :--- | :--- | :--- | :--- |
| **Tahap 1** | `parsing_link_jdih.py` + teks web BPK | `metadata_regulasi.json` | Dibaca oleh Tahap 2 (`graf_relasi_uu.py`) |
| **Tahap 2** | `graf_relasi_uu.py` + `metadata_regulasi.json` + `output.md` | `lapisan1.json` & `jangkar.json` | Dibaca oleh Tahap 3 (`kepala_chunk.py`) & Tahap 5 |
| **Tahap 3** | `kepala_chunk.py` + `chunks_uu_45_2009.json` + `jangkar.json` | `chunks_hasil_uu45_berjangkar.json` | Dibaca oleh Tahap 4 (MiniRAG indexing) |
| **Tahap 4** | `prompt_indexing_layer2_uu-V3.py` + LLM Gemma 4:12B | `storage_lapisan2_gemma4/` | Dibaca oleh Tahap 5 (`tautkan_layer_hirarki.py`) |
| **Tahap 5** | `tautkan_layer_hirarki.py` + Lapisan 1 + Lapisan 2 | `gabungan.graphml` | Dianalisis oleh Tahap 6 (Evaluasi & QA Benchmark) |
| **Tahap 6** | `evaluate_mentor_metrics.py` terhadap `gabungan.graphml` | `LAPORAN_KOMPARASI_V3.md` | Laporan akhir pertanggungjawaban ke mentor |

