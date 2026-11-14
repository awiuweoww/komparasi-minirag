#!/bin/bash
# ==============================================================================
# SLURM SBATCH: Tahap 2 - Penerjemahan UNCLOS 1982 Menggunakan GPT (gpt-5.4)
# Cluster: BRIN MAHAMERU-AI
# Partition: a100-short
# ==============================================================================
#SBATCH --job-name=unclos_translate
#SBATCH --partition=a100-short
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=unclos_translate_%j.log
#SBATCH --error=unclos_translate_%j.err

echo "=========================================================="
echo "Job ID       : $SLURM_JOB_ID"
echo "Compute Node : $(hostname)"
echo "Waktu Mulai  : $(date)"
echo "Tugas        : Tahap 2 - Penerjemahan UNCLOS GPT (gpt-5.4)"
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

# Pastikan dependensi httpx terpasang
$PYTHON_EXEC -c "import httpx" 2>/dev/null || $PYTHON_EXEC -m pip install httpx

# 3. Validasi Berkas Masukan & .env
if [ ! -f "hasilmineru/output.md" ]; then
    echo "[ERROR] Berkas hasilmineru/output.md belum ada! Jalankan 01_run_mineru.sbatch terlebih dahulu."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "[ERROR] Berkas .env tidak ditemukan di $(pwd)/.env!"
    exit 1
fi

# 4. Jalankan Skrip Penerjemahan GPT (unbuffered output)
$PYTHON_EXEC -u skrip/02_translate_gpt.py

echo "=========================================================="
echo "Selesai pada : $(date)"
echo "Hasil di     : $(pwd)/indonesiaversion/default/"
echo "=========================================================="
