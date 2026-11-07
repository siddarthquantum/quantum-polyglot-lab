/*
 * Doubly linked list in Java: push/pop at both ends, insert, delete, search,
 * get, O(1) removal of a held node, reverse, and a glibc-style integrity check.
 *
 * Same algorithm as the C version. The garbage collector owns the memory, so
 * there is no free() and no use-after-free -- but the four links per splice
 * still have to be kept consistent by hand. The GC protects you from memory
 * errors, not from a prev pointer that disagrees with a next pointer.
 *
 *   java DoublyLinkedListLab          -> step-by-step demo (same output as C/Python/Rust)
 *   java DoublyLinkedListLab bench    -> timing run used for the language comparison
 *
 * Build:  javac -Xlint:all -Werror -d out java/doubly_linked_list/DoublyLinkedListLab.java
 *
 * Production Java uses java.util.LinkedList (also doubly linked) or, far more
 * often, ArrayDeque, which is array-backed and faster for push/pop at the ends.
 */
import java.util.Locale;

public final class DoublyLinkedListLab {

    /** One element. The handle type: holding a Node lets you remove it in O(1). */
    static final class Node {
        int value;
        Node prev; // null on the head
        Node next; // null on the tail

        Node(int value) {
            this.value = value;
        }
    }

    /** Thrown for invalid operations. The message matches the other languages. */
    static final class ListOpException extends RuntimeException {
        private static final long serialVersionUID = 1L;

        ListOpException(String message) {
            super(message);
        }
    }

    private static final String EMPTY = "list is empty";
    private static final String RANGE = "position out of range";
    private static final String NOT_FOUND = "value not found";
    private static final String CORRUPT = "corrupted double-linked list";

    private Node head;
    private Node tail;
    private long len;

    // Set by nodeAt() so the demo can show which end the walk started from.
    private boolean lastFromHead;
    private long lastSteps;

    /** PUSH_FRONT: O(1). */
    public Node pushFront(int value) {
        Node n = new Node(value);
        n.next = head;
        if (head != null) {
            head.prev = n;
        } else {
            tail = n;
        }
        head = n;
        len++;
        return n;
    }

    /** PUSH_BACK: O(1) because we keep a tail reference. */
    public Node pushBack(int value) {
        Node n = new Node(value);
        n.prev = tail;
        if (tail != null) {
            tail.next = n;
        } else {
            head = n;
        }
        tail = n;
        len++;
        return n;
    }

    /** Walk from the nearer end. O(min(pos, len-1-pos)). Caller checks bounds. */
    private Node nodeAt(long pos) {
        Node cur;
        if (pos < len - pos) {
            lastFromHead = true;
            lastSteps = pos;
            cur = head;
            for (long i = 0; i < pos; i++) {
                cur = cur.next;
            }
        } else {
            lastFromHead = false;
            lastSteps = len - 1 - pos;
            cur = tail;
            for (long i = 0; i < lastSteps; i++) {
                cur = cur.prev;
            }
        }
        return cur;
    }

    /** GET: O(min(pos, n-pos)). */
    public int get(long pos) {
        if (pos < 0 || pos >= len) {
            throw new ListOpException(RANGE);
        }
        return nodeAt(pos).value;
    }

    /** INSERT before the node currently at pos (0 <= pos <= len). */
    public void insert(long pos, int value) {
        if (pos < 0 || pos > len) {
            throw new ListOpException(RANGE);
        }
        if (pos == 0) {
            pushFront(value);
            return;
        }
        if (pos == len) {
            pushBack(value);
            return;
        }
        Node succ = nodeAt(pos);
        Node n = new Node(value);
        n.prev = succ.prev; // 1. new node points at both neighbours
        n.next = succ;
        succ.prev.next = n; // 2. neighbours point at the new node
        succ.prev = n;
        len++;
    }

    /**
     * REMOVE a held node in O(1), after the same neighbour check glibc runs
     * before unlinking a free chunk. Returns the removed value.
     */
    public int removeNode(Node node) {
        if (node.prev != null ? node.prev.next != node : head != node) {
            throw new ListOpException(CORRUPT);
        }
        if (node.next != null ? node.next.prev != node : tail != node) {
            throw new ListOpException(CORRUPT);
        }
        if (node.prev != null) {
            node.prev.next = node.next;
        } else {
            head = node.next;
        }
        if (node.next != null) {
            node.next.prev = node.prev;
        } else {
            tail = node.prev;
        }
        node.prev = null;
        node.next = null;
        len--;
        return node.value;
    }

    /** POP_FRONT: O(1). */
    public int popFront() {
        if (head == null) {
            throw new ListOpException(EMPTY);
        }
        return removeNode(head);
    }

    /** POP_BACK: O(1) -- the operation a singly linked list cannot do cheaply. */
    public int popBack() {
        if (tail == null) {
            throw new ListOpException(EMPTY);
        }
        return removeNode(tail);
    }

