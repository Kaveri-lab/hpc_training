#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[])
{
    int i, rank, nprocs, count, start, stop, nloops, total_nloops;

    MPI_Init(&argc, &argv);

    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &nprocs);

    // Total iterations = 1000
    count = 1000 / (nprocs - 1);   // divide only among three processes

    nloops = 0;

    if (rank != 0)
    {
        // Three processes (p1, p2, p3)

        start = (rank - 1) * count;
        stop  = start + count;

        for (i = start; i < stop; ++i)
        {
            ++nloops;
        }

        printf("Process %d performed %d iterations of the loop.\n",
               rank, nloops);

        MPI_Send(&nloops, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
    }
    else
    {
        // Master process (p0)

        total_nloops = 0;

        for (i = 1; i < nprocs; ++i)
        {
            MPI_Recv(&nloops, 1, MPI_INT, i, 0, MPI_COMM_WORLD, MPI_STATUS_>
            total_nloops += nloops;
        }

        // P0 performs remaining iterations
        nloops = 0;

        for (i = total_nloops; i < 1000; ++i)
        {
            ++nloops;
        }
        printf("Process 0 received total_nloops = %d\n", total_nloops);
        printf("Process 0 performed the remaining %d iterations of the loop>
               nloops);

    }

    MPI_Finalize();
    return 0;
}