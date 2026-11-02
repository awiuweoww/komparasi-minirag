#!/usr/bin/env python3
from __future__ import annotations
"""
Ekstraksi Dokumen MinerU v4 & Hierarchical Legal Chunker
Dokumen: UU Nomor 45 Tahun 2009 tentang Perikanan
Kompatibel penuh dengan skema ekstraksi chatbot-regulasi-id & MiniRAG.
"""

import os
import sys

# Auto re-exec jika terpanggil oleh python sistem lama (< 3.8) di CentOS 7
_CONDA_PY = os.path.expanduser("~/miniconda3/envs/minirag/bin/python")
if sys.version_info < (3, 8) and os.path.exists(_CONDA_PY) and sys.executable != _CONDA_PY:
    os.execv(_CONDA_PY, [_CONDA_PY] + sys.argv)

import re
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

# ==============================================================================
# 1. HIERARCHICAL LEGAL CHUNKER (Resmi dari chatbot-regulasi-id)
# ==============================================================================

_NOISE_TYPES = {"header", "footer", "page_number", "page_footnote", "aside_text"}
_NOISE_TEXT_RE = re.compile(
    r"^\s*(?:-\s*\d+\s*-|\d+\s*/\s*\d+|PRESIDEN\s+REPUBLIK\s+INDONESIA\.?|.*\.{3,}|ttd\.?|DR\.\s+H\..*|PATRIALIS.*|LEMBARAN\s+NEGARA.*)\s*$",
    re.IGNORECASE,
)


def _union_box(a: Optional[Dict[str, float]], b: Dict[str, float]) -> Dict[str, float]:
    """Menggabungkan dua bounding box menjadi kotak terluar yang mencakup keduanya."""
    if not a:
        return dict(b)
    return {
        "l": min(a["l"], b["l"]),
        "t": min(a["t"], b["t"]),
        "r": max(a["r"], b["r"]),
        "b": max(a["b"], b["b"]),
    }


class LegalChunk:
    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        doc_title: str,
        pasal: str,
        bab: str,
        text: str,
        page: int = 1,
        box: Optional[Dict[str, float]] = None,
        category: str = "pasal",
        boxes: Optional[List[Dict[str, float]]] = None,
        doc_type: str = "regulasi",
    ):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.doc_title = doc_title
        self.pasal = pasal
        self.bab = bab
        self.text = text
        self.page = page
        self.box = box or {"l": 0.0, "t": 0.0, "r": 0.0, "b": 0.0}
        self.category = category
        self.boxes = boxes or []
        self.doc_type = doc_type

    def to_embedding_text(self) -> str:
        return f"{self.doc_title} | {self.bab} | {self.pasal}\n{self.text}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "pasal": self.pasal,
            "bab": self.bab,
            "text": self.text,
            "page": self.page,
            "box": self.box,
            "boxes": self.boxes,
            "category": self.category,
            "doc_type": self.doc_type,
            "words": len(self.text.split()),
        }


