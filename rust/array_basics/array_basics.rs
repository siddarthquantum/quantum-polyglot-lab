//! Array basics in Rust: traverse, insert, delete.
//!
//! The array has a fixed CAPACITY (a pre-allocated boxed slice) and a SIZE
//! (slots in use). Every insert/delete keeps elements packed at 0 .. size-1.
//!
//!   ./array_basics            -> step-by-step demo (same output as C/Java/Python)
//!   ./array_basics bench      -> timing run used for the language comparison
//!
//! Build:  rustc -O --edition 2021 -o array_basics rust/array_basics/array_basics.rs
//! Tests:  rustc --edition 2021 --test -o array_basics_test rust/array_basics/array_basics.rs && ./array_basics_test

use std::fmt;
use std::time::Instant;

/// Every way an operation can fail. The compiler forces callers to handle each one.
#[derive(Debug, PartialEq)]
enum ArrayError {
    Full,
    Empty,
    OutOfRange,
}

impl fmt::Display for ArrayError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        f.write_str(match self {
            ArrayError::Full => "array is full",
            ArrayError::Empty => "array is empty",
            ArrayError::OutOfRange => "position out of range",
        })
    }
}

struct FixedArray {
    data: Box<[i32]>, // owns its memory; freed automatically when FixedArray is dropped
    size: usize,      // usize can never be negative
}

impl FixedArray {
    /// Space O(capacity).
    fn new(capacity: usize) -> Self {
        FixedArray { data: vec![0; capacity].into_boxed_slice(), size: 0 }
    }

    fn capacity(&self) -> usize {
        self.data.len()
    }

    /// Only the used part. Out-of-bounds reads panic instead of reading garbage.
    fn as_slice(&self) -> &[i32] {
        &self.data[..self.size]
    }

    /// INSERT at pos (0 <= pos <= size). Shift right from the end.
    /// Time O(n) worst (pos = 0), O(1) best (pos = size). Extra space O(1).
    fn insert(&mut self, pos: usize, value: i32) -> Result<(), ArrayError> {
        if self.size == self.capacity() {
            return Err(ArrayError::Full);
        }
        if pos > self.size {
            return Err(ArrayError::OutOfRange);
        }
        for i in (pos + 1..=self.size).rev() {
            self.data[i] = self.data[i - 1];
        }
        // Idiomatic one-liner for the loop above: self.data.copy_within(pos..self.size, pos + 1);
        self.data[pos] = value;
        self.size += 1;
        Ok(())
    }

    /// DELETE and return the element at pos (0 <= pos < size). Shift left.
    /// Time O(n) worst (pos = 0), O(1) best (pos = size-1). Extra space O(1).
    fn delete(&mut self, pos: usize) -> Result<i32, ArrayError> {
        if self.size == 0 {
            return Err(ArrayError::Empty);
        }
        if pos >= self.size {
            return Err(ArrayError::OutOfRange);
        }
        let removed = self.data[pos];
        for i in pos..self.size - 1 {
            self.data[i] = self.data[i + 1];
        }
        self.size -= 1;
        Ok(removed)
    }
}

/// TRAVERSE: visit every element once. Time O(n).
impl fmt::Display for FixedArray {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let parts: Vec<String> = self.as_slice().iter().map(|v| v.to_string()).collect();
        write!(f, "[{}]  size={}", parts.join(", "), self.size)
    }
}

// ------------------------------------------------------------------ demo

/// A position typed by a user can be negative. Rust makes the conversion to an
/// index (usize) explicit, so a negative number can never silently become an index.
fn to_index(pos: i64) -> Result<usize, ArrayError> {
    usize::try_from(pos).map_err(|_| ArrayError::OutOfRange)
}

fn show_insert(a: &mut FixedArray, text: &str, pos: i64, value: i32) {
    match to_index(pos).and_then(|p| a.insert(p, value)) {
        Ok(()) => println!("{:<17}: {}", text, a),
        Err(e) => println!("{:<17}: error: {}", text, e),
    }
}

fn show_delete(a: &mut FixedArray, text: &str, pos: i64) {
    match to_index(pos).and_then(|p| a.delete(p)) {
        Ok(removed) => println!("{:<17}: removed {} -> {}", text, removed, a),
        Err(e) => println!("{:<17}: error: {}", text, e),
    }
}

