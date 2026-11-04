#!/usr/bin/env python3
"""
Script Audit Substantif & Metrik Komparatif Komprehensif MiniRAG
Mengimplementasikan 11 Parameter Evaluasi Mentor:
Gemma 4 (Chandra) vs Gemma 3 (Arjun)

namun ada beberapa kriteria yang belum benar-benar dipastikan sesuai atau benar standar penilaiannya,
seperti :
1. Daftar Ground Truth 26 Definisi di Pasal 1
2. Daftar Ground Truth 11 Asas Pengelolaan Perikanan (Pasal 2)
3. Nomor-nomor Pasal Nyata UU 45/2009 (~55 pasal revisi/sisipan)

"""
import os
import sys
import re
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
import difflib
import networkx as nx

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEXT_PATH = os.path.join(BASE_DIR, "1_dokumen_sumber", "UU_Nomor_45_Tahun_2009", "output.md")

DIR_ARJUN = os.path.join(BASE_DIR, "2_minirag_mjundewana", "UU Nomor 45 Tahun 2009")
DIR_CHANDRA_V1 = os.path.join(BASE_DIR, "3_minirag_chandra", "hasil_indexing", "storage_gemma4_uu45")

# Chandra V2 Percobaan 1
DIR_CHANDRA_V2_RUN1 = os.path.join(BASE_DIR, "4_minirag_chandra_v2", "hasil_indexing", "percobaan_ke1", "storage_gemma4_uu45")
if not os.path.exists(DIR_CHANDRA_V2_RUN1):
    DIR_CHANDRA_V2_RUN1 = os.path.join(BASE_DIR, "4_minirag_chandra_v2", "hasil_indexing", "storage_gemma4_uu45")

# Chandra V2 Percobaan 2
DIR_CHANDRA_V2_RUN2 = os.path.join(BASE_DIR, "4_minirag_chandra_v2", "hasil_indexing", "percobaan_ke2", "storage_gemma4_uu45")
if not os.path.exists(DIR_CHANDRA_V2_RUN2):
    DIR_CHANDRA_V2_RUN2 = os.path.join(BASE_DIR, "4_minirag_chandra_v2", "hasil_indexing", "storage_gemma4_uu45_run2")

# Chandra V2.1 (Strict MinerU JSON AST Mode)
DIR_CHANDRA_V2_1 = os.path.join(BASE_DIR, "5_minirag_chandra_v2.1", "hasil_indexing", "storage_gemma4_uu45")
DIR_CHANDRA = DIR_CHANDRA_V2_RUN1

# 1. Daftar Ground Truth 26 Definisi di Pasal 1
DEFINISI_PASAL_1 = [
    "perikanan",
    "sumber daya ikan",
    "lingkungan sumber daya ikan",
    "ikan",
    "penangkapan ikan",
    "pembudidayaan ikan",
    "pengelolaan perikanan",
    "konservasi sumber daya ikan",
    "kapal perikanan",
    "kapal penangkap ikan",
    "kapal pengangkut ikan",
    "kapal latih perikanan",
    "kapal penelitian",
    "kapal pendukung",
    "surat izin usaha perikanan",
    "surat izin penangkapan ikan",
    "surat izin kapal pengangkut ikan",
    "nelayan",
    "nelayan kecil",
    "pembudidaya-ikan",
    "pembudidaya-ikan kecil",
    "setiap orang",
    "korporasi",
    "persetujuan pengadaan kapal perikanan",
    "pelabuhan perikanan",
    "laut lepas"
]

# 2. Daftar Ground Truth 11 Asas Pengelolaan Perikanan (Pasal 2)
ASAS_PERIKANAN = [
    "kemanfaatan",
    "keadilan",
    "kebersamaan",
    "kemitraan",
    "kemandirian",
    "pemerataan",
    "keterpaduan",
    "keterbukaan",
    "efisiensi",
    "kelestarian",
    "berkelanjutan"
]

# 3. 5 Singkatan Izin / Finansial Kunci
SINGKATAN_KUNCI = ["siup", "sipi", "sikpi", "zeei", "pnbp"]

# 4. Nomor-nomor Pasal Nyata UU 45/2009 (~55 pasal revisi/sisipan)
PASAL_REVISI_RESMI = [
    "1", "7", "9", "14", "15a", "18", "20", "21", "23", "25", "25a", "25b", "25c",
    "27", "27a", "28", "28a", "32", "35a", "36", "41a", "42", "43", "44", "46", "46a",
    "48", "50", "65", "66", "66a", "69", "71", "71a", "73", "73a", "73b", "76", "76a",
    "78a", "83a", "85", "93", "94a", "98", "100a", "100b", "100c", "100d", "110", "110a"
]