class HierarchicalLegalChunker:
    """
    Parser khusus dokumen perundangan Republik Indonesia.
    Memecah teks berdasarkan batas Pasal utuh, Bab, dan Penjelasan resmi.
    """

    BAB_PATTERN = re.compile(r'^(BAB\s+[IVXLCDM]+.*?)(?:\n|$)', re.IGNORECASE | re.MULTILINE)
    PASAL_HEADING_PATTERN = re.compile(
        r'^\s*(?:#+\s*)?(Pasal\s+\d+\s?[A-Za-z]?|PASAL\s+[IVXLCDM]+|\d+\.\s+(?:Ketentuan\s+Pasal|Pasal)\s+\d+[a-zA-Z]?)\b',
        re.IGNORECASE
    )
    PENJELASAN_PATTERN = re.compile(r'^\s*(?:#+\s*)?(?:TAMBAHAN\s+LEMBARAN\s+NEGARA.*?|PENJELASAN\s+ATAS.*?|PENJELASAN\b)', re.IGNORECASE)
    PASAL_DEMI_PASAL_PATTERN = re.compile(r'^\s*(?:#+\s*)?(?:II\.\s*)?PASAL\s+DEMI\s+PASAL\b', re.IGNORECASE)
    ANGKA_EXPLAIN_PATTERN = re.compile(r'^\s*(?:#+\s*)?(?:Angka|Pasal)\s+(\d+[a-zA-Z]?)\b', re.IGNORECASE)

    @staticmethod
    def _item_text(item: Dict[str, Any]) -> str:
        if "content" in item:
            c_val = item["content"]
            if isinstance(c_val, list):
                parts = []
                for sub in c_val:
                    if isinstance(sub, dict):
                        parts.append(str(sub.get("content") or sub.get("text") or ""))
                    elif isinstance(sub, str):
                        parts.append(sub)
                extracted = "\n".join(p.strip() for p in parts if p.strip()).strip()
                if extracted:
                    return extracted
            elif isinstance(c_val, str) and c_val.strip():
                return c_val.strip()

        return (item.get("text") or "").strip()

    @staticmethod
    def _item_box(item: Dict[str, Any]) -> Optional[Dict[str, float]]:
        raw = item.get("bbox")
        if raw and isinstance(raw, (list, tuple)) and len(raw) == 4:
            try:
                return {"l": float(raw[0]), "t": float(raw[1]), "r": float(raw[2]), "b": float(raw[3])}
            except (TypeError, ValueError):
                return None
        return None

    @classmethod
    def chunk_mineru_content_list(
        cls,
        content_list_json_path: Path,
        doc_id: str,
        doc_title: str
    ) -> List[LegalChunk]:
        if not content_list_json_path.exists():
            return []

        with open(content_list_json_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        # Normalisasi schema MinerU v4: {"pages": [{"page_idx": 0, "blocks": [...]}]}
        if isinstance(items, dict) and "pages" in items:
            flattened = []
            for p_info in items.get("pages", []):
                p_idx = p_info.get("page_idx", 0)
                for blk in p_info.get("blocks", []):
                    blk_item = dict(blk)
                    blk_item["page_idx"] = p_idx
                    flattened.append(blk_item)
            items = flattened

        if not isinstance(items, list):
            return []

        chunks: List[LegalChunk] = []
        state: Dict[str, Any] = {
            "bab": "Ketentuan Umum",
            "pasal": "Pembukaan",
            "texts": [],
            "heading_box": None,
            "page_boxes": {},
        }
        chunk_idx = 0
        in_penjelasan = False

        def flush() -> None:
            nonlocal chunk_idx
            if not state["texts"]:
                return
            text = "\n".join(state["texts"]).strip()
            if len(text) < 15:
                state["texts"], state["page_boxes"], state["heading_box"] = [], {}, None
                return

            pages_sorted = sorted(state["page_boxes"].keys())
            boxes = [{"page": p, **state["page_boxes"][p]} for p in pages_sorted]
            first_page = pages_sorted[0] if pages_sorted else 1
            chunk_idx += 1
            chunk_box = state.get("heading_box") or state["page_boxes"].get(first_page)

            chunks.append(LegalChunk(
                chunk_id=f"{doc_id}_c_{chunk_idx:03d}",
                doc_id=doc_id,
                doc_title=doc_title,
                pasal=state["pasal"],
                bab=state["bab"],
                text=text,
                page=first_page,
                box=chunk_box,
                boxes=boxes,
                category="penjelasan" if in_penjelasan else "pasal",
                doc_type="regulasi",
            ))
            state["texts"], state["page_boxes"], state["heading_box"] = [], {}, None

        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("type", "") in _NOISE_TYPES:
                continue

            text = cls._item_text(item)
            if not text or _NOISE_TEXT_RE.match(text):
                continue

            page = int(item.get("page_idx", 0)) + 1
            box = cls._item_box(item)
            first_line = text.split("\n", 1)[0].strip()

            # Deteksi bagian penjelasan
            if cls.PENJELASAN_PATTERN.search(first_line):
                flush()
                in_penjelasan = True
                state["bab"] = "Penjelasan Resmi"
                state["pasal"] = "Penjelasan Umum"
                state["heading_box"] = dict(box) if box else None
                state["texts"].append(text)
                if box:
                    state["page_boxes"][page] = _union_box(state["page_boxes"].get(page), box)
                continue

            if in_penjelasan:
                if cls.PASAL_DEMI_PASAL_PATTERN.search(first_line):
                    flush()
                    state["pasal"] = "Penjelasan Pasal demi Pasal"
                    state["heading_box"] = dict(box) if box else None
                else:
                    m_angka = cls.ANGKA_EXPLAIN_PATTERN.search(first_line)
                    if m_angka:
                        flush()
                        state["pasal"] = f"Penjelasan {m_angka.group(0).strip()}"
                        state["heading_box"] = dict(box) if box else None
            else:
                m_bab = cls.BAB_PATTERN.search(first_line)
                if m_bab:
                    state["bab"] = m_bab.group(1).strip()

                m_pasal = cls.PASAL_HEADING_PATTERN.search(first_line)
                if m_pasal:
                    flush()
                    state["pasal"] = m_pasal.group(1).strip()
                    state["heading_box"] = dict(box) if box else None

            state["texts"].append(text)
            if box:
                state["page_boxes"][page] = _union_box(state["page_boxes"].get(page), box)

        flush()
        return chunks


# ==============================================================================
# 2. RUNNER CLI MINERU
# ==============================================================================

def execute_mineru_v4(pdf_path: Path, output_dir: Path, device: str = "cuda") -> Path:
    """Mengeksekusi parsing MinerU v4 standar, menghasilkan content_list.json, output.md, origin.pdf."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Cari binary mineru
    venv_bin = Path(sys.executable).parent
    candidates = [
        venv_bin / "mineru-kit",
        venv_bin / "magic-pdf",
        venv_bin / "mineru",
        shutil.which("mineru-kit"),
        shutil.which("magic-pdf"),
        shutil.which("mineru"),
    ]

    selected_bin = None
    for cand in candidates:
        if cand and Path(cand).exists() and os.access(str(cand), os.X_OK):
            selected_bin = str(cand)
            break

    if not selected_bin:
        print("[WARNING] Executable mineru-kit / magic-pdf belum terpasang di PATH conda.")
        print("          Mencoba instalasi otomatis 'mineru[core]' ke environment...")
        subprocess.run([sys.executable, "-m", "pip", "install", "mineru[core]>=4.0.0", "pymupdf"], check=False)
        selected_bin = shutil.which("mineru-kit") or shutil.which("mineru")

    if not selected_bin:
        raise RuntimeError("Tidak dapat menemukan atau menginstal mineru-kit. Mohon jalankan: pip install 'mineru[core]>=4.0.0'")

    print(f"[MINERU] Menggunakan binary: {selected_bin}")
    print(f"[MINERU] Mengekstrak dokumen: {pdf_path}")
    print(f"[MINERU] Target output   : {output_dir}")

    sub_env = os.environ.copy()
    if device == "cuda":
        sub_env["CUDA_VISIBLE_DEVICES"] = "0"
        sub_env["MINERU_DEVICE_MODE"] = "cuda"
    else:
        sub_env["MINERU_DEVICE_MODE"] = "cpu"

    # 1. Jalankan ekstraksi middle_json jika content_list.json belum ada
    target_cl = output_dir / "content_list.json"
    if not target_cl.exists():
        print(f"[MINERU] Menghasilkan middle_json (layout & visual bounding box)...")
        cmd_json = [selected_bin, "parse", str(pdf_path), "-o", str(output_dir), "-f", "middle_json", "--pages", "all", "--tier", "standard"]
        t0 = time.time()
        subprocess.run(cmd_json, env=sub_env)
        print(f"[MINERU] Ekstraksi JSON selesai ({time.time() - t0:.2f}s).")

    # 2. Jalankan ekstraksi markdown jika output.md belum ada
    target_md = output_dir / "output.md"
    if not target_md.exists():
        print(f"[MINERU] Menghasilkan naskah markdown...")
        cmd_md = [selected_bin, "parse", str(pdf_path), "-o", str(output_dir), "-f", "markdown", "--pages", "all", "--tier", "standard"]
        t0 = time.time()
        subprocess.run(cmd_md, env=sub_env)
        print(f"[MINERU] Ekstraksi Markdown selesai ({time.time() - t0:.2f}s).")

    # Normalisasi berkas output MinerU agar terstandarisasi:
    # content_list.json, output.md, origin.pdf
    md_files = list(output_dir.rglob("*.md"))
    cl_files = [f for f in output_dir.rglob("*.json") if f.name != "chunks_uu_45_2009.json" and f.name != "chunks_uu_45_2009_structured.json"]

    if cl_files and not target_cl.exists():
        shutil.copy2(cl_files[0], target_cl)

    if md_files and not target_md.exists():
        shutil.copy2(md_files[0], target_md)

    if pdf_path.exists() and not (output_dir / "origin.pdf").exists():
        shutil.copy2(pdf_path, output_dir / "origin.pdf")

    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Ekstraksi Dokumen MinerU v4 & Hierarchical Legal Chunker")
    parser.add_argument("--pdf", type=str, default="1_dokumen_sumber/UU Nomor 45 Tahun 2009.pdf", help="Path berkas PDF")
    parser.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"], help="Hardware device (cuda/cpu)")
    parser.add_argument("--skip-cli", action="store_true", help="Lewati CLI mineru jika content_list.json sudah ada")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent
    if root_dir.name == "proses_indexing":
        root_dir = root_dir.parent.parent

    doc_sumber_dir = root_dir / "1_dokumen_sumber"
    mineru_out_dir = doc_sumber_dir / "UU_Nomor_45_Tahun_2009"
    proses_data_dir = root_dir / "3_minirag_chandra" / "proses_indexing" / "data"
    proses_data_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = Path(args.pdf)
    if not pdf_path.is_absolute():
        pdf_path = root_dir / pdf_path
    if not pdf_path.exists():
        pdf_path = doc_sumber_dir / "UU Nomor 45 Tahun 2009.pdf"

    print("=" * 70)
    print("EKSTRAKSI MINERU V4 & HIERARCHICAL LEGAL CHUNKER: UU 45/2009")
    print(f"PDF Sumber       : {pdf_path}")
    print(f"Output Ekstraksi : {mineru_out_dir}")
    print("=" * 70)

    content_list_file = mineru_out_dir / "content_list.json"
    if not content_list_file.exists():
        cl_cand = list(doc_sumber_dir.rglob("*content_list*.json"))
        if cl_cand:
            content_list_file = cl_cand[0]

    if not args.skip_cli or not content_list_file.exists():
        execute_mineru_v4(pdf_path, mineru_out_dir, device=args.device)
        content_list_file = mineru_out_dir / "content_list.json"

    if not content_list_file.exists():
        raise FileNotFoundError(f"Berkas content_list.json tidak ditemukan di {mineru_out_dir}")

    print(f"\n[CHUNKER] Memproses berkas MinerU otentik: {content_list_file}")
    chunks = HierarchicalLegalChunker.chunk_mineru_content_list(
        content_list_json_path=content_list_file,
        doc_id="uu_45_2009",
        doc_title="UU Nomor 45 Tahun 2009"
    )

    if not chunks:
        raise RuntimeError("Chunker tidak menghasilkan potongan pasal dari content_list.json")

    # Format teks murni untuk MiniRAG (Array of string)
    clean_texts = [c.to_embedding_text() for c in chunks]
    # Format terstruktur dengan visual bounding box
    structured_data = [c.to_dict() for c in chunks]

    # Simpan ke target
    out_txt_1 = doc_sumber_dir / "chunks_uu_45_2009.json"
    out_txt_2 = proses_data_dir / "chunks_uu_45_2009.json"
    out_struct = mineru_out_dir / "chunks_uu_45_2009_structured.json"

    with open(out_txt_1, "w", encoding="utf-8") as f:
        json.dump(clean_texts, f, ensure_ascii=False, indent=2)
    with open(out_txt_2, "w", encoding="utf-8") as f:
        json.dump(clean_texts, f, ensure_ascii=False, indent=2)
    with open(out_struct, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)

    total_words = sum(c.get("words", 0) for c in structured_data)
    avg_words = total_words // len(chunks) if chunks else 0

    print(f"\n[SUKSES] Menghasilkan {len(chunks)} Chunk Berbasis Pasal:")
    print(f"  - Batang Tubuh : {sum(1 for c in structured_data if c['category'] == 'pasal')} pasal")
    print(f"  - Penjelasan   : {sum(1 for c in structured_data if c['category'] == 'penjelasan')} bagian")
    print(f"  - Rata-rata    : {avg_words} kata per chunk")
    print(f"\n[BERKAS DISIMPAN]:")
    print(f"  1. {mineru_out_dir / 'content_list.json'}")
    print(f"  2. {mineru_out_dir / 'output.md'}")
    print(f"  3. {mineru_out_dir / 'origin.pdf'}")
    print(f"  4. {out_txt_1}")
    print(f"  5. {out_txt_2}")
    print("=" * 70)
    print("Perintah untuk menyalin hasil ekstraksi ke laptop Anda:")
    print("rsync -avzP csupriatna@mahoni01:~/projek-legal-rag/1_dokumen_sumber/ /home/chandreu/brin-2026/pengujian-komparasi-minirag/1_dokumen_sumber/")
    print("=" * 70)


if __name__ == "__main__":
    main()
