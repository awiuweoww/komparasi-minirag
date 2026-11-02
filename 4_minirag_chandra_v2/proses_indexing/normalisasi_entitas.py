"""
Normalisasi & deduplikasi entitas untuk indexing MiniRAG (domain UU / perikanan).

Dua cara pakai:
  1. SAAT INDEXING  : panggil canonical_name() di parser record entitas/relasi MiniRAG
                      (minirag/operate.py: _handle_single_entity_extraction dan
                       _handle_single_relationship_extraction), dan buang record bila
                       is_junk() bernilai True.
  2. SESUDAH INDEXING: python3 normalisasi_entitas.py input.graphml output.graphml [teks_sumber.md]
                      -> menggabungkan node duplikat, menyambung ulang edge, membuang placeholder,
                         dan (opsional) melaporkan node yang tidak ada di teks sumber.
"""
import re
import sys
import unicodedata

import networkx as nx

SEP = "<SEP>"

# ---------------------------------------------------------------------------
# 1. Kamus alias: singkatan / variasi -> satu nama kanonik
#    Tambahkan sesuai dokumen. Kunci & nilai ditulis dalam bentuk ternormalisasi (huruf kecil).
# ---------------------------------------------------------------------------
ALIASES = {
    "zeei": "zona ekonomi eksklusif indonesia",
    "zee indonesia": "zona ekonomi eksklusif indonesia",
    "zona ekonomi eksklusif indonesia (zeei)": "zona ekonomi eksklusif indonesia",
    "zona ekonomi eksklusif indonesia (zee)": "zona ekonomi eksklusif indonesia",
    "zona ekonomi eksklusif (zeei)": "zona ekonomi eksklusif indonesia",
    "siup": "surat izin usaha perikanan",
    "sipi": "surat izin penangkapan ikan",
    "sikpi": "surat izin kapal pengangkut ikan",
    "pnbp": "penerimaan negara bukan pajak",
    "wpp-nri": "wilayah pengelolaan perikanan negara republik indonesia",
    "wpp nri": "wilayah pengelolaan perikanan negara republik indonesia",
    "jpu": "penuntut umum",
    "jaksa penuntut umum": "penuntut umum",
    "ppns perikanan": "penyidik pegawai negeri sipil perikanan",
    "tni al": "tni angkatan laut",
    "uu 45/2009": "uu nomor 45 tahun 2009",
    "uu no 45 tahun 2009": "uu nomor 45 tahun 2009",
    "undang-undang nomor 45 tahun 2009": "uu nomor 45 tahun 2009",
    "undang-undang republik indonesia nomor 45 tahun 2009": "uu nomor 45 tahun 2009",
    "uu nomor 31 tahun 2004 tentang perikanan": "uu nomor 31 tahun 2004",
    "undang-undang nomor 31 tahun 2004": "uu nomor 31 tahun 2004",
    "undang-undang nomor 31 tahun 2004 tentang perikanan": "uu nomor 31 tahun 2004",
    "pembudi daya-ikan kecil": "pembudi daya ikan kecil",
    "pembudidaya ikan kecil": "pembudi daya ikan kecil",
    # ditemukan saat cek terhadap PDF UU 45/2009 dan dataset QA
    "zee": "zona ekonomi eksklusif indonesia",
    "zona ekonomi eksklusif (zee) indonesia": "zona ekonomi eksklusif indonesia",
    "zona ekonomi eksklusif": "zona ekonomi eksklusif indonesia",
    "spb": "surat persetujuan berlayar",
    "psdkp": "pengawasan sumber daya kelautan dan perikanan",
    "wppri": "wilayah pengelolaan perikanan negara republik indonesia",
    "wppnri": "wilayah pengelolaan perikanan negara republik indonesia",
    "wpp-ri": "wilayah pengelolaan perikanan negara republik indonesia",
    "wilayah pengelolaan perikanan republik indonesia": "wilayah pengelolaan perikanan negara republik indonesia",
    "vms": "sistem pemantauan kapal perikanan",
    "vessel monitoring system": "sistem pemantauan kapal perikanan",
    "vessel monitoring system/vms": "sistem pemantauan kapal perikanan",
    "penyidik perwira tni al": "penyidik perwira tni angkatan laut",
    "kuhpidana": "kuhp",
    "kitab undang-undang hukum pidana": "kuhp",
    "kitab undang-undang hukum acara pidana": "kuhap",
}

# Regulasi yang sedang di-index. Rujukan pasal ke regulasi ini ditulis tanpa nama regulasi
# ("pasal 93 ayat (2)"); rujukan ke regulasi lain tetap diberi nama regulasinya
# ("pasal 102 uu nomor 31 tahun 2004") agar Pasal 8 UU 31/2004 tidak tergabung dengan Pasal 8 KUHP.
INDEXED_REGULATION = "uu nomor 45 tahun 2009"

