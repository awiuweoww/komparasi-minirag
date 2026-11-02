"""
Script Indexing MiniRAG (Domain Hukum Kelautan & Perikanan - V2 Tuned):
LLM: Gemma 4:12B (think: false) | Embedding: BGE-M3 (1024-dim)
Dokumen: UU Nomor 45 Tahun 2009 (Perikanan)
Optimasi Terpadu:
- 512-Token Boundary-Aware Chunking dengan Header Regulasi Kanonik
- Prompt Indexing Resmi v2.2.0 (Penamaan Kanonik & Penanganan 'Cukup Jelas')
- Integrasi Penuh normalisasi_entitas.py (Canonical Naming & Graph Deduplication)
- Balanced Tuple Parsing (Bebas Truncation pada Kurung Bersarang)
- Hierarchical Article Anchoring (Zero Isolates, Struktur Pohon Yuridis)
"""
import os
import sys
import time
import json
import re
import asyncio
import httpx
import numpy as np
import networkx as nx
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# Pastikan path modul terbaca
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from minirag.prompt_id_revisi import (
    GRAPH_FIELD_SEP,
    PROMPTS,
    DEFAULT_TUPLE_DELIMITER,
    DEFAULT_RECORD_DELIMITER,
    DEFAULT_COMPLETION_DELIMITER,
    DEFAULT_ENTITY_TYPES,
)

from normalisasi_entitas import (
    canonical_name,
    is_junk,
    canonical_type,
    dedup_graph,
    report,
    INDEXED_REGULATION,
)

raw_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11500")
if not raw_host.startswith("http://") and not raw_host.startswith("https://"):
    raw_host = f"http://{raw_host}"
OLLAMA_HOST = raw_host.replace("0.0.0.0", "127.0.0.1")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:12b")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3:latest")
WORKING_DIR = os.getenv("WORKING_DIR", "../hasil_indexing/storage_gemma4_uu45")
DATA_PATH = os.getenv("DATA_PATH", "./data/chunks_uu_45_2009.json")
CONCURRENCY = int(os.getenv("CONCURRENCY", "4"))
NUM_PREDICT = int(os.getenv("NUM_PREDICT", "3072"))

ALLOWED_ENTITY_TYPES = set(t.lower() for t in DEFAULT_ENTITY_TYPES)

def extract_balanced_tuples(text: str) -> list[str]:
    """
    Ekstrak tuple yang diawali '(' dan diakhiri ')' dengan memperhitungkan
    tanda kurung bersarang (nested parentheses), misalnya:
    ("entity"<|>"Pasal 93 ayat (1) UU Nomor 45 Tahun 2009"<|>"struktur"<|>"...")
    """
    records = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '(':
            start = i
            depth = 1
            i += 1
            in_quote = False
            quote_char = None
            while i < n and depth > 0:
                char = text[i]
                if char in ('"', "'") and (i == 0 or text[i-1] != '\\'):
                    if not in_quote:
                        in_quote = True
                        quote_char = char
                    elif quote_char == char:
                        in_quote = False
                        quote_char = None
                elif not in_quote:
                    if char == '(':
                        depth += 1
                    elif char == ')':
                        depth -= 1
                i += 1
            if depth == 0:
                tuple_str = text[start+1:i-1].strip()
                records.append(tuple_str)
        else:
            i += 1
    return records

