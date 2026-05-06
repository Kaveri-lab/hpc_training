#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[])
{

    int rank, size;
    int value, total;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    value = rank * rank;

    MPI_Reduce(&value, &total, 1, MPI_INT,MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0)
    {
        printf("Total = %d\n", total);
    }

    MPI_Finalize();
    return 0;
}