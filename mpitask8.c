#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[]) {

    int rank, size;
    int m[4][4];
    int row[4];
    int lsum = 0;
    int tsum = 0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Ensure 4 processes
    if (size != 4) {
        if (rank == 0)
            printf("Please run with 4 processes.\n");
        MPI_Finalize();
        return 0;
    }

    // Rank 0 initializes the matrix
    if (rank == 0) {
        int value = 1;
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 4; j++) {
                m[i][j] = value++;
            }
        }
    }
    
    // Distribute one row (4 elements) to each process
    MPI_Scatter(m, 4, MPI_INT,
                row, 4, MPI_INT,
                0, MPI_COMM_WORLD);

    // Each process computes sum of its row
    for (int i = 0; i < 4; i++) {
        lsum += row[i];
    }

    printf("Process %d: Row Sum = %d\n", rank, lsum);

    // Reduce to compute total matrix sum
    MPI_Reduce(&lsum, &tsum, 1,
               MPI_INT, MPI_SUM,
               0, MPI_COMM_WORLD);

    // Rank 0 prints final result
    if (rank == 0) {
        printf("Total Matrix Sum = %d\n", tsum);
    }

    MPI_Finalize();
    return 0;
}