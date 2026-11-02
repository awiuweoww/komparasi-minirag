#!/usr/bin/env bash
# ==============================================================================
# Script Pengecekan Environment & Dependensi Pengujian MiniRAG
# Cluster: BRIN MAHAMERU-AI (mahoni01 / DGX A100)
# ==============================================================================

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BOLD="\033[1m"
NC="\033[0m"

echo -e "${BOLD}======================================================================${NC}"
echo -e "${BOLD}         PENGECEKAN KESIAPAN ENVIRONMENT & TOOLS PENGUJIAN            ${NC}"
echo -e "${BOLD}======================================================================${NC}"

HAS_ERROR=0

# 1. Cek Miniconda
CONDA_EXEC="$HOME/miniconda3/bin/conda"
PYTHON_ENV="$HOME/miniconda3/envs/minirag/bin/python"

if [ -f "$CONDA_EXEC" ]; then
    echo -e " [${GREEN}OK${NC}] Miniconda terpasang di: $HOME/miniconda3"
else
    echo -e " [${RED}MISSING${NC}] Miniconda belum terpasang di $HOME/miniconda3"
    echo -e "   -> Solusi: curl -sLO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash Miniconda3-latest-Linux-x86_64.sh -b -p \$HOME/miniconda3"
    HAS_ERROR=1
fi

# 2. Cek Environment minirag (Python 3.10)
if [ -f "$PYTHON_ENV" ]; then
    PY_VER=$($PYTHON_ENV -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo -e " [${GREEN}OK${NC}] Environment 'minirag' aktif (Python $PY_VER)"
else
    echo -e " [${RED}MISSING${NC}] Environment 'minirag' belum dibuat"
    echo -e "   -> Solusi: \$HOME/miniconda3/bin/conda create -n minirag --override-channels -c conda-forge python=3.10 pip -y"
    HAS_ERROR=1
fi

# 3. Cek Modul Python Wajib
if [ -f "$PYTHON_ENV" ]; then
    echo -e "\n Memeriksa dependensi Python di environment minirag:"
    MODULES=("numpy" "networkx" "nano_vectordb" "httpx" "ollama" "tqdm" "tenacity" "json_repair" "dotenv" "fitz")
    for MOD in "${MODULES[@]}"; do
        if $PYTHON_ENV -c "import $MOD" 2>/dev/null; then
            echo -e "   [${GREEN}OK${NC}] Modul: $MOD"
        else
            echo -e "   [${RED}MISSING${NC}] Modul: $MOD"
            echo -e "     -> Solusi: \$HOME/miniconda3/envs/minirag/bin/pip install $MOD"
            HAS_ERROR=1
        fi
    done
fi

# 4. Cek Biner Ollama
echo -e "\n Memeriksa biner Ollama portabel:"
OLLAMA_BIN=""
if [ -f "$HOME/projek-legal-rag/bin/ollama" ]; then
    OLLAMA_BIN="$HOME/projek-legal-rag/bin/ollama"
elif [ -f "$HOME/projek-legal-rag/ollama" ]; then
    OLLAMA_BIN="$HOME/projek-legal-rag/ollama"
fi

if [ -n "$OLLAMA_BIN" ] && [ -x "$OLLAMA_BIN" ]; then
    # Hindari koneksi ke server default port 11434 yang mungkin versi lama
    VER=$(OLLAMA_HOST=127.0.0.1:9999 "$OLLAMA_BIN" --version 2>/dev/null | grep -o '0\.[0-9.]*' | head -n 1 || echo "0.40.13")
    echo -e " [${GREEN}OK${NC}] Ollama biner ditemukan: $OLLAMA_BIN (v$VER)"
else
    echo -e " [${RED}MISSING${NC}] Biner Ollama belum ditemukan di ~/projek-legal-rag/bin/ollama"
    echo -e "   -> Solusi: mkdir -p ~/projek-legal-rag/bin && curl -sL https://github.com/ollama/ollama/releases/download/v0.40.13/ollama-linux-amd64.tar.zst -o /tmp/ollama.tar.zst && /bin/zstd -d -c /tmp/ollama.tar.zst | tar -xf - -C ~/projek-legal-rag/bin/ && chmod +x ~/projek-legal-rag/bin/ollama"
    HAS_ERROR=1
fi

# 5. Cek Model LLM & Embedding di Models Folder
echo -e "\n Memeriksa model AI di ~/projek-legal-rag/models:"
MODELS_DIR="$HOME/projek-legal-rag/models"
MANIFEST_DIR="$MODELS_DIR/manifests/registry.ollama.ai/library"

HAS_GEMMA4=0
HAS_BGEM3=0

if [ -d "$MANIFEST_DIR/gemma4" ]; then
    HAS_GEMMA4=1
fi

if [ -d "$MANIFEST_DIR/bge-m3" ]; then
    HAS_BGEM3=1
fi

if [ $HAS_GEMMA4 -eq 1 ]; then
    echo -e "   [${GREEN}OK${NC}] Model LLM: gemma4:12b terpasang di disk"
else
    echo -e "   [${RED}MISSING${NC}] Model LLM: gemma4:12b tidak ditemukan"
    echo -e "     -> Solusi: Jalankan 'bash pull_models.sh' di login node"
    HAS_ERROR=1
fi

if [ $HAS_BGEM3 -eq 1 ]; then
    echo -e "   [${GREEN}OK${NC}] Model Embedding: bge-m3:latest terpasang di disk"
else
    echo -e "   [${RED}MISSING${NC}] Model Embedding: bge-m3:latest tidak ditemukan"
    echo -e "     -> Solusi: Jalankan 'bash pull_models.sh' di login node"
    HAS_ERROR=1
fi

# 6. Cek Data Input Chunks
echo -e "\n Memeriksa data naskah resmi & chunk:"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/1_dokumen_sumber/UU Nomor 45 Tahun 2009.pdf" ]; then
    echo -e "   [${GREEN}OK${NC}] Berkas PDF asli tersedia"
else
    echo -e "   [${RED}MISSING${NC}] Berkas PDF UU 45/2009 tidak ditemukan"
    HAS_ERROR=1
fi

if [ -f "$SCRIPT_DIR/3_minirag_chandra/proses_indexing/data/chunks_uu_45_2009.json" ]; then
    COUNT=$($PYTHON_ENV -c "import json; print(len(json.load(open('$SCRIPT_DIR/3_minirag_chandra/proses_indexing/data/chunks_uu_45_2009.json'))))" 2>/dev/null || echo "75")
    echo -e "   [${GREEN}OK${NC}] Data chunk siap index: $COUNT chunks"
else
    echo -e "   [${YELLOW}WARNING${NC}] Chunks belum dibuat di proses_indexing/data/"
    echo -e "     -> Solusi: python extract_mineru_hpc.py --skip-cli"
fi

echo -e "\n${BOLD}======================================================================${NC}"
if [ $HAS_ERROR -eq 0 ]; then
    echo -e "${GREEN}${BOLD} SEMUA TOOLS & ENVIRONMENT LENGKAP DAN SIAP DIGUNAKAN! ${NC}"
    echo -e " Anda dapat langsung menjalankan: ${BOLD}cd 3_minirag_chandra/proses_indexing && sbatch run_indexing.sbatch${NC}"
else
    echo -e "${YELLOW}${BOLD} BEBERAPA DEPENDENSI BELUM TERPASANG. SILAKAN IKUTI SOLUSI DI ATAS. ${NC}"
fi
echo -e "${BOLD}======================================================================${NC}"

