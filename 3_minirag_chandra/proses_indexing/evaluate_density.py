"""
Script Evaluasi Metrik Densitas & Komparasi Graf MiniRAG
Gemma 3:12B (Arjun Dewana) vs Gemma 4:12B (DGX A100)
"""
import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Set, Tuple

ALLOWED_ENTITY_TYPES = {
    "DASAR_HUKUM", "STRUKTUR", "KONSEP", "SANKSI", "PIHAK", "KEWAJIBAN", "HAK"
}

def analyze_storage(storage_dir: str, run_name: str) -> Dict[str, Any]:
    graphml_path = os.path.join(storage_dir, "graph_chunk_entity_relation.graphml")
    chunks_path = os.path.join(storage_dir, "kv_store_text_chunks.json")

    if not os.path.exists(graphml_path):
        raise FileNotFoundError(f"File {graphml_path} tidak ditemukan!")

    num_chunks = 0
    if os.path.exists(chunks_path):
        with open(chunks_path, "r", encoding="utf-8") as f:
            num_chunks = len(json.load(f))

    tree = ET.parse(graphml_path)
    root = tree.getroot()
    ns = {"g": "http://graphml.graphdrawing.org/xmlns"}

    type_key = "d0"
    for k in root.findall(".//g:key", ns):
        if k.attrib.get("attr.name") == "entity_type":
            type_key = k.attrib.get("id")
            break

    nodes_dict = {}
    for n in root.findall(".//g:node", ns):
        nid = n.attrib.get("id", "").strip('"')
        etype = "UNKNOWN"
        for d in n.findall("g:data", ns):
            if d.attrib.get("key") == type_key or d.attrib.get("key") == "entity_type":
                etype = d.text.strip('"').strip() if d.text else "UNKNOWN"
        nodes_dict[nid] = etype

    edges_list = []
    for e in root.findall(".//g:edge", ns):
        s = e.attrib.get("source", "").strip('"')
        t = e.attrib.get("target", "").strip('"')
        edges_list.append((s, t))

    total_nodes = len(nodes_dict)
    total_edges = len(edges_list)

    connected_nodes: Set[str] = set()
    for s, t in edges_list:
        connected_nodes.add(s)
        connected_nodes.add(t)

    isolated_nodes = len(set(nodes_dict.keys()) - connected_nodes)
    isolated_ratio = (isolated_nodes / total_nodes * 100) if total_nodes > 0 else 0

    compliant_nodes = sum(1 for t in nodes_dict.values() if t.upper() in ALLOWED_ENTITY_TYPES)
    compliance_rate = (compliant_nodes / total_nodes * 100) if total_nodes > 0 else 0

    node_density = total_nodes / num_chunks if num_chunks > 0 else 0
    edge_density = total_edges / num_chunks if num_chunks > 0 else 0
    avg_degree = (2 * total_edges) / total_nodes if total_nodes > 0 else 0
    possible_edges = (total_nodes * (total_nodes - 1)) / 2 if total_nodes > 1 else 1
    structural_density = total_edges / possible_edges

    file_size_mb = os.path.getsize(graphml_path) / (1024 * 1024)

    return {
        "run_name": run_name,
        "total_chunks": num_chunks,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "isolated_nodes": isolated_nodes,
        "isolated_ratio": round(isolated_ratio, 2),
        "compliance_rate": round(compliance_rate, 2),
        "node_density": round(node_density, 2),
        "edge_density": round(edge_density, 2),
        "avg_degree": round(avg_degree, 3),
        "structural_density": f"{structural_density:.2e}",
        "file_size_mb": round(file_size_mb, 2),
        "nodes_set": set(nodes_dict.keys()),
    }

def compare(dir_a: str, dir_b: str, name_a="Gemma 3:12B (Arjun)", name_b="Gemma 4:12B (DGX A100)"):
    m_a = analyze_storage(dir_a, name_a)
    m_b = analyze_storage(dir_b, name_b)

    set_a = {k.lower() for k in m_a["nodes_set"]}
    set_b = {k.lower() for k in m_b["nodes_set"]}
    inter = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    jaccard = (inter / union * 100) if union > 0 else 0

    comp_a_str = f"{m_a['compliance_rate']}%"
    comp_b_str = f"{m_b['compliance_rate']}%"
    iso_a_str = f"{m_a['isolated_nodes']} ({m_a['isolated_ratio']}%)"
    iso_b_str = f"{m_b['isolated_nodes']} ({m_b['isolated_ratio']}%)"
    size_a_str = f"{m_a['file_size_mb']} MB"
    size_b_str = f"{m_b['file_size_mb']} MB"
    jaccard_str = f"{jaccard:.2f}%"

    print("\n" + "=" * 78)
    print("=== HASIL EVALUASI METRIK KOMPARATIF KNOWLEDGE GRAPH MINI-RAG ===")
    print("=" * 78)
    print(f"| {'Parameter Metrik':<30} | {name_a:^20} | {name_b:^20} |")
    print(f"|{'-'*32}|{'-'*22}|{'-'*22}|")
    print(f"| {'Total Text Chunks':<30} | {m_a['total_chunks']:^20} | {m_b['total_chunks']:^20} |")
    print(f"| {'Total Nodes (Entitas)':<30} | {m_a['total_nodes']:^20} | {m_b['total_nodes']:^20} |")
    print(f"| {'Total Edges (Relasi)':<30} | {m_a['total_edges']:^20} | {m_b['total_edges']:^20} |")
    print(f"| {'Kepatuhan Skema 7 Tipe (%)':<30} | {comp_a_str:^20} | {comp_b_str:^20} |")
    print(f"| {'Node Terisolasi (Degree 0)':<30} | {iso_a_str:^20} | {iso_b_str:^20} |")
    print(f"| {'Densitas Node / Chunk':<30} | {m_a['node_density']:^20} | {m_b['node_density']:^20} |")
    print(f"| {'Densitas Edge / Chunk':<30} | {m_a['edge_density']:^20} | {m_b['edge_density']:^20} |")
    print(f"| {'Rasio Edge/Node (Avg Degree)':<30} | {m_a['avg_degree']:^20} | {m_b['avg_degree']:^20} |")
    print(f"| {'Densitas Struktural Graf':<30} | {m_a['structural_density']:^20} | {m_b['structural_density']:^20} |")
    print(f"| {'Ukuran File Graf (.graphml)':<30} | {size_a_str:^20} | {size_b_str:^20} |")
    print(f"| {'Overlap Entitas (Jaccard)':<30} | {'-':^20} | {jaccard_str:^20} |")
    print("=" * 78)

if __name__ == "__main__":
    import sys
    d_a = sys.argv[1] if len(sys.argv) > 1 else "../../2_minirag_mjundewana/UU Nomor 45 Tahun 2009"
    d_b = sys.argv[2] if len(sys.argv) > 2 else "../hasil_indexing/storage_gemma4_uu45"
    compare(d_a, d_b)
