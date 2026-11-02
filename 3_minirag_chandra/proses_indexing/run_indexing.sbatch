#!/bin/bash
#SBATCH --job-name=minirag_gemma4_fast
#SBATCH --partition=a100-short
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --output=indexing_%j.log

echo "=========================================================="
echo "Job ID       : $SLURM_JOB_ID"
echo "Running on   : $(hostname)"
echo "Started at   : $(date)"
echo "=========================================================="

cd $HOME/projek-legal-rag/3_minirag_chandra/proses_indexing

unset SSL_CERT_FILE

# Konfigurasi Paralelisme GPU A100 (4 slot paralel murni)
export OLLAMA_HOST=0.0.0.0:11500
export OLLAMA_MODELS=$HOME/projek-legal-rag/models
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2

# Bersihkan instans lama jika ada
pkill -f "ollama serve" || true
sleep 1

echo "Menjalankan Ollama Server (4 Parallel Slots) di node $(hostname) port 11500..."
if [ -f "$HOME/projek-legal-rag/bin/ollama" ]; then
    $HOME/projek-legal-rag/bin/ollama serve > ollama_compute.log 2>&1 &
elif [ -f "$HOME/projek-legal-rag/ollama" ]; then
    $HOME/projek-legal-rag/ollama serve > ollama_compute.log 2>&1 &
fi

echo "Menunggu Ollama server siap..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:11500/api/version >/dev/null; then
        echo "Ollama server siap dalam $i detik!"
        break
    fi
    sleep 1
done

nvidia-smi

echo "Memulai Indexing MiniRAG UU 45/2009 (Concurrency: 4)..."
export OLLAMA_HOST=http://127.0.0.1:11500
export CONCURRENCY=4
export NUM_PREDICT=1024
export PYTHONUNBUFFERED=1

$HOME/miniconda3/envs/minirag/bin/python index_gemma4_fast.py

echo "Membersihkan Ollama background process..."
pkill -f "ollama serve" || true

echo "=========================================================="
echo "Indexing Selesai pada: $(date)"
echo "=========================================================="
