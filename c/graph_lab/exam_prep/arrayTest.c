#include <stdio.h>

int main(void)
{
    int num;
    scanf("%d", &num);
    if(num == 0){
        printf("Array is empty\n");
        return 0;
    }
    // printf("Entered Number is %d", num);

    int arr[100];
    
    int sum=0;

    for(int i=0; i<num; i++){
        scanf("%d", &arr[i]);
    }
    // printf("Entered values are ");
    int max=arr[0];
    for(int j=0; j<num; j++){
        sum = sum+arr[j];
        if(arr[j]>max){
            max = arr[j];
        }

        printf("%d ", arr[j]);
    }
    printf("\n");
    printf("Sum = %d\n", sum);
    printf("Max = %d\n", max);
    return 0;
}
