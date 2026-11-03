use std::{env, fs, time::Instant};

fn halo(a: &mut [u8], n: usize, s: usize) {
    for i in 1..=n { let r = i*s; a[r] = a[r+n]; a[r+n+1] = a[r+1]; }
    unsafe {
        std::ptr::copy_nonoverlapping(a.as_ptr().add(n*s), a.as_mut_ptr(), s);
        std::ptr::copy_nonoverlapping(a.as_ptr().add(s), a.as_mut_ptr().add((n+1)*s), s);
    }
}

fn step(a: &[u8], b: &mut [u8], n: usize, s: usize) -> u64 {
    let mut alive = 0u64;
    unsafe {
        let p = a.as_ptr(); let q = b.as_mut_ptr();
        for i in 1..=n {
            let mut k = i*s + 1;
            for _ in 1..=n {
                let x = *p.add(k-s-1) + *p.add(k-s) + *p.add(k-s+1) + *p.add(k-1)
                      + *p.add(k+1) + *p.add(k+s-1) + *p.add(k+s) + *p.add(k+s+1);
                let v = (x == 3) as u8 | ((x == 2) as u8 & *p.add(k));
                *q.add(k) = v; alive += v as u64; k += 1;
            }
        }
    }
    alive
}

fn main() {
    let v: Vec<String> = env::args().collect(); if v.len() != 4 { return; }
    let n: usize = v[1].parse().unwrap(); let gens: usize = v[2].parse().unwrap();
    let s = n + 2; let mut a = vec![0u8; s*s]; let mut b = vec![0u8; s*s];
    let input = fs::read(&v[3]).unwrap(); let mut q = 0;
    for i in 1..=n { for j in 1..=n { while input[q] == b'\n' || input[q] == b'\r' { q += 1; } a[i*s+j] = (input[q] == b'1') as u8; q += 1; } }
    let start = Instant::now(); let mut alive = 0u64;
    if gens == 0 { for i in 1..=n { for j in 1..=n { alive += a[i*s+j] as u64; } } }
    for _ in 0..gens { halo(&mut a, n, s); alive = step(&a, &mut b, n, s); std::mem::swap(&mut a, &mut b); }
    println!("alive={} sim_ms={:.3}", alive, start.elapsed().as_secs_f64()*1000.0);
}
