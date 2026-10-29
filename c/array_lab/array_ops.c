/*
 * array_ops.c — YOUR exercise file for the array lab.
 *
 * The input reading (main) is done for you. Fill in each function marked
 * TODO, one at a time, in the order of the README. After each one, rebuild
 * and run the tests: more cases turn from FAIL to PASS as you go.
 *
 *   gcc -std=c11 -Wall -Wextra -o array_ops c/array_lab/array_ops.c
 *   c/array_lab/tests/run_tests.sh ./array_ops
 *
 * Input format and messages: see the README. Reference answer:
 * solution/array_ops.c. Write yours first, then compare.
 */
#include <stdio.h>
#include <string.h>

#define MAX 100

/* ---------- operations ---------- */

/* Exercise 1. Print "Array: 10 20 30" (one space before each number), or
 * "Array: (empty)" when n == 0. End with a newline. */
void print_array(const int a[], int n)
{
    /* TODO */
    (void)a;
    (void)n;
}

/* Exercise 2. Insert x at index pos and return the new size.
 *   n == MAX            -> print "Overflow",         return n
 *   pos outside 0..n    -> print "Invalid position", return n
 * Shift a[pos..n-1] one place to the right, STARTING FROM THE END. */
int insert_at(int a[], int n, int pos, int x)
{
    /* TODO */
    (void)a;
    (void)pos;
    (void)x;
    return n;
}

/* Exercise 3. Delete the element at index pos and return the new size.
 *   n == 0              -> print "Underflow",        return n
 *   pos outside 0..n-1  -> print "Invalid position", return n
 * Otherwise print "Deleted <value>" and shift the rest one place left. */
int delete_at(int a[], int n, int pos)
{
    /* TODO */
    (void)a;
    (void)pos;
    return n;
}

/* Exercise 4. Return the first index holding key, or -1. */
int linear_search(const int a[], int n, int key)
{
    /* TODO */
    (void)a;
    (void)n;
    (void)key;
    return -1;
}

/* Exercise 5. Return 1 if a[0] <= a[1] <= ... <= a[n-1], else 0.
 * (An empty or one-element array counts as sorted.) */
int is_sorted(const int a[], int n)
{
    /* TODO */
    (void)a;
    (void)n;
    return 1;
}

/* Exercise 6. Binary search on a sorted array: return an index of key, or -1.
 * Use mid = low + (high - low) / 2. */
int binary_search(const int a[], int n, int key)
{
    /* TODO */
    (void)a;
    (void)n;
    (void)key;
    return -1;
}

/* Exercise 7. Insertion sort, ascending. */
void insertion_sort(int a[], int n)
{
    /* TODO */
    (void)a;
    (void)n;
}

/* Exercise 8. Reverse a[low..high] in place by swapping from both ends. */
void reverse_range(int a[], int low, int high)
{
    /* TODO */
    (void)a;
    (void)low;
    (void)high;
}

/* Exercise 9. Rotate left by k: {1,2,3,4,5}, k=2 -> {3,4,5,1,2}.
 * k can be larger than n (use k % n). Do nothing when n == 0.
 * Challenge: do it with three calls to reverse_range and no extra array. */
void rotate_left(int a[], int n, int k)
{
    /* TODO */
    (void)a;
    (void)n;
    (void)k;
}

/* Exercise 10. Largest, smallest and sum. main() only calls these when n > 0.
 * Why does sum return long long instead of int? */
int find_max(const int a[], int n)
{
    /* TODO */
    (void)n;
    return a[0];
}

int find_min(const int a[], int n)
{
    /* TODO */
    (void)n;
    return a[0];
}

long long sum_array(const int a[], int n)
{
    /* TODO */
    (void)a;
    (void)n;
    return 0;
}

/* ---------- driver (done for you) ---------- */

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