_REG = re.compile(
    r"(?P<jenis>uu darurat|undang-undang darurat|uu|undang-undang|perpu|pp|peraturan pemerintah|"
    r"permen ?kp|peraturan menteri kelautan dan perikanan|perpres|peraturan presiden)"
    r"(?:\s+republik indonesia|\s+ri)?\s*(?:no\.?|nomor)?\s*(?P<no>\d+)"
    r"(?:\s*(?:tahun|/)\s*(?P<th>\d{4}))?(?:\s+tentang\s+.*)?$"
)
_JENIS = {"undang-undang": "uu", "undang-undang darurat": "uu darurat", "peraturan pemerintah": "pp",
          "peraturan menteri kelautan dan perikanan": "permen kp", "permenkp": "permen kp",
          "peraturan presiden": "perpres"}


def canonical_regulation(s: str) -> str | None:
    """'UU No. 45 Tahun 2009 tentang Perikanan' / 'Undang-Undang RI Nomor 45 Tahun 2009' /
    'UU 45/2009' -> 'uu nomor 45 tahun 2009'. Mengembalikan None bila bukan nama regulasi."""
    s = _basic(s) if s != s.lower() else s
    s = ALIASES.get(s, s)
    if s in ("kuhp", "kuhap"):
        return s
    m = _REG.fullmatch(s)
    if not m:
        return None
    jenis = _JENIS.get(m["jenis"], m["jenis"])
    return f"{jenis} nomor {int(m['no'])}" + (f" tahun {m['th']}" if m["th"] else "")


def split_references(raw: str) -> list[str]:
    """Pecah rujukan majemuk menjadi rujukan tunggal yang sudah kanonik.
    'Pasal 93 ayat (1) Jo Pasal 27 ayat (1) UU No. 45 Tahun 2009'
      -> ['pasal 93 ayat (1)', 'pasal 27 ayat (1)']
    Nama regulasi di akhir diwariskan ke semua bagian."""
    s = _basic(raw)
    s = re.sub(r"^(.+?)\s*/\s*(pasal .+)$", r"\2 \1", s)       # 'uu x / pasal y' -> 'pasal y uu x'
    parts = [p for p in re.split(r"\s*(?:\||;|\bjo\.?|\bjuncto)\s*", s) if p]
    reg = None
    m = re.search(r"\s((?:uu|undang-undang|kuhp|kuhap|pp|perpu|perpres|permen|peraturan)\b.*)$", parts[-1])
    if m:
        reg = canonical_regulation(m.group(1))
    out = []
    for p in parts:
        if reg and not re.search(r"\s(?:uu|undang-undang|kuhp|kuhap|pp|perpu|perpres|permen|peraturan)\b", p):
            p = f"{p} {reg}"
        out.append(canonical_name(p))
    return out

# Nama yang pasti bukan entitas (bocoran template prompt, token rusak, kata umum).
PLACEHOLDERS = {
    "name", "entity_name", "entity", "source", "target", "source_entity", "target_entity",
    "description", "entity_description", "relationship_description", "desc",
    "cukup jelas", "...", "-", "n/a", "tidak ada", "gt", "gross ton",
}

JUNK_PATTERN = re.compile(r"<[^>]*>|<\||\|>|unused\d+|intron|wajib diisi|\[x\]", re.I)


def _basic(s: str) -> str:
    """Huruf kecil, unicode NFKC, kutip/spasi dirapikan, kurung yang terpotong ditutup."""
    s = unicodedata.normalize("NFKC", s or "")
    s = s.strip().strip('"').strip("'").strip("“”‘’").strip()
    s = s.lower()
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*-\s*", "-", s)              # "daya - ikan" -> "daya-ikan"
    s = s.rstrip(" .,;:")
    # tutup kurung yang terpotong parser: "ayat (1" -> "ayat (1)"
    if s.count("(") > s.count(")"):
        s += ")" * (s.count("(") - s.count(")"))
    return s


def _canonical_legal_ref(s: str) -> str:
    """Seragamkan rujukan pasal/ayat/huruf/angka.
    'Pasal 14, ayat 1' / 'pasal 14 ayat (1)' / 'pasal 14 (1)' -> 'pasal 14 ayat (1)'
    'Pasal 25 A'      -> 'pasal 25a'
    """
    # Pisahkan nama regulasi di belakang rujukan pasal:
    # "pasal 25 uu no. 45 tahun 2009 tentang perikanan" -> pasal 25 (regulasi yang di-index)
    # "pasal 102 uu no. 31 tahun 2004"                  -> "pasal 102 uu nomor 31 tahun 2004"
    reg = None
    mreg = re.match(r"^(pasal .+?|ayat .+?)\s+((?:uu|undang-undang|kuhp|kuhap|pp|perpu|perpres|permen|peraturan)\b.*)$", s)
    if mreg:
        reg = canonical_regulation(mreg.group(2))
        if reg:
            s = mreg.group(1)
    s = s.replace("ayat ayat", "ayat")
    m = re.fullmatch(
        r"pasal\s+(\d+)\s*([a-z])?\s*,?\s*(?:ayat\s*)?\(?\s*(\d+[a-z]?)?\s*\)?"
        r"(?:\s*(?:huruf)\s*([a-z]))?(?:\s*angka\s*(\d+))?",
        s,
    )
    suffix = f" {reg}" if reg and reg != INDEXED_REGULATION else ""
    if not m:
        m2 = re.fullmatch(r"ayat\s*\(?\s*(\d+[a-z]?)\s*\)?", s)
        return (f"ayat ({m2.group(1)})" if m2 else s) + suffix
    num, suf, ayat, huruf, angka = m.groups()
    out = f"pasal {num}{suf or ''}"
    if ayat:
        out += f" ayat ({ayat})"
    if huruf:
        out += f" huruf {huruf}"
    if angka:
        out += f" angka {angka}"
    return out + suffix


