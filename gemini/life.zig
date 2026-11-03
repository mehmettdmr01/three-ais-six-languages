const std = @import("std");

extern "c" fn fseek(stream: *std.c.FILE, offset: c_long, whence: c_int) c_int;
extern "c" fn ftell(stream: *std.c.FILE) c_long;

pub fn main(init: std.process.Init) !void {
    var iter = std.process.Args.Iterator.init(init.minimal.args);
    _ = iter.next(); // program name
    const n_str = iter.next() orelse return;
    const gens_str = iter.next() orelse return;
    const filename_str = iter.next() orelse return;

    const N = try std.fmt.parseInt(usize, n_str, 10);
    const GENS = try std.fmt.parseInt(usize, gens_str, 10);

    const f = std.c.fopen(filename_str.ptr, "rb") orelse return;
    defer _ = std.c.fclose(f);

    _ = fseek(f, 0, 2); // SEEK_END
    const file_size: usize = @intCast(ftell(f));
    _ = fseek(f, 0, 0); // SEEK_SET

    const allocator = std.heap.c_allocator;
    const file_buf = try allocator.alloc(u8, file_size);
    defer allocator.free(file_buf);
    _ = std.c.fread(file_buf.ptr, 1, file_size, f);

    const W = (N + 63) / 64;
    const rem: u6 = @intCast(N % 64);
    const last_mask: u64 = if (rem == 0) ~@as(u64, 0) else (@as(u64, 1) << rem) - 1;
    const last_bit_idx: u6 = if (rem == 0) 63 else rem - 1;

    var cur = try allocator.alloc(u64, N * W);
    defer allocator.free(cur);
    @memset(cur, 0);

    var nxt = try allocator.alloc(u64, N * W);
    defer allocator.free(nxt);
    @memset(nxt, 0);

    var file_idx: usize = 0;
    var r: usize = 0;
    while (r < N and file_idx < file_size) : (r += 1) {
        var c: usize = 0;
        while (c < N and file_idx < file_size) {
            const ch = file_buf[file_idx];
            file_idx += 1;
            if (ch == '1') {
                cur[r * W + (c / 64)] |= @as(u64, 1) << @intCast(c % 64);
                c += 1;
            } else if (ch == '0') {
                c += 1;
            }
        }
        while (file_idx < file_size and (file_buf[file_idx] == '\r' or file_buf[file_idx] == '\n')) {
            file_idx += 1;
        }
    }

    var s1 = try allocator.alloc(u64, W);
    defer allocator.free(s1);
    var c1 = try allocator.alloc(u64, W);
    defer allocator.free(c1);
    var s1_l = try allocator.alloc(u64, W);
    defer allocator.free(s1_l);
    var s1_r = try allocator.alloc(u64, W);
    defer allocator.free(s1_r);
    var c1_l = try allocator.alloc(u64, W);
    defer allocator.free(c1_l);
    var c1_r = try allocator.alloc(u64, W);
    defer allocator.free(c1_r);

    var ts0: std.c.timespec = undefined;
    var ts1: std.c.timespec = undefined;
    _ = std.c.clock_gettime(std.c.CLOCK.MONOTONIC, &ts0);

    for (0..GENS) |_| {
        for (0..N) |row_idx| {
            const r_up = if (row_idx == 0) N - 1 else row_idx - 1;
            const r_dn = if (row_idx == N - 1) 0 else row_idx + 1;

            const u_off = r_up * W;
            const m_off = row_idx * W;
            const d_off = r_dn * W;

            for (0..W) |k| {
                const u = cur[u_off + k];
                const m = cur[m_off + k];
                const d = cur[d_off + k];
                const u_xor_m = u ^ m;
                s1[k] = u_xor_m ^ d;
                c1[k] = (u & m) | (d & u_xor_m);
            }

            for (0..W) |k| {
                var l = s1[k] << 1;
                if (k > 0) {
                    l |= (s1[k - 1] >> 63) & 1;
                } else {
                    l |= (s1[W - 1] >> last_bit_idx) & 1;
                }
                if (k == W - 1) l &= last_mask;
                s1_l[k] = l;

                var right = s1[k] >> 1;
                if (k < W - 1) {
                    right |= (s1[k + 1] & 1) << 63;
                } else {
                    right |= (s1[0] & 1) << last_bit_idx;
                }
                if (k == W - 1) right &= last_mask;
                s1_r[k] = right;

                var l_c = c1[k] << 1;
                if (k > 0) {
                    l_c |= (c1[k - 1] >> 63) & 1;
                } else {
                    l_c |= (c1[W - 1] >> last_bit_idx) & 1;
                }
                if (k == W - 1) l_c &= last_mask;
                c1_l[k] = l_c;

                var right_c = c1[k] >> 1;
                if (k < W - 1) {
                    right_c |= (c1[k + 1] & 1) << 63;
                } else {
                    right_c |= (c1[0] & 1) << last_bit_idx;
                }
                if (k == W - 1) right_c &= last_mask;
                c1_r[k] = right_c;
            }

            for (0..W) |k| {
                const sL = s1_l[k];
                const sC = s1[k];
                const sR = s1_r[k];

                const cL = c1_l[k];
                const cC = c1[k];
                const cR = c1_r[k];

                const s_xor = sL ^ sC;
                const s_s = s_xor ^ sR;
                const c_s = (sL & sC) | (s_xor & sR);

                const c_xor = cL ^ cC;
                const s_c_sum = c_xor ^ cR;
                const c_c_sum = (cL & cC) | (c_xor & cR);

                const b0 = s_s;
                const b1 = s_c_sum ^ c_s;
                const c_sc = s_c_sum & c_s;
                const b2 = c_c_sum ^ c_sc;
                const b3 = c_c_sum & c_sc;

                const x = b0 & b1;
                const y = b0 | b1;
                const m = cur[m_off + k];

                var res = (~b3) & ((x & ~b2) | (~y & b2 & m));
                if (k == W - 1) res &= last_mask;
                nxt[m_off + k] = res;
            }
        }
        const tmp = cur;
        cur = nxt;
        nxt = tmp;
    }

    _ = std.c.clock_gettime(std.c.CLOCK.MONOTONIC, &ts1);
    const ms = @as(f64, @floatFromInt(ts1.sec - ts0.sec)) * 1000.0 +
        @as(f64, @floatFromInt(ts1.nsec - ts0.nsec)) / 1000000.0;
    const sim_ms: u64 = @intFromFloat(@round(ms));

    var alive: u64 = 0;
    for (cur) |val| {
        alive += @popCount(val);
    }

    _ = std.c.printf("alive=%llu sim_ms=%llu\n", alive, sim_ms);
}
