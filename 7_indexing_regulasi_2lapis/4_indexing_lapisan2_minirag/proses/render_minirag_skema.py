#!/usr/bin/env python3
"""
Render prompt indexing MiniRAG multi-regulasi dari skema_relasi_regulasi.yaml (v1.2) + metadata_regulasi.json.

Yang diambil dari skema/metadata (tidak diketik di prompt):
  - jenis entitas dan panduannya             <- layer2.entity_types
  - daftar relasi, arah (dari -> ke), kelompok <- layer2.relasi_norma, layer2.kelompok_relasi
  - format kepala chunk                      <- layer2.kepala_chunk
  - daftar peraturan korpus yang DILARANG ditulis LLM <- metadata ruang_lingkup (label + alias)
  - label versi untuk kata kunci kueri        <- metadata (urut tanggal berlaku; Perpu -> UU penetapan)
Contoh: 8 contoh berjangkar render_lapisan2.py (teks asli UU 31/2004, UU 45/2009, UU 11/2020), divalidasi
terhadap skema: kata kunci terdaftar, arah dari/ke sah, struktur = jangkar kepala, tanpa nama peraturan korpus.

Keluaran: out/prompt_id_revisi_lapisan2_skema.py  (pengganti lightrag/minirag prompt.py)
"""
import json
import re
import sys

import yaml

sys.path.insert(0, "/home/claude/onto")
SK = yaml.safe_load(open("skema_relasi_regulasi.yaml", encoding="utf-8"))
META = json.load(open("metadata_regulasi.json", encoding="utf-8"))
L2 = SK["layer2"]
REL = L2["relasi_norma"]
TYPES = list(L2["entity_types"])

# ------------------------------------------------------------------ contoh (diambil dari render_lapisan2.py)
src = open("render_lapisan2.py", encoding="utf-8").read().split("# ============================================================================ MiniRAG")[0]
ns = {}
exec(src, ns)
EX = ns["EX"]

# ------------------------------------------------------------------ data dari metadata
per = {p["id"]: p for p in META["peraturan"]}
lingkup = META["ruang_lingkup"]["peraturan"]
korpus = []
for pid in lingkup:
    p = per[pid]
    korpus += [p["label"]] + [a for a in p.get("alias", []) if a not in korpus]
    if p.get("induk_alias"):
        korpus.append(p["induk_alias"])
korpus = list(dict.fromkeys(korpus))
KORPUS_UTAMA = [per[p]["label"] for p in lingkup if per[p].get("jenis_perubahan") not in ("pelaksana",)]
penetap = {p["id"]: (p.get("relasi", {}).get("ditetapkan_dengan") or [None])[0] for p in META["peraturan"]}
versi_sumber = sorted((per[p]["tanggal_berlaku"], p) for p in lingkup
                      if per[p].get("jenis_perubahan") in ("induk", "perubahan", "omnibus") and per[p].get("tanggal_berlaku"))
LABEL_VERSI = []
for tgl, p in versi_sumber:
    lab = per[penetap[p]]["label"] if penetap.get(p) else per[p]["label"]
    if lab not in LABEL_VERSI:
        LABEL_VERSI.append((lab, tgl))
LABEL_VERSI = list(dict.fromkeys(LABEL_VERSI))
induk_alias = per[META["ruang_lingkup"]["induk"]]["induk_alias"]

# ------------------------------------------------------------------ potongan prompt dari skema
def fold(t):
    return " ".join(str(t).split())


TYPE_GUIDE = "\n".join(f"- {k}: {fold(v)}" for k, v in L2["entity_types"].items())


def arah(x):
    return "/".join(x) if isinstance(x, list) else x


RELS = []
for g, judul in L2["kelompok_relasi"].items():
    kws = [f'"{kw}" ({arah(v["dari"])} -> {arah(v["ke"])})' for kw, v in REL.items() if v["kelompok"] == g]
    RELS.append(f"{g}. {judul}: " + "; ".join(kws) + ";")
RELS = "\n".join(RELS)

GOAL = ("Graf terdiri atas dua lapisan. Lapisan 1 (peraturan, pasal, versi pasal, perubahan, pencabutan, penetapan Perpu, "
        "putusan uji materi, penyesuaian pidana, rujukan antar-pasal) sudah dibangun sistem dari metadata JDIH BPK dan teks. "
        "Tugas Anda hanya Lapisan 2: norma di dalam teks (kewajiban, larangan, kewenangan, tindak pidana, ancaman pidana, "
        "pihak, konsep) beserta hubungannya, yang ditautkan ke versi pasal pada kepala teks.")