def load_graphml(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} tidak ditemukan!")
    G = nx.Graph()
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"g": "http://graphml.graphdrawing.org/xmlns"}

    # Cari key id untuk entity_type dan entity_name
    key_type = "d1"
    key_name = "d0"
    for k in root.findall(".//g:key", ns):
        attr = k.attrib.get("attr.name")
        if attr == "entity_type":
            key_type = k.attrib.get("id")
        elif attr == "entity_name":
            key_name = k.attrib.get("id")

    for n in root.findall(".//g:node", ns):
        nid = n.attrib.get("id", "").strip('"').strip()
        etype = "konsep"
        ename = nid
        for d in n.findall("g:data", ns):
            k = d.attrib.get("key")
            if k == key_type or k == "entity_type":
                etype = (d.text or "konsep").strip('"').strip()
            elif k == key_name or k == "entity_name":
                ename = (d.text or nid).strip('"').strip()
        G.add_node(nid, entity_name=ename, entity_type=etype)

    for e in root.findall(".//g:edge", ns):
        s = e.attrib.get("source", "").strip('"').strip()
        t = e.attrib.get("target", "").strip('"').strip()
        G.add_edge(s, t)

    return G

def is_legal_distinction(n1: str, n2: str) -> bool:
    """
    Memeriksa apakah perbedaan dua nama entitas hukum adalah pembeda substansial
    (misal nomor pasal/ayat/angka berbeda, nominal sanksi berbeda, atau status hukum berlawanan),
    bukan sekadar duplikasi ejaan typo/tanda baca. Berlaku universal untuk semua naskah regulasi RI.
    """
    nums1 = re.findall(r"\d+", n1)
    nums2 = re.findall(r"\d+", n2)
    if nums1 != nums2:
        return True
    codes1 = re.findall(r"\d+[a-z]", n1)
    codes2 = re.findall(r"\d+[a-z]", n2)
    if codes1 != codes2:
        return True
    h1 = re.findall(r"\bhuruf\s+([a-z])\b", n1)
    h2 = re.findall(r"\bhuruf\s+([a-z])\b", n2)
    if h1 and h2 and h1 != h2:
        return True
    opposites = [
        ("asing", "indonesia"), ("penangkap", "pengangkut"),
        ("sipi", "sikpi"), ("menteri", "pemerintah"),
        ("kemandirian", "kemitraan"), ("keterbukaan", "keterpaduan"),
        ("nusantara", "pantai")
    ]
    for w1, w2 in opposites:
        if (w1 in n1 and w2 in n2) or (w2 in n1 and w1 in n2):
            return True
    return False

