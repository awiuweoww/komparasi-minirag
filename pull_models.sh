#!/usr/bin/env bash
# ==============================================================================
# Script Unduh Model Ollama (Gemma 4:12B & BGE-M3) menggunakan Port Terisolasi
# Cluster: BRIN MAHAMERU-AI (Login Node mahoni01)
# ==============================================================================

set -e

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BOLD="\033[1m"
NC="\033[0m"

echo -e "${BOLD}======================================================================${NC}"
echo -e "${BOLD}         UNDUH MODEL OLLAMA: GEMMA 4:12B & BGE-M3                    ${NC}"
echo -e "${BOLD}======================================================================${NC}"

OLLAMA_BIN=""
if [ -f "$HOME/projek-legal-rag/bin/ollama" ]; then
    OLLAMA_BIN="$HOME/projek-legal-rag/bin/ollama"
elif [ -f "$HOME/projek-legal-rag/ollama" ]; then
    OLLAMA_BIN="$HOME/projek-legal-rag/ollama"
else
    echo -e "${RED}[ERROR] Biner Ollama portabel tidak ditemukan di ~/projek-legal-rag/bin/ollama${NC}"
    exit 1
fi

MODELS_DIR="$HOME/projek-legal-rag/models"
mkdir -p "$MODELS_DIR"

PORT=11500
export OLLAMA_HOST="127.0.0.1:${PORT}"
export OLLAMA_MODELS="$MODELS_DIR"

echo -e "Target Folder Models : ${BOLD}$MODELS_DIR${NC}"
echo -e "Ollama Server Port   : ${BOLD}http://$OLLAMA_HOST${NC} (Port terisolasi v0.40.13)"

# 1. Jalankan Ollama Server v0.40.13 di port 11500 jika belum aktif
SERVER_STARTED=0
if ! curl -s "http://${OLLAMA_HOST}/api/version" >/dev/null 2>&1; then
    echo -e "\nMenjalankan server Ollama v0.40.13 di background..."
    "$OLLAMA_BIN" serve > /tmp/ollama_temp_${PORT}.log 2>&1 &
    SERVER_PID=$!
    SERVER_STARTED=1

    echo "Menunggu server siap..."
    for i in {1..30}; do
        if curl -s "http://${OLLAMA_HOST}/api/version" >/dev/null 2>&1; then
            echo -e "${GREEN}Server Ollama v0.40.13 siap pada percobaan ke-$i!${NC}"
            break
        fi
        sleep 1
    done
else
    echo -e "${GREEN}Server Ollama pada port $PORT sudah aktif.${NC}"
fi

# Tampilkan versi server yang aktif
ACTIVE_VER=$(curl -s "http://${OLLAMA_HOST}/api/version" | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "0.40.13")
echo -e "Versi Server Aktif: ${BOLD}$ACTIVE_VER${NC}"

# 2. Unduh Gemma 4:12B
echo -e "\n${BOLD}[1/2] Mengunduh LLM Gemma 4:12B (~7.4 GB)...${NC}"
"$OLLAMA_BIN" pull gemma4:12b

# 3. Unduh BGE-M3 Embedding
echo -e "\n${BOLD}[2/2] Mengunduh Embedding BGE-M3 (~1.2 GB)...${NC}"
"$OLLAMA_BIN" pull bge-m3:latest

# 4. Verifikasi Model
echo -e "\n${BOLD}Daftar Model yang Berhasil Terpasang di $MODELS_DIR:${NC}"
"$OLLAMA_BIN" list

# 5. Hentikan server temporer jika tadi dimulai oleh skrip ini
if [ $SERVER_STARTED -eq 1 ]; then
    echo -e "\nMenutup server temporer (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
fi

echo -e "\n${GREEN}${BOLD}======================================================================${NC}"
echo -e "${GREEN}${BOLD} SEMUA MODEL BERHASIL DIUNDUH DAN SIAP DIGUNAKAN DI DGX A100!       ${NC}"
echo -e "${GREEN}${BOLD}======================================================================${NC}"