    /** DELETE at pos: nearer-end walk plus O(1) unlink. */
    public int deleteAt(long pos) {
        if (len == 0) {
            throw new ListOpException(EMPTY);
        }
        if (pos < 0 || pos >= len) {
            throw new ListOpException(RANGE);
        }
        return removeNode(nodeAt(pos));
    }

    /** FIND: the node holding value, or null. O(n). */
    public Node find(int value) {
        for (Node cur = head; cur != null; cur = cur.next) {
            if (cur.value == value) {
                return cur;
            }
        }
        return null;
    }

    /** SEARCH: index of the first node holding value, or -1. O(n). */
    public long search(int value) {
        long i = 0;
        for (Node cur = head; cur != null; cur = cur.next, i++) {
            if (cur.value == value) {
                return i;
            }
        }
        return -1;
    }

    /** DELETE the first node holding value. */
    public void deleteValue(int value) {
        if (len == 0) {
            throw new ListOpException(EMPTY);
        }
        Node n = find(value);
        if (n == null) {
            throw new ListOpException(NOT_FOUND);
        }
        removeNode(n);
    }

    /** REVERSE: swap prev/next on every node, then swap head and tail. O(n), O(1) space. */
    public void reverse() {
        Node cur = head;
        while (cur != null) {
            Node tmp = cur.next;
            cur.next = cur.prev;
            cur.prev = tmp;
            cur = tmp;
        }
        Node tmp = head;
        head = tail;
        tail = tmp;
    }

    /**
     * INTEGRITY CHECK. Returns -2 when consistent, -1 for a corrupt list with
     * no single culprit, otherwise the index of the first bad node. O(n),
     * capped at len + 1 steps so a cycle cannot hang the check.
     */
    public long check() {
        if ((head == null) != (tail == null)) {
            return -1;
        }
        if (head != null && head.prev != null) {
            return 0;
        }
        long i = 0;
        Node prev = null;
        for (Node cur = head; cur != null; prev = cur, cur = cur.next, i++) {
            if (i > len || cur.prev != prev) {
                return i;
            }
        }
        if (prev != tail || i != len) {
            return i;
        }
        return -2;
    }

    /** CLEAR: drop both ends; the GC reclaims the chain. */
    public void clear() {
        head = null;
        tail = null;
        len = 0;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("[");
        for (Node cur = head; cur != null; cur = cur.next) {
            if (cur != head) {
                sb.append(", ");
            }
            sb.append(cur.value);
        }
        return sb.append("]  len=").append(len).toString();
    }

    // ------------------------------------------------------------------ demo

    private static void line(String label, String text) {
        System.out.printf("%-17s: %s%n", label, text);
    }

    private interface Op {
        void run();
    }

    private interface IntOp {
        int run();
    }

    private void show(String label, Op op) {
        try {
            op.run();
            line(label, toString());
        } catch (ListOpException e) {
            line(label, "error: " + e.getMessage());
        }
    }

    private void showRemoved(String label, IntOp op) {
        try {
            int removed = op.run();
            line(label, "removed " + removed + " -> " + this);
        } catch (ListOpException e) {
            line(label, "error: " + e.getMessage());
        }
    }

    private void showGet(String label, long pos) {
        try {
            int v = get(pos);
            String unit = lastSteps == 1 ? "step" : "steps";
            line(label, v + "  (" + lastSteps + " " + unit + " from " + (lastFromHead ? "head" : "tail") + ")");
        } catch (ListOpException e) {
            line(label, "error: " + e.getMessage());
        }
    }

    private void showSearch(String label, int value) {
        long idx = search(value);
        line(label, idx >= 0 ? "found at index " + idx : "not found");
    }

    private void showWalk(String label, boolean forward) {
        StringBuilder sb = new StringBuilder();
        Node start = forward ? head : tail;
        for (Node cur = start; cur != null; cur = forward ? cur.next : cur.prev) {
            if (cur != start) {
                sb.append(' ');
            }
            sb.append(cur.value);
        }
        line(label, sb.toString());
    }

    private void showCheck(String label) {
        long bad = check();
        if (bad == -2) {
            line(label, "ok");
        } else if (bad >= 0) {
            line(label, "error: " + CORRUPT + " at index " + bad);
        } else {
            line(label, "error: " + CORRUPT);
        }
    }

