/*
 * Doubly linked list in C: push/pop at both ends, insert, delete, search,
 * get, O(1) removal of a held node, reverse, and an integrity check modelled
 * on glibc's "safe unlinking".
 *
 * A singly linked node knows only what comes NEXT. A doubly linked node also
 * knows what came BEFORE, and the list keeps a pointer to both ends:
 *
 *   head                              tail
 *    |                                 |
 *    v                                 v
 *   [/|10|*] <-> [*|20|*] <-> [*|30|/]
 *    prev  next
 *
 * The extra pointer per node buys three things the singly linked list in
 * c/linked_list/ cannot do in O(1): pop_back, push_back without a walk, and
 * removing a node you are already holding (no need to find its predecessor).
 * The price is one more pointer per node and twice as many links to keep
 * consistent on every insert and delete.
 *
 *   ./doubly_linked_list          -> step-by-step demo (same output as Java/Python/Rust)
 *   ./doubly_linked_list bench    -> timing run used for the language comparison
 *
 * Build:  gcc -std=c11 -Wall -Wextra -O2 -o doubly_linked_list c/doubly_linked_list/doubly_linked_list.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct Node {
    int value;
    struct Node *prev;   /* NULL on the head */
    struct Node *next;   /* NULL on the tail */
} Node;

typedef struct {
    Node *head;
    Node *tail;
    long len;
} DList;

typedef enum { OK = 0, ERR_EMPTY, ERR_RANGE, ERR_NOTFOUND, ERR_NOMEM, ERR_CORRUPT } Status;

static const char *status_text(Status s) {
    switch (s) {
    case ERR_EMPTY:    return "list is empty";
    case ERR_RANGE:    return "position out of range";
    case ERR_NOTFOUND: return "value not found";
    case ERR_NOMEM:    return "out of memory";
    case ERR_CORRUPT:  return "corrupted double-linked list";
    default:           return "ok";
    }
}

static void dl_init(DList *l) {
    l->head = NULL;
    l->tail = NULL;
    l->len = 0;
}

static Node *new_node(int value) {
    Node *n = malloc(sizeof *n);
    if (n != NULL) {
        n->value = value;
        n->prev = NULL;
        n->next = NULL;
    }
    return n;
}

/* PUSH_FRONT: O(1). */
static Status dl_push_front(DList *l, int value) {
    Node *n = new_node(value);
    if (n == NULL) return ERR_NOMEM;
    n->next = l->head;
    if (l->head != NULL) l->head->prev = n;
    else l->tail = n;                  /* first node is both ends */
    l->head = n;
    l->len++;
    return OK;
}

/* PUSH_BACK: O(1) because we keep a tail pointer. Mirror image of push_front. */
static Status dl_push_back(DList *l, int value) {
    Node *n = new_node(value);
    if (n == NULL) return ERR_NOMEM;
    n->prev = l->tail;
    if (l->tail != NULL) l->tail->next = n;
    else l->head = n;
    l->tail = n;
    l->len++;
    return OK;
}

/*
 * NODE_AT: walk from whichever end is nearer. Time O(min(pos, len-1-pos)):
 * the worst case is n/2 steps instead of n. Still O(n), but halved.
 * Caller guarantees 0 <= pos < len. *from_head and *steps feed the demo.
 */
static Node *node_at(const DList *l, long pos, int *from_head, long *steps) {
    Node *cur;
    if (pos < l->len - pos) {
        *from_head = 1;
        *steps = pos;
        cur = l->head;
        for (long i = 0; i < pos; i++) cur = cur->next;
    } else {
        *from_head = 0;
        *steps = l->len - 1 - pos;
        cur = l->tail;
        for (long i = 0; i < *steps; i++) cur = cur->prev;
    }
    return cur;
}

/* GET: O(min(pos, n-pos)). */
static Status dl_get(const DList *l, long pos, int *out, int *from_head, long *steps) {
    if (pos < 0 || pos >= l->len) return ERR_RANGE;
    *out = node_at(l, pos, from_head, steps)->value;
    return OK;
}

/*
 * INSERT value at pos (0 <= pos <= len). The new node goes BEFORE the node
 * currently at pos. Four links change, and the order is chosen so the list
 * is never unreachable: wire the new node first, then point the neighbours
 * at it.
 */
static Status dl_insert(DList *l, long pos, int value) {
    if (pos < 0 || pos > l->len) return ERR_RANGE;
    if (pos == 0) return dl_push_front(l, value);
    if (pos == l->len) return dl_push_back(l, value);

    int fh;
    long st;
    Node *succ = node_at(l, pos, &fh, &st);
    Node *n = new_node(value);
    if (n == NULL) return ERR_NOMEM;
    n->prev = succ->prev;          /* 1. new node points at both neighbours */
    n->next = succ;
    succ->prev->next = n;          /* 2. neighbours point at the new node   */
    succ->prev = n;
    l->len++;
    return OK;
}

