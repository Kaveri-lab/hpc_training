#!/bin/bash
#SBATCH --job-name=stream_run
#SBATCH --partition=caribou_node
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:10:00
#SBATCH --output=/home/kaveripk/Caribou/results/stream/%j/run.out
#SBATCH --error=/home/kaveripk/Caribou/results/stream/%j/run.err
mkdir -p /home/kaveripk/Caribou/results/stream/$SLURM_JOB_ID

module load intel/oneapi

echo "Job started at $(date) on $(hostname)"

echo "--- threads=8 iteration=1 ---"
export OMP_NUM_THREADS=8
/home/kaveripk/stream/stream_omp
echo "--- threads=8 iteration=2 ---"
export OMP_NUM_THREADS=8
/home/kaveripk/stream/stream_omp

echo "Job finished at $(date)"
