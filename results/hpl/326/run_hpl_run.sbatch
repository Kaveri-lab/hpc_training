#!/bin/bash
#SBATCH --job-name=hpl_run
#SBATCH --partition=caribou_node
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --output=/home/kaveripk/Caribou/results/hpl/%j/run.out
#SBATCH --error=/home/kaveripk/Caribou/results/hpl/%j/run.err
mkdir -p /home/kaveripk/Caribou/results/hpl/$SLURM_JOB_ID

module load intel/oneapi

echo "Job started at $(date) on $(hostname)"

echo "--- threads=1 iteration=1 ---"
export OMP_NUM_THREADS=1
cd /home/kaveripk/hpl-2.3/bin/intel
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/intel/xhpl
echo "--- threads=1 iteration=2 ---"
export OMP_NUM_THREADS=1
cd /home/kaveripk/hpl-2.3/bin/intel
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/intel/xhpl
echo "--- threads=2 iteration=1 ---"
export OMP_NUM_THREADS=2
cd /home/kaveripk/hpl-2.3/bin/intel
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/intel/xhpl
echo "--- threads=2 iteration=2 ---"
export OMP_NUM_THREADS=2
cd /home/kaveripk/hpl-2.3/bin/intel
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/intel/xhpl
echo "--- threads=4 iteration=1 ---"
export OMP_NUM_THREADS=4
cd /home/kaveripk/hpl-2.3/bin/intel
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/intel/xhpl
echo "--- threads=4 iteration=2 ---"
export OMP_NUM_THREADS=4
cd /home/kaveripk/hpl-2.3/bin/intel
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/intel/xhpl
echo "--- threads=8 iteration=1 ---"
export OMP_NUM_THREADS=8
cd /home/kaveripk/hpl-2.3/bin/intel
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/intel/xhpl
echo "--- threads=8 iteration=2 ---"
export OMP_NUM_THREADS=8
cd /home/kaveripk/hpl-2.3/bin/intel
/opt/intel/oneapi/mpi/2021.17/bin/mpirun -np $SLURM_NTASKS /home/kaveripk/hpl-2.3/bin/intel/xhpl

echo "Job finished at $(date)"
