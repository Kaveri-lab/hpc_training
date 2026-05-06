#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[])
 {

    int rank, size;
    int svalue, rvalue;
    int next, prev;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    svalue = rank;

    next = (rank + 1) % size;
    prev = (rank - 1 + size) % size;

    // Send to next and receive from previous
    MPI_Sendrecv(&svalue, 1, MPI_INT, next, 0,
                 &rvalue, 1, MPI_INT, prev, 0,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);

    printf("Rank %d received %d\n", rank, rvalue);

    MPI_Finalize();
    return 0;
}