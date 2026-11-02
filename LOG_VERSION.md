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
+ Diberikan potongan teks peraturan perundang-undangan dan daftar jenis entitas, ekstrak entitas hukum yang TERTULIS di teks beserta hubungan antar-entitas tersebut, untuk membangun knowledge graph.
+ 
+ -Jenis Entitas-
+ Gunakan HANYA jenis berikut: [{entity_types}]
+ - dasar_hukum: nama peraturan (UU, PP, Peraturan Menteri, KUHP).
+ - struktur: pasal, ayat, huruf, angka, atau bagian penjelasan.
+ - pihak: orang, badan, jabatan, atau lembaga (Setiap Orang, Nelayan Kecil, Menteri, Pengawas Perikanan, Pengadilan Perikanan).
+ - kewajiban: perbuatan yang diwajibkan atau dilarang.
+ - hak: hak atau kewenangan suatu pihak.
+ - sanksi: pidana penjara, pidana denda, atau sanksi administratif beserta besarannya.
+ - konsep: istilah hukum, izin, dokumen, kapal, alat, atau wilayah (Surat Izin Penangkapan Ikan, Zona Ekonomi Eksklusif Indonesia).
```

---

#### 1. Judul Perbaikan
**Pembaruan Prompt Indexing Resmi BRIN v2.2.0 (Penamaan Kanonik & Penanganan 'Cukup Jelas')**

#### 2. Deskripsi Perbaikan
Memperbarui prompt ke Versi 2.2.0 resmi BRIN dengan aturan penamaan entitas kanonik:
1. Nama peraturan ditulis tanpa *"tentang..."* (misal: `UU Nomor 45 Tahun 2009`).
2. Pasal selalu disertai nama peraturannya (misal: `Pasal 93 ayat (1) UU Nomor 45 Tahun 2009`). Dilarang keras membuat entitas `Ayat 1` tanpa nomor pasal.
3. Istilah singkatan ditulis kepanjangannya (`Surat Izin Penangkapan Ikan`, bukan `SIPI`).
4. Angka sanksi ditulis persis sesuai teks (`Pidana penjara paling lama 6 tahun`).
5. Potongan penjelasan non-normatif (*"Cukup jelas."*) langsung menghasilkan stop delimiter `<|SELESAI|>` tanpa membuang kuota LLM.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/minirag/prompt_id_revisi.py`

#### 4. File Pembaruan
`prompt_id_revisi.py`