def parse_extracted_records(raw_text: str):
    """
    Parser adaptif selaras dengan normalisasi_entitas.py:
    1. Bersihkan token stop & codeblock markdown
    2. Tangkap tuple seimbang (balanced parentheses)
    3. Terapkan is_junk() dan canonical_name() pada setiap entitas dan relasi
    """
    entities = []
    relationships = []
    
    text = re.sub(r"```[a-zA-Z]*", "", raw_text)
    text = text.replace("<|SELESAI|>", "").replace("<|COMPLETE|>", "").replace("```", "")
    
    # Jika hanya memuat stop token / 'Cukup jelas.', lewati
    cleaned_lower = text.strip().lower()
    if not cleaned_lower or cleaned_lower in ("cukup jelas", "cukup jelas.", "<|selesai|>"):
        return entities, relationships
        
    records = extract_balanced_tuples(text)
    
    for rec in records:
        rec = rec.strip()
        sep = "<|>" if "<|>" in rec else "|"
        parts = [p.strip().strip('"\'`') for p in rec.split(sep)]
        if not parts:
            continue
            
        lead = parts[0].strip().lower()
        
        # 1. Format eksplisit entitas: ("entity"<|>name<|>type<|>desc)
        if lead in ("entity", "entitas") and len(parts) >= 2:
            raw_name = parts[1].strip()
            if is_junk(raw_name):
                continue
            c_name = canonical_name(raw_name)
            if is_junk(c_name):
                continue
                
            raw_type = parts[2].strip() if len(parts) > 2 else "konsep"
            c_type = canonical_type(raw_type)
            if c_type not in ALLOWED_ENTITY_TYPES:
                c_type = "konsep"
                
            desc = parts[3].strip() if len(parts) > 3 else ""
            entities.append({
                "name": c_name,
                "type": c_type,
                "description": desc
            })
            
        # 2. Format eksplisit relasi: ("relationship"<|>src<|>tgt<|>desc<|>kw<|>weight)
        elif lead in ("relationship", "hubungan", "relasi") and len(parts) >= 3:
            raw_src = parts[1].strip()
            raw_tgt = parts[2].strip()
            if is_junk(raw_src) or is_junk(raw_tgt):
                continue
                
            c_src = canonical_name(raw_src)
            c_tgt = canonical_name(raw_tgt)
            if is_junk(c_src) or is_junk(c_tgt) or c_src == c_tgt:
                continue
                
            desc = parts[3].strip() if len(parts) > 3 else ""
            keywords = parts[4].strip() if len(parts) > 4 else "hubungan hukum"
            weight = 8.0
            if len(parts) > 5:
                try:
                    weight = float(re.sub(r"[^0-9.]", "", parts[5]))
                except ValueError:
                    weight = 8.0
            relationships.append({
                "src": c_src,
                "tgt": c_tgt,
                "description": desc,
                "keywords": keywords,
                "weight": weight
            })
            
        # 3. Fallback jika model menghasilkan tuple tanpa label "entity" di depan
        elif lead not in ("content_keywords", "keywords"):
            if len(parts) >= 3 and parts[1].strip().lower() in ALLOWED_ENTITY_TYPES:
                raw_name = parts[0].strip()
                if not is_junk(raw_name):
                    c_name = canonical_name(raw_name)
                    if not is_junk(c_name):
                        entities.append({
                            "name": c_name,
                            "type": parts[1].strip().lower(),
                            "description": parts[2].strip()
                        })
            elif len(parts) >= 3 and not is_junk(parts[0]) and not is_junk(parts[1]):
                c_src = canonical_name(parts[0].strip())
                c_tgt = canonical_name(parts[1].strip())
                if not is_junk(c_src) and not is_junk(c_tgt) and c_src != c_tgt:
                    desc = parts[2].strip() if len(parts) > 2 else ""
                    kw = parts[3].strip() if len(parts) > 3 else "hubungan hukum"
                    relationships.append({
                        "src": c_src,
                        "tgt": c_tgt,
                        "description": desc,
                        "keywords": kw,
                        "weight": 8.0
                    })
                    
    return entities, relationships

