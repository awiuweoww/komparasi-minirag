#!/usr/bin/env python3
"""
Eksekusi Indexing Lapisan 2 MiniRAG untuk HPC / Server GPU:
- Model LLM: Gemma 4:12B via Ollama (think: false, num_ctx >= 16384)
- Prompt: prompt_indexing_layer2_uu-V3.py (resmi skema v1.2 JDIH BPK)
- Masukan: chunks_hasil_uu45_berjangkar.json (hanya mengekstrak chunk berjangkar lapisan2=True)
- Keluaran: storage_lapisan2_gemma4/graph_chunk_entity_relation.graphml, kv_store, vdb
"""

import os
import sys
import time
import json
import re
import asyncio
import httpx
import networkx as nx
from pathlib import Path

# Path konfigurasi modul
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Import prompt layer 2 v3
import importlib.util
spec = importlib.util.spec_from_file_location("prompt_v3", BASE_DIR / "prompt_indexing_layer2_uu-V3.py")
prompt_v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompt_v3)

PROMPTS = prompt_v3.PROMPTS
DEFAULT_TUPLE_DELIMITER = prompt_v3.DEFAULT_TUPLE_DELIMITER
DEFAULT_RECORD_DELIMITER = prompt_v3.DEFAULT_RECORD_DELIMITER
DEFAULT_COMPLETION_DELIMITER = prompt_v3.DEFAULT_COMPLETION_DELIMITER
DEFAULT_ENTITY_TYPES = prompt_v3.DEFAULT_ENTITY_TYPES
ALLOWED_ENTITY_TYPES = set(t.lower() for t in DEFAULT_ENTITY_TYPES)

# Environment variables untuk HPC
raw_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11500")
if not raw_host.startswith("http://") and not raw_host.startswith("https://"):
    raw_host = f"http://{raw_host}"
OLLAMA_HOST = raw_host.replace("0.0.0.0", "127.0.0.1")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:12b")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3:latest")
WORKING_DIR = os.getenv("WORKING_DIR", str(BASE_DIR.parent / "hasil" / "storage_lapisan2_gemma4"))
DATA_PATH = os.getenv("DATA_PATH", str(BASE_DIR.parent.parent / "3_persiapan_chunk_berjangkar" / "hasil" / "chunks_hasil_uu45_berjangkar.json"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "4"))
NUM_PREDICT = int(os.getenv("NUM_PREDICT", "3072"))


def extract_balanced_tuples(text: str) -> list[str]:
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
    entities = []
    relationships = []
    
    text = re.sub(r"```[a-zA-Z]*", "", raw_text)
    text = text.replace("<|SELESAI|>", "").replace("<|COMPLETE|>", "").replace("```", "")
    
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
            raw_type = parts[2].strip().lower() if len(parts) > 2 else "konsep"
            if raw_type not in ALLOWED_ENTITY_TYPES:
                raw_type = "konsep"
            desc = parts[3].strip() if len(parts) > 3 else ""
            entities.append({
                "name": raw_name,
                "type": raw_type,
                "description": desc
            })
            
        # 2. Format eksplisit relasi: ("relationship"<|>src<|>tgt<|>desc<|>kw<|>weight)
        elif lead in ("relationship", "hubungan", "relasi") and len(parts) >= 3:
            raw_src = parts[1].strip()
            raw_tgt = parts[2].strip()
            if not raw_src or not raw_tgt or raw_src == raw_tgt:
                continue
            desc = parts[3].strip() if len(parts) > 3 else ""
            keywords = parts[4].strip() if len(parts) > 4 else "hubungan norma"
            weight = 8.0
            if len(parts) > 5:
                try:
                    weight = float(re.sub(r"[^0-9.]", "", parts[5]))
                except ValueError:
                    weight = 8.0
            relationships.append({
                "src": raw_src,
                "tgt": raw_tgt,
                "description": desc,
                "keywords": keywords,
                "weight": weight
            })
            
    return entities, relationships