```diff
+ -Aturan Penamaan Entitas-
+ 1. Nama peraturan ditulis "UU Nomor 45 Tahun 2009", "UU Nomor 31 Tahun 2004", "PP Nomor X Tahun Y", "KUHP". Tanpa "tentang ...".
+ 2. Pasal SELALU disertai nama peraturannya: "Pasal 93 ayat (1) UU Nomor 45 Tahun 2009", "Pasal 7 ayat (2) huruf a UU Nomor 45 Tahun 2009". Ambil nama peraturan dari kepala teks; rujukan "sebagaimana dimaksud dalam Pasal X" tanpa nama peraturan lain berarti peraturan yang sama. Jangan pernah membuat entitas "Ayat 1", "Ayat (2)", atau "Huruf a" tanpa nomor pasal.
+ 3. Istilah yang punya singkatan ditulis dengan kepanjangannya: "Surat Izin Penangkapan Ikan" (bukan "SIPI"), "Zona Ekonomi Eksklusif Indonesia" (bukan "ZEEI"); sebutkan singkatannya di deskripsi.
+ 4. Gunakan istilah persis seperti di teks, bentuk dasar dan tunggal, Huruf Kapital Di Awal Kata. Satu konsep = satu nama di seluruh output.
+ 5. Sanksi ditulis dengan angka seperti di teks: "Pidana penjara paling lama 6 tahun", "Denda paling banyak Rp2.000.000.000,00".
+ 6. Jangan membuat entitas dari kata umum (ketentuan, hal, kegiatan, pelaksanaan) atau dari pengetahuan di luar teks.
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
**Parser Tanda Kurung Bersarang (*Balanced Tuple Parsing*) Anti-Truncation**

#### 2. Deskripsi Perbaikan
Memperbaiki kelemahan regex non-greedy `\((.*?)\)` yang sebelumnya terpotong pada tanda kurung pertama di dalam nama klausul (misal: `Pasal 18 ayat (1)` terpotong menjadi `Pasal 18 ayat (1` tanpa kurung tutup). Kelemahan ini sebelumnya menyebabkan 36 nama pasal rusak dan seluruh relasi yang memuat klausul tersebut gagal di-parse. Algoritma baru menghitung kedalaman tanda kurung (*depth counter*) dengan pengabaian string dalam tanda kutip sehingga kurung bersarang dan sanksi nominal tertangkap utuh 100%.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/index_gemma4_fast.py`

#### 4. File Pembaruan
`index_gemma4_fast.py`

```diff
- tuple_pattern = re.compile(
-     r'\(\s*\"?(entity|entitas|relationship|hubungan|relasi)\"?\s*(?:<\|>|\|)(.*?)\)',
-     re.IGNORECASE | re.DOTALL
- )
- matches = tuple_pattern.findall(text)
+ def extract_balanced_tuples(text: str) -> list[str]:
+     records, i, n = [], 0, len(text)
+     while i < n:
+         if text[i] == '(':
+             start, depth, i = i, 1, i + 1
+             in_quote, quote_char = False, None
+             while i < n and depth > 0:
+                 char = text[i]
+                 if char in ('"', "'") and (i == 0 or text[i-1] != '\\'):
+                     if not in_quote: in_quote, quote_char = True, char
+                     elif quote_char == char: in_quote, quote_char = False, None
+                 elif not in_quote:
+                     if char == '(': depth += 1
+                     elif char == ')': depth -= 1
+                 i += 1
+             if depth == 0:
+                 records.append(text[start+1:i-1].strip())
+         else:
+             i += 1
+     return records
```

---

#### 1. Judul Perbaikan
**Integrasi Penuh Modul Kanonikalisasi & Deduplikasi Graf (`normalisasi_entitas.py`)**

#### 2. Deskripsi Perbaikan
Mengintegrasikan modul resmi `normalisasi_entitas.py` langsung ke pipeline indexing V2. Modul ini menjalankan kamus `ALIASES` menyeluruh, penentuan nama kanonik tunggal (`canonical_name`), pendeteksian placeholder/sampah (`is_junk`), dan algoritma deduplikasi pasca-ekstraksi (`dedup_graph`). Simpul duplikat digabungkan, bobot relasi dijumlahkan secara kumulatif, dan deskripsi disatukan dengan pemisah `<SEP>`.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/normalisasi_entitas.py`  
`4_minirag_chandra_v2/proses_indexing/index_gemma4_fast.py`

#### 4. File Pembaruan
`normalisasi_entitas.py` (File Baru Ditambahkan)

```diff
+ """
+ Normalisasi & deduplikasi entitas untuk indexing MiniRAG (domain UU / perikanan).
+
+ Dua cara pakai:
+   1. SAAT INDEXING  : panggil canonical_name() di parser record entitas/relasi MiniRAG
+                       (minirag/operate.py: _handle_single_entity_extraction dan
+                        _handle_single_relationship_extraction), dan buang record bila
+                        is_junk() bernilai True.
+   2. SESUDAH INDEXING: python3 normalisasi_entitas.py input.graphml output.graphml [teks_sumber.md]
+                       -> menggabungkan node duplikat, menyambung ulang edge, membuang placeholder,
+                          dan (opsional) melaporkan node yang tidak ada di teks sumber.
+ """
+ import re
+ import sys
+ import unicodedata
+
+ import networkx as nx
+
+ SEP = "<SEP>"
+
+ # ---------------------------------------------------------------------------
+ # 1. Kamus alias: singkatan / variasi -> satu nama kanonik
+ #    Tambahkan sesuai dokumen. Kunci & nilai ditulis dalam bentuk ternormalisasi (huruf kecil).
+ # ---------------------------------------------------------------------------
+ ALIASES = {
+     "zeei": "zona ekonomi eksklusif indonesia",
+     "zee indonesia": "zona ekonomi eksklusif indonesia",
+     "zona ekonomi eksklusif indonesia (zeei)": "zona ekonomi eksklusif indonesia",
+     "zona ekonomi eksklusif indonesia (zee)": "zona ekonomi eksklusif indonesia",
+     "zona ekonomi eksklusif (zeei)": "zona ekonomi eksklusif indonesia",
+     "siup": "surat izin usaha perikanan",
+     "sipi": "surat izin penangkapan ikan",
+     "sikpi": "surat izin kapal pengangkut ikan",
+     "pnbp": "penerimaan negara bukan pajak",
+     "wpp-nri": "wilayah pengelolaan perikanan negara republik indonesia",
+     "wpp nri": "wilayah pengelolaan perikanan negara republik indonesia",
+     "jpu": "penuntut umum",
+     "jaksa penuntut umum": "penuntut umum",
+     "ppns perikanan": "penyidik pegawai negeri sipil perikanan",
+     "tni al": "tni angkatan laut",
+     "uu 45/2009": "uu nomor 45 tahun 2009",
+     "uu no 45 tahun 2009": "uu nomor 45 tahun 2009",
+     "undang-undang nomor 45 tahun 2009": "uu nomor 45 tahun 2009",
+     "undang-undang republik indonesia nomor 45 tahun 2009": "uu nomor 45 tahun 2009",
+     "uu nomor 31 tahun 2004 tentang perikanan": "uu nomor 31 tahun 2004",
+     "undang-undang nomor 31 tahun 2004": "uu nomor 31 tahun 2004",
+     "undang-undang nomor 31 tahun 2004 tentang perikanan": "uu nomor 31 tahun 2004",
+     "pembudi daya-ikan kecil": "pembudi daya ikan kecil",
+     "pembudidaya ikan kecil": "pembudi daya ikan kecil",
+     # ditemukan saat cek terhadap PDF UU 45/2009 dan dataset QA
+     "zee": "zona ekonomi eksklusif indonesia",
+     "zona ekonomi eksklusif (zee) indonesia": "zona ekonomi eksklusif indonesia",
+     "zona ekonomi eksklusif": "zona ekonomi eksklusif indonesia",
+     "spb": "surat persetujuan berlayar",
+     "psdkp": "pengawasan sumber daya kelautan dan perikanan",
+     "wppri": "wilayah pengelolaan perikanan negara republik indonesia",
+     "wppnri": "wilayah pengelolaan perikanan negara republik indonesia",
+     "wpp-ri": "wilayah pengelolaan perikanan negara republik indonesia",
+     "wilayah pengelolaan perikanan republik indonesia": "wilayah pengelolaan perikanan negara republik indonesia",
+     "vms": "sistem pemantauan kapal perikanan",
+     "vessel monitoring system": "sistem pemantauan kapal perikanan",
+     "vessel monitoring system/vms": "sistem pemantauan kapal perikanan",
+     "penyidik perwira tni al": "penyidik perwira tni angkatan laut",
+     "kuhpidana": "kuhp",
+     "kitab undang-undang hukum pidana": "kuhp",
+     "kitab undang-undang hukum acara pidana": "kuhap",
+ }
+
+ # Regulasi yang sedang di-index. Rujukan pasal ke regulasi ini ditulis tanpa nama regulasi
+ # ("pasal 93 ayat (2)"); rujukan ke regulasi lain tetap diberi nama regulasinya
+ # ("pasal 102 uu nomor 31 tahun 2004") agar Pasal 8 UU 31/2004 tidak tergabung dengan Pasal 8 KUHP.
+ INDEXED_REGULATION = "uu nomor 45 tahun 2009"
+
+ _REG = re.compile(
+     r"(?P<jenis>uu darurat|undang-undang darurat|uu|undang-undang|perpu|pp|peraturan pemerintah|"
+     r"permen ?kp|peraturan menteri kelautan dan perikanan|perpres|peraturan presiden)"
+     r"(?:\s+republik indonesia|\s+ri)?\s*(?:no\.?|nomor)?\s*(?P<no>\d+)"
+     r"(?:\s*(?:tahun|/)\s*(?P<th>\d{4}))?(?:\s+tentang\s+.*)?$"
+ )
+ _JENIS = {"undang-undang": "uu", "undang-undang darurat": "uu darurat", "peraturan pemerintah": "pp",
+           "peraturan menteri kelautan dan perikanan": "permen kp", "permenkp": "permen kp",
+           "peraturan presiden": "perpres"}
+
+
+ def canonical_regulation(s: str) -> str | None:
+     """'UU No. 45 Tahun 2009 tentang Perikanan' / 'Undang-Undang RI Nomor 45 Tahun 2009' /
+     'UU 45/2009' -> 'uu nomor 45 tahun 2009'. Mengembalikan None bila bukan nama regulasi."""
+     s = _basic(s) if s != s.lower() else s
+     s = ALIASES.get(s, s)
+     if s in ("kuhp", "kuhap"):
+         return s
+     m = _REG.fullmatch(s)
+     if not m:
+         return None
+     jenis = _JENIS.get(m["jenis"], m["jenis"])
+     return f"{jenis} nomor {int(m['no'])}" + (f" tahun {m['th']}" if m["th"] else "")
+
+
+ def split_references(raw: str) -> list[str]:
+     """Pecah rujukan majemuk menjadi rujukan tunggal yang sudah kanonik.
+     'Pasal 93 ayat (1) Jo Pasal 27 ayat (1) UU No. 45 Tahun 2009'
+       -> ['pasal 93 ayat (1)', 'pasal 27 ayat (1)']
+     Nama regulasi di akhir diwariskan ke semua bagian."""
+     s = _basic(raw)
+     s = re.sub(r"^(.+?)\s*/\s*(pasal .+)$", r"\2 \1", s)       # 'uu x / pasal y' -> 'pasal y uu x'
+     parts = [p for p in re.split(r"\s*(?:\||;|\bjo\.?|\bjuncto)\s*", s) if p]
+     reg = None
+     m = re.search(r"\s((?:uu|undang-undang|kuhp|kuhap|pp|perpu|perpres|permen|peraturan)\b.*)$", parts[-1])
+     if m:
+         reg = canonical_regulation(m.group(1))
+     out = []
+     for p in parts:
+         if reg and not re.search(r"\s(?:uu|undang-undang|kuhp|kuhap|pp|perpu|perpres|permen|peraturan)\b", p):
+             p = f"{p} {reg}"
+         out.append(canonical_name(p))
+     return out
+
+ # Nama yang pasti bukan entitas (bocoran template prompt, token rusak, kata umum).
+ PLACEHOLDERS = {
+     "name", "entity_name", "entity", "source", "target", "source_entity", "target_entity",
+     "description", "entity_description", "relationship_description", "desc",
+     "cukup jelas", "...", "-", "n/a", "tidak ada", "gt", "gross ton",
+ }
+
+ JUNK_PATTERN = re.compile(r"<[^>]*>|<\||\|>|unused\d+|intron|wajib diisi|\[x\]", re.I)
+
+
+ def _basic(s: str) -> str:
+     """Huruf kecil, unicode NFKC, kutip/spasi dirapikan, kurung yang terpotong ditutup."""
+     s = unicodedata.normalize("NFKC", s or "")
+     s = s.strip().strip('"').strip("'").strip("“”‘’").strip()
+     s = s.lower()
+     s = s.replace("–", "-").replace("—", "-")
+     s = re.sub(r"\s+", " ", s)
+     s = re.sub(r"\s*-\s*", "-", s)              # "daya - ikan" -> "daya-ikan"
+     s = s.rstrip(" .,;:")
+     # tutup kurung yang terpotong parser: "ayat (1" -> "ayat (1)"
+     if s.count("(") > s.count(")"):
+         s += ")" * (s.count("(") - s.count(")"))
+     return s
+
+
+ def _canonical_legal_ref(s: str) -> str:
+     """Seragamkan rujukan pasal/ayat/huruf/angka.
+     'Pasal 14, ayat 1' / 'pasal 14 ayat (1)' / 'pasal 14 (1)' -> 'pasal 14 ayat (1)'
+     'Pasal 25 A'      -> 'pasal 25a'
+     """
+     # Pisahkan nama regulasi di belakang rujukan pasal:
+     # "pasal 25 uu no. 45 tahun 2009 tentang perikanan" -> pasal 25 (regulasi yang di-index)
+     # "pasal 102 uu no. 31 tahun 2004"                  -> "pasal 102 uu nomor 31 tahun 2004"
+     reg = None
+     mreg = re.match(r"^(pasal .+?|ayat .+?)\s+((?:uu|undang-undang|kuhp|kuhap|pp|perpu|perpres|permen|peraturan)\b.*)$", s)
+     if mreg:
+         reg = canonical_regulation(mreg.group(2))
+         if reg:
+             s = mreg.group(1)
+     s = s.replace("ayat ayat", "ayat")
+     m = re.fullmatch(
+         r"pasal\s+(\d+)\s*([a-z])?\s*,?\s*(?:ayat\s*)?\(?\s*(\d+[a-z]?)?\s*\)?"
+         r"(?:\s*(?:huruf)\s*([a-z]))?(?:\s*angka\s*(\d+))?",
+         s,
+     )
+     suffix = f" {reg}" if reg and reg != INDEXED_REGULATION else ""
+     if not m:
+         m2 = re.fullmatch(r"ayat\s*\(?\s*(\d+[a-z]?)\s*\)?", s)
+         return (f"ayat ({m2.group(1)})" if m2 else s) + suffix
+     num, suf, ayat, huruf, angka = m.groups()
+     out = f"pasal {num}{suf or ''}"
+     if ayat:
+         out += f" ayat ({ayat})"
+     if huruf:
+         out += f" huruf {huruf}"
+     if angka:
+         out += f" angka {angka}"
+     return out + suffix
+
+
+ def canonical_name(raw: str) -> str:
+     """Satu-satunya fungsi yang boleh menentukan nama/ID node."""
+     s = _basic(raw)
+     reg = canonical_regulation(s)
+     if reg:
+         return reg
+     s = _canonical_legal_ref(s)
+     s = ALIASES.get(s, s)
+     # alias juga dicek setelah membuang singkatan dalam kurung: "surat izin usaha perikanan (siup)"
+     no_paren = re.sub(r"\s*\([^)]*\)$", "", s)
+     if no_paren != s and (no_paren in ALIASES.values() or no_paren in ALIASES):
+         s = ALIASES.get(no_paren, no_paren)
+     return s
+
+
+ def is_junk(raw: str) -> bool:
+     s = _basic(raw)
+     if not s or len(s) < 2 or JUNK_PATTERN.search(raw or ""):
+         return True
+     if s in PLACEHOLDERS or s.strip("<>") in PLACEHOLDERS:
+         return True
+     if re.fullmatch(r"[\d\W]+", s):          # hanya angka/tanda baca
+         return True
+     if len(s.split()) > 12:                  # kalimat, bukan nama entitas
+         return True
+     return False
+
+
+ def canonical_type(raw: str) -> str:
+     t = _basic(raw).replace(" ", "_")
+     return t or "unknown"
+
+
+ # ---------------------------------------------------------------------------
+ # 2. Penggabungan node duplikat pada graf yang sudah jadi
+ # ---------------------------------------------------------------------------
+ def _join(a: str, b: str) -> str:
+     parts = []
+     for x in (a or "").split(SEP) + (b or "").split(SEP):
+         x = x.strip()
+         if x and x not in parts:          # buang deskripsi/source_id yang identik
+             parts.append(x)
+     return SEP.join(parts)
+
+
+ def dedup_graph(G: nx.Graph) -> tuple[nx.Graph, dict]:
+     H = nx.Graph()
+     mapping, dropped = {}, []
+     for n, d in G.nodes(data=True):
+         name = d.get("entity_name", n)
+         if is_junk(name) or is_junk(n):
+             dropped.append(n)
+             continue
+         key = canonical_name(name)
+         mapping[n] = key
+         if key in H:
+             h = H.nodes[key]
+             for f in ("description", "source_id"):
+                 h[f] = _join(h.get(f, ""), d.get(f, ""))
+             h["_types"].append(canonical_type(d.get("entity_type", "")))
+         else:
+             attrs = {k: v for k, v in d.items() if k not in ("entity_name", "entity_type")}
+             H.add_node(key, **attrs, entity_name=key,
+                        _types=[canonical_type(d.get("entity_type", ""))])
+     # tipe = mayoritas dari node yang digabung
+     for k, d in H.nodes(data=True):
+         ts = d.pop("_types")
+         d["entity_type"] = max(set(ts), key=ts.count)
+     for u, v, d in G.edges(data=True):
+         if u not in mapping or v not in mapping:
+             continue
+         a, b = mapping[u], mapping[v]
+         if a == b:
+             continue                        # self-loop akibat penggabungan
+         if H.has_edge(a, b):
+             e = H.edges[a, b]
+             e["weight"] = float(e.get("weight", 1)) + float(d.get("weight", 1))
+             for f in ("description", "keywords", "source_id"):
+                 e[f] = _join(e.get(f, ""), d.get(f, ""))
+         else:
+             H.add_edge(a, b, **d)
+     return H, {"dropped_junk": dropped, "mapping": mapping}
+
+
+ def report(G: nx.Graph, label: str, source_text: str | None = None) -> None:
+     n, e = G.number_of_nodes(), G.number_of_edges()
+     iso = nx.number_of_isolates(G)
+     print(f"[{label}] node={n} edge={e} terisolasi={iso} ({iso / max(n, 1):.1%})")
+     if source_text:
+         flat = re.sub(r"[^a-z0-9]", "", _basic(source_text))
+         ungrounded = [x for x in G.nodes
+                       if re.sub(r"[^a-z0-9]", "", _basic(x)) not in flat]
+         print(f"[{label}] nama node yang tidak ada di teks sumber: {len(ungrounded)} "
+               f"({len(ungrounded) / max(n, 1):.1%})")
+
+
+ if __name__ == "__main__":
+     if len(sys.argv) < 3:
+         sys.exit(__doc__)
+     src = open(sys.argv[3], encoding="utf-8").read() if len(sys.argv) > 3 else None
+     G = nx.read_graphml(sys.argv[1])
+     report(G, "sebelum", src)
+     H, info = dedup_graph(G)
+     merged = len(info["mapping"]) - H.number_of_nodes()
+     print(f"dibuang (placeholder/sampah): {len(info['dropped_junk'])} | node digabung: {merged}")
+     report(H, "sesudah", src)
+     nx.write_graphml(H, sys.argv[2])
+
```

Dan integrasi di `index_gemma4_fast.py`:

```diff
+ from normalisasi_entitas import (
+     canonical_name,
+     is_junk,
+     canonical_type,
+     dedup_graph,
+     INDEXED_REGULATION,
+ )
...
+ graph, dedup_info = dedup_graph(graph)
+ print(f"Hasil Dedup: Dibuang={len(dedup_info['dropped_junk'])} | Digabung={len(dedup_info['mapping']) - graph.number_of_nodes()}")
```

---

#### 1. Judul Perbaikan
**Re-Chunking Semantik (*Boundary-Aware*) dengan Kepala Teks Regulasi Kanonik**

#### 2. Deskripsi Perbaikan
Mengganti pemotongan token buta (*naive slicing*) dengan pemotongan berbasis batas paragraf dan kalimat utuh (maksimal 490 token + 90 overlap) sehingga tidak ada definisi atau kata hukum yang terpotong di tengah kalimat. Di setiap awal chunk, disisipkan kepala teks regulasi (`UU Nomor 45 Tahun 2009 | Pasal X`) agar LLM mengenali induk peraturan dan konteks pasal secara konsisten.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/rechunk_512.py`  
`4_minirag_chandra_v2/proses_indexing/data/chunks_uu_45_2009.json`

#### 4. File Pembaruan
`rechunk_512.py` (File Baru Ditambahkan)

```diff
+ #!/usr/bin/env python3
+ """
+ Script Re-Chunking Standar MiniRAG (512 Token + Header Regulasi Kanonik)
+ Dokumen: UU Nomor 45 Tahun 2009 (Perikanan)
+ Sumber: output.md hasil ekstraksi otentik MinerU v4
+ Menyertakan kepala teks (UU Nomor 45 Tahun 2009 | Pasal X) sesuai arahan prompt kanonik mentor.
+ """
+ import os
+ import sys
+ import json
+ import re
+ import tiktoken
+
+ BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+ DOC_PATH = os.path.join(BASE_DIR, "1_dokumen_sumber", "UU_Nomor_45_Tahun_2009", "output.md")
+ OUT_DATA_PATH = os.path.join(BASE_DIR, "4_minirag_chandra_v2", "proses_indexing", "data", "chunks_uu_45_2009.json")
+ OUT_SOURCE_PATH = os.path.join(BASE_DIR, "1_dokumen_sumber", "chunks_uu_45_2009_512.json")
+
+ CHUNK_SIZE = 490
+ CHUNK_OVERLAP = 90
+
+ def clean_markdown_text(text: str) -> str:
+     text = re.sub(r"\r\n", "\n", text)
+     text = re.sub(r"\n\s*-\s*\d+\s*-\s*\n", "\n", text)
+     text = re.sub(r"www\.djpp\.depkumham\.go\.id[^\n]*", "", text, flags=re.IGNORECASE)
+     text = re.sub(r"Lembaran Negara Republik Indonesia[^\n]*", "", text, flags=re.IGNORECASE)
+     text = re.sub(r"\n{3,}", "\n\n", text)
+     return text.strip()
+
+ def detect_article_label(text: str, current_state: str) -> str:
+     """Melacak pasal aktif secara kontekstual."""
+     is_penjelasan = "penjelasan" in current_state.lower() or "# penjelasan" in text.lower()
+     m_pasal = re.search(r"(?:##\s*|Ketentuan\s+|Angka\s+\d+\s+)(Pasal\s+\d+[a-zA-Z]?)", text, re.IGNORECASE)
+    
+     if is_penjelasan:
+         if m_pasal:
+             return f"Penjelasan {m_pasal.group(1).title()}"
+         return current_state if "penjelasan" in current_state.lower() else "Penjelasan Umum"
+        
+     if "menimbang" in text.lower() or "mengingat" in text.lower() or "memutuskan" in text.lower():
+         if not m_pasal or "pasal 20" in text.lower():
+             return "Pembukaan & Konsiderans"
+            
+     if m_pasal:
+         return m_pasal.group(1).title()
+        
+     return current_state
+
+ def chunk_with_legal_headers(text: str, chunk_size: int = 490, overlap: int = 90):
+     enc = tiktoken.get_encoding("cl100k_base")
+     paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
+    
+     chunks = []
+     curr_paras = []
+     curr_tokens = 0
+     current_pasal = "Pembukaan"
+    
+     for p in paragraphs:
+         current_pasal = detect_article_label(p, current_pasal)
+         p_tokens = len(enc.encode(p))
+        
+         # Jika satu paragraf sangat panjang (> 420 token), pecah per kalimat
+         if p_tokens > 420:
+             sentences = re.split(r"(?<=[.;])\s+", p)
+             for s in sentences:
+                 s_tok = len(enc.encode(s))
+                 if curr_tokens + s_tok > chunk_size and curr_paras:
+                     raw_chunk = "\n\n".join(curr_paras)
+                     header = f"UU Nomor 45 Tahun 2009 | {current_pasal}\n\n"
+                     full_content = header + raw_chunk
+                     chunks.append({
+                         "chunk_id": f"chunk-{len(chunks)+1:04d}",
+                         "tokens": len(enc.encode(full_content)),
+                         "pasal_ref": current_pasal,
+                         "content": full_content
+                     })
+                     overlap_paras = []
+                     overlap_toks = 0
+                     for op in reversed(curr_paras):
+                         ot = len(enc.encode(op))
+                         if overlap_toks + ot <= overlap:
+                             overlap_paras.insert(0, op)
+                             overlap_toks += ot
+                         else:
+                             break
+                     curr_paras = list(overlap_paras)
+                     curr_tokens = overlap_toks
+                 curr_paras.append(s)
+                 curr_tokens += s_tok
+         else:
+             if curr_tokens + p_tokens > chunk_size and curr_paras:
+                 raw_chunk = "\n\n".join(curr_paras)
+                 header = f"UU Nomor 45 Tahun 2009 | {current_pasal}\n\n"
+                 full_content = header + raw_chunk
+                 chunks.append({
+                     "chunk_id": f"chunk-{len(chunks)+1:04d}",
+                     "tokens": len(enc.encode(full_content)),
+                     "pasal_ref": current_pasal,
+                     "content": full_content
+                 })
+                 overlap_paras = []
+                 overlap_toks = 0
+                 for op in reversed(curr_paras):
+                     ot = len(enc.encode(op))
+                     if overlap_toks + ot <= overlap:
+                         overlap_paras.insert(0, op)
+                         overlap_toks += ot
+                     else:
+                         break
+                 curr_paras = list(overlap_paras)
+                 curr_tokens = overlap_toks
+             curr_paras.append(p)
+             curr_tokens += p_tokens
+            
+     if curr_paras:
+         raw_chunk = "\n\n".join(curr_paras)
+         header = f"UU Nomor 45 Tahun 2009 | {current_pasal}\n\n"
+         full_content = header + raw_chunk
+         chunks.append({
+             "chunk_id": f"chunk-{len(chunks)+1:04d}",
+             "tokens": len(enc.encode(full_content)),
+             "pasal_ref": current_pasal,
+             "content": full_content
+         })
+        
+     return chunks
+
+ def main():
+     if not os.path.exists(DOC_PATH):
+         print(f"Error: Dokumen {DOC_PATH} tidak ditemukan!")
+         sys.exit(1)
+        
+     print(f"Membaca naskah resmi MinerU v4: {DOC_PATH} ...")
+     with open(DOC_PATH, "r", encoding="utf-8") as f:
+         raw_text = f.read()
+        
+     cleaned_text = clean_markdown_text(raw_text)
+     chunks = chunk_with_legal_headers(cleaned_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
+    
+     print(f"Berhasil menghasilkan: {len(chunks)} chunk (dengan kepala teks regulasi kanonik)")
+    
+     os.makedirs(os.path.dirname(OUT_DATA_PATH), exist_ok=True)
+     with open(OUT_SOURCE_PATH, "w", encoding="utf-8") as f:
+         json.dump(chunks, f, ensure_ascii=False, indent=2)
+     print(f"Tersimpan di: {OUT_SOURCE_PATH}")
+    
+     with open(OUT_DATA_PATH, "w", encoding="utf-8") as f:
+         json.dump(chunks, f, ensure_ascii=False, indent=2)
+     print(f"Tersimpan di: {OUT_DATA_PATH}")
+
+     token_lens = [c["tokens"] for c in chunks]
+     word_lens = [len(c["content"].split()) for c in chunks]
+     print("=" * 60)
+     print(f"Statistik Chunking Boundary-Aware MiniRAG 512:")
+     print(f"Total Chunks       : {len(chunks)}")
+     print(f"Rata-rata Token    : {sum(token_lens)/len(token_lens):.1f} token (Min: {min(token_lens)}, Max: {max(token_lens)})")
+     print(f"Rata-rata Kata     : {sum(word_lens)/len(word_lens):.1f} kata (Min: {min(word_lens)}, Max: {max(word_lens)})")
+     print("=" * 60)
+
+ if __name__ == "__main__":
+     main()
```

---

#### 1. Judul Perbaikan
**Penautan Hierarkis Pasal (*Hierarchical Article Anchoring*) Pencegah Graf Bintang Datar**

#### 2. Deskripsi Perbaikan
Menggantikan strategi penautan darurat sebelumnya yang menghubungkan seluruh entitas terisolasi secara langsung ke root dokumen (membentuk flat star graph). Pada logika baru, entitas tanpa relasi ditautkan terlebih dahulu ke node Pasal asalnya (`Pasal 27`), dan node Pasal tersebut dihubungkan ke root dokumen (`UU Nomor 45 Tahun 2009`). Pendekatan ini mempertahankan struktur pohon regulasi otentik dan memudahkan penelusuran multi-hop RAG.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/index_gemma4_fast.py`

#### 4. File Pembaruan
`index_gemma4_fast.py`

```diff
- for iso_node in isolated:
-     graph.add_edge(doc_node_id, iso_node, weight=7.0)
+ for iso_node in isolated:
+     target_parent = doc_node_id
+     pref = node_to_pasal.get(iso_node, "")
+     m_pasal = re.search(r"Pasal\s+\d+[a-zA-Z]?", pref, re.IGNORECASE)
+     if m_pasal:
+         pasal_name = canonical_name(m_pasal.group(0))
+         if pasal_name not in graph:
+             graph.add_node(pasal_name, entity_name=pasal_name, entity_type="struktur")
+         if not graph.has_edge(doc_node_id, pasal_name):
+             graph.add_edge(doc_node_id, pasal_name, weight=10.0)
+         target_parent = pasal_name
+     graph.add_edge(target_parent, iso_node, weight=7.0)
```

---

#### 1. Judul Perbaikan
**Alokasi Port Dinamis SLURM Anti-Collision (`PORT = 11600 + (JOB_ID % 1000)`)**

#### 2. Deskripsi Perbaikan
Menghindari konflik port `bind: address already in use` di node komputasi bersama (shared A100 node) akibat proses background Ollama yang masih menempati port 11500 dari sesi sebelumnya. Menggunakan port dinamis berbasis Job ID SLURM dan menangkap PID proses secara eksklusif untuk di-terminate saat job selesai.

#### 3. Path File
`4_minirag_chandra_v2/proses_indexing/run_indexing.sbatch`

#### 4. File Pembaruan
`run_indexing.sbatch`

```diff
- export OLLAMA_HOST=0.0.0.0:11500
+ PORT=$((11600 + ($SLURM_JOB_ID % 1000)))
+ export OLLAMA_HOST=0.0.0.0:$PORT
...
+ kill $OLLAMA_PID || true
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
