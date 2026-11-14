#!/bin/bash
# ==============================================================================
# Script Sinkronisasi: Lokal -> HPC Mahoni01 (BRIN DGX A100)
# ==============================================================================
set -e

LOCAL_DIR="/home/chandreu/brin-2026/pengujian-komparasi-minirag/8_unclos/"
REMOTE_TARGET="mahoni01:~/projek-legal-rag/8_unclos/"

echo "=========================================================="
echo "SINKRONISASI KE HPC MAHONI01: 8_UNCLOS"
echo "Dari : $LOCAL_DIR"
echo "Ke   : $REMOTE_TARGET"
echo "=========================================================="

rsync -avzP --exclude '__pycache__' --exclude '*.pyc' --exclude '*.log' --exclude '*.err' \
    "$LOCAL_DIR" "$REMOTE_TARGET"

echo "=========================================================="
echo "[SUKSES] Seluruh file 8_unclos telah tersinkron ke HPC!"
echo "Langkah selanjutnya di HPC (3 tahap manual):"
echo "  ssh mahoni01"
echo "  cd ~/projek-legal-rag/8_unclos"
echo "  1. sbatch sbatch/01_run_mineru.sbatch      (Tunggu sampai selesai)"
echo "  2. sbatch sbatch/02_run_translate.sbatch   (Tunggu sampai selesai)"
echo "  3. sbatch sbatch/03_run_chunking.sbatch    (Tunggu sampai selesai)"
echo "=========================================================="

