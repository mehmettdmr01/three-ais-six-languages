// Conway's Game of Life on an N x N torus, bit-parallel: 64 cells per u64.
use std::env;
use std::fs;
use std::time::Instant;

// Horizontal 3-cell sum (left + self + right) of one row, as two bit planes.
#[inline(always)]
fn hsum_row(r: &[u64], h0: &mut [u64], h1: &mut [u64], lastbit: u32) {
    let w = r.len();
    let (h0, h1) = (&mut h0[..w], &mut h1[..w]);
    #[inline(always)]
    fn put(l: u64, c: u64, r: u64) -> (u64, u64) {
        let x = l ^ c;
        (x ^ r, (l & c) | (x & r))
    }
    if w == 1 {
        let c = r[0];
        let (a, b) = put((c << 1) | ((c >> lastbit) & 1), c, (c >> 1) | ((c & 1) << lastbit));
        h0[0] = a;
        h1[0] = b;
        return;
    }
    let c = r[0];
    let (a, b) = put((c << 1) | ((r[w - 1] >> lastbit) & 1), c, (c >> 1) | (r[1] << 63));
    h0[0] = a;
    h1[0] = b;
    for i in 1..w - 1 {
        let c = r[i];
        let (a, b) = put((c << 1) | (r[i - 1] >> 63), c, (c >> 1) | (r[i + 1] << 63));
        h0[i] = a;
        h1[i] = b;
    }
    let c = r[w - 1];
    let (a, b) = put((c << 1) | (r[w - 2] >> 63), c, (c >> 1) | ((r[0] & 1) << lastbit));
    h0[w - 1] = a;
    h1[w - 1] = b;
}

// Next state of one row from the 3-cell sums of the rows above, at and below.
// Total of the 3x3 block (self included): alive next iff total == 3, or total == 4 and alive.
#[inline(always)]
fn step_row(a0: &[u64], a1: &[u64], b0: &[u64], b1: &[u64], c0: &[u64], c1: &[u64],
            cur: &[u64], out: &mut [u64]) {
    let w = out.len();
    let (a0, a1, b0, b1, c0, c1, cur) =
        (&a0[..w], &a1[..w], &b0[..w], &b1[..w], &c0[..w], &c1[..w], &cur[..w]);
    for i in 0..w {
        let p = a0[i] ^ b0[i];
        let ones = p ^ c0[i];
        let carry = (a0[i] & b0[i]) | (p & c0[i]);
        let s = a1[i] ^ b1[i];
        let sc = a1[i] & b1[i];
        let t = c1[i] ^ carry;
        let tc = c1[i] & carry;
        let x = s ^ t;
        let eq3 = ones & x & !(sc | tc);
        let eq4 = !(ones | x) & ((s & t) | (sc ^ tc));
        out[i] = eq3 | (cur[i] & eq4);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        eprintln!("usage: {} N GENS SEED_FILE", args[0]);
        std::process::exit(1);
    }
    let n: usize = args[1].parse().expect("bad N");
    let gens: u64 = args[2].parse().expect("bad GENS");
    let data = fs::read(&args[3]).expect("cannot read seed file");

    let w = (n + 63) / 64;
    let lastbit = ((n - 1) & 63) as u32;
    let lastmask: u64 = if n & 63 != 0 { (1u64 << (n & 63)) - 1 } else { !0 };
    let cells = n * w;
    let mut g = vec![0u64; cells];
    let mut ng = vec![0u64; cells];
    let mut h0 = vec![0u64; cells];
    let mut h1 = vec![0u64; cells];

    let total = n * n;
    let mut k = 0usize;
    for &ch in data.iter() {
        if k >= total {
            break;
        }
        if ch == b'0' || ch == b'1' {
            if ch == b'1' {
                let (y, x) = (k / n, k % n);
                g[y * w + x / 64] |= 1u64 << (x & 63);
            }
            k += 1;
        }
    }

    let t0 = Instant::now();
    for _ in 0..gens {
        for ((r, a), b) in g.chunks_exact(w).zip(h0.chunks_exact_mut(w)).zip(h1.chunks_exact_mut(w)) {
            hsum_row(r, a, b, lastbit);
        }
        for y in 0..n {
            let up = (if y == 0 { n - 1 } else { y - 1 }) * w;
            let mid = y * w;
            let dn = (if y == n - 1 { 0 } else { y + 1 }) * w;
            let out = &mut ng[mid..mid + w];
            step_row(&h0[up..up + w], &h1[up..up + w], &h0[mid..mid + w], &h1[mid..mid + w],
                     &h0[dn..dn + w], &h1[dn..dn + w], &g[mid..mid + w], out);
            out[w - 1] &= lastmask;
        }
        std::mem::swap(&mut g, &mut ng);
    }
    let ms = t0.elapsed().as_secs_f64() * 1e3;

    let alive: u64 = g.iter().map(|v| v.count_ones() as u64).sum();
    println!("alive={} sim_ms={:.3}", alive, ms);
}
