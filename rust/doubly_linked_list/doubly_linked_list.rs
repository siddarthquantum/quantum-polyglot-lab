//! Doubly linked list in Rust: both ends O(1), held-node removal, reverse,
//! and a glibc-style integrity check.
//!
//! The singly linked list in rust/linked_list/ used `Option<Box<Node>>`: each
//! node owned the next one. That cannot work here. In a doubly linked list
//! every interior node is pointed at by TWO neighbours, and `Box` means
//! exactly one owner. There are three ways out, and the choice is the lesson:
//!
//!   1. `Rc<RefCell<Node>>` forward, `Weak` backward. Safe, but every link
//!      access is a runtime borrow check and a refcount bump, and the code is
//!      famously unpleasant.
//!   2. Raw pointers in `unsafe` blocks. This is what `std::collections::LinkedList`
//!      does. Fast, but you are back to C's rules, with no compiler help.
//!   3. An ARENA: store every node in one `Vec` and make the links `usize`
//!      indices into it. Entirely safe code, no refcounts, and the nodes sit
//!      next to each other in memory. This file uses option 3.
//!
//! An index is not a pointer, so it cannot dangle into freed memory. But a
//! freed slot is REUSED, and an old index would then name a different node:
//! the arena's version of use-after-free. It cannot corrupt memory, but it is
//! still a logic bug. The fix is a GENERATIONAL INDEX: each slot counts how
//! many times it has been freed, a `Handle` records the count it was issued
//! with, and a mismatch is rejected as `StaleHandle`.
//!
//!   ./doubly_linked_list          -> step-by-step demo (same output as C/Java/Python)
//!   ./doubly_linked_list bench    -> timing run used for the language comparison
//!
//! Build:  rustc -O --edition 2021 -o doubly_linked_list rust/doubly_linked_list/doubly_linked_list.rs
//! Tests:  rustc --edition 2021 --test -o dll_test rust/doubly_linked_list/doubly_linked_list.rs && ./dll_test

use std::fmt;
use std::time::Instant;

#[derive(Debug, PartialEq)]
enum ListError {
    Empty,
    OutOfRange,
    NotFound,
    Corrupt,
    StaleHandle,
}

impl fmt::Display for ListError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        f.write_str(match self {
            ListError::Empty => "list is empty",
            ListError::OutOfRange => "position out of range",
            ListError::NotFound => "value not found",
            ListError::Corrupt => "corrupted double-linked list",
            ListError::StaleHandle => "stale handle",
        })
    }
}

/// Reject negative demo positions explicitly; `usize` cannot hold them.
fn to_index(pos: i64) -> Result<usize, ListError> {
    usize::try_from(pos).map_err(|_| ListError::OutOfRange)
}

/// A reference to one node that survives other insertions and removals.
/// `Copy`, so holding one never borrows the list.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Handle {
    index: usize,
    generation: u32,
}

struct Slot {
    value: i32,
    prev: Option<usize>, // None on the head
    next: Option<usize>, // None on the tail
    generation: u32,     // bumped every time this slot is freed
    live: bool,
}

struct DoublyLinkedList {
    slots: Vec<Slot>,
    free: Vec<usize>, // indices of dead slots, reused before the Vec grows
    head: Option<usize>,
    tail: Option<usize>,
    len: usize,
    last_from_head: bool,
    last_steps: usize,
}

impl DoublyLinkedList {
    fn new() -> Self {
        DoublyLinkedList {
            slots: Vec::new(),
            free: Vec::new(),
            head: None,
            tail: None,
            len: 0,
            last_from_head: true,
            last_steps: 0,
        }
    }

    fn len(&self) -> usize {
        self.len
    }

    /// Take a free slot (or grow the Vec) and return its index.
    fn alloc(&mut self, value: i32) -> usize {
        match self.free.pop() {
            Some(i) => {
                let s = &mut self.slots[i];
                s.value = value;
                s.prev = None;
                s.next = None;
                s.live = true;
                i
            }
            None => {
                self.slots.push(Slot { value, prev: None, next: None, generation: 0, live: true });
                self.slots.len() - 1
            }
        }
    }

