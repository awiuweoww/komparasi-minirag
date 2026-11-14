#!/bin/bash
# ==============================================================================
# SLURM SBATCH: Tahap 1 - Ekstraksi MinerU Dokumen UNCLOS 1982
# Cluster: BRIN MAHAMERU-AI (NVIDIA DGX A100)
# Partition: a100-short (1 GPU A100-SXM4-80GB)
# ==============================================================================
#SBATCH --job-name=unclos_mineru
#SBATCH --partition=a100-short
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=80G
#SBATCH --time=02:30:00
#SBATCH --output=unclos_mineru_%j.log
#SBATCH --error=unclos_mineru_%j.err

echo "=========================================================="
echo "Job ID       : $SLURM_JOB_ID"
echo "Compute Node : $(hostname)"
echo "Waktu Mulai  : $(date)"
echo "Tugas        : Tahap 1 - Ekstraksi MinerU UNCLOS 1982"
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

nvidia-smi

# 3. Jalankan Ekstraksi MinerU
$PYTHON_EXEC skrip/01_extract_mineru.py --device cuda

echo "=========================================================="
echo "Selesai pada : $(date)"
echo "Hasil di     : $(pwd)/hasilmineru/"
echo "=========================================================="
