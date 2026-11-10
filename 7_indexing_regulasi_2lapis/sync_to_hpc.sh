#!/bin/bash
# ==============================================================================
# Script Sinkronisasi: Laptop/WSL -> HPC Mahoni01 (DGX A100)
# ==============================================================================
set -e

LOCAL_DIR="/home/chandreu/brin-2026/pengujian-komparasi-minirag/7_indexing_regulasi_2lapis/"
REMOTE_TARGET="mahoni01:~/projek-legal-rag/7_indexing_regulasi_2lapis/"

echo "=========================================================="
echo "SINKRONISASI KE HPC MAHONI01"
echo "Dari : $LOCAL_DIR"
echo "Ke   : $REMOTE_TARGET"
echo "=========================================================="

rsync -avzP --exclude '__pycache__' --exclude '*.pyc' \
    "$LOCAL_DIR" "$REMOTE_TARGET"

echo "=========================================================="
echo "[SUKSES] Seluruh file 7_indexing_regulasi_2lapis telah tersinkron ke HPC!"
echo "=========================================================="

