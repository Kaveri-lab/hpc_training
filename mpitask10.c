#include<stdio.h>
#include<mpi.h>

#define N 4

int main(int argc,char *argv[])
{
int rank,size;
int mat[N][N];
int row[N];
int lmax,gmax;

MPI_Init(&argc,&argv);
MPI_Comm_rank(MPI_COMM_WORLD,&rank);
MPI_Comm_size(MPI_COMM_WORLD,&size);

//only rank 0 initializes matrix

if(rank == 0)
{
 int temp[N][N]={
            {10, 20, 30, 40},
             {5, 25, 35, 15},
             {45, 22, 11, 9},
             {8, 18, 28, 38}
        };

  for(int i=0;i<N;i++)
  for(int j=0;j<N;j++)
     mat[i][j]=temp[i][j];
}

//scatter rows
MPI_Scatter(mat,N,MPI_INT,row,N,MPI_INT,0,MPI_COMM_WORLD);

//find local maximum
lmax=row[0];
for(int i=1;i<N;i++)
{
 if(row[i]>lmax)
   lmax=row[i];
}

printf("Process %d local max = %d\n", rank, lmax);

    // Reduce to find global maximum
    MPI_Reduce(&lmax, &gmax, 1, MPI_INT, MPI_MAX, 0, MPI_COMM_WORLD);
    // Print result at root
    if (rank == 0) {
        printf("\nGlobal Maximum = %d\n", gmax);
    }

    MPI_Finalize();
    return 0;
}