    /// Return a slot to the free list. The generation bump is what invalidates
    /// every handle that still names it.
    fn release(&mut self, i: usize) {
        let s = &mut self.slots[i];
        s.live = false;
        s.prev = None;
        s.next = None;
        s.generation = s.generation.wrapping_add(1);
        self.free.push(i);
    }

    fn handle_of(&self, i: usize) -> Handle {
        Handle { index: i, generation: self.slots[i].generation }
    }

    fn resolve(&self, h: Handle) -> Result<usize, ListError> {
        match self.slots.get(h.index) {
            Some(s) if s.live && s.generation == h.generation => Ok(h.index),
            _ => Err(ListError::StaleHandle),
        }
    }

    /// PUSH_FRONT: O(1) amortised (the Vec may grow).
    fn push_front(&mut self, value: i32) -> Handle {
        let n = self.alloc(value);
        self.slots[n].next = self.head;
        match self.head {
            Some(h) => self.slots[h].prev = Some(n),
            None => self.tail = Some(n),
        }
        self.head = Some(n);
        self.len += 1;
        self.handle_of(n)
    }

    /// PUSH_BACK: O(1) amortised.
    fn push_back(&mut self, value: i32) -> Handle {
        let n = self.alloc(value);
        self.slots[n].prev = self.tail;
        match self.tail {
            Some(t) => self.slots[t].next = Some(n),
            None => self.head = Some(n),
        }
        self.tail = Some(n);
        self.len += 1;
        self.handle_of(n)
    }

    /// Walk from the nearer end. O(min(pos, len-1-pos)). Caller checks bounds.
    fn node_at(&mut self, pos: usize) -> Result<usize, ListError> {
        let mut cur;
        if pos < self.len - pos {
            self.last_from_head = true;
            self.last_steps = pos;
            cur = self.head.ok_or(ListError::Corrupt)?;
            for _ in 0..pos {
                cur = self.slots[cur].next.ok_or(ListError::Corrupt)?;
            }
        } else {
            self.last_from_head = false;
            self.last_steps = self.len - 1 - pos;
            cur = self.tail.ok_or(ListError::Corrupt)?;
            for _ in 0..self.last_steps {
                cur = self.slots[cur].prev.ok_or(ListError::Corrupt)?;
            }
        }
        Ok(cur)
    }

    /// GET: O(min(pos, n-pos)). Takes `&mut self` only to record the walk for the demo.
    fn get(&mut self, pos: usize) -> Result<i32, ListError> {
        if pos >= self.len {
            return Err(ListError::OutOfRange);
        }
        let i = self.node_at(pos)?;
        Ok(self.slots[i].value)
    }

    /// INSERT before the node currently at pos (0 <= pos <= len).
    fn insert(&mut self, pos: usize, value: i32) -> Result<Handle, ListError> {
        if pos > self.len {
            return Err(ListError::OutOfRange);
        }
        if pos == 0 {
            return Ok(self.push_front(value));
        }
        if pos == self.len {
            return Ok(self.push_back(value));
        }
        let succ = self.node_at(pos)?;
        let pred = self.slots[succ].prev.ok_or(ListError::Corrupt)?;
        let n = self.alloc(value);
        self.slots[n].prev = Some(pred); // 1. new node points at both neighbours
        self.slots[n].next = Some(succ);
        self.slots[pred].next = Some(n); // 2. neighbours point at the new node
        self.slots[succ].prev = Some(n);
        self.len += 1;
        Ok(self.handle_of(n))
    }

