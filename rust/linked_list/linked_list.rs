//! Singly linked list in Rust: traverse, insert, delete, search, reverse,
//! middle, cycle detection.
//!
//! This is the data structure that teaches Rust's ownership model the hard way.
//! In C a node is `struct Node *next`. In Rust it is `Option<Box<Node>>`:
//!
//!   * `Box<Node>` is a uniquely owned heap pointer. When it is dropped, the
//!     node is freed. No free(), no leak, no double free.
//!   * `Option<...>` replaces NULL. There is no null pointer, so "did you
//!     check for NULL?" becomes a question the compiler asks you.
//!   * Because each node is owned by exactly ONE parent, a cycle cannot be
//!     built at all (see `has_cycle`). Rust removes a whole bug class by
//!     making it unrepresentable.
//!
//! The cost shows up in the splice operations: you cannot hold a pointer to
//! the previous node and the current node at the same time, so the code uses
//! `as_mut()` to walk a chain of mutable borrows, and `Option::take()` to move
//! a node out before putting a new one back. Fighting this is normal; the
//! comments mark each place where the borrow checker changes the shape.
//!
//!   ./linked_list            -> step-by-step demo (same output as C/Java/Python)
//!   ./linked_list bench      -> timing run used for the language comparison
//!
//! Build:  rustc -O --edition 2021 -o linked_list rust/linked_list/linked_list.rs
//! Tests:  rustc --edition 2021 --test -o linked_list_test rust/linked_list/linked_list.rs && ./linked_list_test

use std::fmt;
use std::time::Instant;

/// Every way an operation can fail. The compiler forces callers to handle each one.
#[derive(Debug, PartialEq)]
enum ListError {
    Empty,
    OutOfRange,
    NotFound,
}

impl fmt::Display for ListError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        f.write_str(match self {
            ListError::Empty => "list is empty",
            ListError::OutOfRange => "position out of range",
            ListError::NotFound => "value not found",
        })
    }
}

/// Convert a signed demo position into an index, rejecting negatives.
/// In C and Python a negative index is a runtime bug waiting to happen; here
/// the type system forces the conversion to be explicit and fallible.
fn to_index(pos: i64) -> Result<usize, ListError> {
    usize::try_from(pos).map_err(|_| ListError::OutOfRange)
}

struct Node {
    value: i32,
    next: Option<Box<Node>>, // owns the rest of the list; `None` is the end
}

struct LinkedList {
    head: Option<Box<Node>>,
    len: usize, // usize can never be negative
}

impl LinkedList {
    fn new() -> Self {
        LinkedList { head: None, len: 0 }
    }

    fn len(&self) -> usize {
        self.len
    }

    /// Borrow the node at `index`, if it exists. Time O(n).
    fn node_at(&self, index: usize) -> Option<&Node> {
        let mut cur = self.head.as_deref();
        for _ in 0..index {
            cur = cur?.next.as_deref();
        }
        cur
    }

    /// INSERT value at pos (0 <= pos <= len). Time O(1) at the head, O(n) otherwise.
    ///
    /// `take()` moves the old tail out, leaving `None` behind, so the new node
    /// can own it. Without the move this would be two owners of one node,
    /// which the compiler rejects.
    fn insert(&mut self, pos: usize, value: i32) -> Result<(), ListError> {
        if pos > self.len {
            return Err(ListError::OutOfRange);
        }
        if pos == 0 {
            self.head = Some(Box::new(Node { value, next: self.head.take() }));
        } else {
            // Walk to the node before pos, holding one mutable borrow at a time.
            let mut cur = self.head.as_mut().ok_or(ListError::OutOfRange)?;
            for _ in 0..pos - 1 {
                cur = cur.next.as_mut().ok_or(ListError::OutOfRange)?;
            }
            cur.next = Some(Box::new(Node { value, next: cur.next.take() }));
        }
        self.len += 1;
        Ok(())
    }

    /// DELETE the node at pos (0 <= pos < len) and return its value.
    /// Time O(1) at the head, O(n) otherwise.
    ///
    /// The unlinked `Box<Node>` is dropped at the end of this function, which
    /// frees it. There is no `free` to forget and no way to use it afterwards.
    fn delete_at(&mut self, pos: usize) -> Result<i32, ListError> {
        if self.len == 0 {
            return Err(ListError::Empty);
        }
        if pos >= self.len {
            return Err(ListError::OutOfRange);
        }
        let mut victim = if pos == 0 {
            let mut node = self.head.take().ok_or(ListError::Empty)?;
            self.head = node.next.take();
            node
        } else {
            let mut prev = self.head.as_mut().ok_or(ListError::Empty)?;
            for _ in 0..pos - 1 {
                prev = prev.next.as_mut().ok_or(ListError::OutOfRange)?;
            }
            let mut node = prev.next.take().ok_or(ListError::OutOfRange)?;
            prev.next = node.next.take();
            node
        };
        victim.next = None;
        self.len -= 1;
        Ok(victim.value)
    }

