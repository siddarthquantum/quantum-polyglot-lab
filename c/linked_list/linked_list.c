/*
 * Singly linked list in C: traverse, insert, delete, search, reverse, middle,
 * cycle detection.
 *
 * An array stores elements side by side in one block. A LINKED LIST stores each
 * element in its own NODE, allocated separately, and each node holds a POINTER
 * to the next one. The list itself is just a pointer to the first node (head).
 *
 *   head -> [10|*] -> [20|*] -> [30|/]
 *
 * That one difference drives every complexity in this file: there is no address
 * arithmetic, so reaching index i costs i steps (O(n)), but splicing a node in
 * or out costs O(1) once you are holding the right pointer.
 *
 *   ./linked_list            -> step-by-step demo (same output as Java/Python/Rust)
 *   ./linked_list bench      -> timing run used for the language comparison
 *
 * Build:  gcc -std=c11 -Wall -Wextra -O2 -o linked_list c/linked_list/linked_list.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct Node {
    int value;
    struct Node *next;   /* NULL marks the last node */
} Node;

typedef struct {
    Node *head;          /* NULL means the list is empty */
    long len;            /* kept in sync so length() is O(1) instead of O(n) */
} List;

typedef enum { OK = 0, ERR_EMPTY, ERR_RANGE, ERR_NOTFOUND, ERR_NOMEM } Status;

static const char *status_text(Status s) {
    switch (s) {
    case ERR_EMPTY:    return "list is empty";
    case ERR_RANGE:    return "position out of range";
    case ERR_NOTFOUND: return "value not found";
    case ERR_NOMEM:    return "out of memory";
    default:           return "ok";
    }
}

static void list_init(List *l) {
    l->head = NULL;
    l->len = 0;
}

/*
 * TRAVERSE: follow next pointers until NULL. Time O(n), extra space O(1).
 * This is the only way to visit a linked list: there is no a[i].
 */
static void list_print(const List *l) {
    printf("[");
    for (const Node *cur = l->head; cur != NULL; cur = cur->next) {
        printf(cur == l->head ? "%d" : ", %d", cur->value);
    }
    printf("]  len=%ld", l->len);
}

/*
 * INSERT value at pos (0 <= pos <= len).
 * Walk to the node BEFORE pos, then splice: the new node points at what the
 * previous node pointed at, and the previous node points at the new node.
 * Order matters: link the new node first, or you lose the rest of the list.
 * Time: O(1) at the head, O(n) otherwise (the walk). Extra space O(1).
 */
static Status list_insert(List *l, long pos, int value) {
    if (pos < 0 || pos > l->len) return ERR_RANGE;   /* C will NOT check this for you */

    Node *node = malloc(sizeof *node);
    if (node == NULL) return ERR_NOMEM;              /* always check malloc */
    node->value = value;

    if (pos == 0) {
        node->next = l->head;                        /* 1. new node points at old head */
        l->head = node;                              /* 2. head now points at new node */
    } else {
        Node *prev = l->head;
        for (long i = 0; i < pos - 1; i++) prev = prev->next;
        node->next = prev->next;
        prev->next = node;
    }
    l->len++;
    return OK;
}

/*
 * DELETE the node at pos (0 <= pos < len), hand its value back via *removed.
 * Unlink it, then free it. Keep a pointer to the victim BEFORE unlinking,
 * otherwise it becomes unreachable and leaks.
 * Time: O(1) at the head, O(n) otherwise. Extra space O(1).
 */
static Status list_delete_at(List *l, long pos, int *removed) {
    if (l->len == 0) return ERR_EMPTY;
    if (pos < 0 || pos >= l->len) return ERR_RANGE;

    Node *victim;
    if (pos == 0) {
        victim = l->head;
        l->head = victim->next;
    } else {
        Node *prev = l->head;
        for (long i = 0; i < pos - 1; i++) prev = prev->next;
        victim = prev->next;
        prev->next = victim->next;
    }
    *removed = victim->value;
    free(victim);                 /* the node is unlinked, so nothing points at it */
    l->len--;
    return OK;
}

/* DELETE the first node holding `value`. Time O(n), extra space O(1). */
static Status list_delete_value(List *l, int value) {
    if (l->len == 0) return ERR_EMPTY;

    Node *prev = NULL;
    Node *cur = l->head;
    while (cur != NULL && cur->value != value) {
        prev = cur;
        cur = cur->next;
    }
    if (cur == NULL) return ERR_NOTFOUND;

    if (prev == NULL) l->head = cur->next;   /* deleting the head */
    else prev->next = cur->next;
    free(cur);
    l->len--;
    return OK;
}

