#!/bin/bash
# ==============================================================================
# Script Tarik Hasil: HPC Mahoni01 (BRIN DGX A100) -> Lokal
# ==============================================================================
set -e

REMOTE_SOURCE="mahoni01:~/projek-legal-rag/8_unclos/"
LOCAL_DIR="/home/chandreu/brin-2026/pengujian-komparasi-minirag/8_unclos/"

echo "=========================================================="
echo "MENARIK HASIL EKSTRAKSI & TERJEMAHAN DARI HPC MAHONI01"
echo "Dari : $REMOTE_SOURCE"
echo "Ke   : $LOCAL_DIR"
echo "=========================================================="

rsync -avzP --exclude '__pycache__' --exclude '*.pyc' \
    "$REMOTE_SOURCE" "$LOCAL_DIR"

echo "=========================================================="
echo "[SUKSES] Hasil ekstraksi, terjemahan default, dan struktur pasal telah tersinkron ke lokal!"
echo "=========================================================="

