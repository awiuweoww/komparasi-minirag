#!/usr/bin/env python3
"""
Script Re-Chunking Standar MiniRAG (512 Token + Header Regulasi Kanonik)
Dokumen: UU Nomor 45 Tahun 2009 (Perikanan)
Sumber: output.md hasil ekstraksi otentik MinerU v4
Menyertakan kepala teks (UU Nomor 45 Tahun 2009 | Pasal X) sesuai arahan prompt kanonik mentor.
"""
import os
import sys
import json
import re
import tiktoken

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC_PATH = os.path.join(BASE_DIR, "1_dokumen_sumber", "UU_Nomor_45_Tahun_2009", "output.md")
OUT_DATA_PATH = os.path.join(BASE_DIR, "4_minirag_chandra_v2", "proses_indexing", "data", "chunks_uu_45_2009.json")
OUT_SOURCE_PATH = os.path.join(BASE_DIR, "1_dokumen_sumber", "chunks_uu_45_2009_512.json")

CHUNK_SIZE = 490
CHUNK_OVERLAP = 90

def clean_markdown_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n\s*-\s*\d+\s*-\s*\n", "\n", text)
    text = re.sub(r"www\.djpp\.depkumham\.go\.id[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Lembaran Negara Republik Indonesia[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def detect_article_label(text: str, current_state: str) -> str:
    """Melacak pasal aktif secara kontekstual."""
    is_penjelasan = "penjelasan" in current_state.lower() or "# penjelasan" in text.lower()
    m_pasal = re.search(r"(?:##\s*|Ketentuan\s+|Angka\s+\d+\s+)(Pasal\s+\d+[a-zA-Z]?)", text, re.IGNORECASE)
    
    if is_penjelasan:
        if m_pasal:
            return f"Penjelasan {m_pasal.group(1).title()}"
        return current_state if "penjelasan" in current_state.lower() else "Penjelasan Umum"
        
    if "menimbang" in text.lower() or "mengingat" in text.lower() or "memutuskan" in text.lower():
        if not m_pasal or "pasal 20" in text.lower():
            return "Pembukaan & Konsiderans"
            
    if m_pasal:
        return m_pasal.group(1).title()
        
    return current_state

def chunk_with_legal_headers(text: str, chunk_size: int = 490, overlap: int = 90):
    enc = tiktoken.get_encoding("cl100k_base")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    chunks = []
    curr_paras = []
    curr_tokens = 0
    current_pasal = "Pembukaan"
    
    for p in paragraphs:
        current_pasal = detect_article_label(p, current_pasal)
        p_tokens = len(enc.encode(p))
        
        # Jika satu paragraf sangat panjang (> 420 token), pecah per kalimat
        if p_tokens > 420:
            sentences = re.split(r"(?<=[.;])\s+", p)
            for s in sentences:
                s_tok = len(enc.encode(s))
                if curr_tokens + s_tok > chunk_size and curr_paras:
                    raw_chunk = "\n\n".join(curr_paras)
                    header = f"UU Nomor 45 Tahun 2009 | {current_pasal}\n\n"
                    full_content = header + raw_chunk
                    chunks.append({
                        "chunk_id": f"chunk-{len(chunks)+1:04d}",
                        "tokens": len(enc.encode(full_content)),
                        "pasal_ref": current_pasal,
                        "content": full_content
                    })
                    overlap_paras = []
                    overlap_toks = 0
                    for op in reversed(curr_paras):
                        ot = len(enc.encode(op))
                        if overlap_toks + ot <= overlap:
                            overlap_paras.insert(0, op)
                            overlap_toks += ot
                        else:
                            break
                    curr_paras = list(overlap_paras)
                    curr_tokens = overlap_toks
                curr_paras.append(s)
                curr_tokens += s_tok
        else:
            if curr_tokens + p_tokens > chunk_size and curr_paras:
                raw_chunk = "\n\n".join(curr_paras)
                header = f"UU Nomor 45 Tahun 2009 | {current_pasal}\n\n"
                full_content = header + raw_chunk
                chunks.append({
                    "chunk_id": f"chunk-{len(chunks)+1:04d}",
                    "tokens": len(enc.encode(full_content)),
                    "pasal_ref": current_pasal,
                    "content": full_content
                })
                overlap_paras = []
                overlap_toks = 0
                for op in reversed(curr_paras):
                    ot = len(enc.encode(op))
                    if overlap_toks + ot <= overlap:
                        overlap_paras.insert(0, op)
                        overlap_toks += ot
                    else:
                        break
                curr_paras = list(overlap_paras)
                curr_tokens = overlap_toks
            curr_paras.append(p)
            curr_tokens += p_tokens
            
    if curr_paras:
        raw_chunk = "\n\n".join(curr_paras)
        header = f"UU Nomor 45 Tahun 2009 | {current_pasal}\n\n"
        full_content = header + raw_chunk
        chunks.append({
            "chunk_id": f"chunk-{len(chunks)+1:04d}",
            "tokens": len(enc.encode(full_content)),
            "pasal_ref": current_pasal,
            "content": full_content
        })
        
    return chunks

def main():
    if not os.path.exists(DOC_PATH):
        print(f"Error: Dokumen {DOC_PATH} tidak ditemukan!")
        sys.exit(1)
        
    print(f"Membaca naskah resmi MinerU v4: {DOC_PATH} ...")
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()
        
    cleaned_text = clean_markdown_text(raw_text)
    chunks = chunk_with_legal_headers(cleaned_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    
    print(f"Berhasil menghasilkan: {len(chunks)} chunk (dengan kepala teks regulasi kanonik)")
    
    os.makedirs(os.path.dirname(OUT_DATA_PATH), exist_ok=True)
    with open(OUT_SOURCE_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Tersimpan di: {OUT_SOURCE_PATH}")
    
    with open(OUT_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Tersimpan di: {OUT_DATA_PATH}")

    token_lens = [c["tokens"] for c in chunks]
    word_lens = [len(c["content"].split()) for c in chunks]
    print("=" * 60)
    print(f"Statistik Chunking Boundary-Aware MiniRAG 512:")
    print(f"Total Chunks       : {len(chunks)}")
    print(f"Rata-rata Token    : {sum(token_lens)/len(token_lens):.1f} token (Min: {min(token_lens)}, Max: {max(token_lens)})")
    print(f"Rata-rata Kata     : {sum(word_lens)/len(word_lens):.1f} kata (Min: {min(word_lens)}, Max: {max(word_lens)})")
    print("=" * 60)

if __name__ == "__main__":
    main()