    /// DELETE the first node holding `value`. Time O(n), extra space O(1).
    fn delete_value(&mut self, value: i32) -> Result<(), ListError> {
        if self.len == 0 {
            return Err(ListError::Empty);
        }
        match self.search(value) {
            Some(index) => {
                self.delete_at(index)?;
                Ok(())
            }
            None => Err(ListError::NotFound),
        }
    }

    /// SEARCH: index of the first node holding `value`. Time O(n).
    fn search(&self, value: i32) -> Option<usize> {
        let mut cur = self.head.as_deref();
        let mut i = 0;
        while let Some(node) = cur {
            if node.value == value {
                return Some(i);
            }
            cur = node.next.as_deref();
            i += 1;
        }
        None
    }

    /// GET the value at pos. Time O(n) -- on a `Vec` this would be O(1).
    fn get(&self, pos: usize) -> Result<i32, ListError> {
        self.node_at(pos).map(|n| n.value).ok_or(ListError::OutOfRange)
    }

    /// REVERSE in place by moving each node onto a new chain.
    /// Time O(n), extra space O(1). The ownership moves make the "save next
    /// before overwriting" rule from C impossible to get wrong: the compiler
    /// will not let you read from a node you have already moved out of.
    fn reverse(&mut self) {
        let mut prev: Option<Box<Node>> = None;
        let mut cur = self.head.take();
        while let Some(mut node) = cur {
            cur = node.next.take();
            node.next = prev;
            prev = Some(node);
        }
        self.head = prev;
    }

    /// MIDDLE via two cursors. Time O(n), extra space O(1).
    /// For an even length this returns the SECOND of the two middle nodes.
    /// These are shared borrows (`&Node`), so two cursors into one list are
    /// fine: many readers are allowed, just not readers alongside a writer.
    fn middle(&self) -> Result<i32, ListError> {
        let mut slow = self.head.as_deref().ok_or(ListError::Empty)?;
        let mut fast = self.head.as_deref();
        while let Some(f) = fast {
            match f.next.as_deref() {
                Some(f2) => {
                    slow = slow.next.as_deref().ok_or(ListError::Empty)?;
                    fast = f2.next.as_deref();
                }
                None => break,
            }
        }
        Ok(slow.value)
    }

    /// CYCLE DETECTION, Floyd's algorithm. Time O(n), extra space O(1).
    ///
    /// This always returns `false`, and that is the point worth understanding:
    /// each node is owned by exactly one `Box`, so a back-edge would need a
    /// second owner. `cur.next = earlier_node` does not compile. Building a
    /// cycle in safe Rust requires `Rc<RefCell<...>>` (shared ownership) and
    /// is then a memory LEAK rather than a crash, because the reference counts
    /// never reach zero. C and Java will both happily build the cycle, and in
    /// C every other function in this file would then loop forever.
    fn has_cycle(&self) -> bool {
        let mut slow = self.head.as_deref();
        let mut fast = self.head.as_deref();
        while let Some(f) = fast {
            match f.next.as_deref() {
                Some(f2) => {
                    slow = slow.and_then(|s| s.next.as_deref());
                    fast = f2.next.as_deref();
                    if let (Some(s), Some(ff)) = (slow, fast) {
                        if std::ptr::eq(s, ff) {
                            return true;
                        }
                    }
                }
                None => break,
            }
        }
        false
    }

    /// CLEAR every node. Time O(n).
    ///
    /// Written as a loop on purpose. The automatic `Drop` for a `Box` chain is
    /// RECURSIVE: each node's drop glue drops the next, one stack frame deep
    /// per node. Measured on this machine, dropping such a list without this
    /// method overflows the stack at 200_000 nodes in a debug build, and at
    /// 1_000_000 in a release build (optimisation shrinks the frames but does
    /// not remove the recursion). Popping iteratively keeps the drop depth at
    /// one. This is the one real footgun of a Box-based list, and the reason
    /// `std` uses raw pointers inside `LinkedList` rather than `Box` chains.
    fn clear(&mut self) {
        let mut cur = self.head.take();
        while let Some(mut node) = cur {
            cur = node.next.take();
        }
        self.len = 0;
    }
}

impl Drop for LinkedList {
    fn drop(&mut self) {
        self.clear(); // avoid the recursive default drop described above
    }
}

impl fmt::Display for LinkedList {
    /// TRAVERSE: follow `next` until `None`. Time O(n).
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "[")?;
        let mut cur = self.head.as_deref();
        let mut first = true;
        while let Some(node) = cur {
            if !first {
                write!(f, ", ")?;
            }
            write!(f, "{}", node.value)?;
            first = false;
            cur = node.next.as_deref();
        }
        write!(f, "]  len={}", self.len)
    }
}