    /// Unlink slot i in O(1), after glibc's safe-unlink neighbour check.
    fn unlink(&mut self, i: usize) -> Result<i32, ListError> {
        let (prev, next) = (self.slots[i].prev, self.slots[i].next);
        let prev_ok = match prev {
            Some(p) => self.slots[p].next == Some(i),
            None => self.head == Some(i),
        };
        let next_ok = match next {
            Some(n) => self.slots[n].prev == Some(i),
            None => self.tail == Some(i),
        };
        if !prev_ok || !next_ok {
            return Err(ListError::Corrupt);
        }
        match prev {
            Some(p) => self.slots[p].next = next,
            None => self.head = next,
        }
        match next {
            Some(n) => self.slots[n].prev = prev,
            None => self.tail = prev,
        }
        let value = self.slots[i].value;
        self.release(i);
        self.len -= 1;
        Ok(value)
    }

    /// REMOVE a held node: O(1). A stale handle is rejected, never misread.
    fn remove_node(&mut self, h: Handle) -> Result<i32, ListError> {
        let i = self.resolve(h)?;
        self.unlink(i)
    }

    fn pop_front(&mut self) -> Result<i32, ListError> {
        let h = self.head.ok_or(ListError::Empty)?;
        self.unlink(h)
    }

    /// POP_BACK: O(1) -- the operation a singly linked list cannot do cheaply.
    fn pop_back(&mut self) -> Result<i32, ListError> {
        let t = self.tail.ok_or(ListError::Empty)?;
        self.unlink(t)
    }

    fn delete_at(&mut self, pos: usize) -> Result<i32, ListError> {
        if self.len == 0 {
            return Err(ListError::Empty);
        }
        if pos >= self.len {
            return Err(ListError::OutOfRange);
        }
        let i = self.node_at(pos)?;
        self.unlink(i)
    }

    /// FIND: a handle to the node holding value. O(n).
    fn find(&self, value: i32) -> Option<Handle> {
        let mut cur = self.head;
        while let Some(i) = cur {
            if self.slots[i].value == value {
                return Some(self.handle_of(i));
            }
            cur = self.slots[i].next;
        }
        None
    }

    fn search(&self, value: i32) -> Option<usize> {
        let mut cur = self.head;
        let mut idx = 0;
        while let Some(i) = cur {
            if self.slots[i].value == value {
                return Some(idx);
            }
            cur = self.slots[i].next;
            idx += 1;
        }
        None
    }

    fn delete_value(&mut self, value: i32) -> Result<(), ListError> {
        if self.len == 0 {
            return Err(ListError::Empty);
        }
        let h = self.find(value).ok_or(ListError::NotFound)?;
        self.remove_node(h).map(|_| ())
    }

    /// REVERSE: swap prev/next on every node, then swap head and tail. O(n), O(1) space.
    fn reverse(&mut self) {
        let mut cur = self.head;
        while let Some(i) = cur {
            let s = &mut self.slots[i];
            std::mem::swap(&mut s.prev, &mut s.next);
            cur = s.prev; // the old next
        }
        std::mem::swap(&mut self.head, &mut self.tail);
    }

    /// INTEGRITY CHECK. `Err(Some(i))` names the first bad node, `Err(None)`
    /// means corrupt with no single culprit. Capped at len + 1 steps.
    fn check(&self) -> Result<(), Option<usize>> {
        if self.head.is_none() != self.tail.is_none() {
            return Err(None);
        }
        if let Some(h) = self.head {
            if self.slots[h].prev.is_some() {
                return Err(Some(0));
            }
        }
        let mut i = 0;
        let mut prev = None;
        let mut cur = self.head;
        while let Some(c) = cur {
            if i > self.len || self.slots[c].prev != prev {
                return Err(Some(i));
            }
            prev = Some(c);
            cur = self.slots[c].next;
            i += 1;
        }
        if prev != self.tail || i != self.len {
            return Err(Some(i));
        }
        Ok(())
    }

    /// CLEAR: free every live slot, bumping generations so old handles die too.
    /// Truncating the Vec instead would reset generations to 0 and let an old
    /// handle match a brand-new node.
    fn clear(&mut self) {
        for i in 0..self.slots.len() {
            if self.slots[i].live {
                self.release(i);
            }
        }
        self.head = None;
        self.tail = None;
        self.len = 0;
    }