FMT = L2['kepala_chunk']['format'].replace("{", "<").replace("}", ">")
ANCHOR_RULES = f"""1. Kepala teks berbentuk "{FMT}". Setiap label setelah "jangkar:" adalah node VERSI pasal yang sudah ada di Lapisan 1, misalnya "{L2['kepala_chunk']['contoh'].split('jangkar: ')[1]}". Tulis node itu sebagai entitas jenis "struktur" dengan nama PERSIS seperti di kepala teks, tanpa akhiran "(lanjutan)". Jangan membuat entitas struktur lain.
2. Semua norma dihubungkan ke jangkar tempat norma itu tertulis. Bila kepala memuat beberapa jangkar, pilih menurut judul pasal dan nomor ayat di teks; teks di awal chunk berlanjut dari jangkar pertama. Jangkar berawalan "Penjelasan" dipakai untuk teks penjelasan, dengan kata kunci "penjelasan pasal".
3. Label versi menyebut peraturan yang MENETAPKAN rumusan itu. Rumusan dari {per['perpu/2022/2']['label']} berlabel "versi {per['uu/2023/6']['label']}" karena Perpu itu ditetapkan menjadi undang-undang; ikuti label di kepala apa adanya.
4. JANGAN menulis entitas untuk peraturan korpus ({'; '.join(KORPUS_UTAMA)}; juga sebutan "{induk_alias}" dan "UU Cipta Kerja"), node pasal tanpa versi, maupun relasi perubahan, penyisipan, penghapusan, pencabutan, penetapan, atau rujukan "sebagaimana dimaksud dalam/pada ...". Semua itu disediakan Lapisan 1. Peraturan LAIN yang menjadi tujuan delegasi atau dasar sanksi ("diatur dengan Peraturan Pemerintah", "sebagaimana dimaksud dalam KUHP") ditulis sebagai "dasar_hukum".
5. Tulis angka pidana PERSIS seperti teks. Jangan menyesuaikannya dengan KUHP atau undang-undang penyesuaian pidana; penyesuaian itu dicatat Lapisan 1.
6. Bila jangkar berbunyi "(dihapus)" atau teks tidak memuat norma (misalnya hanya "Cukup jelas."), tulis penanda selesai saja."""

NORM_RULES = re.sub(r"^(\d+)\. ", lambda m: f"{int(m.group(1)) + 2}. ", ns["NORM_RULES"], flags=re.M)  # 5-10 -> 7-12

# ------------------------------------------------------------------ validasi contoh terhadap skema
def norm(s):
    return re.sub(r"\s+\(lanjutan\)$", "", s.strip())


errors = []
for i, ex in enumerate(EX, 1):
    head = ex["text"].split("\n", 1)[0]
    jang = [norm(x) for x in head.split("jangkar:", 1)[1].split(";")] if "jangkar:" in head else []
    T = {r[1]: r[2] for r in ex["records"] if r[0] == "e"}
    for r in ex["records"]:
        if r[0] == "e":
            if r[2] not in TYPES:
                errors.append(f"contoh {i}: jenis {r[2]} tidak ada di skema")
            if r[2] == "struktur" and r[1] not in jang:
                errors.append(f"contoh {i}: struktur '{r[1]}' bukan jangkar kepala")
            if r[1] in korpus:
                errors.append(f"contoh {i}: entitas peraturan korpus '{r[1]}'")
        else:
            kw = r[4]
            if kw not in REL:
                errors.append(f"contoh {i}: kata kunci '{kw}' tidak ada di skema")
                continue
            d, k = REL[kw]["dari"], REL[kw]["ke"]
            d, k = d if isinstance(d, list) else [d], k if isinstance(k, list) else [k]
            if T.get(r[1]) not in d or T.get(r[2]) not in k:
                errors.append(f"contoh {i}: '{kw}' {T.get(r[1])}->{T.get(r[2])} melanggar arah {d}->{k}")
if errors:
    print("\n".join(errors))
    sys.exit("contoh tidak sesuai skema")

# ------------------------------------------------------------------ MiniRAG entity_extraction
TD, RD, CD = "{tuple_delimiter}", "{record_delimiter}", "{completion_delimiter}"


def m_example(i, ex):
    rows = [f'("entity"{TD}"{r[1]}"{TD}"{r[2]}"{TD}"{r[3]}")' if r[0] == "e"
            else f'("relationship"{TD}"{r[1]}"{TD}"{r[2]}"{TD}"{r[3]}"{TD}"{r[4]}"{TD}{r[5]})' for r in ex["records"]]
    body = CD if not rows else (RD + "\n").join(rows) + RD + "\n" + f'("content_keywords"{TD}"{ex["kw"]}"){CD}'
    return (f"Contoh {i}:\n\nEntity_types: [{', '.join(TYPES)}]\nText:\n{ex['text']}\n################\n"
            f"Output:\n{body}\n#############################")