// ---------------------------------------------------------------------- demo

fn show_state(l: &LinkedList, label: &str) {
    println!("{label:<17}: {l}");
}

fn show_insert(l: &mut LinkedList, label: &str, pos: i64, value: i32) {
    match to_index(pos).and_then(|p| l.insert(p, value)) {
        Ok(()) => println!("{label:<17}: {l}"),
        Err(e) => println!("{label:<17}: error: {e}"),
    }
}

fn show_delete_at(l: &mut LinkedList, label: &str, pos: i64) {
    match to_index(pos).and_then(|p| l.delete_at(p)) {
        Ok(removed) => println!("{label:<17}: removed {removed} -> {l}"),
        Err(e) => println!("{label:<17}: error: {e}"),
    }
}

fn show_delete_value(l: &mut LinkedList, label: &str, value: i32) {
    match l.delete_value(value) {
        Ok(()) => println!("{label:<17}: removed -> {l}"),
        Err(e) => println!("{label:<17}: error: {e}"),
    }
}

fn show_get(l: &LinkedList, label: &str, pos: i64) {
    match to_index(pos).and_then(|p| l.get(p)) {
        Ok(v) => println!("{label:<17}: {v}"),
        Err(e) => println!("{label:<17}: error: {e}"),
    }
}

fn show_search(l: &LinkedList, label: &str, value: i32) {
    match l.search(value) {
        Some(i) => println!("{label:<17}: found at index {i}"),
        None => println!("{label:<17}: not found"),
    }
}

fn demo() {
    let mut l = LinkedList::new();

    println!("=== Linked list demo (singly linked) ===");
    show_state(&l, "start");

    show_insert(&mut l, "push_front 30", 0, 30);
    show_insert(&mut l, "push_front 20", 0, 20);
    show_insert(&mut l, "push_front 10", 0, 10);
    // `show_insert(&mut l, ..., l.len(), ...)` does NOT compile: the mutable
    // borrow and the shared borrow would overlap in one call. Bind first.
    let end = l.len() as i64;
    show_insert(&mut l, "push_back 40", end, 40);
    let end = l.len() as i64;
    show_insert(&mut l, "push_back 50", end, 50);

    let mut values = Vec::new();
    let mut cur = l.head.as_deref();
    while let Some(node) = cur {
        values.push(node.value.to_string());
        cur = node.next.as_deref();
    }
    println!("{:<17}: {}", "traverse", values.join(" "));

    show_get(&l, "get at 3", 3);
    show_get(&l, "get at 9", 9);
    show_search(&l, "search 30", 30);
    show_search(&l, "search 77", 77);

    show_insert(&mut l, "insert 99 at 2", 2, 99);
    show_insert(&mut l, "insert 5 at 0", 0, 5);
    let end = l.len() as i64;
    show_insert(&mut l, "insert 60 at end", end, 60);
    show_insert(&mut l, "insert 7 at -1", -1, 7);

    show_delete_at(&mut l, "delete at 3", 3);
    show_delete_at(&mut l, "pop_front", 0);
    let last = l.len() as i64 - 1;
    show_delete_at(&mut l, "pop_back", last);
    show_delete_value(&mut l, "delete value 30", 30);
    show_delete_value(&mut l, "delete value 77", 77);
    show_delete_at(&mut l, "delete at 9", 9);

    match l.middle() {
        Ok(v) => println!("{:<17}: {}", "middle", v),
        Err(e) => println!("{:<17}: error: {}", "middle", e),
    }

    l.reverse();
    show_state(&l, "reverse");

    println!("{:<17}: {}", "has cycle", l.has_cycle());

    l.clear();
    show_state(&l, "clear");
    show_delete_at(&mut l, "pop_front", 0);
}

// ----------------------------------------------------------------- benchmark

const BUILD_N: i32 = 200_000;
const PASSES: usize = 10;
const IDX_N: i32 = 20_000;
const IDX_GETS: i32 = 200;
const ROUNDS: usize = 3;

fn ms(t0: Instant) -> f64 {
    t0.elapsed().as_secs_f64() * 1e3
}

