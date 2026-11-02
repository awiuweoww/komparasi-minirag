# LOG VERSION - PENGUJIAN KOMPARASI MINIRAG

Dokumen ini mencatat riwayat pembaruan, perubahan arsitektur, parameter, prompt, serta perbandingan hasil kuantitatif antar-versi Knowledge Graph MiniRAG (Gemma 4:12B + BGE-M3) untuk korpus perundang-undangan Indonesia.

---

======================================
perbaikan V2 
======================================

### Rincian Perubahan V2

#### 1. Judul Perbaikan
**Standar Taksonomi Yuridis Nasional (UU No. 12/2011) & Mandat Konektivitas Graf**

#### 2. Deskripsi Perbaikan
Mengganti prompt ad-hoc yang sebelumnya berorientasi spesifik perikanan menjadi standar pembentukan perundang-undangan nasional yang berlaku universal untuk UU apa pun. Mewajibkan model mengekstrak 6 pilar yuridis (Ketentuan Umum, Asas/Tujuan, Subjek-Norma Kewajiban/Larangan, Instrumen Perizinan, Aparat/Kelembagaan, dan Sanksi). Memberikan instruksi eksplisit agar setiap entitas wajib memiliki minimal satu relasi substantif dengan target 15–30 relasi per chunk untuk mencegah graf ompong.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/minirag/prompt_id_revisi.py`

#### 4. File Pembaruan
`prompt_id_revisi.py`

```diff
- PROMPTS["entity_extraction"] = """-Tujuan-
- Diberikan dokumen teks hukum yang relevan dan daftar jenis entitas, identifikasi semua entitas...
- PENTING UNTUK KELENGKAPAN SUBSTANSI:
- - Ekstrak seluruh definisi hukum substantif secara lengkap, terutama jika teks memuat Pasal 1...
- - Ekstrak seluruh asas pengelolaan perikanan...
- - Ekstrak instrumen kepatuhan dan perizinan...
+ PROMPTS["entity_extraction"] = """-Tujuan-
+ Diberikan teks naskah perundang-undangan Republik Indonesia dan daftar jenis entitas, lakukan ekstraksi pengetahuan hukum (Legal Knowledge Graph) yang komprehensif, presisi tinggi, dan terhubung penuh.
+ 
+ -Standar Taksonomi Perundang-undangan Indonesia (Baku & Berlaku Universal)-
+ 1. Ketentuan Umum & Definisi Substantif: Ekstrak seluruh batasan pengertian, istilah yuridis pokok (terutama Pasal 1), dan objek pengaturan.
+ 2. Asas & Tujuan: Ekstrak seluruh prinsip dasar, asas pelaksanaan, landasan filosofis, dan tujuan pengaturan perundang-undangan.
+ 3. Subjek Hukum & Norma Perilaku: Ekstrak subjek hukum (Setiap Orang, Korporasi, Pemerintah, Menteri, Pejabat Berwenang), norma imperatif ("wajib" -> kewajiban), norma larangan negatif ("dilarang" -> larangan), serta hak/perlindungan hukum.
+ 4. Instrumen Perizinan & Kepatuhan: Ekstrak seluruh jenis izin, persetujuan, sertifikasi, dokumen legalitas, tanda bukti, serta pungutan resmi negara/retribusi.
+ 5. Aparat Penegak Hukum & Kelembagaan: Ekstrak aparat pengawas, penyidik, kepolisian, kejaksaan/penuntut umum, hakim, dan lembaga peradilan berwenang.
+ 6. Sanksi Yuridis: Ekstrak sanksi pidana (pidana penjara/kurungan, besaran nominal denda) dan sanksi administratif (pencabutan izin, pembekuan, pembongkaran).
+ 
+ 2. Identifikasi SEMUA pasangan entitas yang berhubungan (Prioritas Konektivitas Graf Penuh):
+ PENTING: Pastikan setiap entitas yang diekstrak pada langkah 1 terhubung minimal ke satu entitas lain!
+ Petakan relasi substantif lengkap:
+ - Subjek Hukum <-> Kewajiban / Larangan / Hak
+ - Pelanggaran Norma <-> Sanksi Pidana / Administratif
+ - Subjek / Kegiatan <-> Instrumen Izin
+ - Aparat / Pejabat <-> Wewenang Pengawasan / Penyidikan
+ - Hierarki Struktur Regulasi (Undang-Undang memuat Pasal, Pasal memuat Ayat)
+ - Konsep Induk <-> Definisi / Asas
+ Targetkan 15 sampai 30 pasangan relasi substantif per teks.
```

---

#### 1. Judul Perbaikan
**Ekspansi Kuota Token Prediksi Output (`NUM_PREDICT = 3072`)**

#### 2. Deskripsi Perbaikan
Pada V1, batas token output dibatasi `1024` token. Ketika satu chunk memuat 20–29 entitas beserta deskripsinya, kuota 1024 token habis sebelum model sempat menulis bagian `("relationship"<|...)`, menyebabkan beberapa chunk menghasilkan relasi 0. Pada V2, batas dinaikkan menjadi `3072` token sehingga seluruh relasi tercetak lengkap tanpa terpotong.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/index_gemma4_fast.py`  
`4_minirag_chandra_v2/proses_indexing/run_indexing.sbatch`

#### 4. File Pembaruan
`index_gemma4_fast.py` & `run_indexing.sbatch`