    private static void demo() {
        DoublyLinkedListLab l = new DoublyLinkedListLab();

        System.out.println("=== Doubly linked list demo ===");
        line("start", l.toString());

        l.show("push_back 20", () -> l.pushBack(20));
        l.show("push_back 30", () -> l.pushBack(30));
        l.show("push_front 10", () -> l.pushFront(10));
        l.show("push_back 40", () -> l.pushBack(40));
        l.show("push_back 50", () -> l.pushBack(50));

        l.showWalk("forward", true);
        l.showWalk("backward", false);

        l.showGet("get at 1", 1);
        l.showGet("get at 3", 3);
        l.showGet("get at 9", 9);
        l.showSearch("search 30", 30);
        l.showSearch("search 77", 77);

        l.show("insert 99 at 2", () -> l.insert(2, 99));
        l.show("insert 5 at 0", () -> l.insert(0, 5));
        l.show("insert 60 at end", () -> l.insert(l.len, 60));
        l.show("insert 7 at -1", () -> l.insert(-1, 7));

        l.showRemoved("pop_front", l::popFront);
        l.showRemoved("pop_back", l::popBack);
        l.showRemoved("delete at 2", () -> l.deleteAt(2));
        l.show("delete value 40", () -> l.deleteValue(40));
        l.show("delete value 77", () -> l.deleteValue(77));

        Node held = l.find(30);
        line("hold node 30", held != null ? "handle kept" : "not found");
        l.showRemoved("remove held node", () -> l.removeNode(held));

        l.reverse();
        line("reverse", l.toString());
        l.showWalk("backward", false);
        l.showCheck("integrity check");

        Node victim = l.head.next; // holds 20
        Node savedPrev = victim.prev;
        victim.prev = victim;
        line("corrupt node 20", "prev now points at itself");
        l.showCheck("integrity check");
        l.showRemoved("remove node 20", () -> l.removeNode(victim));
        victim.prev = savedPrev;
        line("repair node 20", "prev restored");
        l.showCheck("integrity check");

        l.clear();
        line("clear", l.toString());
        l.showRemoved("pop_front", l::popFront);
        l.showRemoved("pop_back", l::popBack);
    }

    // ------------------------------------------------------------- benchmark

    private static final int BUILD_N = 200000;
    private static final int PASSES = 10;
    private static final int IDX_N = 20000;
    private static final int IDX_GETS = 200;
    private static final int ROUNDS = 3;

    private static double ms(long startNanos) {
        return (System.nanoTime() - startNanos) / 1e6;
    }

    private static void bench() {
        double bestB = Double.MAX_VALUE;
        double bestT = Double.MAX_VALUE;
        double bestR = Double.MAX_VALUE;
        double bestP = Double.MAX_VALUE;
        double bestG = Double.MAX_VALUE;
        long sumB = 0;
        long sumT = 0;
        long sumR = 0;
        long sumP = 0;
        long sumG = 0;
        Node[] handles = new Node[BUILD_N];

        for (int round = 0; round < ROUNDS; round++) {
            DoublyLinkedListLab l = new DoublyLinkedListLab();

            long t0 = System.nanoTime();
            for (int i = 0; i < BUILD_N; i++) {
                handles[i] = l.pushBack(i);
            }
            bestB = Math.min(bestB, ms(t0));
            sumB = 0;
            for (Node c = l.head; c != null; c = c.next) {
                sumB += c.value;
            }

            t0 = System.nanoTime();
            sumT = 0;
            for (int p = 0; p < PASSES; p++) {
                if (p % 2 == 0) {
                    for (Node c = l.head; c != null; c = c.next) {
                        sumT += c.value;
                    }
                } else {
                    for (Node c = l.tail; c != null; c = c.prev) {
                        sumT += c.value;
                    }
                }
            }
            bestT = Math.min(bestT, ms(t0));

            t0 = System.nanoTime();
            for (int i = 0; i < BUILD_N; i += 2) {
                l.removeNode(handles[i]);
            }
            bestR = Math.min(bestR, ms(t0));
            sumR = 0;
            for (Node c = l.head; c != null; c = c.next) {
                sumR += c.value;
            }

            t0 = System.nanoTime();
            sumP = 0;
            for (long step = 1; l.len > 0; step++) {
                sumP += step * l.popBack();
            }
            bestP = Math.min(bestP, ms(t0));

            DoublyLinkedListLab g = new DoublyLinkedListLab();
            for (int i = 0; i < IDX_N; i++) {
                g.pushBack(i);
            }
            t0 = System.nanoTime();
            sumG = 0;
            for (int k = 0; k < IDX_GETS; k++) {
                sumG += g.get((k * 97) % IDX_N);
            }
            bestG = Math.min(bestG, ms(t0));
        }

        System.out.printf(Locale.ROOT, "build_back    checksum=%d time_ms=%.3f%n", sumB, bestB);
        System.out.printf(Locale.ROOT, "traverse      checksum=%d time_ms=%.3f%n", sumT, bestT);
        System.out.printf(Locale.ROOT, "remove_held   checksum=%d time_ms=%.3f%n", sumR, bestR);
        System.out.printf(Locale.ROOT, "pop_back      checksum=%d time_ms=%.3f%n", sumP, bestP);
        System.out.printf(Locale.ROOT, "index_access  checksum=%d time_ms=%.3f%n", sumG, bestG);
    }

    public static void main(String[] args) {
        if (args.length > 0 && "bench".equals(args[0])) {
            bench();
        } else {
            demo();
        }
    }
}