async def ollama_bge_m3_embed(texts: list[str]) -> np.ndarray:
    url = f"{OLLAMA_HOST.rstrip('/')}/api/embed"
    all_embeddings = []
    batch_size = 16
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            res = await client.post(url, json={"model": EMBEDDING_MODEL, "input": batch})
            if res.status_code == 200:
                all_embeddings.extend(res.json()["embeddings"])
            else:
                for t in batch:
                    r2 = await client.post(
                        f"{OLLAMA_HOST.rstrip('/')}/api/embeddings",
                        json={"model": EMBEDDING_MODEL, "prompt": t}
                    )
                    if r2.status_code == 200:
                        all_embeddings.append(r2.json()["embedding"])
                    else:
                        raise RuntimeError(f"Ollama Embed Error ({r2.status_code}): {r2.text}")
    return np.array(all_embeddings, dtype=np.float32)

async def extract_chunk_streamlined(
    chunk_idx: int,
    total_chunks: int,
    chunk_data: any,
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient
):
    chunk_text = chunk_data.get("content", str(chunk_data)) if isinstance(chunk_data, dict) else str(chunk_data)
    pasal_ref = chunk_data.get("pasal_ref", "Umum") if isinstance(chunk_data, dict) else "Umum"
    
    async with sem:
        t0 = time.time()
        
        prompt_extract = PROMPTS["entity_extraction"].format(
            tuple_delimiter=DEFAULT_TUPLE_DELIMITER,
            record_delimiter=DEFAULT_RECORD_DELIMITER,
            completion_delimiter=DEFAULT_COMPLETION_DELIMITER,
            entity_types=",".join(DEFAULT_ENTITY_TYPES),
            input_text=chunk_text,
        )
        
        options = {
            "num_predict": NUM_PREDICT,
            "temperature": 0.0,
        }
        
        # Ekstraksi Komprehensif Satu Siklus dengan Mode Berpikir Dimatikan (think: false)
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt_extract}],
            "stream": False,
            "options": options,
            "think": False
        }
        
        res = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=180.0)
        res.raise_for_status()
        msg_obj = res.json().get("message", {})
        content = msg_obj.get("content", "")
        thinking = msg_obj.get("thinking", "")
        
        full_text = content if content.strip() else thinking
        entities, relationships = parse_extracted_records(full_text)
        
        # Filter pencegahan duplikasi dalam 1 chunk
        unique_entities = {}
        for e in entities:
            if e["name"] not in unique_entities:
                unique_entities[e["name"]] = e
        entities = list(unique_entities.values())
        
        duration = time.time() - t0
        print(f"[{chunk_idx+1:03d}/{total_chunks:03d}] {pasal_ref[:25]:<25} | Entitas: {len(entities):<2} | Relasi: {len(relationships):<2} | Durasi: {duration:5.2f}s", flush=True)
        if len(entities) == 0 and len(full_text.strip()) > 0 and "<|SELESAI|>" not in full_text:
            print(f"  [RAW SNIPPET]: {repr(full_text[:120])}", flush=True)
            
        return chunk_idx, pasal_ref, entities, relationships, chunk_text

