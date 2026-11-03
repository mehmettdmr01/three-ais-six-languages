use std::env;
use std::fs::File;
use std::io::Read;
use std::time::Instant;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        eprintln!("Usage: {} N GENS SEED_FILE", args[0]);
        return;
    }

    let n: usize = args[1].parse().expect("Failed to parse N");
    let gens: usize = args[2].parse().expect("Failed to parse GENS");
    let filename = &args[3];

    let mut file = File::open(filename).expect("Failed to open file");
    let mut file_bytes = Vec::new();
    file.read_to_end(&mut file_bytes).expect("Failed to read file");

    let w = (n + 63) / 64;
    let rem = n % 64;
    let last_mask: u64 = if rem == 0 { !0u64 } else { (1u64 << rem) - 1 };
    let last_bit_idx: u32 = if rem == 0 { 63 } else { (rem - 1) as u32 };

    let mut cur = vec![0u64; n * w];
    let mut nxt = vec![0u64; n * w];

    let mut file_pos = 0;
    let file_len = file_bytes.len();
    for r in 0..n {
        if file_pos >= file_len {
            break;
        }
        let mut c = 0;
        while c < n && file_pos < file_len {
            let b = file_bytes[file_pos];
            file_pos += 1;
            if b == b'1' {
                cur[r * w + (c / 64)] |= 1u64 << (c % 64);
                c += 1;
            } else if b == b'0' {
                c += 1;
            }
        }
        while file_pos < file_len && (file_bytes[file_pos] == b'\r' || file_bytes[file_pos] == b'\n') {
            file_pos += 1;
        }
    }

    let mut s1 = vec![0u64; w];
    let mut c1 = vec![0u64; w];
    let mut s1_l = vec![0u64; w];
    let mut s1_r = vec![0u64; w];
    let mut c1_l = vec![0u64; w];
    let mut c1_r = vec![0u64; w];

    let t0 = Instant::now();

    for _ in 0..gens {
        for r in 0..n {
            let r_up = if r == 0 { n - 1 } else { r - 1 };
            let r_dn = if r == n - 1 { 0 } else { r + 1 };

            let u_off = r_up * w;
            let m_off = r * w;
            let d_off = r_dn * w;

            for k in 0..w {
                let u = cur[u_off + k];
                let m = cur[m_off + k];
                let d = cur[d_off + k];
                let u_xor_m = u ^ m;
                s1[k] = u_xor_m ^ d;
                c1[k] = (u & m) | (d & u_xor_m);
            }

            for k in 0..w {
                let mut l = s1[k] << 1;
                if k > 0 {
                    l |= (s1[k - 1] >> 63) & 1;
                } else {
                    l |= (s1[w - 1] >> last_bit_idx) & 1;
                }
                if k == w - 1 {
                    l &= last_mask;
                }
                s1_l[k] = l;

                let mut right = s1[k] >> 1;
                if k < w - 1 {
                    right |= (s1[k + 1] & 1) << 63;
                } else {
                    right |= (s1[0] & 1) << last_bit_idx;
                }
                if k == w - 1 {
                    right &= last_mask;
                }
                s1_r[k] = right;

                let mut l_c = c1[k] << 1;
                if k > 0 {
                    l_c |= (c1[k - 1] >> 63) & 1;
                } else {
                    l_c |= (c1[w - 1] >> last_bit_idx) & 1;
                }
                if k == w - 1 {
                    l_c &= last_mask;
                }
                c1_l[k] = l_c;

                let mut right_c = c1[k] >> 1;
                if k < w - 1 {
                    right_c |= (c1[k + 1] & 1) << 63;
                } else {
                    right_c |= (c1[0] & 1) << last_bit_idx;
                }
                if k == w - 1 {
                    right_c &= last_mask;
                }
                c1_r[k] = right_c;
            }

            for k in 0..w {
                let s_l = s1_l[k];
                let s_c = s1[k];
                let s_r = s1_r[k];

                let c_l = c1_l[k];
                let c_c = c1[k];
                let c_r = c1_r[k];

                let s_xor = s_l ^ s_c;
                let s_s = s_xor ^ s_r;
                let c_s = (s_l & s_c) | (s_xor & s_r);

                let c_xor = c_l ^ c_c;
                let s_c_sum = c_xor ^ c_r;
                let c_c_sum = (c_l & c_c) | (c_xor & c_r);

                let b0 = s_s;
                let b1 = s_c_sum ^ c_s;
                let c_sc = s_c_sum & c_s;
                let b2 = c_c_sum ^ c_sc;
                let b3 = c_c_sum & c_sc;

                let x = b0 & b1;
                let y = b0 | b1;
                let m = cur[m_off + k];

                let mut res = (!b3) & ((x & !b2) | (!y & b2 & m));
                if k == w - 1 {
                    res &= last_mask;
                }
                nxt[m_off + k] = res;
            }
        }
        std::mem::swap(&mut cur, &mut nxt);
    }

    let elapsed = t0.elapsed();
    let sim_ms = (elapsed.as_secs_f64() * 1000.0).round() as u64;

    let mut alive: u64 = 0;
    for &val in &cur {
        alive += val.count_ones() as u64;
    }

    println!("alive={} sim_ms={}", alive, sim_ms);
}
