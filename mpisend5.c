#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[])
{

    int rank, size;
    int value, total = 0;
    int received;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    value = rank * rank;

    if (rank == 0) 
    {

        total = value;  // include its own value

        for (int i = 1; i < size; i++) 
        {
            MPI_Recv(&received, 1, MPI_INT, i, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            total += received;
        }

        printf("Total = %d\n", total);

    } 
    else 
    {

        MPI_Send(&value, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);

    }

    MPI_Finalize();
    return 0;
}