async def main():
    print("=" * 70)
    print("MEMULAI INDEXING MINIRAG V2 TUNED: GEMMA 4:12B + BGE-M3 (PROMPT v2.2.0 + KANONIKAL)")
    print(f"Ollama Host   : {OLLAMA_HOST}")
    print(f"LLM Model     : {OLLAMA_MODEL} (think: false)")
    print(f"Embed Model   : {EMBEDDING_MODEL} (1024-dim)")
    print(f"Concurrency   : {CONCURRENCY} parallel slots")
    print(f"Max Predict   : {NUM_PREDICT} tokens")
    print(f"Working Dir   : {WORKING_DIR}")
    print(f"Input Doc     : {DATA_PATH}")
    print("=" * 70, flush=True)

    os.makedirs(WORKING_DIR, exist_ok=True)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    total_chunks = len(chunks)
    print(f"Dokumen MinerU berhasil dimuat: {total_chunks} chunk (Header Kanonik + 512 token).\n", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    start_time = time.time()

    async with httpx.AsyncClient(timeout=180.0) as client:
        tasks = [
            extract_chunk_streamlined(i, total_chunks, chunk_item, sem, client)
            for i, chunk_item in enumerate(chunks)
        ]
        results = await asyncio.gather(*tasks)

    print("\n" + "=" * 70)
    print("Ekstraksi selesai. Merajut Knowledge Graph Hierarkis...", flush=True)

    graph = nx.Graph()
    doc_node_id = INDEXED_REGULATION  # "uu nomor 45 tahun 2009"
    graph.add_node(
        doc_node_id,
        entity_name="UU Nomor 45 Tahun 2009",
        entity_type="dasar_hukum",
        description="Undang-Undang Republik Indonesia Nomor 45 Tahun 2009 tentang Perubahan atas UU Nomor 31 Tahun 2004 tentang Perikanan",
        source_id="doc_root"
    )

    kv_chunks = {}
    nodes_registry = {}
    node_to_pasal = {}

    for chunk_idx, pasal_ref, entities, relationships, chunk_text in results:
        chunk_id = f"chunk-{chunk_idx+1:04d}"
        kv_chunks[chunk_id] = {
            "chunk_id": chunk_id,
            "pasal": pasal_ref,
            "content": chunk_text
        }

        # 1. Daftarkan entitas
        for ent in entities:
            k = ent["name"]
            if is_junk(k):
                continue
            if k not in node_to_pasal:
                node_to_pasal[k] = pasal_ref
                
            if k not in graph:
                graph.add_node(
                    k,
                    entity_name=ent["name"],
                    entity_type=ent["type"],
                    description=ent["description"],
                    source_id=chunk_id
                )
                nodes_registry[k] = ent
            else:
                existing_desc = graph.nodes[k].get("description", "")
                if ent["description"] and ent["description"] not in existing_desc:
                    graph.nodes[k]["description"] = (existing_desc + " <SEP> " + ent["description"]).strip()

        # 2. Daftarkan relasi
        for rel in relationships:
            s = rel["src"]
            t = rel["tgt"]
            if is_junk(s) or is_junk(t) or s == t:
                continue
            if s not in graph:
                graph.add_node(s, entity_name=s, entity_type="konsep", description="", source_id=chunk_id)
                if s not in node_to_pasal:
                    node_to_pasal[s] = pasal_ref
            if t not in graph:
                graph.add_node(t, entity_name=t, entity_type="konsep", description="", source_id=chunk_id)
                if t not in node_to_pasal:
                    node_to_pasal[t] = pasal_ref

            if graph.has_edge(s, t):
                graph.edges[s, t]["weight"] = float(graph.edges[s, t].get("weight", 8.0)) + 1.0
            else:
                graph.add_edge(
                    s,
                    t,
                    weight=rel["weight"],
                    description=rel["description"],
                    keywords=rel["keywords"],
                    source_id=chunk_id
                )

    # 3. KONEKTIVITAS PENUH BERBASIS HIERARKI HUKUM (Hierarchical Article Anchoring)
    isolated = [n for n in graph.nodes if graph.degree(n) == 0 and n != doc_node_id]
    print(f"Mengintegrasikan {len(isolated)} entitas tanpa relasi melalui Hierarchical Article Anchoring...")

    for iso_node in isolated:
        target_parent = doc_node_id
        pref = node_to_pasal.get(iso_node, "")
        
        m_pasal = re.search(r"Pasal\s+\d+[a-zA-Z]?", pref, re.IGNORECASE)
        if m_pasal:
            pasal_name = canonical_name(m_pasal.group(0))
            if pasal_name != iso_node and not is_junk(pasal_name):
                if pasal_name not in graph:
                    graph.add_node(
                        pasal_name,
                        entity_name=pasal_name,
                        entity_type="struktur",
                        description=f"Pasal dalam struktur peraturan perundang-undangan UU Nomor 45 Tahun 2009",
                        source_id="legal_hierarchy"
                    )
                if not graph.has_edge(doc_node_id, pasal_name):
                    graph.add_edge(
                        doc_node_id,
                        pasal_name,
                        weight=10.0,
                        description=f"UU Nomor 45 Tahun 2009 memuat ketentuan {pasal_name}",
                        keywords="struktur peraturan",
                        source_id="legal_hierarchy"
                    )
                target_parent = pasal_name

        graph.add_edge(
            target_parent,
            iso_node,
            weight=7.0,
            description=f"Ketentuan materi muatan yuridis dalam {pref if pref else 'UU Nomor 45 Tahun 2009'}",
            keywords="muatan regulasi",
            source_id="hierarchical_anchoring"
        )

    # 4. NORMALISASI & DEDUPLIKASI GRAF (normalisasi_entitas.py)
    print("\nMenjalankan Deduplikasi Graf Kanonik (normalisasi_entitas.py)...", flush=True)
    report(graph, "Sebelum Dedup")
    graph, dedup_info = dedup_graph(graph)
    merged_count = len(dedup_info["mapping"]) - graph.number_of_nodes()
    print(f"Hasil Dedup: Dibuang (sampah)={len(dedup_info['dropped_junk'])} | Node digabung={merged_count}")
    report(graph, "Sesudah Dedup")

    # Pastikan kembali nol isolat setelah deduplikasi
    post_isolated = [n for n in graph.nodes if graph.degree(n) == 0 and n != doc_node_id]
    for iso in post_isolated:
        graph.add_edge(doc_node_id, iso, weight=7.0, description="Ketentuan regulasi", keywords="muatan regulasi", source_id="final_anchoring")

    # Simpan GraphML
    graphml_path = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
    nx.write_graphml(graph, graphml_path)
    print(f"\nGraphML tersimpan di: {graphml_path}")
    print(f"Total Nodes Akhir: {graph.number_of_nodes()} | Total Edges Akhir: {graph.number_of_edges()}")

    # Simpan KV Store Chunks
    chunks_path = os.path.join(WORKING_DIR, "kv_store_text_chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(kv_chunks, f, ensure_ascii=False, indent=2)

    # Vektor Embedding BGE-M3 untuk Seluruh Entitas (Batching)
    print("Membuat Vektor Embedding BGE-M3 (1024-dim) untuk seluruh entitas kanonik...", flush=True)
    all_node_keys = list(graph.nodes.keys())
    node_texts = [f"{graph.nodes[k].get('entity_name', k)}: {graph.nodes[k].get('description', '')}" for k in all_node_keys]
    node_vecs = await ollama_bge_m3_embed(node_texts)

    vdb_entities = {}
    for i, k in enumerate(all_node_keys):
        vdb_entities[k] = {
            "entity_name": graph.nodes[k].get("entity_name", k),
            "entity_type": graph.nodes[k].get("entity_type", "konsep"),
            "description": graph.nodes[k].get("description", ""),
            "__vector__": node_vecs[i].tolist()
        }

    vdb_path = os.path.join(WORKING_DIR, "vdb_entities.json")
    with open(vdb_path, "w", encoding="utf-8") as f:
        json.dump(vdb_entities, f, ensure_ascii=False, indent=2)

    total_duration = time.time() - start_time
    summary = {
        "timestamp": datetime.now().isoformat(),
        "llm_model": OLLAMA_MODEL,
        "embed_model": EMBEDDING_MODEL,
        "concurrency": CONCURRENCY,
        "total_chunks": total_chunks,
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "duration_seconds": round(total_duration, 2),
        "duration_minutes": round(total_duration / 60, 2),
    }
    with open(os.path.join(WORKING_DIR, "indexing_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("=" * 70)
    print(f"INDEXING SELESAI SUKSES DALAM {total_duration/60:.2f} MENIT ({total_duration:.2f} detik)!")
    print(f"Graf Kanonik Akhir: {graph.number_of_nodes()} Nodes, {graph.number_of_edges()} Edges.")
    print("=" * 70, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
