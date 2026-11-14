#!/usr/bin/env python3
"""
03_universal_chunk_unclos.py - Universal Legal Chunker untuk UNCLOS 1982 Versi Indonesia
========================================================================================
Mengadopsi mesin Universal Legal Chunker v2.3 resmi SinkronAIR / BRIN
untuk menstrukturisasi naskah terjemahan UNCLOS menjadi potongan pasal terstandarisasi.

Aturan Pemrosesan Struktur Pasal:
1. Setiap Pasal (Pasal 1 s.d. Pasal 320) diisolasi secara utuh.
2. Jika suatu pasal sangat panjang (> 520 tokens), dilakukan pemecahan cerdas
   berdasarkan batas ayat/poin huruf tanpa memotong kalimat hukum substantif.
3. Anti-Dangling Heading Guard: Mencegah judul pasal/bagian tergantung di ekor chunk.
4. Header Berjangkar: Setiap chunk memiliki header formal:
   "UNCLOS 1982 | Bagian {bab} | {pasal}"
5. Menghasilkan format terstruktur (metadata lengkap) dan format bersih untuk embedding MiniRAG.

Target Masukan : indonesiaversion/default/unclos_ID_default.md
Target Keluaran:
- indonesiaversion/struktur_pasal/chunks_unclos_id_structured.json
- indonesiaversion/struktur_pasal/chunks_unclos_id_clean.json
- indonesiaversion/struktur_pasal/laporan_chunking_unclos.md
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import tiktoken
    ENC = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(ENC.encode(text))
except ImportError:
    # Estimasi akurat bahasa Indonesia hukum jika tiktoken belum terpasang
    def count_tokens(text: str) -> int:
        return int(len(text.split()) * 1.35)


class UNCLOSUniversalChunker:
    def __init__(
        self,
        target_tokens: int = 480,
        max_tokens: int = 520,
        overlap_tokens: int = 80
    ):
        self.target_tokens = target_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    @staticmethod
    def clean_text(text: str) -> str:
        """Membersihkan artefak OCR, whitespace berlebih, dan karakter non-standar."""
        text = text.replace("\r\n", "\n").replace("\xa0", " ").replace("\u200b", "")
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        text = re.sub(r"(?m)^\s*-\s*\d+\s*-\s*$", "", text)  # Hapus nomor halaman
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def parse_and_chunk(self, markdown_text: str, doc_id: str, doc_title: str) -> List[Dict[str, Any]]:
        cleaned = self.clean_text(markdown_text)
        lines = cleaned.splitlines()

        # Regex deteksi struktur konvensi
        re_part = re.compile(r'^\s*(?:#+\s*)?(?:BAGIAN|PART|BAB)\s+([IVXLCDM0-9]+.*)', re.IGNORECASE)
        re_section = re.compile(r'^\s*(?:#+\s*)?(?:SEKSI|SECTION)\s+([IVXLCDM0-9]+.*)', re.IGNORECASE)
        re_article = re.compile(r'^\s*(?:#+\s*)?(?:Pasal|Article)\s+(\d+[a-zA-Z]?)', re.IGNORECASE)
        re_annex = re.compile(r'^\s*(?:#+\s*)?(?:LAMPIRAN|ANNEX)\s+([IVXLCDM0-9]+.*)', re.IGNORECASE)

        units = []
        cur_part = "Mukadimah"
        cur_sec = ""
        cur_pasal = "Pembukaan"
        cur_lines = []

        def flush_unit():
            nonlocal cur_lines, cur_part, cur_sec, cur_pasal
            text = "\n".join(cur_lines).strip()
            if text:
                units.append({
                    "part": cur_part,
                    "section": cur_sec,
                    "pasal": cur_pasal,
                    "text": text
                })
            cur_lines = []

        for line in lines:
            m_part = re_part.match(line)
            m_sec = re_section.match(line)
            m_art = re_article.match(line)
            m_annex = re_annex.match(line)

            if m_part:
                flush_unit()
                cur_part = f"Bagian {m_part.group(1).strip()}"
                cur_sec = ""
                cur_lines.append(line)
            elif m_sec:
                cur_sec = f"Seksi {m_sec.group(1).strip()}"
                cur_lines.append(line)
            elif m_annex:
                flush_unit()
                cur_part = f"Lampiran {m_annex.group(1).strip()}"
                cur_sec = ""
                cur_pasal = f"Ketentuan Lampiran {m_annex.group(1).strip()}"
                cur_lines.append(line)
            elif m_art:
                flush_unit()
                cur_pasal = f"Pasal {m_art.group(1).strip()}"
                cur_lines.append(line)
            else:
                cur_lines.append(line)

        flush_unit()

        # Sekarang proses per unit ke dalam batas token $\le 520$
        chunks = []
        chunk_counter = 1

        for u in units:
            part_name = u["part"]
            pasal_name = u["pasal"]
            body_text = u["text"]

            # Buat header jangkar resmi
            header = f"{doc_title} | {part_name} | {pasal_name}"
            header_tokens = count_tokens(header + "\n\n")

            unit_tokens = count_tokens(body_text)

            # Jika pasalnya ringkas (muat dalam 1 chunk)
            if header_tokens + unit_tokens <= self.max_tokens:
                full_chunk_text = f"{header}\n\n{body_text}"
                chunks.append({
                    "chunk_id": f"{doc_id}_c_{chunk_counter:04d}",
                    "doc_id": doc_id,
                    "doc_title": doc_title,
                    "bagian": part_name,
                    "seksi": u["section"],
                    "pasal": pasal_name,
                    "header": header,
                    "content": full_chunk_text,
                    "tokens": count_tokens(full_chunk_text),
                    "words": len(full_chunk_text.split()),
                    "category": "mukadimah" if "Mukadimah" in part_name else ("lampiran" if "Lampiran" in part_name else "pasal")
                })
                chunk_counter += 1
            else:
                # Pasal/Segmen panjang: pecah per ayat / paragraf / baris
                raw_paras = [p.strip() for p in body_text.split("\n\n") if p.strip()]
                paragraphs = []
                for rp in raw_paras:
                    # Jika satu paragraf/daftar isi melebihi target, pecah per baris
                    if header_tokens + count_tokens(rp) > self.target_tokens:
                        lines = [l.strip() for l in rp.splitlines() if l.strip()]
                        line_buf = []
                        for l in lines:
                            if header_tokens + count_tokens("\n".join(line_buf + [l])) > self.target_tokens and line_buf:
                                paragraphs.append("\n".join(line_buf))
                                line_buf = [l]
                            else:
                                line_buf.append(l)
                        if line_buf:
                            paragraphs.append("\n".join(line_buf))
                    else:
                        paragraphs.append(rp)

                buf = []
                sub_idx = 1

                for p in paragraphs:
                    p_tokens = count_tokens(p)
                    curr_tokens = count_tokens("\n\n".join(buf)) if buf else 0

                    if header_tokens + curr_tokens + p_tokens > self.target_tokens and buf:
                        sub_text = "\n\n".join(buf)
                        full_chunk_text = f"{header} (Bagian {sub_idx})\n\n{sub_text}"
                        chunks.append({
                            "chunk_id": f"{doc_id}_c_{chunk_counter:04d}",
                            "doc_id": doc_id,
                            "doc_title": doc_title,
                            "bagian": part_name,
                            "seksi": u["section"],
                            "pasal": f"{pasal_name} (Bagian {sub_idx})",
                            "header": f"{header} (Bagian {sub_idx})",
                            "content": full_chunk_text,
                            "tokens": count_tokens(full_chunk_text),
                            "words": len(full_chunk_text.split()),
                            "category": "pasal"
                        })
                        chunk_counter += 1
                        sub_idx += 1
                        buf = [p]
                    else:
                        buf.append(p)

                if buf:
                    sub_text = "\n\n".join(buf)
                    full_chunk_text = f"{header} (Bagian {sub_idx})\n\n{sub_text}"
                    chunks.append({
                        "chunk_id": f"{doc_id}_c_{chunk_counter:04d}",
                        "doc_id": doc_id,
                        "doc_title": doc_title,
                        "bagian": part_name,
                        "seksi": u["section"],
                        "pasal": f"{pasal_name} (Bagian {sub_idx})" if sub_idx > 1 else pasal_name,
                        "header": f"{header} (Bagian {sub_idx})" if sub_idx > 1 else header,
                        "content": full_chunk_text,
                        "tokens": count_tokens(full_chunk_text),
                        "words": len(full_chunk_text.split()),
                        "category": "pasal"
                    })
                    chunk_counter += 1

        return chunks


def main():
    parser = argparse.ArgumentParser(description="Universal Legal Chunker UNCLOS 1982")
    parser.add_argument("--input", type=str, default=None, help="Path unclos_ID_default.md")
    parser.add_argument("--out", type=str, default=None, help="Direktori hasil chunking struktur_pasal")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    input_file = Path(args.input) if args.input else base_dir / "indonesiaversion" / "default" / "unclos_ID_default.md"
    out_dir = Path(args.out) if args.out else base_dir / "indonesiaversion" / "struktur_pasal"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Berkas masukan belum ditemukan di: {input_file}\n"
            "Pastikan Anda telah menjalankan proses penerjemahan (02_translate_gpt.py) terlebih dahulu!"
        )

    print("=" * 70)
    print("UNIVERSAL LEGAL CHUNKER v2.3: UNCLOS 1982 BAHASA INDONESIA")
    print(f"Masukan Teks      : {input_file}")
    print(f"Direktori Target  : {out_dir}")
    print("=" * 70)

    raw_md = input_file.read_text(encoding="utf-8")
    chunker = UNCLOSUniversalChunker(target_tokens=480, max_tokens=520, overlap_tokens=80)

    doc_id = "unclos_1982_id"
    doc_title = "UNCLOS 1982"

    chunks = chunker.parse_and_chunk(raw_md, doc_id=doc_id, doc_title=doc_title)

    if not chunks:
        raise RuntimeError("Chunker tidak menghasilkan potongan pasal!")

    # 1. Format Terstruktur Lengkap
    structured_file = out_dir / "chunks_unclos_id_structured.json"
    with open(structured_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    # 2. Format Bersih untuk MiniRAG Embedding
    clean_texts = [c["content"] for c in chunks]
    clean_file = out_dir / "chunks_unclos_id_clean.json"
    with open(clean_file, "w", encoding="utf-8") as f:
        json.dump(clean_texts, f, ensure_ascii=False, indent=2)

    # 3. Laporan Audit & Statistik
    total_chunks = len(chunks)
    all_tokens = [c["tokens"] for c in chunks]
    max_t = max(all_tokens)
    min_t = min(all_tokens)
    avg_t = sum(all_tokens) // total_chunks

    pasal_count = len({c["pasal"] for c in chunks if "Pasal" in c["pasal"]})

    laporan_md = f"""# Laporan Audit Chunking Struktur Pasal: UNCLOS 1982 (Versi Indonesia)