/*
 * UNLINK a node you hold, in O(1). This is THE operation that justifies the
 * prev pointer: a singly linked list must walk O(n) to find the predecessor.
 *
 * Before touching anything we check that both neighbours agree they point at
 * `node`. glibc's malloc does exactly this on its own free lists and aborts
 * with "corrupted double-linked list" when it fails, because blindly writing
 * through a corrupted prev/next pointer is the classic "unlink" heap exploit:
 * an attacker who controls those two pointers gets an arbitrary write.
 *
 * Does NOT free the node; callers decide. Extra space O(1).
 */
static Status dl_unlink(DList *l, Node *node) {
    if (node->prev != NULL ? node->prev->next != node : l->head != node) return ERR_CORRUPT;
    if (node->next != NULL ? node->next->prev != node : l->tail != node) return ERR_CORRUPT;

    if (node->prev != NULL) node->prev->next = node->next;
    else l->head = node->next;
    if (node->next != NULL) node->next->prev = node->prev;
    else l->tail = node->prev;

    node->prev = NULL;            /* a detached node keeps no stale links */
    node->next = NULL;
    l->len--;
    return OK;
}

/* REMOVE a held node and free it. O(1). The handle is dangling afterwards. */
static Status dl_remove_node(DList *l, Node *node, int *removed) {
    Status s = dl_unlink(l, node);
    if (s != OK) return s;
    *removed = node->value;
    free(node);
    return OK;
}

/* POP_FRONT / POP_BACK: O(1) -- pop_back is the one a singly linked list can't do. */
static Status dl_pop_front(DList *l, int *removed) {
    if (l->head == NULL) return ERR_EMPTY;
    return dl_remove_node(l, l->head, removed);
}

static Status dl_pop_back(DList *l, int *removed) {
    if (l->tail == NULL) return ERR_EMPTY;
    return dl_remove_node(l, l->tail, removed);
}

/* DELETE at pos: walk from the nearer end, then O(1) unlink. */
static Status dl_delete_at(DList *l, long pos, int *removed) {
    if (l->len == 0) return ERR_EMPTY;
    if (pos < 0 || pos >= l->len) return ERR_RANGE;
    int fh;
    long st;
    return dl_remove_node(l, node_at(l, pos, &fh, &st), removed);
}

/* FIND: the node holding value, or NULL. O(n). This is how you get a handle. */
static Node *dl_find(const DList *l, int value) {
    for (Node *cur = l->head; cur != NULL; cur = cur->next) {
        if (cur->value == value) return cur;
    }
    return NULL;
}

/* SEARCH: index of the first node holding value, or -1. O(n). */
static long dl_search(const DList *l, int value) {
    long i = 0;
    for (const Node *cur = l->head; cur != NULL; cur = cur->next, i++) {
        if (cur->value == value) return i;
    }
    return -1;
}

/* DELETE the first node holding value. O(n) to find, O(1) to unlink. */
static Status dl_delete_value(DList *l, int value) {
    if (l->len == 0) return ERR_EMPTY;
    Node *n = dl_find(l, value);
    if (n == NULL) return ERR_NOTFOUND;
    int removed;
    return dl_remove_node(l, n, &removed);
}

/*
 * REVERSE in place: swap every node's prev and next, then swap head and tail.
 * O(n) time, O(1) space. Simpler than the singly linked version because no
 * link is lost: each node already knows both neighbours.
 */
static void dl_reverse(DList *l) {
    Node *cur = l->head;
    while (cur != NULL) {
        Node *tmp = cur->next;
        cur->next = cur->prev;
        cur->prev = tmp;
        cur = tmp;                     /* tmp is the old next */
    }
    Node *tmp = l->head;
    l->head = l->tail;
    l->tail = tmp;
}

/*
 * INTEGRITY CHECK: every forward link must have a matching back link, the
 * ends must be terminated, and the count must match len. O(n).
 * *bad_index is the first node whose links disagree. The walk is capped at
 * len + 1 steps so a cycle cannot make the check itself loop forever.
 */
static Status dl_check(const DList *l, long *bad_index) {
    *bad_index = -1;
    if ((l->head == NULL) != (l->tail == NULL)) return ERR_CORRUPT;
    if (l->head != NULL && l->head->prev != NULL) { *bad_index = 0; return ERR_CORRUPT; }

    long i = 0;
    const Node *prev = NULL;
    for (const Node *cur = l->head; cur != NULL; prev = cur, cur = cur->next, i++) {
        if (i > l->len || cur->prev != prev) { *bad_index = i; return ERR_CORRUPT; }
    }
    if (prev != l->tail || i != l->len) { *bad_index = i; return ERR_CORRUPT; }
    return OK;
}

