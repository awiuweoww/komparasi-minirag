#!/bin/bash
#SBATCH --job-name=minirag_gemma4_fast
#SBATCH --partition=a100-short
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=100G
#SBATCH --output=indexing_%j.log

echo "=========================================================="
echo "Job ID       : $SLURM_JOB_ID"
echo "Running on   : $(hostname)"
echo "Started at   : $(date)"
echo "=========================================================="

cd $HOME/projek-legal-rag/4_minirag_chandra_v2/proses_indexing

unset SSL_CERT_FILE

# Alokasi Port Dinamis Berbasis SLURM Job ID (Anti-Collision 100%)
PORT=$((11600 + ($SLURM_JOB_ID % 1000)))
echo "Port Dinamis Ollama: $PORT"

export OLLAMA_HOST=0.0.0.0:$PORT
export OLLAMA_MODELS=$HOME/projek-legal-rag/models
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2

echo "Menjalankan Ollama Server (4 Parallel Slots) di node $(hostname) port $PORT..."
if [ -f "$HOME/projek-legal-rag/bin/ollama" ]; then
    $HOME/projek-legal-rag/bin/ollama serve > ollama_compute_${SLURM_JOB_ID}.log 2>&1 &
elif [ -f "$HOME/projek-legal-rag/ollama" ]; then
    $HOME/projek-legal-rag/ollama serve > ollama_compute_${SLURM_JOB_ID}.log 2>&1 &
fi
OLLAMA_PID=$!

echo "Menunggu Ollama server siap di port $PORT..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:$PORT/api/version >/dev/null; then
        echo "Ollama server siap dalam $i detik di port $PORT!"
        break
    fi
    sleep 1
done

nvidia-smi

echo "Memulai Indexing MiniRAG UU 45/2009 (Port: $PORT, Concurrency: 4)..."
export OLLAMA_HOST=http://127.0.0.1:$PORT
export CONCURRENCY=4
export NUM_PREDICT=3072
export PYTHONUNBUFFERED=1

$HOME/miniconda3/envs/minirag/bin/python index_gemma4_fast.py

echo "Membersihkan Ollama background process (PID: $OLLAMA_PID)..."
kill $OLLAMA_PID || true

echo "=========================================================="
echo "Indexing Selesai pada: $(date)"
echo "=========================================================="
