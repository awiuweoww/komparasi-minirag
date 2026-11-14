#!/usr/bin/env python3
"""
01_extract_mineru.py - Ekstraksi Dokumen UNCLOS 1982 Menggunakan MinerU v4 di HPC
================================================================================
Mengekstrak berkas PDF naskah bahasa Inggris UNCLOS (236 halaman) menjadi:
1. output.md          : Naskah teks lengkap dalam format Markdown
2. content_list.json  : Layout bounding box dan blok hierarki AST MinerU
3. origin.pdf         : Salinan berkas PDF asli terstandarisasi

Target Input : unclosraw/unclos_EN.pdf
Target Output: hasilmineru/
"""

import os
import sys
import time
import shutil
import argparse
import subprocess
from pathlib import Path

# Auto-re-exec ke python environment minirag jika terpanggil oleh python sistem lama
_CONDA_PY = os.path.expanduser("~/miniconda3/envs/minirag/bin/python")
if sys.version_info < (3, 8) and os.path.exists(_CONDA_PY) and sys.executable != _CONDA_PY:
    os.execv(_CONDA_PY, [_CONDA_PY] + sys.argv)


def find_mineru_binary() -> str:
    """Mendeteksi executable mineru-kit / magic-pdf di PATH conda atau virtualenv."""
    venv_bin = Path(sys.executable).parent
    candidates = [
        venv_bin / "mineru-kit",
        venv_bin / "magic-pdf",
        venv_bin / "mineru",
        shutil.which("mineru-kit"),
        shutil.which("magic-pdf"),
        shutil.which("mineru"),
    ]

    for cand in candidates:
        if cand and Path(cand).exists() and os.access(str(cand), os.X_OK):
            return str(cand)

    print("[WARNING] Executable mineru-kit / magic-pdf belum terdeteksi di PATH aktif.")
    print("          Mencoba instalasi dependensi mineru...")
    subprocess.run([sys.executable, "-m", "pip", "install", "mineru[core]>=4.0.0", "pymupdf"], check=False)
    bin_found = shutil.which("mineru-kit") or shutil.which("magic-pdf") or shutil.which("mineru")
    if bin_found:
        return bin_found

    raise RuntimeError(
        "Executable MinerU tidak ditemukan! Pastikan environment conda 'minirag' aktif "
        "dan jalankan: pip install 'mineru[core]>=4.0.0' pymupdf"
    )


def execute_mineru(pdf_path: Path, output_dir: Path, device: str = "cuda") -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    bin_path = find_mineru_binary()

    print("=" * 70)
    print("EKSTRAKSI MINERU V4: UNCLOS 1982 (ENGLISH VERSION)")
    print(f"Biner CLI        : {bin_path}")
    print(f"Berkas PDF       : {pdf_path}")
    print(f"Direktori Output : {output_dir}")
    print(f"Device Target    : {device.upper()}")
    print("=" * 70)

    sub_env = os.environ.copy()
    if device == "cuda":
        sub_env["CUDA_VISIBLE_DEVICES"] = os.getenv("CUDA_VISIBLE_DEVICES", "0")
        sub_env["MINERU_DEVICE_MODE"] = "cuda"
    else:
        sub_env["MINERU_DEVICE_MODE"] = "cpu"

    target_md = output_dir / "output.md"
    target_cl = output_dir / "content_list.json"

    # 1. Ekstraksi middle_json (layout & visual bounding box) jika belum ada
    if not target_cl.exists():
        print("\n[1/2] Menjalankan ekstraksi middle_json (AST & Bounding Box)...")
        cmd_json = [
            bin_path, "parse",
            str(pdf_path),
            "-o", str(output_dir),
            "-f", "middle_json",
            "--pages", "all",
            "--tier", "standard"
        ]
        t0 = time.time()
        res_json = subprocess.run(cmd_json, env=sub_env)
        if res_json.returncode != 0:
            print("[INFO] Fallback ke perintah magic-pdf...")
            subprocess.run(["magic-pdf", "-p", str(pdf_path), "-o", str(output_dir), "-m", "auto"], env=sub_env, check=False)
        print(f"[OK] Ekstraksi JSON selesai ({time.time() - t0:.2f} detik).")

    # 2. Ekstraksi markdown jika output.md belum ada
    if not target_md.exists():
        print("\n[2/2] Menjalankan ekstraksi naskah Markdown...")
        cmd_md = [
            bin_path, "parse",
            str(pdf_path),
            "-o", str(output_dir),
            "-f", "markdown",
            "--pages", "all",
            "--tier", "standard"
        ]
        t0 = time.time()
        res_md = subprocess.run(cmd_md, env=sub_env)
        if res_md.returncode != 0:
            print("[INFO] Fallback format markdown...")
            subprocess.run(["magic-pdf", "-p", str(pdf_path), "-o", str(output_dir), "-m", "auto"], env=sub_env, check=False)
        print(f"[OK] Ekstraksi Markdown selesai ({time.time() - t0:.2f} detik).")

    # 3. Normalisasi nama berkas agar berada persis di root hasilmineru/
    # MinerU sering kali membuat subfolder bernama unclos_EN/
    md_files = [f for f in output_dir.rglob("*.md") if f.name != "README.md"]
    cl_files = [f for f in output_dir.rglob("*.json") if "content_list" in f.name or "middle" in f.name]

    if md_files and not target_md.exists():
        shutil.copy2(md_files[0], target_md)
        print(f"[NORMALIZE] Menyalin markdown ke: {target_md}")

    if cl_files and not target_cl.exists():
        shutil.copy2(cl_files[0], target_cl)
        print(f"[NORMALIZE] Menyalin content_list ke: {target_cl}")

    target_pdf = output_dir / "origin.pdf"
    if pdf_path.exists() and not target_pdf.exists():
        shutil.copy2(pdf_path, target_pdf)

    print("\n" + "=" * 70)
    print("STATUS EKSTRAKSI MINERU:")
    print(f"  Markdown     : {'[ADA] ' + str(target_md) if target_md.exists() else '[BELUM TERBENTUK]'}")
    print(f"  Content List : {'[ADA] ' + str(target_cl) if target_cl.exists() else '[BELUM TERBENTUK]'}")
    print(f"  Origin PDF   : {'[ADA] ' + str(target_pdf) if target_pdf.exists() else '[BELUM TERBENTUK]'}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Ekstraksi Dokumen UNCLOS 1982 Menggunakan MinerU v4")
    parser.add_argument("--pdf", type=str, default=None, help="Path berkas PDF UNCLOS bahasa Inggris")
    parser.add_argument("--out", type=str, default=None, help="Direktori hasil ekstraksi MinerU")
    parser.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"], help="Perangkat komputasi")
    parser.add_argument("--skip-if-exists", action="store_true", help="Lewati ekstraksi jika output.md sudah ada")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    pdf_path = Path(args.pdf) if args.pdf else base_dir / "unclosraw" / "unclos_EN.pdf"
    output_dir = Path(args.out) if args.out else base_dir / "hasilmineru"

    if not pdf_path.exists():
        raise FileNotFoundError(f"Berkas PDF tidak ditemukan di: {pdf_path}")

    if args.skip_if_exists and (output_dir / "output.md").exists():
        print(f"[INFO] output.md sudah ada di {output_dir}. Melewati ekstraksi MinerU (--skip-if-exists).")
        return

    execute_mineru(pdf_path, output_dir, device=args.device)


if __name__ == "__main__":
    main()