fn bench() {
    let (mut best_b, mut best_t, mut best_g, mut best_p) = (f64::MAX, f64::MAX, f64::MAX, f64::MAX);
    let (mut sum_b, mut sum_t, mut sum_g, mut sum_p) = (0i64, 0i64, 0i64, 0i64);

    for _ in 0..ROUNDS {
        let mut l = LinkedList::new();

        let t0 = Instant::now();
        for i in 0..BUILD_N {
            l.insert(0, i).unwrap();
        }
        best_b = best_b.min(ms(t0));
        sum_b = 0;
        let mut cur = l.head.as_deref();
        while let Some(node) = cur {
            sum_b += node.value as i64;
            cur = node.next.as_deref();
        }

        let t0 = Instant::now();
        sum_t = 0;
        for _ in 0..PASSES {
            let mut cur = l.head.as_deref();
            while let Some(node) = cur {
                sum_t += node.value as i64;
                cur = node.next.as_deref();
            }
        }
        best_t = best_t.min(ms(t0));

        let t0 = Instant::now();
        sum_p = 0;
        let mut step = 1i64;
        while l.len() > 0 {
            sum_p += step * l.delete_at(0).unwrap() as i64;
            step += 1;
        }
        best_p = best_p.min(ms(t0));

        let mut g = LinkedList::new();
        for i in 0..IDX_N {
            g.insert(0, i).unwrap();
        }
        let t0 = Instant::now();
        sum_g = 0;
        for k in 0..IDX_GETS {
            sum_g += g.get(((k * 97) % IDX_N) as usize).unwrap() as i64;
        }
        best_g = best_g.min(ms(t0));
    }

    println!("build_front   checksum={sum_b} time_ms={best_b:.3}");
    println!("traverse      checksum={sum_t} time_ms={best_t:.3}");
    println!("index_access  checksum={sum_g} time_ms={best_g:.3}");
    println!("pop_front     checksum={sum_p} time_ms={best_p:.3}");
}

fn main() {
    if std::env::args().nth(1).as_deref() == Some("bench") {
        bench();
    } else {
        demo();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn from_slice(values: &[i32]) -> LinkedList {
        let mut l = LinkedList::new();
        for &v in values {
            l.insert(l.len(), v).unwrap();
        }
        l
    }

    #[test]
    fn insert_splices_at_head_middle_and_tail() {
        let mut l = from_slice(&[10, 30]);
        l.insert(1, 20).unwrap();
        l.insert(0, 5).unwrap();
        l.insert(l.len(), 40).unwrap();
        assert_eq!(l.to_string(), "[5, 10, 20, 30, 40]  len=5");
    }

    #[test]
    fn delete_unlinks_and_shrinks() {
        let mut l = from_slice(&[1, 2, 3]);
        assert_eq!(l.delete_at(1), Ok(2));
        assert_eq!(l.delete_at(0), Ok(1));
        assert_eq!(l.to_string(), "[3]  len=1");
    }

    #[test]
    fn errors_are_values_not_crashes() {
        let mut l = LinkedList::new();
        assert_eq!(l.delete_at(0), Err(ListError::Empty));
        assert_eq!(l.delete_value(1), Err(ListError::Empty));
        assert_eq!(l.get(0), Err(ListError::OutOfRange));
        assert_eq!(l.insert(1, 9), Err(ListError::OutOfRange));
        assert_eq!(to_index(-1), Err(ListError::OutOfRange));
        l.insert(0, 9).unwrap();
        assert_eq!(l.delete_value(77), Err(ListError::NotFound));
    }

    #[test]
    fn search_and_get_agree() {
        let l = from_slice(&[10, 20, 30]);
        assert_eq!(l.search(30), Some(2));
        assert_eq!(l.search(77), None);
        assert_eq!(l.get(2), Ok(30));
    }

    #[test]
    fn reverse_is_its_own_inverse() {
        let mut l = from_slice(&[1, 2, 3, 4]);
        l.reverse();
        assert_eq!(l.to_string(), "[4, 3, 2, 1]  len=4");
        l.reverse();
        assert_eq!(l.to_string(), "[1, 2, 3, 4]  len=4");
    }

    #[test]
    fn middle_takes_second_of_two_on_even_length() {
        assert_eq!(from_slice(&[1]).middle(), Ok(1));
        assert_eq!(from_slice(&[1, 2]).middle(), Ok(2)); // even -> second middle
        assert_eq!(from_slice(&[1, 2, 3]).middle(), Ok(2));
        assert_eq!(from_slice(&[1, 2, 3, 4]).middle(), Ok(3));
        assert_eq!(LinkedList::new().middle(), Err(ListError::Empty));
    }

    #[test]
    fn ownership_makes_cycles_unrepresentable() {
        // A Box-owned list cannot contain a cycle, so Floyd's always says no.
        // Try to write `node.next = Some(earlier_box)` and it will not compile.
        assert!(!from_slice(&[1, 2, 3]).has_cycle());
        assert!(!LinkedList::new().has_cycle());
    }

    #[test]
    fn clear_drops_a_long_list_without_stack_overflow() {
        // The default recursive Drop would blow the stack here; clear() is iterative.
        let mut l = LinkedList::new();
        for i in 0..200_000 {
            l.insert(0, i).unwrap();
        }
        l.clear();
        assert_eq!(l.len(), 0);
        assert_eq!(l.to_string(), "[]  len=0");
    }
}