    fn values(&self, forward: bool) -> Vec<i32> {
        let mut out = Vec::with_capacity(self.len);
        let mut cur = if forward { self.head } else { self.tail };
        while let Some(i) = cur {
            out.push(self.slots[i].value);
            cur = if forward { self.slots[i].next } else { self.slots[i].prev };
        }
        out
    }
}

impl fmt::Display for DoublyLinkedList {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let parts: Vec<String> = self.values(true).iter().map(|v| v.to_string()).collect();
        write!(f, "[{}]  len={}", parts.join(", "), self.len)
    }
}

// ---------------------------------------------------------------------- demo

fn line(label: &str, text: &str) {
    println!("{label:<17}: {text}");
}

fn show_state(l: &DoublyLinkedList, label: &str) {
    line(label, &l.to_string());
}

fn show_unit(l: &DoublyLinkedList, label: &str, r: Result<(), ListError>) {
    match r {
        Ok(()) => show_state(l, label),
        Err(e) => line(label, &format!("error: {e}")),
    }
}

fn show_removed(l: &DoublyLinkedList, label: &str, r: Result<i32, ListError>) {
    match r {
        Ok(v) => line(label, &format!("removed {v} -> {l}")),
        Err(e) => line(label, &format!("error: {e}")),
    }
}

fn show_get(l: &mut DoublyLinkedList, label: &str, pos: i64) {
    match to_index(pos).and_then(|p| l.get(p)) {
        Ok(v) => {
            let unit = if l.last_steps == 1 { "step" } else { "steps" };
            let end = if l.last_from_head { "head" } else { "tail" };
            line(label, &format!("{v}  ({} {unit} from {end})", l.last_steps));
        }
        Err(e) => line(label, &format!("error: {e}")),
    }
}

fn show_search(l: &DoublyLinkedList, label: &str, value: i32) {
    match l.search(value) {
        Some(i) => line(label, &format!("found at index {i}")),
        None => line(label, "not found"),
    }
}

fn show_walk(l: &DoublyLinkedList, label: &str, forward: bool) {
    let parts: Vec<String> = l.values(forward).iter().map(|v| v.to_string()).collect();
    line(label, &parts.join(" "));
}

fn show_check(l: &DoublyLinkedList, label: &str) {
    match l.check() {
        Ok(()) => line(label, "ok"),
        Err(Some(i)) => line(label, &format!("error: {} at index {i}", ListError::Corrupt)),
        Err(None) => line(label, &format!("error: {}", ListError::Corrupt)),
    }
}

