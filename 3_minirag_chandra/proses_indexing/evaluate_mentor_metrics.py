#!/usr/bin/env python3
"""
Script Audit Substantif & Metrik Komparatif Komprehensif MiniRAG
Mengimplementasikan 11 Parameter Evaluasi Mentor:
Gemma 4 (Chandra) vs Gemma 3 (Arjun)
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
DIR_CHANDRA_V2 = os.path.join(BASE_DIR, "4_minirag_chandra_v2", "hasil_indexing", "storage_gemma4_uu45")
DIR_CHANDRA = DIR_CHANDRA_V2

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

def main():
    print(f"Membaca naskah resmi UU 45/2009 dari: {TEXT_PATH}")
    with open(TEXT_PATH, "r", encoding="utf-8") as f:
        doc_raw = f.read()
        
    print(f"Menganalisis Graf Chandra V2 (Tuned): {DIR_CHANDRA_V2} ...")
    res_v2 = audit_knowledge_graph(DIR_CHANDRA_V2, doc_raw)
    
    print(f"Menganalisis Graf Chandra V1 (Awal): {DIR_CHANDRA_V1} ...")
    res_v1 = audit_knowledge_graph(DIR_CHANDRA_V1, doc_raw)

    print(f"Menganalisis Graf Arjun (Baseline): {DIR_ARJUN} ...")
    res_a = audit_knowledge_graph(DIR_ARJUN, doc_raw)
    
    val_nodes_v2 = f"{res_v2['num_nodes']} / {res_v2['num_edges']}"
    val_nodes_v1 = f"{res_v1['num_nodes']} / {res_v1['num_edges']}"
    val_nodes_a  = f"{res_a['num_nodes']} / {res_a['num_edges']}"
    
    val_chunks_v2 = f"{res_v2['total_chunks']} chunks"
    val_chunks_v1 = f"{res_v1['total_chunks']} chunks"
    val_chunks_a  = f"{res_a['total_chunks']} / {res_a['total_chunks']}"
    
    val_pasal_v2 = f"{res_v2['pasal_found']} dari ~55"
    val_pasal_v1 = f"{res_v1['pasal_found']} dari ~55"
    val_pasal_a  = f"{res_a['pasal_found']} dari ~55"
    
    val_def_v2 = f"{res_v2['def_exact']} persis, {res_v2['def_partial']} seb"
    val_def_v1 = f"{res_v1['def_exact']} persis, {res_v1['def_partial']} seb"
    val_def_a  = f"{res_a['def_exact']} / 26"
    
    val_asas_v2 = f"{res_v2['asas_found']} / 11"
    val_asas_v1 = f"{res_v1['asas_found']} / 11"
    val_asas_a  = f"{res_a['asas_found']} / 11"
    
    val_sing_v2 = f"{res_v2['singkatan_found']} / 5"
    val_sing_v1 = f"{res_v1['singkatan_found']} / 5"
    val_sing_a  = f"{res_a['singkatan_found']} / 5"
    
    val_pct_v2 = f"{res_v2['pct_in_text']}%"
    val_pct_v1 = f"{res_v1['pct_in_text']}%"
    val_pct_a  = f"{res_a['pct_in_text']}%"
    
    val_iso_v2 = f"{res_v2['num_isolated']} ({res_v2['num_components']} komp)"
    val_iso_v1 = f"{res_v1['num_isolated']} ({res_v1['num_components']} komp)"
    val_iso_a  = f"{res_a['num_isolated']} ({res_a['pct_isolated']}%)"
    
    val_dup_v2 = str(res_v2['duplicate_groups'])
    val_dup_v1 = str(res_v1['duplicate_groups'])
    val_dup_a  = str(res_a['duplicate_groups'])
    
    val_junk_v2 = f"{len(res_v2['junk_nodes'])} node"
    val_junk_v1 = f"{len(res_v1['junk_nodes'])} node"
    val_junk_a  = f"{len(res_a['junk_nodes'])} node"

    print("\n" + "=" * 105)
    print(f"{'PARAMETER METRIK':<32} | {'CHANDRA V2 (BARU)':<22} | {'CHANDRA V1 (AWAL)':<22} | {'ARJUN (BASELINE)':<22}")
    print("=" * 105)
    print(f"{'Jumlah node / edge':<32} | {val_nodes_v2:<22} | {val_nodes_v1:<22} | {val_nodes_a:<22}")
    print(f"{'Chunk teks':<32} | {val_chunks_v2:<22} | {val_chunks_v1:<22} | {val_chunks_a:<22}")
    print(f"{'Pasal yang diubah (~55)':<32} | {val_pasal_v2:<22} | {val_pasal_v1:<22} | {val_pasal_a:<22}")
    print(f"{'26 definisi di Pasal 1':<32} | {val_def_v2:<22} | {val_def_v1:<22} | {val_def_a:<22}")
    print(f"{'11 asas':<32} | {val_asas_v2:<22} | {val_asas_v1:<22} | {val_asas_a:<22}")
    print(f"{'SIUP / SIPI / SIKPI / ZEEI / PNBP':<32} | {val_sing_v2:<22} | {val_sing_v1:<22} | {val_sing_a:<22}")
    print(f"{'Nama node muncul di teks UU (%)':<32} | {val_pct_v2:<22} | {val_pct_v1:<22} | {val_pct_a:<22}")
    print(f"{'Node terisolasi':<32} | {val_iso_v2:<22} | {val_iso_v1:<22} | {val_iso_a:<22}")
    print(f"{'Kelompok nama hampir duplikat':<32} | {val_dup_v2:<22} | {val_dup_v1:<22} | {val_dup_a:<22}")
    print(f"{'Node sampah / placeholder':<32} | {val_junk_v2:<22} | {val_junk_v1:<22} | {val_junk_a:<22}")
    print("=" * 105)

if __name__ == "__main__":
    main()
