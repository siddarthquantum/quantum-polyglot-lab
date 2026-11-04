/*
 * Singly linked list in Java: traverse, insert, delete, search, reverse,
 * middle, cycle detection.
 *
 * Same algorithm as the C version, but the runtime owns the memory: there is
 * no free(). When the last reference to a node disappears, the garbage
 * collector reclaims it. "Deleting" a node means unlinking it; it is collected
 * later, at a time Java chooses.
 *
 *   java LinkedListLab            -> step-by-step demo (same output as C/Python/Rust)
 *   java LinkedListLab bench      -> timing run used for the language comparison
 *
 * Build:  javac -Xlint:all -Werror -d out java/linked_list/LinkedListLab.java
 *
 * Named LinkedListLab, not LinkedList, so it never shadows java.util.LinkedList
 * (which is the doubly linked list you would actually use in production).
 */
public final class LinkedListLab {

    /** One element. Package-private fields keep the teaching code short. */
    private static final class Node {
        int value;
        Node next; // null marks the last node

        Node(int value, Node next) {
            this.value = value;
            this.next = next;
        }
    }

    /** Thrown for invalid operations (empty, bad position, missing value). */
    static final class ListOpException extends RuntimeException {
        private static final long serialVersionUID = 1L;

        ListOpException(String message) {
            super(message);
        }
    }

    private Node head; // null means empty
    private long len;  // kept in sync so length() is O(1)

    public long length() {
        return len;
    }

    /** TRAVERSE: follow next until null. Time O(n), extra space O(n) for the text. */
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

    /**
     * INSERT value at pos (0 <= pos <= len). Splice the new node in: it points
     * at what the previous node pointed at, then the previous node points at it.
     * Time O(1) at the head, O(n) otherwise. Extra space O(1).
     */
    public void insert(long pos, int value) {
        if (pos < 0 || pos > len) {
            throw new ListOpException("position out of range");
        }
        if (pos == 0) {
            head = new Node(value, head);
        } else {
            Node prev = head;
            for (long i = 0; i < pos - 1; i++) {
                prev = prev.next;
            }
            prev.next = new Node(value, prev.next);
        }
        len++;
    }

    /**
     * DELETE the node at pos (0 <= pos < len) and return its value.
     * Unlinking is enough: the GC frees the node once nothing refers to it.
     * Time O(1) at the head, O(n) otherwise. Extra space O(1).
     */
    public int deleteAt(long pos) {
        if (len == 0) {
            throw new ListOpException("list is empty");
        }
        if (pos < 0 || pos >= len) {
            throw new ListOpException("position out of range");
        }
        Node victim;
        if (pos == 0) {
            victim = head;
            head = victim.next;
        } else {
            Node prev = head;
            for (long i = 0; i < pos - 1; i++) {
                prev = prev.next;
            }
            victim = prev.next;
            prev.next = victim.next;
        }
        victim.next = null; // help the GC; also stops accidental traversal through it
        len--;
        return victim.value;
    }

    /** DELETE the first node holding value. Time O(n), extra space O(1). */
    public void deleteValue(int value) {
        if (len == 0) {
            throw new ListOpException("list is empty");
        }
        Node prev = null;
        Node cur = head;
        while (cur != null && cur.value != value) {
            prev = cur;
            cur = cur.next;
        }
        if (cur == null) {
            throw new ListOpException("value not found");
        }
        if (prev == null) {
            head = cur.next;
        } else {
            prev.next = cur.next;
        }
        cur.next = null;
        len--;
    }

    /** SEARCH: index of the first node holding value, or -1. Time O(n). */
    public long search(int value) {
        long i = 0;
        for (Node cur = head; cur != null; cur = cur.next, i++) {
            if (cur.value == value) {
                return i;
            }
        }
        return -1;
    }

    /** GET the value at pos. Time O(n) -- on an array this would be O(1). */
    public int get(long pos) {
        if (pos < 0 || pos >= len) {
            throw new ListOpException("position out of range");
        }
        Node cur = head;
        for (long i = 0; i < pos; i++) {
            cur = cur.next;
        }
        return cur.value;
    }

    /**
     * REVERSE in place by flipping every next pointer. Time O(n), extra space O(1).
     * Save next before overwriting cur.next, or the rest of the list is lost.
     */
    public void reverse() {
        Node prev = null;
        Node cur = head;
        while (cur != null) {
            Node next = cur.next;
            cur.next = prev;
            prev = cur;
            cur = next;
        }
        head = prev;
    }

    /**
     * MIDDLE via two pointers: fast moves two steps per one of slow, so slow
     * ends up halfway. Time O(n), extra space O(1).
     * For an even length this returns the SECOND of the two middle nodes.
     */
    public int middle() {
        if (head == null) {
            throw new ListOpException("list is empty");
        }
        Node slow = head;
        Node fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        return slow.value;
    }