ENT = f'''PROMPTS["entity_extraction"] = """-Tujuan-
Diberikan potongan teks peraturan perundang-undangan dan daftar jenis entitas, ekstrak entitas hukum yang TERTULIS di teks beserta hubungan antar-entitas tersebut, untuk knowledge graph multi-regulasi. {GOAL}

-Aturan Output (WAJIB)-
- Mulai LANGSUNG dengan record pertama. Jangan menulis analisis, penalaran, ringkasan input, judul, markdown, atau bahasa Inggris.
- Gunakan Bahasa Indonesia. Ikuti format record persis seperti contoh.
- Jangan pernah menyalin kata dari template seperti <entity_name>, <source_entity>, <description>, entity_name, source, atau target sebagai isi record.

-Jenis Entitas-
Gunakan HANYA jenis berikut: [{{entity_types}}]
{TYPE_GUIDE}

-Aturan Jangkar (Lapisan 1)-
{ANCHOR_RULES.replace("penanda selesai", "{completion_delimiter}")}

-Aturan Penamaan Norma-
{NORM_RULES}

-Langkah-
1. Untuk setiap entitas, tulis:
("entity"{{tuple_delimiter}}<entity_name>{{tuple_delimiter}}<entity_type>{{tuple_delimiter}}<entity_description>)
entity_description: 1-2 kalimat berdasarkan teks; masukkan singkatan resmi, besaran sanksi, dan jangka waktu bila ada.

2. Untuk setiap pasangan entitas yang jelas berhubungan di teks, tulis:
("relationship"{{tuple_delimiter}}<source_entity>{{tuple_delimiter}}<target_entity>{{tuple_delimiter}}<relationship_description>{{tuple_delimiter}}<relationship_keywords>{{tuple_delimiter}}<relationship_strength>)
- source_entity dan target_entity harus sama persis dengan nama pada langkah 1. relationship_strength: bilangan 1-10.
- relationship_keywords: SATU kata kunci dari daftar di bawah, dengan arah sumber -> target sesuai jenis entitas dalam kurung. Jangan memakai kata kunci lain.
- SETIAP entitas wajib muncul di minimal satu relasi. Entitas yang tidak dapat dihubungkan jangan ditulis.
- Daftar kata kunci relasi (sumber -> target):
{RELS}

3. Tulis per ayat: entitas ayat tersebut, lalu langsung relasinya, baru ayat berikutnya. Paling banyak 40 entitas; untuk teks definisi (Pasal 1) ekstrak setiap istilah yang didefinisikan.

4. Tulis kata kunci tingkat tinggi teks:
("content_keywords"{{tuple_delimiter}}<high_level_keywords>)

5. Pisahkan setiap record dengan {{record_delimiter}} dan akhiri dengan {{completion_delimiter}}

######################
-Contoh-
######################
''' + "\n".join(m_example(i, e) for i, e in enumerate(EX, 1)) + '''
-Data Sebenarnya-
######################
Entity_types: {entity_types}
Text:
{input_text}
######################
Output:
"""
'''

# ------------------------------------------------------------------ prompt kueri sadar versi
VERSI_TXT = "; ".join(f'"versi {lab}" (berlaku sejak {tgl})' for lab, tgl in LABEL_VERSI)
QUERY = f'''PROMPTS["minirag_query2kwd"] = """---Peran---
Anda adalah asisten ahli hukum perikanan yang bertugas mengekstrak kata kunci pencarian dari pertanyaan pengguna untuk knowledge graph multi-regulasi.

---Instruksi---
- Output kata kunci dalam format JSON dengan dua kunci:
  - "answer_type_keywords": jenis jawaban yang diharapkan, diambil dari pool.
  - "entities_from_query": entitas atau detail spesifik dari pertanyaan pengguna.
- Masukkan ke "entities_from_query" apa adanya: nomor pasal dan ayat, nama peraturan, tahun atau tanggal kejadian, pihak, kapal, izin, wilayah, dan perbuatan.
- Pasal UU Perikanan disimpan per versi. Bila pertanyaan menunjuk rumusan tertentu (menyebut peraturan pengubah, "sebelum/sesudah perubahan", "setelah UU Cipta Kerja", atau tanggal kejadian), tambahkan label versi yang sesuai ke "entities_from_query": {VERSI_TXT}. Bila tidak menunjuk versi, jangan menambah label versi.
- Jangan menambahkan pasal atau peraturan yang tidak disebut atau tersirat jelas dalam pertanyaan.

-Data Sebenarnya-
######################
Query: {{query}}
Answer type pool: {{TYPE_POOL}}
######################
Output:
"""

PROMPTS["rag_response"] = """---Konteks---

{{context_data}}

---Peran---

Anda adalah SinkronAIR, asisten hukum maritim BRIN yang menjawab pertanyaan berbasis skenario kasus HANYA menggunakan informasi dari konteks pasal regulasi yang diberikan.

---Instruksi---

1. Jawab dalam Bahasa Indonesia yang baku, tegas, dan berbobot yuridis.
2. Dasarkan jawaban HANYA pada konteks yang diberikan. Jika informasi tidak ditemukan dalam konteks, nyatakan secara jujur bahwa informasi tidak tersedia -- JANGAN mengarang pasal.
3. Konteks memuat versi pasal berlabel "<pasal> {induk_alias} versi <peraturan>" beserta masa berlakunya. Pilih versi yang berlaku pada tanggal kejadian dalam skenario; bila tidak ada tanggal, pakai versi yang masih berlaku (tanpa tanggal akhir) dan sebutkan bila rumusan sebelumnya berbeda.
4. Jangan menggabungkan unsur atau angka sanksi dari dua versi berbeda. Bila pertanyaan membandingkan versi, sajikan per versi.
5. Sebut dasar hukum lengkap dengan pola "Pasal X ayat (n) UU Nomor 31 Tahun 2004 tentang Perikanan sebagaimana telah diubah dengan <peraturan yang menetapkan versi itu>".
6. Bila konteks menyebut versi berstatus perlu dicek, pencabutan tanpa rumusan pengganti, penyesuaian pidana oleh undang-undang penyesuaian pidana, atau tafsir putusan Mahkamah Konstitusi, sampaikan hal itu sebagai catatan; jangan menganggap angka dalam konteks pasti berlaku.
7. Jawab langsung pada substansi tanpa mengulang pertanyaan.

{{response_type}}
"""
'''

