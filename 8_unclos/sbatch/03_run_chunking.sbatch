#!/bin/bash
# ==============================================================================
# SLURM SBATCH: Tahap 3 - Strukturisasi & Universal Legal Chunking UNCLOS 1982
# Cluster: BRIN MAHAMERU-AI
# Partition: a100-short
# ==============================================================================
#SBATCH --job-name=unclos_chunking
#SBATCH --partition=a100-short
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=unclos_chunking_%j.log
#SBATCH --error=unclos_chunking_%j.err

echo "=========================================================="
echo "Job ID       : $SLURM_JOB_ID"
echo "Compute Node : $(hostname)"
echo "Waktu Mulai  : $(date)"
echo "Tugas        : Tahap 3 - Universal Legal Chunking UNCLOS"
echo "=========================================================="

# 1. Pindah ke direktori proyek 8_unclos
cd $HOME/projek-legal-rag/8_unclos 2>/dev/null || cd "$SLURM_SUBMIT_DIR"
echo "Direktori Kerja: $(pwd)"

# 2. Path Python Conda Minirag Resmi
PYTHON_EXEC="$HOME/miniconda3/envs/minirag/bin/python"
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="$(which python3)"
fi
echo "Menggunakan Python: $PYTHON_EXEC"

# Pastikan dependensi tiktoken terpasang
$PYTHON_EXEC -c "import tiktoken" 2>/dev/null || $PYTHON_EXEC -m pip install tiktoken

# 3. Validasi Naskah Terjemahan
if [ ! -f "indonesiaversion/default/unclos_ID_default.md" ]; then
    echo "[ERROR] indonesiaversion/default/unclos_ID_default.md belum ada!"
    echo "        Jalankan Tahap 2 (02_run_translate.sbatch) terlebih dahulu."
    exit 1
fi

# 4. Jalankan Universal Chunker
$PYTHON_EXEC skrip/03_universal_chunk_unclos.py

echo "=========================================================="
echo "Selesai pada : $(date)"
echo "Hasil di     : $(pwd)/indonesiaversion/struktur_pasal/"
echo "=========================================================="