fn demo() {
    let mut l = DoublyLinkedList::new();

    println!("=== Doubly linked list demo ===");
    show_state(&l, "start");

    l.push_back(20);
    show_state(&l, "push_back 20");
    l.push_back(30);
    show_state(&l, "push_back 30");
    l.push_front(10);
    show_state(&l, "push_front 10");
    l.push_back(40);
    show_state(&l, "push_back 40");
    l.push_back(50);
    show_state(&l, "push_back 50");

    show_walk(&l, "forward", true);
    show_walk(&l, "backward", false);

    show_get(&mut l, "get at 1", 1);
    show_get(&mut l, "get at 3", 3);
    show_get(&mut l, "get at 9", 9);
    show_search(&l, "search 30", 30);
    show_search(&l, "search 77", 77);

    let r = to_index(2).and_then(|p| l.insert(p, 99)).map(|_| ());
    show_unit(&l, "insert 99 at 2", r);
    let r = to_index(0).and_then(|p| l.insert(p, 5)).map(|_| ());
    show_unit(&l, "insert 5 at 0", r);
    let end = l.len() as i64; // bind first: l.len() inside a call taking &mut l won't borrow-check
    let r = to_index(end).and_then(|p| l.insert(p, 60)).map(|_| ());
    show_unit(&l, "insert 60 at end", r);
    let r = to_index(-1).and_then(|p| l.insert(p, 7)).map(|_| ());
    show_unit(&l, "insert 7 at -1", r);

    let r = l.pop_front();
    show_removed(&l, "pop_front", r);
    let r = l.pop_back();
    show_removed(&l, "pop_back", r);
    let r = l.delete_at(2);
    show_removed(&l, "delete at 2", r);
    let r = l.delete_value(40);
    show_unit(&l, "delete value 40", r);
    let r = l.delete_value(77);
    show_unit(&l, "delete value 77", r);

    let held = l.find(30);
    line("hold node 30", if held.is_some() { "handle kept" } else { "not found" });
    let r = held.ok_or(ListError::NotFound).and_then(|h| l.remove_node(h));
    show_removed(&l, "remove held node", r);

    l.reverse();
    show_state(&l, "reverse");
    show_walk(&l, "backward", false);
    show_check(&l, "integrity check");

    // Corrupt one back link on purpose. Safe Rust cannot overflow a buffer to
    // do this, but a logic bug inside the module can, so the check still matters.
    let victim = l.head.and_then(|h| l.slots[h].next).expect("demo list has a second node");
    let saved_prev = l.slots[victim].prev;
    l.slots[victim].prev = Some(victim);
    line("corrupt node 20", "prev now points at itself");
    show_check(&l, "integrity check");
    let r = l.remove_node(l.handle_of(victim));
    show_removed(&l, "remove node 20", r);
    l.slots[victim].prev = saved_prev;
    line("repair node 20", "prev restored");
    show_check(&l, "integrity check");

    l.clear();
    show_state(&l, "clear");
    let r = l.pop_front();
    show_removed(&l, "pop_front", r);
    let r = l.pop_back();
    show_removed(&l, "pop_back", r);
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

fn sum_forward(l: &DoublyLinkedList) -> i64 {
    let mut s = 0i64;
    let mut cur = l.head;
    while let Some(i) = cur {
        s += l.slots[i].value as i64;
        cur = l.slots[i].next;
    }
    s
}

fn bench() {
    let (mut best_b, mut best_t, mut best_r, mut best_p, mut best_g) = (f64::MAX, f64::MAX, f64::MAX, f64::MAX, f64::MAX);
    let (mut sum_b, mut sum_t, mut sum_r, mut sum_p, mut sum_g) = (0i64, 0i64, 0i64, 0i64, 0i64);
    let mut handles: Vec<Handle> = Vec::with_capacity(BUILD_N as usize);

    for _ in 0..ROUNDS {
        let mut l = DoublyLinkedList::new();
        handles.clear();

        let t0 = Instant::now();
        for i in 0..BUILD_N {
            handles.push(l.push_back(i));
        }
        best_b = best_b.min(ms(t0));
        sum_b = sum_forward(&l);

        let t0 = Instant::now();
        sum_t = 0;
        for p in 0..PASSES {
            let forward = p % 2 == 0;
            let mut cur = if forward { l.head } else { l.tail };
            while let Some(i) = cur {
                sum_t += l.slots[i].value as i64;
                cur = if forward { l.slots[i].next } else { l.slots[i].prev };
            }
        }
        best_t = best_t.min(ms(t0));

        let t0 = Instant::now();
        for h in handles.iter().step_by(2) {
            l.remove_node(*h).unwrap();
        }
        best_r = best_r.min(ms(t0));
        sum_r = sum_forward(&l);

        let t0 = Instant::now();
        sum_p = 0;
        let mut step = 1i64;
        while l.len() > 0 {
            sum_p += step * l.pop_back().unwrap() as i64;
            step += 1;
        }
        best_p = best_p.min(ms(t0));

        let mut g = DoublyLinkedList::new();
        for i in 0..IDX_N {
            g.push_back(i);
        }
        let t0 = Instant::now();
        sum_g = 0;
        for k in 0..IDX_GETS {
            sum_g += g.get(((k * 97) % IDX_N) as usize).unwrap() as i64;
        }
        best_g = best_g.min(ms(t0));
    }

    println!("build_back    checksum={sum_b} time_ms={best_b:.3}");
    println!("traverse      checksum={sum_t} time_ms={best_t:.3}");
    println!("remove_held   checksum={sum_r} time_ms={best_r:.3}");
    println!("pop_back      checksum={sum_p} time_ms={best_p:.3}");
    println!("index_access  checksum={sum_g} time_ms={best_g:.3}");
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

    fn from_slice(values: &[i32]) -> DoublyLinkedList {
        let mut l = DoublyLinkedList::new();
        for &v in values {
            l.push_back(v);
        }
        l
    }

    #[test]
    fn both_ends_are_constant_time_operations() {
        let mut l = from_slice(&[2, 3]);
        l.push_front(1);
        l.push_back(4);
        assert_eq!(l.pop_front(), Ok(1));
        assert_eq!(l.pop_back(), Ok(4));
        assert_eq!(l.to_string(), "[2, 3]  len=2");
        assert_eq!(l.check(), Ok(()));
    }

    #[test]
    fn get_walks_from_the_nearer_end() {
        let mut l = from_slice(&[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
        assert_eq!(l.get(2), Ok(2));
        assert!(l.last_from_head && l.last_steps == 2);
        assert_eq!(l.get(8), Ok(8));
        assert!(!l.last_from_head && l.last_steps == 1);
    }

    #[test]
    fn insert_links_both_directions() {
        let mut l = from_slice(&[10, 30]);
        l.insert(1, 20).unwrap();
        assert_eq!(l.values(true), vec![10, 20, 30]);
        assert_eq!(l.values(false), vec![30, 20, 10]);
        assert_eq!(l.insert(4, 1), Err(ListError::OutOfRange));
        assert_eq!(l.check(), Ok(()));
    }

    #[test]
    fn held_node_removal_needs_no_walk() {
        let mut l = from_slice(&[1, 2, 3]);
        let h = l.find(2).unwrap();
        assert_eq!(l.remove_node(h), Ok(2));
        assert_eq!(l.values(false), vec![3, 1]);
    }

    #[test]
    fn generations_reject_a_handle_to_a_reused_slot() {
        let mut l = from_slice(&[1, 2, 3]);
        let old = l.find(2).unwrap();
        l.remove_node(old).unwrap();
        let fresh = l.push_back(99); // reuses the freed slot
        assert_eq!(fresh.index, old.index);
        assert_eq!(l.remove_node(old), Err(ListError::StaleHandle));
        assert_eq!(l.remove_node(fresh), Ok(99));
    }

    #[test]
    fn clear_invalidates_every_handle() {
        let mut l = from_slice(&[1, 2]);
        let h = l.find(1).unwrap();
        l.clear();
        l.push_back(5); // may land in h's old slot
        assert_eq!(l.remove_node(h), Err(ListError::StaleHandle));
    }

    #[test]
    fn corruption_is_detected_and_unlink_refuses() {
        let mut l = from_slice(&[1, 2, 3]);
        let mid = l.slots[l.head.unwrap()].next.unwrap();
        l.slots[mid].prev = Some(mid);
        assert_eq!(l.check(), Err(Some(1)));
        assert_eq!(l.remove_node(l.handle_of(mid)), Err(ListError::Corrupt));
    }

    #[test]
    fn reverse_twice_is_identity_and_stays_consistent() {
        let mut l = from_slice(&[1, 2, 3, 4]);
        l.reverse();
        assert_eq!(l.values(true), vec![4, 3, 2, 1]);
        assert_eq!(l.check(), Ok(()));
        l.reverse();
        assert_eq!(l.values(true), vec![1, 2, 3, 4]);
    }

    #[test]
    fn empty_list_errors_are_values() {
        let mut l = DoublyLinkedList::new();
        assert_eq!(l.pop_front(), Err(ListError::Empty));
        assert_eq!(l.pop_back(), Err(ListError::Empty));
        assert_eq!(l.delete_value(1), Err(ListError::Empty));
        assert_eq!(to_index(-1), Err(ListError::OutOfRange));
        assert_eq!(l.check(), Ok(()));
    }
}