/* CLEAR: free every node. O(n). Save next before free, or it is use-after-free. */
static void dl_clear(DList *l) {
    Node *cur = l->head;
    while (cur != NULL) {
        Node *next = cur->next;
        free(cur);
        cur = next;
    }
    dl_init(l);
}

/* ---------------------------------------------------------------- demo */

static void dl_print(const DList *l) {
    printf("[");
    for (const Node *cur = l->head; cur != NULL; cur = cur->next) {
        printf(cur == l->head ? "%d" : ", %d", cur->value);
    }
    printf("]  len=%ld", l->len);
}

static void show_state(const DList *l, const char *label) {
    printf("%-17s: ", label);
    dl_print(l);
    printf("\n");
}

static void show_result(const DList *l, const char *label, Status s) {
    printf("%-17s: ", label);
    if (s == OK) dl_print(l);
    else printf("error: %s", status_text(s));
    printf("\n");
}

static void show_removed(const DList *l, const char *label, Status s, int removed) {
    printf("%-17s: ", label);
    if (s == OK) {
        printf("removed %d -> ", removed);
        dl_print(l);
    } else {
        printf("error: %s", status_text(s));
    }
    printf("\n");
}

static void show_get(const DList *l, const char *label, long pos) {
    int out = 0, fh = 0;
    long steps = 0;
    Status s = dl_get(l, pos, &out, &fh, &steps);
    printf("%-17s: ", label);
    if (s == OK) printf("%d  (%ld step%s from %s)\n", out, steps, steps == 1 ? "" : "s", fh ? "head" : "tail");
    else printf("error: %s\n", status_text(s));
}

static void show_search(const DList *l, const char *label, int value) {
    long idx = dl_search(l, value);
    printf("%-17s: ", label);
    if (idx >= 0) printf("found at index %ld\n", idx);
    else printf("not found\n");
}

static void show_walk(const DList *l, const char *label, int forward) {
    printf("%-17s: ", label);
    const Node *start = forward ? l->head : l->tail;
    for (const Node *cur = start; cur != NULL; cur = forward ? cur->next : cur->prev) {
        printf(cur == start ? "%d" : " %d", cur->value);
    }
    printf("\n");
}

static void show_check(const DList *l, const char *label) {
    long bad = -1;
    Status s = dl_check(l, &bad);
    printf("%-17s: ", label);
    if (s == OK) printf("ok\n");
    else if (bad >= 0) printf("error: %s at index %ld\n", status_text(s), bad);
    else printf("error: %s\n", status_text(s));
}

static int demo(void) {
    DList l;
    dl_init(&l);
    int removed = 0;

    printf("=== Doubly linked list demo ===\n");
    show_state(&l, "start");

    show_result(&l, "push_back 20", dl_push_back(&l, 20));
    show_result(&l, "push_back 30", dl_push_back(&l, 30));
    show_result(&l, "push_front 10", dl_push_front(&l, 10));
    show_result(&l, "push_back 40", dl_push_back(&l, 40));
    show_result(&l, "push_back 50", dl_push_back(&l, 50));

    show_walk(&l, "forward", 1);
    show_walk(&l, "backward", 0);

    show_get(&l, "get at 1", 1);
    show_get(&l, "get at 3", 3);
    show_get(&l, "get at 9", 9);
    show_search(&l, "search 30", 30);
    show_search(&l, "search 77", 77);

    show_result(&l, "insert 99 at 2", dl_insert(&l, 2, 99));
    show_result(&l, "insert 5 at 0", dl_insert(&l, 0, 5));
    show_result(&l, "insert 60 at end", dl_insert(&l, l.len, 60));
    show_result(&l, "insert 7 at -1", dl_insert(&l, -1, 7));

    Status s = dl_pop_front(&l, &removed);
    show_removed(&l, "pop_front", s, removed);
    s = dl_pop_back(&l, &removed);
    show_removed(&l, "pop_back", s, removed);
    s = dl_delete_at(&l, 2, &removed);
    show_removed(&l, "delete at 2", s, removed);
    show_result(&l, "delete value 40", dl_delete_value(&l, 40));
    show_result(&l, "delete value 77", dl_delete_value(&l, 77));

    /* Hold a node: one O(n) search, then O(1) removal with no walk at all. */
    Node *held = dl_find(&l, 30);
    printf("%-17s: %s\n", "hold node 30", held != NULL ? "handle kept" : "not found");
    s = dl_remove_node(&l, held, &removed);
    show_removed(&l, "remove held node", s, removed);

    dl_reverse(&l);
    show_state(&l, "reverse");
    show_walk(&l, "backward", 0);
    show_check(&l, "integrity check");

    /* Corrupt one back link on purpose, the way a heap overflow would. */
    Node *victim = l.head->next;           /* holds 20 */
    Node *saved_prev = victim->prev;
    victim->prev = victim;
    printf("%-17s: %s\n", "corrupt node 20", "prev now points at itself");
    show_check(&l, "integrity check");
    s = dl_remove_node(&l, victim, &removed);
    show_removed(&l, "remove node 20", s, removed);   /* refused, like glibc */
    victim->prev = saved_prev;
    printf("%-17s: %s\n", "repair node 20", "prev restored");
    show_check(&l, "integrity check");

    dl_clear(&l);
    show_state(&l, "clear");
    s = dl_pop_front(&l, &removed);
    show_removed(&l, "pop_front", s, removed);
    s = dl_pop_back(&l, &removed);
    show_removed(&l, "pop_back", s, removed);

    dl_clear(&l);
    return 0;
}

