#include<stdio.h>
int main(){

    int n, pos, x;
    scanf("%d", &n);
    int arr[100];
    for(int i=0; i<n; i++){
       scanf("%d", &arr[i]);
    }
    scanf("%d %d", &pos, &x);

    if (pos < 0 || pos > n){
        printf("Invaid position\n");
        return 0;
    }


    for(int j=n-1; j>=pos; j--){
        arr[j+1] = arr[j];
    }
    arr[pos] = x;
    n=n+1;
    for(int i=0; i<n; i++){
        printf("%d ", arr[i]);
    }
    printf("\n");

    return 0;
}