#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

int main(int argc, char *argv[]) {

    int rank, size;
    int N;
    int *data = NULL;
    int l_n;
    int *l_data;
    int l_sum = 0, g_sum = 0;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Rank 0 reads N number of elements
    if (rank == 0) {
        printf("Enter total number of elements (N): ");
        scanf("%d", &N);
    }

    // Broadcast N to all processes
    MPI_Bcast(&N, 1, MPI_INT, 0, MPI_COMM_WORLD);

    l_n = N / size;  // elements per process

    l_data = (int*) malloc(l_n * sizeof(int));

    // Rank 0 allocates and reads data
    if (rank == 0) {
        data = (int*) malloc(N * sizeof(int));
        printf("Enter %d numbers:\n", N);
        for (int i = 0; i < N; i++) {
            scanf("%d", &data[i]);
        }
    }

    // Scatter data to all processes
    MPI_Scatter(data, l_n, MPI_INT,l_data, l_n, MPI_INT,0, MPI_COMM_WORLD);

    // Each process computes local sum
    for (int i = 0; i < l_n; i++) {
        l_sum += l_data[i];
    }

    // Reduce all local sums to global sum
    MPI_Reduce(&l_sum, &g_sum, 1, MPI_INT,MPI_SUM, 0, MPI_COMM_WORLD);

    // Rank 0 computes average
    if (rank == 0) {
        double average = (double)g_sum / N;
        printf("Global Sum = %d\n", g_sum);
        printf("Average = %.2f\n", average);
    }

    MPI_Finalize();
    return 0;
}