/* ----------------------------------------------------------- benchmark */

static double now_ms(void) {
    struct timespec t;
    timespec_get(&t, TIME_UTC);
    return (double)t.tv_sec * 1e3 + (double)t.tv_nsec / 1e6;
}

enum {
    BUILD_N = 200000,   /* nodes pushed at the back                 */
    PASSES = 10,        /* traversal passes, alternating directions */
    IDX_N = 20000,      /* smaller list for index access            */
    IDX_GETS = 200,     /* number of get(i) calls                   */
    ROUNDS = 3
};

static int bench(void) {
    double best_b = 1e18, best_t = 1e18, best_r = 1e18, best_p = 1e18, best_g = 1e18;
    long long sum_b = 0, sum_t = 0, sum_r = 0, sum_p = 0, sum_g = 0;

    Node **handles = malloc(sizeof *handles * BUILD_N);
    if (handles == NULL) return 1;

    for (int round = 0; round < ROUNDS; round++) {
        DList l;
        dl_init(&l);

        /* build_back: O(1) per push thanks to the tail pointer */
        double t0 = now_ms();
        for (int i = 0; i < BUILD_N; i++) {
            if (dl_push_back(&l, i) != OK) return 1;
            handles[i] = l.tail;
        }
        double t1 = now_ms();
        if (t1 - t0 < best_b) best_b = t1 - t0;
        sum_b = 0;
        for (const Node *c = l.head; c != NULL; c = c->next) sum_b += c->value;

        /* traverse: even passes forward, odd passes backward */
        t0 = now_ms();
        sum_t = 0;
        for (int p = 0; p < PASSES; p++) {
            if (p % 2 == 0) {
                for (const Node *c = l.head; c != NULL; c = c->next) sum_t += c->value;
            } else {
                for (const Node *c = l.tail; c != NULL; c = c->prev) sum_t += c->value;
            }
        }
        t1 = now_ms();
        if (t1 - t0 < best_t) best_t = t1 - t0;

        /* remove_held: drop every even-indexed node by handle, O(1) each */
        t0 = now_ms();
        for (int i = 0; i < BUILD_N; i += 2) {
            int removed = 0;
            dl_remove_node(&l, handles[i], &removed);
        }
        t1 = now_ms();
        if (t1 - t0 < best_r) best_r = t1 - t0;
        sum_r = 0;
        for (const Node *c = l.head; c != NULL; c = c->next) sum_r += c->value;

        /* pop_back: O(1) each -- quadratic on a singly linked list */
        t0 = now_ms();
        sum_p = 0;
        for (long long step = 1; l.len > 0; step++) {
            int removed = 0;
            dl_pop_back(&l, &removed);
            sum_p += step * removed;
        }
        t1 = now_ms();
        if (t1 - t0 < best_p) best_p = t1 - t0;
        dl_clear(&l);

        /* index_access: O(min(i, n-i)) per get */
        DList g;
        dl_init(&g);
        for (int i = 0; i < IDX_N; i++) {
            if (dl_push_back(&g, i) != OK) return 1;
        }
        t0 = now_ms();
        sum_g = 0;
        for (int k = 0; k < IDX_GETS; k++) {
            int out = 0, fh = 0;
            long st = 0;
            dl_get(&g, (long)((k * 97) % IDX_N), &out, &fh, &st);
            sum_g += out;
        }
        t1 = now_ms();
        if (t1 - t0 < best_g) best_g = t1 - t0;
        dl_clear(&g);
    }
    free(handles);

    printf("build_back    checksum=%lld time_ms=%.3f\n", sum_b, best_b);
    printf("traverse      checksum=%lld time_ms=%.3f\n", sum_t, best_t);
    printf("remove_held   checksum=%lld time_ms=%.3f\n", sum_r, best_r);
    printf("pop_back      checksum=%lld time_ms=%.3f\n", sum_p, best_p);
    printf("index_access  checksum=%lld time_ms=%.3f\n", sum_g, best_g);
    return 0;
}

int main(int argc, char **argv) {
    if (argc > 1 && strcmp(argv[1], "bench") == 0) return bench();
    return demo();
}
