/*
 * Array basics in C: traverse, insert, delete.
 *
 * The array has a fixed CAPACITY (slots reserved in memory) and a SIZE
 * (slots actually in use). Every insert/delete keeps elements packed at
 * indexes 0 .. size-1 with no gaps.
 *
 *   ./array_basics            -> step-by-step demo (same output as Java/Python/Rust)
 *   ./array_basics bench      -> timing run used for the language comparison
 *
 * Build:  gcc -std=c11 -Wall -Wextra -O2 -o array_basics c/array_basics/array_basics.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    int *data;      /* pointer to the first slot                         */
    int size;       /* how many slots are in use                         */
    int capacity;   /* how many slots exist; never changes after create  */
} IntArray;

typedef enum { OK = 0, ERR_FULL, ERR_EMPTY, ERR_RANGE } Status;

static const char *status_text(Status s) {
    switch (s) {
    case ERR_FULL:  return "array is full";
    case ERR_EMPTY: return "array is empty";
    case ERR_RANGE: return "position out of range";
    default:        return "ok";
    }
}

/* Space O(capacity). Returns 0 on success, -1 if memory is not available. */
static int array_create(IntArray *a, int capacity) {
    a->data = calloc((size_t)capacity, sizeof *a->data);
    a->size = 0;
    a->capacity = capacity;
    return a->data ? 0 : -1;
}

static void array_free(IntArray *a) {
    free(a->data);
    a->data = NULL;           /* avoid a dangling pointer */
    a->size = a->capacity = 0;
}

/* TRAVERSE: visit every element once.  Time O(n), extra space O(1). */
static void array_print(const IntArray *a) {
    printf("[");
    for (int i = 0; i < a->size; i++) {
        printf(i ? ", %d" : "%d", a->data[i]);
    }
    printf("]  size=%d", a->size);
}

/*
 * INSERT value at pos (0 <= pos <= size).
 * Shift a[pos..size-1] one step RIGHT, starting from the END so nothing
 * is overwritten before it is copied.
 * Time: O(n) worst (pos = 0), O(1) best (pos = size). Extra space O(1).
 */
static Status array_insert(IntArray *a, int pos, int value) {
    if (a->size == a->capacity) return ERR_FULL;
    if (pos < 0 || pos > a->size) return ERR_RANGE;   /* C will NOT check this for you */
    for (int i = a->size; i > pos; i--) {
        a->data[i] = a->data[i - 1];
    }
    a->data[pos] = value;
    a->size++;
    return OK;
}

/*
 * DELETE the element at pos (0 <= pos < size) and hand it back via *removed.
 * Shift a[pos+1..size-1] one step LEFT to close the gap.
 * Time: O(n) worst (pos = 0), O(1) best (pos = size-1). Extra space O(1).
 */
static Status array_delete(IntArray *a, int pos, int *removed) {
    if (a->size == 0) return ERR_EMPTY;
    if (pos < 0 || pos >= a->size) return ERR_RANGE;
    *removed = a->data[pos];
    for (int i = pos; i < a->size - 1; i++) {
        a->data[i] = a->data[i + 1];
    }
    a->size--;
    return OK;
}

/* ---------------------------------------------------------------- demo */

static void show_insert(IntArray *a, const char *label, int pos, int value) {
    printf("%-17s: ", label);
    Status s = array_insert(a, pos, value);
    if (s == OK) array_print(a);
    else printf("error: %s", status_text(s));
    printf("\n");
}

static void show_delete(IntArray *a, const char *label, int pos) {
    printf("%-17s: ", label);
    int removed = 0;
    Status s = array_delete(a, pos, &removed);
    if (s == OK) {
        printf("removed %d -> ", removed);
        array_print(a);
    } else {
        printf("error: %s", status_text(s));
    }
    printf("\n");
}

static int demo(void) {
    IntArray a;
    if (array_create(&a, 8) != 0) return 1;
    const int start[] = {10, 20, 30, 40, 50};
    for (int i = 0; i < 5; i++) array_insert(&a, a.size, start[i]);

    printf("=== Array basics demo (capacity %d) ===\n", a.capacity);
    printf("%-17s: ", "start");
    array_print(&a);
    printf("\n%-17s: ", "traverse");
    for (int i = 0; i < a.size; i++) printf(i ? " %d" : "%d", a.data[i]);
    printf("\n%-17s: %d\n", "access a[3]", a.data[3]);

    show_insert(&a, "insert 99 at 2", 2, 99);
    show_insert(&a, "insert 5 at 0", 0, 5);
    show_insert(&a, "insert 60 at end", a.size, 60);
    show_insert(&a, "insert 1 at 0", 0, 1);        /* full */
    show_delete(&a, "delete at 3", 3);
    show_delete(&a, "delete at 0", 0);
    show_delete(&a, "delete at end", a.size - 1);
    show_delete(&a, "delete at 9", 9);              /* out of range */
    show_insert(&a, "insert 7 at -1", -1, 7);       /* negative index */

    array_free(&a);
    return 0;
}

/* ----------------------------------------------------------- benchmark */

static double now_ms(void) {
    struct timespec t;
    timespec_get(&t, TIME_UTC);   /* standard C11 clock */
    return (double)t.tv_sec * 1e3 + (double)t.tv_nsec / 1e6;
}

enum { TRAVERSE_N = 1000000, TRAVERSE_PASSES = 10, SHIFT_K = 5000, ROUNDS = 3 };

static int bench(void) {
    double best_t = 1e18, best_i = 1e18, best_d = 1e18;
    long long sum_t = 0, sum_i = 0, sum_d = 0;

    for (int round = 0; round < ROUNDS; round++) {
        IntArray a;
        if (array_create(&a, TRAVERSE_N) != 0) return 1;
        for (int i = 0; i < TRAVERSE_N; i++) array_insert(&a, a.size, i);

        double t0 = now_ms();
        sum_t = 0;
        for (int p = 0; p < TRAVERSE_PASSES; p++)
            for (int i = 0; i < a.size; i++) sum_t += a.data[i];
        double t1 = now_ms();
        if (t1 - t0 < best_t) best_t = t1 - t0;
        array_free(&a);

        if (array_create(&a, SHIFT_K) != 0) return 1;
        t0 = now_ms();
        for (int i = 0; i < SHIFT_K; i++) array_insert(&a, 0, i);   /* worst case */
        t1 = now_ms();
        if (t1 - t0 < best_i) best_i = t1 - t0;
        sum_i = 0;
        for (int j = 0; j < a.size; j++) sum_i += (long long)j * a.data[j];

        t0 = now_ms();
        sum_d = 0;
        for (int step = 1; a.size > 0; step++) {
            int removed = 0;
            array_delete(&a, 0, &removed);                           /* worst case */
            sum_d += (long long)step * removed;
        }
        t1 = now_ms();
        if (t1 - t0 < best_d) best_d = t1 - t0;
        array_free(&a);
    }

    printf("traverse      checksum=%lld time_ms=%.3f\n", sum_t, best_t);
    printf("insert_front  checksum=%lld time_ms=%.3f\n", sum_i, best_i);
    printf("delete_front  checksum=%lld time_ms=%.3f\n", sum_d, best_d);
    return 0;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "bench") == 0) return bench();
    return demo();
}