fn demo() {
    let mut a = FixedArray::new(8);
    for v in [10, 20, 30, 40, 50] {
        a.insert(a.size, v).expect("capacity 8 holds 5 values");
    }

    println!("=== Array basics demo (capacity {}) ===", a.capacity());
    println!("{:<17}: {}", "start", a);
    let walk: Vec<String> = a.as_slice().iter().map(|v| v.to_string()).collect();
    println!("{:<17}: {}", "traverse", walk.join(" "));
    println!("{:<17}: {}", "access a[3]", a.as_slice()[3]);

    show_insert(&mut a, "insert 99 at 2", 2, 99);
    show_insert(&mut a, "insert 5 at 0", 0, 5);
    let end = a.size as i64;
    show_insert(&mut a, "insert 60 at end", end, 60);
    show_insert(&mut a, "insert 1 at 0", 0, 1); // full
    show_delete(&mut a, "delete at 3", 3);
    show_delete(&mut a, "delete at 0", 0);
    let last = a.size as i64 - 1;
    show_delete(&mut a, "delete at end", last);
    show_delete(&mut a, "delete at 9", 9); // out of range
    show_insert(&mut a, "insert 7 at -1", -1, 7); // negative index
}

// ------------------------------------------------------------- benchmark

const TRAVERSE_N: usize = 1_000_000;
const TRAVERSE_PASSES: usize = 10;
const SHIFT_K: usize = 5_000;
const ROUNDS: usize = 3;

fn ms(t0: Instant) -> f64 {
    t0.elapsed().as_secs_f64() * 1e3
}

fn bench() {
    let (mut best_t, mut best_i, mut best_d) = (f64::MAX, f64::MAX, f64::MAX);
    let (mut sum_t, mut sum_i, mut sum_d) = (0i64, 0i64, 0i64);

    for _ in 0..ROUNDS {
        let mut a = FixedArray::new(TRAVERSE_N);
        for i in 0..TRAVERSE_N {
            a.insert(a.size, i as i32).unwrap();
        }

        let t0 = Instant::now();
        sum_t = 0;
        for _ in 0..TRAVERSE_PASSES {
            for i in 0..a.size {
                sum_t += a.data[i] as i64;
            }
        }
        best_t = best_t.min(ms(t0));

        let mut a = FixedArray::new(SHIFT_K);
        let t0 = Instant::now();
        for i in 0..SHIFT_K {
            a.insert(0, i as i32).unwrap(); // worst case
        }
        best_i = best_i.min(ms(t0));
        sum_i = a.as_slice().iter().enumerate().map(|(j, &v)| j as i64 * v as i64).sum();

        let t0 = Instant::now();
        sum_d = 0;
        let mut step = 1i64;
        while a.size > 0 {
            sum_d += step * a.delete(0).unwrap() as i64; // worst case
            step += 1;
        }
        best_d = best_d.min(ms(t0));
    }

    println!("traverse      checksum={} time_ms={:.3}", sum_t, best_t);
    println!("insert_front  checksum={} time_ms={:.3}", sum_i, best_i);
    println!("delete_front  checksum={} time_ms={:.3}", sum_d, best_d);
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

    #[test]
    fn insert_shifts_right() {
        let mut a = FixedArray::new(4);
        a.insert(0, 1).unwrap();
        a.insert(1, 3).unwrap();
        a.insert(1, 2).unwrap();
        assert_eq!(a.as_slice(), &[1, 2, 3]);
    }

    #[test]
    fn delete_shifts_left() {
        let mut a = FixedArray::new(4);
        for v in [1, 2, 3] {
            a.insert(a.size, v).unwrap();
        }
        assert_eq!(a.delete(0), Ok(1));
        assert_eq!(a.as_slice(), &[2, 3]);
    }

    #[test]
    fn errors_are_values_not_crashes() {
        let mut a = FixedArray::new(1);
        assert_eq!(a.delete(0), Err(ArrayError::Empty));
        assert_eq!(a.insert(1, 9), Err(ArrayError::OutOfRange));
        a.insert(0, 9).unwrap();
        assert_eq!(a.insert(0, 9), Err(ArrayError::Full));
        assert_eq!(to_index(-1), Err(ArrayError::OutOfRange));
    }
}