async def process_chunk(
    chunk_idx: int,
    total_chunks: int,
    chunk_data: dict,
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient
):
    chunk_id = chunk_data.get("chunk_id", f"chunk-{chunk_idx:04d}")
    pasal_ref = chunk_data.get("pasal_ref", "Umum")
    chunk_text = chunk_data.get("content", "")
    lapisan2 = chunk_data.get("lapisan2", True)
    
    # Aturan skema: abaikan chunk yang tidak memuat norma (pembukaan, konsiderans, peralihan, dll)
    if not lapisan2:
        return chunk_idx, chunk_id, pasal_ref, [], [], chunk_text, True

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
            "num_ctx": 16384
        }
        
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt_extract}],
            "stream": False,
            "options": options,
            "think": False
        }
        
        res = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=240.0)
        res.raise_for_status()
        msg_obj = res.json().get("message", {})
        content = msg_obj.get("content", "")
        thinking = msg_obj.get("thinking", "")
        
        full_text = content if content.strip() else thinking
        entities, relationships = parse_extracted_records(full_text)
        
        duration = time.time() - t0
        print(f"[{chunk_idx+1:03d}/{total_chunks:03d}] {chunk_id} ({pasal_ref[:20]:<20}) | Entitas: {len(entities):<2} | Relasi: {len(relationships):<2} | Durasi: {duration:5.2f}s", flush=True)
        return chunk_idx, chunk_id, pasal_ref, entities, relationships, chunk_text, False


async def main():
    print("=" * 70)
    print("INDEXING LAPISAN 2 MINIRAG: GEMMA 4:12B + PROMPT V3 BERJANGKAR")
    print(f"Ollama Host   : {OLLAMA_HOST}")
    print(f"LLM Model     : {OLLAMA_MODEL} (think: false, num_ctx >= 16384)")
    print(f"Concurrency   : {CONCURRENCY} parallel slots")
    print(f"Working Dir   : {WORKING_DIR}")
    print(f"Input Data    : {DATA_PATH}")
    print("=" * 70, flush=True)

    os.makedirs(WORKING_DIR, exist_ok=True)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    total_chunks = len(chunks)
    print(f"Total chunk dimuat: {total_chunks}")
    
    sem = asyncio.Semaphore(CONCURRENCY)
    timeout = httpx.Timeout(240.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [
            process_chunk(idx, total_chunks, c, sem, client)
            for idx, c in enumerate(chunks)
        ]
        results = await asyncio.gather(*tasks)

    # Konstruksi Graf Lapisan 2 (NetworkX MultiDiGraph / Graph)
    G = nx.Graph()
    all_chunks_kv = {}
    
    for idx, chunk_id, pasal_ref, entities, relationships, chunk_text, skipped in results:
        all_chunks_kv[chunk_id] = {
            "content": chunk_text,
            "pasal_ref": pasal_ref,
            "skipped": skipped
        }
        if skipped:
            continue
            
        for ent in entities:
            nm = ent["name"]
            if not G.has_node(nm):
                G.add_node(nm, entity_type=ent["type"], description=ent["description"], source_id=chunk_id)
            else:
                curr_desc = G.nodes[nm].get("description", "")
                if ent["description"] and ent["description"] not in curr_desc:
                    G.nodes[nm]["description"] = (curr_desc + " " + ent["description"]).strip()

        for rel in relationships:
            src, tgt = rel["src"], rel["tgt"]
            if not G.has_node(src):
                G.add_node(src, entity_type="konsep", description="", source_id=chunk_id)
            if not G.has_node(tgt):
                G.add_node(tgt, entity_type="konsep", description="", source_id=chunk_id)
            if not G.has_edge(src, tgt):
                G.add_edge(src, tgt, weight=rel["weight"], description=rel["description"], keywords=rel["keywords"], source_id=chunk_id)

    # Ekspor Graf Lapisan 2
    out_graphml = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
    nx.write_graphml(G, out_graphml)
    
    with open(os.path.join(WORKING_DIR, "kv_store_text_chunks.json"), "w", encoding="utf-8") as f:
        json.dump(all_chunks_kv, f, ensure_ascii=False, indent=2)

    summary = {
        "total_chunks": total_chunks,
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "node_types": dict(nx.get_node_attributes(G, "entity_type")),
        "waktu_selesai": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(os.path.join(WORKING_DIR, "indexing_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("INDEXING LAPISAN 2 SELESAI")
    print(f"Total Node Lapisan 2: {G.number_of_nodes()}")
    print(f"Total Edge Lapisan 2: {G.number_of_edges()}")
    print(f"Graf tersimpan di    : {out_graphml}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