    /**
     * CYCLE DETECTION, Floyd's algorithm. Time O(n), extra space O(1).
     * Java cannot stop you building a cycle (see the unit-test style check in
     * the shared README); it only stops you corrupting memory while you do.
     */
    public boolean hasCycle() {
        Node slow = head;
        Node fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                return true;
            }
        }
        return false;
    }

    /** CLEAR: drop the head and let the GC reclaim the chain. Time O(1) here. */
    public void clear() {
        head = null;
        len = 0;
    }

    // ------------------------------------------------------------------ demo

    private void showState(String label) {
        System.out.printf("%-17s: %s%n", label, this);
    }

    private void showInsert(String label, long pos, int value) {
        System.out.printf("%-17s: ", label);
        try {
            insert(pos, value);
            System.out.println(this);
        } catch (ListOpException e) {
            System.out.println("error: " + e.getMessage());
        }
    }

    private void showDeleteAt(String label, long pos) {
        System.out.printf("%-17s: ", label);
        try {
            System.out.println("removed " + deleteAt(pos) + " -> " + this);
        } catch (ListOpException e) {
            System.out.println("error: " + e.getMessage());
        }
    }

    private void showDeleteValue(String label, int value) {
        System.out.printf("%-17s: ", label);
        try {
            deleteValue(value);
            System.out.println("removed -> " + this);
        } catch (ListOpException e) {
            System.out.println("error: " + e.getMessage());
        }
    }

    private void showGet(String label, long pos) {
        System.out.printf("%-17s: ", label);
        try {
            System.out.println(get(pos));
        } catch (ListOpException e) {
            System.out.println("error: " + e.getMessage());
        }
    }

    private void showSearch(String label, int value) {
        long idx = search(value);
        System.out.printf("%-17s: %s%n", label, idx >= 0 ? "found at index " + idx : "not found");
    }

    private static void demo() {
        LinkedListLab l = new LinkedListLab();

        System.out.println("=== Linked list demo (singly linked) ===");
        l.showState("start");

        l.showInsert("push_front 30", 0, 30);
        l.showInsert("push_front 20", 0, 20);
        l.showInsert("push_front 10", 0, 10);
        l.showInsert("push_back 40", l.len, 40);
        l.showInsert("push_back 50", l.len, 50);

        System.out.printf("%-17s: ", "traverse");
        StringBuilder sb = new StringBuilder();
        for (Node cur = l.head; cur != null; cur = cur.next) {
            if (cur != l.head) {
                sb.append(' ');
            }
            sb.append(cur.value);
        }
        System.out.println(sb);

        l.showGet("get at 3", 3);
        l.showGet("get at 9", 9);
        l.showSearch("search 30", 30);
        l.showSearch("search 77", 77);

        l.showInsert("insert 99 at 2", 2, 99);
        l.showInsert("insert 5 at 0", 0, 5);
        l.showInsert("insert 60 at end", l.len, 60);
        l.showInsert("insert 7 at -1", -1, 7);

        l.showDeleteAt("delete at 3", 3);
        l.showDeleteAt("pop_front", 0);
        l.showDeleteAt("pop_back", l.len - 1);
        l.showDeleteValue("delete value 30", 30);
        l.showDeleteValue("delete value 77", 77);
        l.showDeleteAt("delete at 9", 9);

        System.out.printf("%-17s: %d%n", "middle", l.middle());

        l.reverse();
        l.showState("reverse");

        System.out.printf("%-17s: %b%n", "has cycle", l.hasCycle());

        l.clear();
        l.showState("clear");
        l.showDeleteAt("pop_front", 0);
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
        double bestG = Double.MAX_VALUE;
        double bestP = Double.MAX_VALUE;
        long sumB = 0;
        long sumT = 0;
        long sumG = 0;
        long sumP = 0;

        for (int round = 0; round < ROUNDS; round++) {
            LinkedListLab l = new LinkedListLab();

            long t0 = System.nanoTime();
            for (int i = 0; i < BUILD_N; i++) {
                l.insert(0, i);
            }
            bestB = Math.min(bestB, ms(t0));
            sumB = 0;
            for (Node cur = l.head; cur != null; cur = cur.next) {
                sumB += cur.value;
            }

            t0 = System.nanoTime();
            sumT = 0;
            for (int p = 0; p < PASSES; p++) {
                for (Node cur = l.head; cur != null; cur = cur.next) {
                    sumT += cur.value;
                }
            }
            bestT = Math.min(bestT, ms(t0));

            t0 = System.nanoTime();
            sumP = 0;
            for (long step = 1; l.len > 0; step++) {
                sumP += step * l.deleteAt(0);
            }
            bestP = Math.min(bestP, ms(t0));

            LinkedListLab g = new LinkedListLab();
            for (int i = 0; i < IDX_N; i++) {
                g.insert(0, i);
            }
            t0 = System.nanoTime();
            sumG = 0;
            for (int k = 0; k < IDX_GETS; k++) {
                sumG += g.get((k * 97) % IDX_N);
            }
            bestG = Math.min(bestG, ms(t0));
        }

        System.out.printf("build_front   checksum=%d time_ms=%.3f%n", sumB, bestB);
        System.out.printf("traverse      checksum=%d time_ms=%.3f%n", sumT, bestT);
        System.out.printf("index_access  checksum=%d time_ms=%.3f%n", sumG, bestG);
        System.out.printf("pop_front     checksum=%d time_ms=%.3f%n", sumP, bestP);
    }

    public static void main(String[] args) {
        if (args.length > 0 && "bench".equals(args[0])) {
            bench();
        } else {
            demo();
        }
    }
}
