#!/bin/bash
# ==============================================================================
# Script Sinkronisasi: HPC Mahoni01 (DGX A100) -> Laptop/WSL
# ==============================================================================
set -e

REMOTE_SRC="mahoni01:~/projek-legal-rag/7_indexing_regulasi_2lapis/"
LOCAL_TARGET="/home/chandreu/brin-2026/pengujian-komparasi-minirag/7_indexing_regulasi_2lapis/"

echo "=========================================================="
echo "SINKRONISASI HASIL DARI HPC MAHONI01 KE LAPTOP"
echo "Dari : $REMOTE_SRC"
echo "Ke   : $LOCAL_TARGET"
echo "=========================================================="

rsync -avzP --exclude '__pycache__' --exclude '*.pyc' \
    "$REMOTE_SRC" "$LOCAL_TARGET"

echo "=========================================================="
echo "[SUKSES] Seluruh hasil eksekusi dari HPC tersalin kembali ke laptop!"
echo "=========================================================="

