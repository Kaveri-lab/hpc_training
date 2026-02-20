#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[])
{
    int rank, size;
    int arr[8];
    int lsum = 0;

    MPI_Init(&argc, &argv);

    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Rank 0 initializes array
    if (rank == 0)
   {
        int temp[8] = {1,2,3,4,5,6,7,8};
        for (int i = 0; i < 8; i++)
        {
            arr[i] = temp[i];
        }
        printf("Rank 0 initialized the array.\n");
    }

    // Broadcast array to all processes
    MPI_Bcast(arr, 8, MPI_INT, 0, MPI_COMM_WORLD);

    // Each process computes local sum
    for (int i = 0; i < 8; i++)
   {
        lsum += arr[i];
    }

    printf("Process %d: Local Sum = %d\n", rank, lsum);

    MPI_Finalize();
    return 0;
}