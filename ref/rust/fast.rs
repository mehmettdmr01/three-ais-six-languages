// Same algorithm as c/fast.c: the wrap is handled only for the first and last column. The inner columns
// use iterators over three-cell windows, so there are no index bounds checks and the loop can vectorize.
use std::{env, fs};

#[inline(always)]
fn rule(n: u8, c: u8) -> u8 {
    ((n == 3) as u8) | (((n == 2) as u8) & c)
}

fn step(n: usize, cur: &[u8], next: &mut [u8]) {
    for (y, o) in next.chunks_exact_mut(n).enumerate() {
        let row = |i: usize| &cur[i * n..(i + 1) * n];
        let (u, m, d) = (row(if y == 0 { n - 1 } else { y - 1 }), row(y), row(if y == n - 1 { 0 } else { y + 1 }));
        for (o, ((u, m), d)) in o[1..n - 1].iter_mut().zip(u.windows(3).zip(m.windows(3)).zip(d.windows(3))) {
            let c = u[0] + u[1] + u[2] + m[0] + m[2] + d[0] + d[1] + d[2];
            *o = rule(c, m[1]);
        }
        o[0] = rule(u[n - 1] + u[0] + u[1] + m[n - 1] + m[1] + d[n - 1] + d[0] + d[1], m[0]);
        o[n - 1] = rule(u[n - 2] + u[n - 1] + u[0] + m[n - 2] + m[0] + d[n - 2] + d[n - 1] + d[0], m[n - 1]);
    }
}

fn main() {
    let a: Vec<String> = env::args().collect();
    let n: usize = a[1].parse().unwrap();
    let gens: usize = a[2].parse().unwrap();
    let text = fs::read(&a[3]).unwrap();
    let mut cur: Vec<u8> = text.iter().filter(|b| **b != b'\n').map(|b| (*b == b'1') as u8).collect();
    let mut next = vec![0u8; n * n];
    let t0 = std::time::Instant::now();
    for _ in 0..gens {
        step(n, &cur, &mut next);
        std::mem::swap(&mut cur, &mut next);
    }
    let sim_ms = t0.elapsed().as_secs_f64() * 1e3;
    let alive: u64 = cur.iter().map(|&b| b as u64).sum();
    println!("alive={alive} sim_ms={sim_ms:.3}");
}