def audit_knowledge_graph(dir_path: str, doc_raw_text: str):
    graphml_path = os.path.join(dir_path, "graph_chunk_entity_relation.graphml")
    chunks_path = os.path.join(dir_path, "kv_store_text_chunks.json")
    
    if not os.path.exists(graphml_path):
        base_parent = os.path.dirname(os.path.dirname(dir_path))
        data_chunk_path = os.path.join(base_parent, "proses_indexing", "data", "chunks_uu_45_2009.json")
        c_count = 0
        if os.path.exists(data_chunk_path):
            try:
                with open(data_chunk_path, "r", encoding="utf-8") as f:
                    c_count = len(json.load(f))
            except Exception:
                pass
        return {
            "is_pending": True,
            "num_nodes": "[Pending HPC]",
            "num_edges": "-",
            "total_chunks": f"{c_count} chunks (Siap)" if c_count else "[Pending]",
            "pasal_found": "-",
            "def_exact": "-",
            "def_partial": "-",
            "asas_found": "-",
            "singkatan_found": "-",
            "pct_in_text": "-",
            "num_isolated": "-",
            "num_components": "-",
            "duplicate_groups": "-",
            "junk_nodes": [],
            "graph": nx.Graph()
        }

    G = load_graphml(graphml_path)
    
    # 1. Total Node & Edge
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    
    # 2. Chunk Teks & Chunk Kosong
    total_chunks = 0
    empty_chunks = 0
    if os.path.exists(chunks_path):
        with open(chunks_path, "r", encoding="utf-8") as f:
            cdata = json.load(f)
            total_chunks = len(cdata)
            # Periksa jika ada metadata chunk kosong
            # Estimasi jika ada selisih
            
    # 3. Analisis Tipe Entitas & Label Pasal
    type_counts = Counter()
    pasal_label_nodes = 0
    for n, d in G.nodes(data=True):
        t = d.get("entity_type", "konsep").lower()
        name = d.get("entity_name", n).lower()
        type_counts[t] += 1
        if re.search(r"\bpasal\s+\d+", name) or re.search(r"\bayat\s+\d+", name):
            pasal_label_nodes += 1
            
    # 4. Cek Keberadaan Pasal Revisi Resmi (~55)
    all_node_names = []
    for n, d in G.nodes(data=True):
        all_node_names.append(n.lower().strip())
        if "entity_name" in d:
            all_node_names.append(str(d["entity_name"]).lower().strip())
    pasal_found = 0
    for p in PASAL_REVISI_RESMI:
        p_pattern = rf"\bpasal\s+{p}\b"
        if any(re.search(p_pattern, name) for name in all_node_names):
            pasal_found += 1
            
    # 5. Cek 26 Definisi di Pasal 1 (Persis vs Sebagian)
    def_exact = 0
    def_partial = 0
    for d in DEFINISI_PASAL_1:
        exact_match = False
        partial_match = False
        for name in all_node_names:
            if name == d:
                exact_match = True
                break
            elif d in name:
                partial_match = True
        if exact_match:
            def_exact += 1
        elif partial_match:
            def_partial += 1
            
    # 6. Cek 11 Asas Perikanan
    asas_found = 0
    for a in ASAS_PERIKANAN:
        if any(a in name for name in all_node_names):
            asas_found += 1
            
    # 7. Cek 5 Singkatan Kunci (SIUP, SIPI, SIKPI, ZEEI, PNBP)
    # Memeriksa baik bentuk singkatan maupun bentuk kanonikal kepanjangannya
    canonical_singkatan = {
        "siup": "surat izin usaha perikanan",
        "sipi": "surat izin penangkapan ikan",
        "sikpi": "surat izin kapal pengangkut ikan",
        "zeei": "zona ekonomi eksklusif indonesia",
        "pnbp": "penerimaan negara bukan pajak",
    }
    singkatan_found = 0
    for s, full in canonical_singkatan.items():
        if any(re.search(rf"\b{s}\b", name) or full in name for name in all_node_names):
            singkatan_found += 1
            
    # 8. Persentase Nama Node Muncul Persis di Teks UU
    doc_norm = re.sub(r"\s+", " ", doc_raw_text.lower())
    in_text_count = 0
    for n, d in G.nodes(data=True):
        name = str(d.get("entity_name", n)).lower()
        node_id = str(n).lower()
        if (len(name) > 2 and name in doc_norm) or (len(node_id) > 2 and node_id in doc_norm):
            in_text_count += 1
    pct_in_text = (in_text_count / num_nodes * 100) if num_nodes > 0 else 0
    
    # 9. Node Terisolasi & Komponen
    isolated = [n for n in G.nodes if G.degree(n) == 0]
    num_isolated = len(isolated)
    pct_isolated = (num_isolated / num_nodes * 100) if num_nodes > 0 else 0
    components = list(nx.connected_components(G))
    num_components = len(components)
    
    # 10. Kelompok Nama Hampir Duplikat
    # Pisahkan antara duplikat redundan (typo/variasi ejaan) vs perbedaan substansial (nomor pasal/ayat/sanksi berbeda)
    duplicate_groups = 0
    raw_fuzzy_dups = 0
    sorted_names = sorted(list(set(all_node_names)))
    for i in range(len(sorted_names) - 1):
        n1 = sorted_names[i]
        n2 = sorted_names[i+1]
        if n1 != n2 and len(n1) > 4 and len(n2) > 4:
            sim = difflib.SequenceMatcher(None, n1, n2).quick_ratio()
            if sim >= 0.85:
                raw_fuzzy_dups += 1
                if not is_legal_distinction(n1, n2):
                    duplicate_groups += 1
                
    # 11. Node Sampah / Placeholder Template
    junk_nodes = []
    for n in all_node_names:
        if n.startswith("<") or n.endswith(">") or "unused" in n or n in ("...", "gt", "name", "target", "source"):
            junk_nodes.append(n)
            
    return {
        "graph": G,
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "total_chunks": total_chunks,
        "pasal_label_nodes": pasal_label_nodes,
        "type_counts": type_counts,
        "pasal_found": pasal_found,
        "def_exact": def_exact,
        "def_partial": def_partial,
        "asas_found": asas_found,
        "singkatan_found": singkatan_found,
        "pct_in_text": round(pct_in_text, 1),
        "num_isolated": num_isolated,
        "pct_isolated": round(pct_isolated, 1),
        "num_components": num_components,
        "duplicate_groups": duplicate_groups,
        "junk_nodes": junk_nodes,
    }