def canonical_name(raw: str) -> str:
    """Satu-satunya fungsi yang boleh menentukan nama/ID node."""
    s = _basic(raw)
    reg = canonical_regulation(s)
    if reg:
        return reg
    s = _canonical_legal_ref(s)
    s = ALIASES.get(s, s)
    # alias juga dicek setelah membuang singkatan dalam kurung: "surat izin usaha perikanan (siup)"
    no_paren = re.sub(r"\s*\([^)]*\)$", "", s)
    if no_paren != s and (no_paren in ALIASES.values() or no_paren in ALIASES):
        s = ALIASES.get(no_paren, no_paren)
    return s


def is_junk(raw: str) -> bool:
    s = _basic(raw)
    if not s or len(s) < 2 or JUNK_PATTERN.search(raw or ""):
        return True
    if s in PLACEHOLDERS or s.strip("<>") in PLACEHOLDERS:
        return True
    if re.fullmatch(r"[\d\W]+", s):          # hanya angka/tanda baca
        return True
    if len(s.split()) > 12:                  # kalimat, bukan nama entitas
        return True
    return False


def canonical_type(raw: str) -> str:
    t = _basic(raw).replace(" ", "_")
    return t or "unknown"


# ---------------------------------------------------------------------------
# 2. Penggabungan node duplikat pada graf yang sudah jadi
# ---------------------------------------------------------------------------
def _join(a: str, b: str) -> str:
    parts = []
    for x in (a or "").split(SEP) + (b or "").split(SEP):
        x = x.strip()
        if x and x not in parts:          # buang deskripsi/source_id yang identik
            parts.append(x)
    return SEP.join(parts)


def dedup_graph(G: nx.Graph) -> tuple[nx.Graph, dict]:
    H = nx.Graph()
    mapping, dropped = {}, []
    for n, d in G.nodes(data=True):
        name = d.get("entity_name", n)
        if is_junk(name) or is_junk(n):
            dropped.append(n)
            continue
        key = canonical_name(name)
        mapping[n] = key
        if key in H:
            h = H.nodes[key]
            for f in ("description", "source_id"):
                h[f] = _join(h.get(f, ""), d.get(f, ""))
            h["_types"].append(canonical_type(d.get("entity_type", "")))
        else:
            attrs = {k: v for k, v in d.items() if k not in ("entity_name", "entity_type")}
            H.add_node(key, **attrs, entity_name=key,
                       _types=[canonical_type(d.get("entity_type", ""))])
    # tipe = mayoritas dari node yang digabung
    for k, d in H.nodes(data=True):
        ts = d.pop("_types")
        d["entity_type"] = max(set(ts), key=ts.count)
    for u, v, d in G.edges(data=True):
        if u not in mapping or v not in mapping:
            continue
        a, b = mapping[u], mapping[v]
        if a == b:
            continue                        # self-loop akibat penggabungan
        if H.has_edge(a, b):
            e = H.edges[a, b]
            e["weight"] = float(e.get("weight", 1)) + float(d.get("weight", 1))
            for f in ("description", "keywords", "source_id"):
                e[f] = _join(e.get(f, ""), d.get(f, ""))
        else:
            H.add_edge(a, b, **d)
    return H, {"dropped_junk": dropped, "mapping": mapping}


def report(G: nx.Graph, label: str, source_text: str | None = None) -> None:
    n, e = G.number_of_nodes(), G.number_of_edges()
    iso = nx.number_of_isolates(G)
    print(f"[{label}] node={n} edge={e} terisolasi={iso} ({iso / max(n, 1):.1%})")
    if source_text:
        flat = re.sub(r"[^a-z0-9]", "", _basic(source_text))
        ungrounded = [x for x in G.nodes
                      if re.sub(r"[^a-z0-9]", "", _basic(x)) not in flat]
        print(f"[{label}] nama node yang tidak ada di teks sumber: {len(ungrounded)} "
              f"({len(ungrounded) / max(n, 1):.1%})")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src = open(sys.argv[3], encoding="utf-8").read() if len(sys.argv) > 3 else None
    G = nx.read_graphml(sys.argv[1])
    report(G, "sebelum", src)
    H, info = dedup_graph(G)
    merged = len(info["mapping"]) - H.number_of_nodes()
    print(f"dibuang (placeholder/sampah): {len(info['dropped_junk'])} | node digabung: {merged}")
    report(H, "sesudah", src)
    nx.write_graphml(H, sys.argv[2])