# ------------------------------------------------------------------ rakit dari prompt v5.0 (bagian lain tetap)
base = open("out/prompt_id_revisi_lapisan2.py", encoding="utf-8").read()
a, b = base.index('PROMPTS["entity_extraction"] = """'), base.index('PROMPTS["summarize_entity_descriptions"]')
base = base[:a] + ENT + "\n" + base[b:]
a, b = base.index('PROMPTS["minirag_query2kwd"] = """'), base.index('PROMPTS["keywords_extraction"]')
base = base[:a] + QUERY + "\n" + base[b:]
base = re.sub(r"Version     : 5\.0\.0-lapisan2.*?\n(?=\"\"\")", f'''Version     : 5.1.0-skema
Created     : 08-11-2026
Description : Prompt indexing MiniRAG multi-regulasi berjangkar (Lapisan 2), DIRENDER dari skema_relasi_regulasi.yaml
              v{SK["version"]} dan metadata_regulasi.json (JDIH BPK, diambil {META["diambil_pada"]}). Korpus: {"; ".join(KORPUS_UTAMA)}.
              Peraturan, pasal, versi pasal, perubahan, pencabutan, penetapan Perpu, uji materi, dan rujukan
              dibangun kode (Lapisan 1, bangun_lapisan1.py); kepala chunk dari kepala_chunk.py; hasil ekstraksi
              ditautkan dengan tautkan_lapisan2.py. Jangan mengedit prompt ini langsung: ubah skema lalu render ulang.
              Jalankan dengan num_ctx >= 16384 dan think=false.
''', base, count=1, flags=re.S)
base = base.replace('    "dasar_hukum",\n    "struktur",\n    "konsep",\n    "sanksi",\n    "pihak",\n    "kewajiban",\n    "hak",\n    "tindak_pidana",\n',
                    "".join(f'    "{t}",\n' for t in TYPES))
open("out/prompt_id_revisi_lapisan2_skema.py", "w", encoding="utf-8").write(base)

# ------------------------------------------------------------------ cek akhir
ns2 = {}
exec(base, ns2)
P = ns2["PROMPTS"]
for key in ("entity_extraction", "minirag_query2kwd", "rag_response"):
    left = set(re.findall(r"\{(\w+)\}", P[key]))
    print(f"{key}: placeholder {sorted(left)}")
P["entity_extraction"].format(tuple_delimiter="<|>", record_delimiter="##", completion_delimiter="<|SELESAI|>",
                              entity_types=",".join(TYPES), input_text="X")
P["minirag_query2kwd"].format(query="q", TYPE_POOL="p")
P["rag_response"].format(context_data="c", response_type="r")
n = len(P["entity_extraction"].format(tuple_delimiter="<|>", record_delimiter="##", completion_delimiter="<|SELESAI|>",
                                     entity_types=",".join(TYPES), input_text=""))
print(f"entity_extraction setelah format: {n} karakter (~{n / 3.2:.0f} token, perkiraan), {len(EX)} contoh lolos validasi skema, "
      f"{len(REL)} kata kunci relasi, korpus dilarang: {len(korpus)} nama")
print("label versi kueri:", [l for l, _ in LABEL_VERSI])
