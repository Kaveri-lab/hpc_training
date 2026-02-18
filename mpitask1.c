Excercise:
Take an interger array of 10^4, 10^5, 10^6  elements.
Try accessing the array elements using np 1,2,4 and  the run total run_time for this accessing elements.


-->nano taskmpi.c
#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
int main(int argc, char *argv[]) {
    int rank, size;
    long N = atol(argv[1]);  // Take array size from command line
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    long local_n = N / size;
    int *arr = (int*) malloc(local_n * sizeof(int));
    // Initialize local array
    for(long i = 0; i < local_n; i++)
        arr[i] = 1;
    long long local_sum = 0;
    double start = MPI_Wtime();

    // Access elements
    for(long i = 0; i < local_n; i++)
        local_sum += arr[i];
    double end = MPI_Wtime();
    double local_time = end - start;
    double total_time;
    MPI_Reduce(&local_time, &total_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    if(rank == 0) {
        printf("Array Size = %ld, Processes = %d, Total Run Time = %f seconds\n",
               N, size, total_time);
    }
    free(arr);
    MPI_Finalize();
    return 0;
}


