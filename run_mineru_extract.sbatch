#!/bin/bash
# ==============================================================================
# SLURM SBATCH: Ekstraksi MinerU UU 45/2009
# Cluster: BRIN MAHAMERU-AI (NVIDIA DGX A100)
# Partition: a100-short (1 GPU NVIDIA A100-SXM4-80GB)
# ==============================================================================
#SBATCH --job-name=mineru_v4
#SBATCH --output=mineru_%j.log
#SBATCH --error=mineru_%j.err
#SBATCH --partition=a100-short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=100G
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00

echo "=================================================================="
echo "Job ID         : $SLURM_JOB_ID"
echo "Compute Node   : $SLURMD_NODENAME"
echo "Start Time     : $(date)"
echo "CUDA Devices   : $CUDA_VISIBLE_DEVICES"
echo "=================================================================="

# 1. Muat Environment Conda
CONDA_DIR="$HOME/miniconda3"
if [ -d "$CONDA_DIR" ]; then
    source "$CONDA_DIR/etc/profile.d/conda.sh"
    conda activate minirag
else
    echo "[ERROR] Conda di $CONDA_DIR tidak ditemukan."
    exit 1
fi

echo "Python: $(which python)"
nvidia-smi

# Pastikan mineru dan pymupdf terinstall di environment conda minirag
pip show mineru >/dev/null 2>&1 || pip install "mineru[core]>=4.0.0" pymupdf

# 2. Pindah ke Folder Direktori Kerja Pengujian
if [ -n "$SLURM_SUBMIT_DIR" ]; then
    cd "$SLURM_SUBMIT_DIR"
else
    cd "$HOME/projek-legal-rag"
fi

echo "Direktori Kerja: $(pwd)"

# 3. Jalankan Ekstraksi MinerU & Hierarchical Legal Chunker
python extract_mineru_hpc.py --device cuda

echo "=================================================================="
echo "Selesai: $(date)"
echo "Hasil tersimpan di 1_dokumen_sumber/UU_Nomor_45_Tahun_2009/"
echo "=================================================================="
