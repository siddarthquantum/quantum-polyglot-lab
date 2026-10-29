/*
 * array_ops.c — reference solution for the array lab.
 *
 * Input format
 *   n                      number of elements (0..MAX)
 *   a[0] a[1] ... a[n-1]   the elements
 *   commands, one per line, until END or end of input:
 *     PRINT                print the array
 *     INSERT pos x         insert x at index pos (0..n)
 *     DELETE pos           delete the element at index pos (0..n-1)
 *     SEARCH key           linear search
 *     BSEARCH key          binary search (array must be sorted ascending)
 *     SORT                 insertion sort, ascending
 *     REVERSE              reverse in place
 *     ROTATE k             rotate left by k positions
 *     MAX | MIN | SUM      print the largest / smallest element / the sum
 *     END                  stop
 *
 * Error handling
 *   Malformed input (bad n, missing numbers, unknown command) -> message on
 *   stderr and exit code 1.  Operation errors on valid input (overflow, bad
 *   position, empty array) -> message on stdout and the program carries on,
 *   the way a lab-exam menu program behaves.
 */
#include <stdio.h>
#include <string.h>

#define MAX 100

/* ---------- operations ---------- */

void print_array(const int a[], int n)
{
    if (n == 0) {
        printf("Array: (empty)\n");
        return;
    }
    printf("Array:");
    for (int i = 0; i < n; i++)
        printf(" %d", a[i]);
    printf("\n");
}

/* Shift a[pos..n-1] one place right, starting from the end. O(n) */
int insert_at(int a[], int n, int pos, int x)
{
    if (n == MAX) {
        printf("Overflow\n");
        return n;
    }
    if (pos < 0 || pos > n) {
        printf("Invalid position\n");
        return n;
    }
    for (int i = n - 1; i >= pos; i--)
        a[i + 1] = a[i];
    a[pos] = x;
    return n + 1;
}

/* Shift a[pos+1..n-1] one place left. O(n) */
int delete_at(int a[], int n, int pos)
{
    if (n == 0) {
        printf("Underflow\n");
        return n;
    }
    if (pos < 0 || pos >= n) {
        printf("Invalid position\n");
        return n;
    }
    printf("Deleted %d\n", a[pos]);
    for (int i = pos; i < n - 1; i++)
        a[i] = a[i + 1];
    return n - 1;
}

/* O(n): returns the first index holding key, or -1 */
int linear_search(const int a[], int n, int key)
{
    for (int i = 0; i < n; i++)
        if (a[i] == key)
            return i;
    return -1;
}

int is_sorted(const int a[], int n)
{
    for (int i = 1; i < n; i++)
        if (a[i - 1] > a[i])
            return 0;
    return 1;
}

/* O(log n): array must be sorted ascending. Returns an index of key, or -1 */
int binary_search(const int a[], int n, int key)
{
    int low = 0, high = n - 1;
    while (low <= high) {
        int mid = low + (high - low) / 2;   /* avoids overflow of low + high */
        if (a[mid] == key)
            return mid;
        else if (a[mid] < key)
            low = mid + 1;
        else
            high = mid - 1;
    }
    return -1;
}

/* Insertion sort. O(n^2) worst, O(n) when already sorted */
void insertion_sort(int a[], int n)
{
    for (int i = 1; i < n; i++) {
        int key = a[i];
        int j = i - 1;
        while (j >= 0 && a[j] > key) {
            a[j + 1] = a[j];
            j--;
        }
        a[j + 1] = key;
    }
}

/* Two-pointer swap from both ends. O(n), O(1) extra space */
void reverse_range(int a[], int low, int high)
{
    while (low < high) {
        int t = a[low];
        a[low] = a[high];
        a[high] = t;
        low++;
        high--;
    }
}

/* Left rotation by k using three reversals. O(n), O(1) extra space */
void rotate_left(int a[], int n, int k)
{
    if (n == 0)
        return;
    k %= n;
    if (k < 0)
        k += n;
    reverse_range(a, 0, k - 1);
    reverse_range(a, k, n - 1);
    reverse_range(a, 0, n - 1);
}

int find_max(const int a[], int n)
{
    int m = a[0];
    for (int i = 1; i < n; i++)
        if (a[i] > m)
            m = a[i];
    return m;
}

int find_min(const int a[], int n)
{
    int m = a[0];
    for (int i = 1; i < n; i++)
        if (a[i] < m)
            m = a[i];
    return m;
}

long long sum_array(const int a[], int n)
{
    long long s = 0;   /* int could overflow for 100 large values */
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}

/* ---------- driver ---------- */

static int read_int(int *out, const char *what)
{
    if (scanf("%d", out) != 1) {
        fprintf(stderr, "error: expected %s\n", what);
        return 0;
    }
    return 1;
}

int main(void)
{
    int a[MAX];
    int n;
    char cmd[16];

    if (!read_int(&n, "n"))
        return 1;
    if (n < 0 || n > MAX) {
        fprintf(stderr, "error: n must be between 0 and %d\n", MAX);
        return 1;
    }
    for (int i = 0; i < n; i++)
        if (!read_int(&a[i], "array element"))
            return 1;

    while (scanf("%15s", cmd) == 1) {
        int x, y;

        if (strcmp(cmd, "END") == 0) {
            break;
        } else if (strcmp(cmd, "PRINT") == 0) {
            print_array(a, n);
        } else if (strcmp(cmd, "INSERT") == 0) {
            if (!read_int(&x, "position") || !read_int(&y, "value"))
                return 1;
            n = insert_at(a, n, x, y);
        } else if (strcmp(cmd, "DELETE") == 0) {
            if (!read_int(&x, "position"))
                return 1;
            n = delete_at(a, n, x);
        } else if (strcmp(cmd, "SEARCH") == 0 || strcmp(cmd, "BSEARCH") == 0) {
            if (!read_int(&x, "key"))
                return 1;
            int idx;
            if (cmd[0] == 'B') {
                if (!is_sorted(a, n)) {
                    printf("Array not sorted\n");
                    continue;
                }
                idx = binary_search(a, n, x);
            } else {
                idx = linear_search(a, n, x);
            }
            if (idx == -1)
                printf("%d not found\n", x);
            else
                printf("%d found at index %d\n", x, idx);
        } else if (strcmp(cmd, "SORT") == 0) {
            insertion_sort(a, n);
        } else if (strcmp(cmd, "REVERSE") == 0) {
            reverse_range(a, 0, n - 1);
        } else if (strcmp(cmd, "ROTATE") == 0) {
            if (!read_int(&x, "rotation count"))
                return 1;
            rotate_left(a, n, x);
        } else if (strcmp(cmd, "MAX") == 0 || strcmp(cmd, "MIN") == 0 ||
                   strcmp(cmd, "SUM") == 0) {
            if (n == 0)
                printf("Array is empty\n");
            else if (strcmp(cmd, "MAX") == 0)
                printf("Max = %d\n", find_max(a, n));
            else if (strcmp(cmd, "MIN") == 0)
                printf("Min = %d\n", find_min(a, n));
            else
                printf("Sum = %lld\n", sum_array(a, n));
        } else {
            fprintf(stderr, "error: unknown command '%s'\n", cmd);
            return 1;
        }
    }
    return 0;
}
