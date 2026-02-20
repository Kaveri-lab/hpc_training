#include <stdio.h>
#include <mpi.h>

int main(int argc, char *argv[]) 
{

    int rank, size;

    int mat[4][4];
    int vector[4];
    int row[4];
    int lresult = 0;
    int result[4];

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size != 4) 
    {
        if (rank == 0)
            printf("Run with 4 processes.\n");
        MPI_Finalize();
        return 0;
    }

    // Initialize matrix and vector on rank 0
    if (rank == 0)
     {

        int value = 1;
        for (int i = 0; i < 4; i++)
         {
            for (int j = 0; j < 4; j++) 
            {
                mat[i][j] = value++;
            }
        }
        
        // Example vector
        for (int i = 0; i < 4; i++) 
        {
            vector[i] = 1;   // simple vector [1,1,1,1]
        }
    }

    // Scatter rows of matrix
    MPI_Scatter(mat, 4, MPI_INT,row, 4, MPI_INT,0, MPI_COMM_WORLD);

    // Broadcast vector to all processes
    MPI_Bcast(vector, 4, MPI_INT, 0, MPI_COMM_WORLD);

    // Each process computes dot product
    for (int i = 0; i < 4; i++) {
        lresult += row[i] * vector[i];
    }

    printf("Process %d: Computed y[%d] = %d\n",
           rank, rank, lresult);

    // Gather results into final vector
    MPI_Gather(&lresult, 1, MPI_INT,result, 1, MPI_INT,0, MPI_COMM_WORLD);

    if (rank == 0)
     {
        printf("\nFinal Result Vector y:\n");
        for (int i = 0; i < 4; i++)
         {
            printf("%d ", result[i]);
        }
        printf("\n");
    }

    MPI_Finalize();
    return 0;
}
