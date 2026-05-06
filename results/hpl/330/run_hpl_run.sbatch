#!/bin/bash
#SBATCH --job-name=hpl_run
#SBATCH --partition=caribou_node
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=2
#SBATCH --time=00:30:00
#SBATCH --output=/home/kaveripk/Caribou/results/hpl/%j/run.out
#SBATCH --error=/home/kaveripk/Caribou/results/hpl/%j/run.err
mkdir -p /home/kaveripk/Caribou/results/hpl/$SLURM_JOB_ID

module load aocc/4.2
module load aocl/4.2

echo "Job started at $(date) on $(hostname)"

echo "--- threads=2 iteration=1 ---"
export OMP_NUM_THREADS=2
cd /home/kaveripk/hpl-2.3/bin/aocc
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/aocc/xhpl
echo "--- threads=2 iteration=2 ---"
export OMP_NUM_THREADS=2
cd /home/kaveripk/hpl-2.3/bin/aocc
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/aocc/xhpl

echo "Job finished at $(date)"
