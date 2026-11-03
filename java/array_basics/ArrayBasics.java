/*
 * Array basics in Java: traverse, insert, delete.
 *
 * The array has a fixed CAPACITY (int[] length) and a SIZE (slots in use).
 * Every insert/delete keeps elements packed at indexes 0 .. size-1.
 *
 *   java ArrayBasics          -> step-by-step demo (same output as C/Python/Rust)
 *   java ArrayBasics bench    -> timing run used for the language comparison
 *
 * Build:  javac -d out java/array_basics/ArrayBasics.java && java -cp out ArrayBasics
 */
public final class ArrayBasics {

    /** Thrown for invalid operations. Java makes us handle errors explicitly. */
    static final class ArrayOpException extends Exception {
        private static final long serialVersionUID = 1L;

        ArrayOpException(String message) {
            super(message);
        }
    }

    private final int[] data; // the JVM zero-fills this and remembers its length
    private int size;

    ArrayBasics(int capacity) {
        data = new int[capacity]; // Space O(capacity)
    }

    int size() {
        return size;
    }

    int capacity() {
        return data.length;
    }

    int get(int i) {
        return data[i]; // the JVM bounds-checks this; bad i -> ArrayIndexOutOfBoundsException
    }

    /** TRAVERSE: visit every element once. Time O(n), extra space O(1). */
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < size; i++) {
            if (i > 0) sb.append(", ");
            sb.append(data[i]);
        }
        return sb.append("]  size=").append(size).toString();
    }

    /**
     * INSERT value at pos (0 <= pos <= size). Shift data[pos..size-1] one step right,
     * starting from the end. Time O(n) worst (pos = 0), O(1) best (pos = size). Space O(1).
     */
    void insert(int pos, int value) throws ArrayOpException {
        if (size == data.length) throw new ArrayOpException("array is full");
        if (pos < 0 || pos > size) throw new ArrayOpException("position out of range");
        for (int i = size; i > pos; i--) {
            data[i] = data[i - 1];
        }
        data[pos] = value;
        size++;
    }

    /**
     * DELETE and return the element at pos (0 <= pos < size). Shift data[pos+1..] one step
     * left. Time O(n) worst (pos = 0), O(1) best (pos = size-1). Space O(1).
     */
    int delete(int pos) throws ArrayOpException {
        if (size == 0) throw new ArrayOpException("array is empty");
        if (pos < 0 || pos >= size) throw new ArrayOpException("position out of range");
        int removed = data[pos];
        for (int i = pos; i < size - 1; i++) {
            data[i] = data[i + 1];
        }
        size--;
        return removed;
    }

    // ------------------------------------------------------------------ demo

    private static String label(String s) {
        return String.format("%-17s: ", s);
    }

    private static void showInsert(ArrayBasics a, String text, int pos, int value) {
        try {
            a.insert(pos, value);
            System.out.println(label(text) + a);
        } catch (ArrayOpException e) {
            System.out.println(label(text) + "error: " + e.getMessage());
        }
    }

    private static void showDelete(ArrayBasics a, String text, int pos) {
        try {
            int removed = a.delete(pos);
            System.out.println(label(text) + "removed " + removed + " -> " + a);
        } catch (ArrayOpException e) {
            System.out.println(label(text) + "error: " + e.getMessage());
        }
    }

    private static void demo() throws ArrayOpException {
        ArrayBasics a = new ArrayBasics(8);
        for (int v : new int[] {10, 20, 30, 40, 50}) a.insert(a.size(), v);

        System.out.println("=== Array basics demo (capacity " + a.capacity() + ") ===");
        System.out.println(label("start") + a);
        StringBuilder walk = new StringBuilder();
        for (int i = 0; i < a.size(); i++) walk.append(i > 0 ? " " : "").append(a.get(i));
        System.out.println(label("traverse") + walk);
        System.out.println(label("access a[3]") + a.get(3));

        showInsert(a, "insert 99 at 2", 2, 99);
        showInsert(a, "insert 5 at 0", 0, 5);
        showInsert(a, "insert 60 at end", a.size(), 60);
        showInsert(a, "insert 1 at 0", 0, 1); // full
        showDelete(a, "delete at 3", 3);
        showDelete(a, "delete at 0", 0);
        showDelete(a, "delete at end", a.size() - 1);
        showDelete(a, "delete at 9", 9); // out of range
        showInsert(a, "insert 7 at -1", -1, 7); // negative index
    }

    // ------------------------------------------------------------- benchmark

    static final int TRAVERSE_N = 1_000_000;
    static final int TRAVERSE_PASSES = 10;
    static final int SHIFT_K = 5_000;
    static final int ROUNDS = 3;

    private static void bench() throws ArrayOpException {
        double bestT = Double.MAX_VALUE, bestI = Double.MAX_VALUE, bestD = Double.MAX_VALUE;
        long sumT = 0, sumI = 0, sumD = 0;

        for (int round = 0; round < ROUNDS; round++) {
            ArrayBasics a = new ArrayBasics(TRAVERSE_N);
            for (int i = 0; i < TRAVERSE_N; i++) a.insert(a.size(), i);

            long t0 = System.nanoTime();
            sumT = 0;
            for (int p = 0; p < TRAVERSE_PASSES; p++)
                for (int i = 0; i < a.size(); i++) sumT += a.data[i];
            bestT = Math.min(bestT, (System.nanoTime() - t0) / 1e6);

            a = new ArrayBasics(SHIFT_K);
            t0 = System.nanoTime();
            for (int i = 0; i < SHIFT_K; i++) a.insert(0, i); // worst case
            bestI = Math.min(bestI, (System.nanoTime() - t0) / 1e6);
            sumI = 0;
            for (int j = 0; j < a.size(); j++) sumI += (long) j * a.data[j];

            t0 = System.nanoTime();
            sumD = 0;
            for (int step = 1; a.size() > 0; step++) sumD += (long) step * a.delete(0); // worst case
            bestD = Math.min(bestD, (System.nanoTime() - t0) / 1e6);
        }

        System.out.printf("traverse      checksum=%d time_ms=%.3f%n", sumT, bestT);
        System.out.printf("insert_front  checksum=%d time_ms=%.3f%n", sumI, bestI);
        System.out.printf("delete_front  checksum=%d time_ms=%.3f%n", sumD, bestD);
    }

    public static void main(String[] args) throws ArrayOpException {
        if (args.length > 0 && args[0].equals("bench")) bench();
        else demo();
    }
}