```diff
# index_gemma4_fast.py
- NUM_PREDICT = int(os.getenv("NUM_PREDICT", "1024"))
+ NUM_PREDICT = int(os.getenv("NUM_PREDICT", "3072"))

# run_indexing.sbatch
- export NUM_PREDICT=1024
+ export NUM_PREDICT=3072
```

---

#### 1. Judul Perbaikan
**Sanitasi Entitas Universal & Normalisasi Dinamis `Nama Lengkap (SINGKATAN)`**

#### 2. Deskripsi Perbaikan
Menambahkan fungsi pembersih teks universal `clean_entity_text` untuk menghapus sisa tag HTML/token delimiter rusak, kurung menggantung, dan tanda hubung kata ganda (contoh: `pembudi daya-ikan` -> `pembudidaya ikan`). Mengimplementasikan deteksi otomatis pola regex `Nama Lengkap (Singkatan)` sehingga entitas resmi dan singkatannya otomatis terkanonikalisasi ke satu node yang sama.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/index_gemma4_fast.py`

#### 4. File Pembaruan
`index_gemma4_fast.py`

```diff
+ def clean_entity_text(text: str) -> str:
+     """Membersihkan format string entitas dari sisa delimiter, quote, atau tag rusak."""
+     if not text:
+         return ""
+     t = re.sub(r"<\|.*?\|>", "", text)
+     t = re.sub(r'["\'`]+', "", t)
+     t = re.sub(r"\s+", " ", t).strip()
+     t = re.sub(r"pembudi\s*daya-ikan", "pembudidaya ikan", t, flags=re.I)
+     t = re.sub(r"pembudi\s*daya\s*ikan", "pembudidaya ikan", t, flags=re.I)
+     if t.endswith("(") or t.endswith("["):
+         t = t[:-1].strip()
+     return t

  def norm_name(name: str) -> str:
-     n = re.sub(r"\s+", " ", (name or "").strip().strip('"').strip("'")).lower()
+     n = clean_entity_text(name).lower()
+     m = re.match(r"^(.*?)\s*\(([a-z0-9_-]+)\)$", n)
+     if m:
+         full_part, abbr = m.group(1).strip(), m.group(2).strip()
+         return SYNONYM_MAP.get(abbr, SYNONYM_MAP.get(full_part, abbr))
      return SYNONYM_MAP.get(n, n)
```

---

#### 1. Judul Perbaikan
**Re-Chunking Berbasis Token Baku (512 Token + 100 Token Overlap)**

#### 2. Deskripsi Perbaikan
Mengganti skema pemotongan teks berbasis pasal MinerU (144 chunk yang menghasilkan label semu seperti "Pasal 25 P" dan "Pasal 25 C") menjadi skema standar MiniRAG dengan panjang 512 token dan overlapping 100 token menggunakan tokenizer resmi. Menghasilkan 58 chunk yang menjaga keutuhan 26 definisi Pasal 1 dan 11 asas perikanan.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/rechunk_512.py`  
`4_minirag_chandra_v2/proses_indexing/data/chunks_uu_45_2009.json`

#### 4. File Pembaruan
`rechunk_512.py` (Script Baru)

```python
# Inti logika rechunk 512 token
enc = tiktoken.get_encoding("cl100k_base")
tokens = enc.encode(text)
chunks = []
start = 0
while start < len(tokens):
    end = min(start + 512, len(tokens))
    chunk_tokens = tokens[start:end]
    chunk_text = enc.decode(chunk_tokens)
    chunks.append({
        "chunk_id": f"chunk-{len(chunks)+1:04d}",
        "content": chunk_text
    })
    start += (512 - 100) # 100 token overlap
```

---

#### 1. Judul Perbaikan
**Pembeda Cerdas Evaluator Duplikat Yuridis (Distinct Provisions vs Redundant Duplicates)**

#### 2. Deskripsi Perbaikan
Memperbaiki algoritma fuzzy matching di skrip evaluasi. Sebelumnya, teks hukum dengan kemiripan string tinggi (seperti `Pasal 15 ayat (1)` vs `Pasal 15 ayat (2)` [94% mirip], atau `WNA` vs `WNI` [85% mirip]) salah diklasifikasikan sebagai duplikat. Logika baru memisahkan antara perbedaan substansi hukum sejati (beda pasal, ayat, denda, atau status subjek) dengan duplikat redundan (typo ejaan atau tanda strip).

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/evaluate_mentor_metrics.py`

#### 4. File Pembaruan
`evaluate_mentor_metrics.py`

```diff
+ def is_legal_distinction(n1: str, n2: str) -> bool:
+     nums1 = re.findall(r"\d+", n1)
+     nums2 = re.findall(r"\d+", n2)
+     if nums1 != nums2:
+         return True # Beda nomor pasal/ayat/denda/tahun = BUKAN duplikat
+     codes1 = re.findall(r"\d+[a-z]", n1)
+     codes2 = re.findall(r"\d+[a-z]", n2)
+     if codes1 != codes2:
+         return True # Beda pasal sisipan (100a vs 100b) = BUKAN duplikat
+     opposites = [("asing", "indonesia"), ("penangkap", "pengangkut"), ("sipi", "sikpi")]
+     for w1, w2 in opposites:
+         if (w1 in n1 and w2 in n2) or (w2 in n1 and w1 in n2):
+             return True # Status hukum berlawanan = BUKAN duplikat
+     return False
```

---

======================================
perbaikan V3 (Template / Rencana Mendatang)
======================================
1. judul perbaikan
2. deskripsi perbaikan
3. path file
4. file pembaruan

```diff
+ code ....
- code ...
```