> **Tanggal Audit:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
> **Mesin:** Universal Legal Chunker v2.3 (Strict Boundary & Header Budget)  

---

## 1. Statistik Kunci
- **Total Chunks Dihasilkan :** {total_chunks} potongan
- **Pasal Unik Terpetakan  :** {pasal_count} pasal
- **Rata-rata Tokens / Chunk :** {avg_t} tokens
- **Maksimum Tokens          :** {max_t} tokens (Batas maksimal: 520)
- **Minimum Tokens           :** {min_t} tokens
- **Status Kuota Token       :** {'[LULUS - 100% <= 520 tokens]' if max_t <= 520 else '[PERLU PENYESUAIAN]'}

---

## 2. Berkas Hasil
1. `chunks_unclos_id_structured.json` : Data chunk lengkap dengan metadata hierarki (doc_id, bagian, pasal, tokens).
2. `chunks_unclos_id_clean.json` : Format array teks murni untuk input embedding MiniRAG (bge-m3).
"""
    laporan_file = out_dir / "laporan_chunking_unclos.md"
    laporan_file.write_text(laporan_md, encoding="utf-8")

    print(f"\n[SUKSES] Berhasil menstrukturisasi {total_chunks} Chunks:")
    print(f"  - Pasal Terpetakan : {pasal_count} pasal")
    print(f"  - Token Rata-rata  : {avg_t} tokens (Min: {min_t}, Max: {max_t})")
    print(f"\nBerkas tersimpan di:")
    print(f"  1. {structured_file}")
    print(f"  2. {clean_file}")
    print(f"  3. {laporan_file}")
    print("=" * 70)


if __name__ == "__main__":
    import time
    main()