/* SEARCH: index of the first node holding `value`, or -1. Time O(n). */
static long list_search(const List *l, int value) {
    long i = 0;
    for (const Node *cur = l->head; cur != NULL; cur = cur->next, i++) {
        if (cur->value == value) return i;
    }
    return -1;
}

/*
 * GET the value at pos. Time O(n) -- this is the price of a linked list.
 * On an array this same operation is O(1).
 */
static Status list_get(const List *l, long pos, int *out) {
    if (pos < 0 || pos >= l->len) return ERR_RANGE;
    const Node *cur = l->head;
    for (long i = 0; i < pos; i++) cur = cur->next;
    *out = cur->value;
    return OK;
}

/*
 * REVERSE in place by flipping every next pointer. Time O(n), extra space O(1).
 * Three pointers are needed: you must save `next` before overwriting
 * cur->next, or the rest of the list is lost.
 */
static void list_reverse(List *l) {
    Node *prev = NULL;
    Node *cur = l->head;
    while (cur != NULL) {
        Node *next = cur->next;   /* save it first */
        cur->next = prev;         /* flip */
        prev = cur;
        cur = next;
    }
    l->head = prev;
}

/*
 * MIDDLE via the two-pointer (tortoise and hare) trick: `fast` moves two steps
 * for every one of `slow`, so when fast falls off the end, slow is halfway.
 * One pass, no length needed. Time O(n), extra space O(1).
 * For an even length this returns the SECOND of the two middle nodes.
 */
static Status list_middle(const List *l, int *out) {
    if (l->head == NULL) return ERR_EMPTY;
    const Node *slow = l->head;
    const Node *fast = l->head;
    while (fast != NULL && fast->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
    }
    *out = slow->value;
    return OK;
}

/*
 * CYCLE DETECTION, Floyd's algorithm. If a next pointer loops back, the hare
 * laps the tortoise and they meet; otherwise the hare reaches NULL.
 * Time O(n), extra space O(1) -- no "visited" set needed.
 * A corrupted list makes every other operation here loop forever, so this is
 * the guard you run first when a list comes from untrusted code.
 */
static int list_has_cycle(const List *l) {
    const Node *slow = l->head;
    const Node *fast = l->head;
    while (fast != NULL && fast->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return 1;
    }
    return 0;
}

/* CLEAR: free every node. Time O(n). Forgetting this is a textbook memory leak. */
static void list_clear(List *l) {
    Node *cur = l->head;
    while (cur != NULL) {
        Node *next = cur->next;   /* save before freeing, or this is use-after-free */
        free(cur);
        cur = next;
    }
    l->head = NULL;
    l->len = 0;
}

/* ---------------------------------------------------------------- demo */

static void show_insert(List *l, const char *label, long pos, int value) {
    printf("%-17s: ", label);
    Status s = list_insert(l, pos, value);
    if (s == OK) list_print(l);
    else printf("error: %s", status_text(s));
    printf("\n");
}

static void show_delete_at(List *l, const char *label, long pos) {
    printf("%-17s: ", label);
    int removed = 0;
    Status s = list_delete_at(l, pos, &removed);
    if (s == OK) {
        printf("removed %d -> ", removed);
        list_print(l);
    } else {
        printf("error: %s", status_text(s));
    }
    printf("\n");
}

static void show_delete_value(List *l, const char *label, int value) {
    printf("%-17s: ", label);
    Status s = list_delete_value(l, value);
    if (s == OK) {
        printf("removed -> ");
        list_print(l);
    } else {
        printf("error: %s", status_text(s));
    }
    printf("\n");
}

static void show_get(const List *l, const char *label, long pos) {
    printf("%-17s: ", label);
    int out = 0;
    Status s = list_get(l, pos, &out);
    if (s == OK) printf("%d\n", out);
    else printf("error: %s\n", status_text(s));
}

static void show_search(const List *l, const char *label, int value) {
    long idx = list_search(l, value);
    printf("%-17s: ", label);
    if (idx >= 0) printf("found at index %ld\n", idx);
    else printf("not found\n");
}

static void show_state(const List *l, const char *label) {
    printf("%-17s: ", label);
    list_print(l);
    printf("\n");
}

