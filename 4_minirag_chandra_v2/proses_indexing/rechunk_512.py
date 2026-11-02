#!/usr/bin/env python3
"""
Script Re-Chunking Standar MiniRAG (512 Token + 100 Token Overlap)
Dokumen: UU Nomor 45 Tahun 2009 (Perikanan)
Sumber: output.md hasil ekstraksi otentik MinerU v4
"""
import os
import sys
import json
import re
import tiktoken

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC_PATH = os.path.join(BASE_DIR, "1_dokumen_sumber", "UU_Nomor_45_Tahun_2009", "output.md")
OUT_DATA_PATH = os.path.join(BASE_DIR, "3_minirag_chandra", "proses_indexing", "data", "chunks_uu_45_2009.json")
OUT_SOURCE_PATH = os.path.join(BASE_DIR, "1_dokumen_sumber", "chunks_uu_45_2009_512.json")

CHUNK_SIZE = 512
CHUNK_OVERLAP = 100

def clean_markdown_text(text: str) -> str:
    # 1. Normalisasi baris baru berlebih
    text = re.sub(r"\r\n", "\n", text)
    # 2. Hapus nomor halaman dan header/footer berulang
    text = re.sub(r"\n\s*-\s*\d+\s*-\s*\n", "\n", text)
    text = re.sub(r"www\.djpp\.depkumham\.go\.id[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Lembaran Negara Republik Indonesia[^\n]*", "", text, flags=re.IGNORECASE)
    # 3. Rapikan spasi ganda
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def chunk_by_tokens(text: str, chunk_size: int = 512, overlap: int = 100):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    total_tokens = len(tokens)
    
    print(f"Total token naskah UU 45/2009: {total_tokens} tokens")
    
    chunks = []
    step = chunk_size - overlap
    
    for i in range(0, total_tokens, step):
        chunk_token_slice = tokens[i:i + chunk_size]
        chunk_text = enc.decode(chunk_token_slice).strip()
        
        # Ekstrak nomor pasal nyata yang ada di dalam teks potongan ini
        pasal_matches = re.findall(r"(?:Pasal\s+\d+[a-zA-Z]?|BAB\s+[IVXLCDM]+)", chunk_text, re.IGNORECASE)
        pasal_list = list(dict.fromkeys([p.title() for p in pasal_matches]))
        pasal_ref = ", ".join(pasal_list[:3]) if pasal_list else "Ketentuan Umum"
        
        chunks.append({
            "chunk_id": f"chunk-{len(chunks)+1:04d}",
            "tokens": len(chunk_token_slice),
            "pasal_ref": pasal_ref,
            "content": chunk_text
        })
        
        if i + chunk_size >= total_tokens:
            break
            
    return chunks

def main():
    if not os.path.exists(DOC_PATH):
        print(f"Error: Dokumen {DOC_PATH} tidak ditemukan!")
        sys.exit(1)
        
    print(f"Membaca naskah resmi MinerU v4: {DOC_PATH} ...")
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()
        
    cleaned_text = clean_markdown_text(raw_text)
    chunks = chunk_by_tokens(cleaned_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    
    print(f"Berhasil menghasilkan: {len(chunks)} chunk (Ukuran: 512 token, Overlap: 100 token)")
    
    # Simpan format terstruktur lengkap
    os.makedirs(os.path.dirname(OUT_DATA_PATH), exist_ok=True)
    with open(OUT_SOURCE_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Tersimpan di: {OUT_SOURCE_PATH}")
    
    # Format kompatibel MiniRAG (list of dict dengan key 'content' dan 'pasal_ref')
    with open(OUT_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Tersimpan di: {OUT_DATA_PATH}")

    # Cetak statistik ringkas
    token_lens = [c["tokens"] for c in chunks]
    word_lens = [len(c["content"].split()) for c in chunks]
    print("=" * 60)
    print(f"Statistik Chunking MiniRAG 512:")
    print(f"Total Chunks       : {len(chunks)}")
    print(f"Rata-rata Token    : {sum(token_lens)/len(token_lens):.1f} token (Min: {min(token_lens)}, Max: {max(token_lens)})")
    print(f"Rata-rata Kata     : {sum(word_lens)/len(word_lens):.1f} kata (Min: {min(word_lens)}, Max: {max(word_lens)})")
    print("=" * 60)

if __name__ == "__main__":
    main()