def calculate_graph_overlap(G1: nx.Graph, G2: nx.Graph):
    """Menghitung metrik konsistensi dan stabilitas (Jaccard similarity) antara dua run."""
    nodes1 = {n.lower().strip() for n in G1.nodes()}
    nodes2 = {n.lower().strip() for n in G2.nodes()}
    
    inter_n = len(nodes1.intersection(nodes2))
    union_n = len(nodes1.union(nodes2))
    jaccard_n = (inter_n / union_n * 100) if union_n > 0 else 0
    
    edges1 = {tuple(sorted([s.lower().strip(), t.lower().strip()])) for s, t in G1.edges()}
    edges2 = {tuple(sorted([s.lower().strip(), t.lower().strip()])) for s, t in G2.edges()}
    
    inter_e = len(edges1.intersection(edges2))
    union_e = len(edges1.union(edges2))
    jaccard_e = (inter_e / union_e * 100) if union_e > 0 else 0
    
    return {
        "inter_nodes": inter_n,
        "union_nodes": union_n,
        "jaccard_nodes": jaccard_n,
        "inter_edges": inter_e,
        "union_edges": union_e,
        "jaccard_edges": jaccard_e,
    }

def main():
    print(f"Membaca naskah resmi UU 45/2009 dari: {TEXT_PATH}")
    with open(TEXT_PATH, "r", encoding="utf-8") as f:
        doc_raw = f.read()
        
    print(f"Menganalisis Graf Chandra V2.1 (Strict JSON AST): {DIR_CHANDRA_V2_1} ...")
    res_v2_1 = audit_knowledge_graph(DIR_CHANDRA_V2_1, doc_raw)

    print(f"Menganalisis Graf Chandra V2 (Percobaan 1): {DIR_CHANDRA_V2_RUN1} ...")
    res_v2_r1 = audit_knowledge_graph(DIR_CHANDRA_V2_RUN1, doc_raw)

    print(f"Menganalisis Graf Chandra V2 (Percobaan 2): {DIR_CHANDRA_V2_RUN2} ...")
    res_v2_r2 = audit_knowledge_graph(DIR_CHANDRA_V2_RUN2, doc_raw)
    
    print(f"Menganalisis Graf Chandra V1 (Awal): {DIR_CHANDRA_V1} ...")
    res_v1 = audit_knowledge_graph(DIR_CHANDRA_V1, doc_raw)

    print(f"Menganalisis Graf Arjun (Baseline): {DIR_ARJUN} ...")
    res_a = audit_knowledge_graph(DIR_ARJUN, doc_raw)
    
    # Hitung metrik stabilitas / overlap Run 1 vs Run 2
    overlap_res = calculate_graph_overlap(res_v2_r1["graph"], res_v2_r2["graph"])

    def fmt_nodes(r):
        if r.get("is_pending"): return "[Pending HPC]"
        return f"{r['num_nodes']} / {r['num_edges']}"
    def fmt_chunks(r):
        if r.get("is_pending"): return str(r['total_chunks'])
        return f"{r['total_chunks']} chunks"
    def fmt_pasal(r):
        if r.get("is_pending"): return "-"
        return f"{r['pasal_found']} dari ~55"
    def fmt_def(r):
        if r.get("is_pending"): return "-"
        return f"{r['def_exact']} persis, {r['def_partial']} seb"
    def fmt_asas(r):
        if r.get("is_pending"): return "-"
        return f"{r['asas_found']} / 11"
    def fmt_sing(r):
        if r.get("is_pending"): return "-"
        return f"{r['singkatan_found']} / 5"
    def fmt_pct(r):
        if r.get("is_pending"): return "-"
        return f"{r['pct_in_text']}%"
    def fmt_iso(r):
        if r.get("is_pending"): return "-"
        return f"{r['num_isolated']} ({r['num_components']} komp)"
    def fmt_dup(r):
        if r.get("is_pending"): return "-"
        return str(r['duplicate_groups'])
    def fmt_junk(r):
        if r.get("is_pending"): return "-"
        return f"{len(r['junk_nodes'])} node"

    # Format nilai untuk kolom tabel
    val_nodes_v21 = fmt_nodes(res_v2_1)
    val_nodes_r1  = fmt_nodes(res_v2_r1)
    val_nodes_r2  = fmt_nodes(res_v2_r2)
    val_nodes_v1  = fmt_nodes(res_v1)
    val_nodes_a   = fmt_nodes(res_a)

    val_chunks_v21 = fmt_chunks(res_v2_1)
    val_chunks_r1  = fmt_chunks(res_v2_r1)
    val_chunks_r2  = fmt_chunks(res_v2_r2)
    val_chunks_v1  = fmt_chunks(res_v1)
    val_chunks_a   = f"{res_a['total_chunks']} / {res_a['total_chunks']}"

    val_pasal_v21 = fmt_pasal(res_v2_1)
    val_pasal_r1  = fmt_pasal(res_v2_r1)
    val_pasal_r2  = fmt_pasal(res_v2_r2)
    val_pasal_v1  = fmt_pasal(res_v1)
    val_pasal_a   = fmt_pasal(res_a)

    val_def_v21 = fmt_def(res_v2_1)
    val_def_r1  = fmt_def(res_v2_r1)
    val_def_r2  = fmt_def(res_v2_r2)
    val_def_v1  = fmt_def(res_v1)
    val_def_a   = f"{res_a['def_exact']} / 26"

    val_asas_v21 = fmt_asas(res_v2_1)
    val_asas_r1  = fmt_asas(res_v2_r1)
    val_asas_r2  = fmt_asas(res_v2_r2)
    val_asas_v1  = fmt_asas(res_v1)
    val_asas_a   = fmt_asas(res_a)

    val_sing_v21 = fmt_sing(res_v2_1)
    val_sing_r1  = fmt_sing(res_v2_r1)
    val_sing_r2  = fmt_sing(res_v2_r2)
    val_sing_v1  = fmt_sing(res_v1)
    val_sing_a   = fmt_sing(res_a)

    val_pct_v21 = fmt_pct(res_v2_1)
    val_pct_r1  = fmt_pct(res_v2_r1)
    val_pct_r2  = fmt_pct(res_v2_r2)
    val_pct_v1  = fmt_pct(res_v1)
    val_pct_a   = fmt_pct(res_a)

    val_iso_v21 = fmt_iso(res_v2_1)
    val_iso_r1  = fmt_iso(res_v2_r1)
    val_iso_r2  = fmt_iso(res_v2_r2)
    val_iso_v1  = fmt_iso(res_v1)
    val_iso_a   = f"{res_a['num_isolated']} ({res_a['pct_isolated']}%)"

    val_dup_v21 = fmt_dup(res_v2_1)
    val_dup_r1  = fmt_dup(res_v2_r1)
    val_dup_r2  = fmt_dup(res_v2_r2)
    val_dup_v1  = fmt_dup(res_v1)
    val_dup_a   = fmt_dup(res_a)

    val_junk_v21 = fmt_junk(res_v2_1)
    val_junk_r1  = fmt_junk(res_v2_r1)
    val_junk_r2  = fmt_junk(res_v2_r2)
    val_junk_v1  = fmt_junk(res_v1)
    val_junk_a   = fmt_junk(res_a)

    w_p, w_v21, w_r1, w_r2, w_v1, w_a = 32, 22, 20, 20, 18, 18
    total_len = w_p + w_v21 + w_r1 + w_r2 + w_v1 + w_a + 15
    sep_line = "=" * total_len

    print("\n" + sep_line)
    print(f"{'PARAMETER METRIK':<{w_p}} | {'CHANDRA V2.1 (NEW)':<{w_v21}} | {'CHANDRA V2 (RUN 1)':<{w_r1}} | {'CHANDRA V2 (RUN 2)':<{w_r2}} | {'CHANDRA V1 (AWAL)':<{w_v1}} | {'ARJUN (BASELINE)':<{w_a}}")
    print(sep_line)
    print(f"{'Jumlah node / edge':<{w_p}} | {val_nodes_v21:<{w_v21}} | {val_nodes_r1:<{w_r1}} | {val_nodes_r2:<{w_r2}} | {val_nodes_v1:<{w_v1}} | {val_nodes_a:<{w_a}}")
    print(f"{'Chunk teks':<{w_p}} | {val_chunks_v21:<{w_v21}} | {val_chunks_r1:<{w_r1}} | {val_chunks_r2:<{w_r2}} | {val_chunks_v1:<{w_v1}} | {val_chunks_a:<{w_a}}")
    print(f"{'Pasal yang diubah (~55)':<{w_p}} | {val_pasal_v21:<{w_v21}} | {val_pasal_r1:<{w_r1}} | {val_pasal_r2:<{w_r2}} | {val_pasal_v1:<{w_v1}} | {val_pasal_a:<{w_a}}")
    print(f"{'26 definisi di Pasal 1':<{w_p}} | {val_def_v21:<{w_v21}} | {val_def_r1:<{w_r1}} | {val_def_r2:<{w_r2}} | {val_def_v1:<{w_v1}} | {val_def_a:<{w_a}}")
    print(f"{'11 asas':<{w_p}} | {val_asas_v21:<{w_v21}} | {val_asas_r1:<{w_r1}} | {val_asas_r2:<{w_r2}} | {val_asas_v1:<{w_v1}} | {val_asas_a:<{w_a}}")
    print(f"{'SIUP / SIPI / SIKPI / ZEEI / PNBP':<{w_p}} | {val_sing_v21:<{w_v21}} | {val_sing_r1:<{w_r1}} | {val_sing_r2:<{w_r2}} | {val_sing_v1:<{w_v1}} | {val_sing_a:<{w_a}}")
    print(f"{'Nama node muncul di teks UU (%)':<{w_p}} | {val_pct_v21:<{w_v21}} | {val_pct_r1:<{w_r1}} | {val_pct_r2:<{w_r2}} | {val_pct_v1:<{w_v1}} | {val_pct_a:<{w_a}}")
    print(f"{'Node terisolasi':<{w_p}} | {val_iso_v21:<{w_v21}} | {val_iso_r1:<{w_r1}} | {val_iso_r2:<{w_r2}} | {val_iso_v1:<{w_v1}} | {val_iso_a:<{w_a}}")
    print(f"{'Kelompok nama hampir duplikat':<{w_p}} | {val_dup_v21:<{w_v21}} | {val_dup_r1:<{w_r1}} | {val_dup_r2:<{w_r2}} | {val_dup_v1:<{w_v1}} | {val_dup_a:<{w_a}}")
    print(f"{'Node sampah / placeholder':<{w_p}} | {val_junk_v21:<{w_v21}} | {val_junk_r1:<{w_r1}} | {val_junk_r2:<{w_r2}} | {val_junk_v1:<{w_v1}} | {val_junk_a:<{w_a}}")
    print(sep_line)

    if not res_v2_1.get("is_pending"):
        overlap_v21 = calculate_graph_overlap(res_v2_1["graph"], res_v2_r1["graph"])
        print("\n" + sep_line)
        print("=== ANALISIS STABILITAS GEMMA 4:12B CHANDRA V2.1 vs CHANDRA V2 ===")
        print(sep_line)
        print(f"Stabilitas / Overlap Entitas (Jaccard Nodes) : {overlap_v21['jaccard_nodes']:.2f}% (Irisan: {overlap_v21['inter_nodes']} / Gabungan: {overlap_v21['union_nodes']})")
        print(f"Stabilitas / Overlap Relasi  (Jaccard Edges) : {overlap_v21['jaccard_edges']:.2f}% (Irisan: {overlap_v21['inter_edges']} / Gabungan: {overlap_v21['union_edges']})")
        print(sep_line + "\n")

    print("\n" + sep_line)
    print("=== ANALISIS STABILITAS & KONSISTENSI DUA KALI RUNNING GEMMA 4:12B (V2) ===")
    print(sep_line)
    print(f"Stabilitas / Overlap Entitas (Jaccard Nodes) : {overlap_res['jaccard_nodes']:.2f}% (Irisan: {overlap_res['inter_nodes']} / Gabungan: {overlap_res['union_nodes']})")
    print(f"Stabilitas / Overlap Relasi  (Jaccard Edges) : {overlap_res['jaccard_edges']:.2f}% (Irisan: {overlap_res['inter_edges']} / Gabungan: {overlap_res['union_edges']})")
    print(sep_line + "\n")

if __name__ == "__main__":
    main()