static int demo(void) {
    List l;
    list_init(&l);

    printf("=== Linked list demo (singly linked) ===\n");
    show_state(&l, "start");

    show_insert(&l, "push_front 30", 0, 30);
    show_insert(&l, "push_front 20", 0, 20);
    show_insert(&l, "push_front 10", 0, 10);
    show_insert(&l, "push_back 40", l.len, 40);
    show_insert(&l, "push_back 50", l.len, 50);

    printf("%-17s: ", "traverse");
    for (const Node *cur = l.head; cur != NULL; cur = cur->next) {
        printf(cur == l.head ? "%d" : " %d", cur->value);
    }
    printf("\n");

    show_get(&l, "get at 3", 3);
    show_get(&l, "get at 9", 9);              /* out of range */
    show_search(&l, "search 30", 30);
    show_search(&l, "search 77", 77);         /* absent */

    show_insert(&l, "insert 99 at 2", 2, 99);
    show_insert(&l, "insert 5 at 0", 0, 5);
    show_insert(&l, "insert 60 at end", l.len, 60);
    show_insert(&l, "insert 7 at -1", -1, 7); /* negative index */

    show_delete_at(&l, "delete at 3", 3);
    show_delete_at(&l, "pop_front", 0);
    show_delete_at(&l, "pop_back", l.len - 1);
    show_delete_value(&l, "delete value 30", 30);
    show_delete_value(&l, "delete value 77", 77);   /* absent */
    show_delete_at(&l, "delete at 9", 9);           /* out of range */

    int mid = 0;
    printf("%-17s: ", "middle");
    if (list_middle(&l, &mid) == OK) printf("%d\n", mid);
    else printf("error: %s\n", status_text(ERR_EMPTY));

    list_reverse(&l);
    show_state(&l, "reverse");

    printf("%-17s: %s\n", "has cycle", list_has_cycle(&l) ? "true" : "false");

    list_clear(&l);
    show_state(&l, "clear");
    show_delete_at(&l, "pop_front", 0);       /* empty */

    list_clear(&l);
    return 0;
}

/* ----------------------------------------------------------- benchmark */

static double now_ms(void) {
    struct timespec t;
    timespec_get(&t, TIME_UTC);   /* standard C11 clock */
    return (double)t.tv_sec * 1e3 + (double)t.tv_nsec / 1e6;
}

enum {
    BUILD_N = 200000,    /* nodes pushed at the front        */
    PASSES = 10,         /* traversal passes                 */
    IDX_N = 20000,       /* smaller list for index access    */
    IDX_GETS = 200,      /* number of get(i) calls           */
    ROUNDS = 3
};

static int bench(void) {
    double best_b = 1e18, best_t = 1e18, best_g = 1e18, best_p = 1e18;
    long long sum_b = 0, sum_t = 0, sum_g = 0, sum_p = 0;

    for (int round = 0; round < ROUNDS; round++) {
        List l;
        list_init(&l);

        /* build_front: O(1) per push -- the operation arrays are bad at */
        double t0 = now_ms();
        for (int i = 0; i < BUILD_N; i++) {
            if (list_insert(&l, 0, i) != OK) return 1;
        }
        double t1 = now_ms();
        if (t1 - t0 < best_b) best_b = t1 - t0;
        sum_b = 0;
        for (const Node *cur = l.head; cur != NULL; cur = cur->next) sum_b += cur->value;

        /* traverse: pointer chasing, cache-unfriendly compared to an array */
        t0 = now_ms();
        sum_t = 0;
        for (int p = 0; p < PASSES; p++) {
            for (const Node *cur = l.head; cur != NULL; cur = cur->next) sum_t += cur->value;
        }
        t1 = now_ms();
        if (t1 - t0 < best_t) best_t = t1 - t0;

        /* pop_front: O(1) per pop */
        t0 = now_ms();
        sum_p = 0;
        for (long long step = 1; l.len > 0; step++) {
            int removed = 0;
            list_delete_at(&l, 0, &removed);
            sum_p += step * removed;
        }
        t1 = now_ms();
        if (t1 - t0 < best_p) best_p = t1 - t0;
        list_clear(&l);

        /* index_access: O(n) per get -- the operation arrays are good at */
        List g;
        list_init(&g);
        for (int i = 0; i < IDX_N; i++) {
            if (list_insert(&g, 0, i) != OK) return 1;
        }
        t0 = now_ms();
        sum_g = 0;
        for (int k = 0; k < IDX_GETS; k++) {
            int out = 0;
            list_get(&g, (long)((k * 97) % IDX_N), &out);
            sum_g += out;
        }
        t1 = now_ms();
        if (t1 - t0 < best_g) best_g = t1 - t0;
        list_clear(&g);
    }

    printf("build_front   checksum=%lld time_ms=%.3f\n", sum_b, best_b);
    printf("traverse      checksum=%lld time_ms=%.3f\n", sum_t, best_t);
    printf("index_access  checksum=%lld time_ms=%.3f\n", sum_g, best_g);
    printf("pop_front     checksum=%lld time_ms=%.3f\n", sum_p, best_p);
    return 0;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "bench") == 0) return bench();
    return demo();
}
