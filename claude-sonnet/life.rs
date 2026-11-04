use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let n: usize = args[1].parse().unwrap();
    let gens: usize = args[2].parse().unwrap();
    let buf = std::fs::read(&args[3]).unwrap();
    let w = (n + 63) / 64;
    let l = n - 64 * (w - 1);
    let lm: u64 = if l == 64 { !0 } else { (1u64 << l) - 1 };
    let mut cur = vec![0u64; n * w];
    let mut nxt = vec![0u64; n * w];
    let mut we = vec![0u64; n * w];
    let mut ee = vec![0u64; n * w];
    let mut k = 0usize;
    for &c in buf.iter() {
        if k >= n * n {
            break;
        }
        if c == b'1' {
            let (r, q) = (k / n, k % n);
            cur[r * w + q / 64] |= 1u64 << (q % 64);
            k += 1;
        } else if c == b'0' {
            k += 1;
        }
    }
    let t0 = Instant::now();
    for _ in 0..gens {
        for r in 0..n {
            let row = &cur[r * w..(r + 1) * w];
            let wr = &mut we[r * w..(r + 1) * w];
            let er = &mut ee[r * w..(r + 1) * w];
            for i in 0..w {
                let x = row[i];
                let e = if i < w - 1 {
                    (x >> 1) | (row[i + 1] << 63)
                } else {
                    (x >> 1) | ((row[0] & 1) << (l - 1))
                };
                let mut wv = if i > 0 {
                    (x << 1) | (row[i - 1] >> 63)
                } else {
                    (x << 1) | ((row[w - 1] >> (l - 1)) & 1)
                };
                if i == w - 1 {
                    wv &= lm;
                }
                wr[i] = wv;
                er[i] = e;
            }
        }
        for r in 0..n {
            let ru = if r == 0 { n - 1 } else { r - 1 };
            let rd = if r == n - 1 { 0 } else { r + 1 };
            let uw = &we[ru * w..(ru + 1) * w];
            let ue = &ee[ru * w..(ru + 1) * w];
            let uc = &cur[ru * w..(ru + 1) * w];
            let mw = &we[r * w..(r + 1) * w];
            let me = &ee[r * w..(r + 1) * w];
            let mc = &cur[r * w..(r + 1) * w];
            let dw = &we[rd * w..(rd + 1) * w];
            let de = &ee[rd * w..(rd + 1) * w];
            let dc = &cur[rd * w..(rd + 1) * w];
            let o = &mut nxt[r * w..(r + 1) * w];
            for i in 0..w {
                let (a, b, c) = (uw[i], uc[i], ue[i]);
                let s1 = a ^ b ^ c;
                let c1 = (a & b) | (c & (a ^ b));
                let (d, e) = (mw[i], me[i]);
                let s2 = d ^ e;
                let c2 = d & e;
                let (a, b, c) = (dw[i], dc[i], de[i]);
                let s3 = a ^ b ^ c;
                let c3 = (a & b) | (c & (a ^ b));
                let on = s1 ^ s2 ^ s3;
                let k1 = (s1 & s2) | (s3 & (s1 ^ s2));
                let par = c1 ^ c2 ^ c3 ^ k1;
                let two = (c1 & c2) | (c3 & k1) | ((c1 | c2) & (c3 | k1));
                o[i] = par & !two & (on | mc[i]);
            }
        }
        std::mem::swap(&mut cur, &mut nxt);
    }
    let ms = t0.elapsed().as_secs_f64() * 1e3;
    let alive: u64 = cur.iter().map(|x| x.count_ones() as u64).sum();
    println!("alive={} sim_ms={:.3}", alive, ms);
}
