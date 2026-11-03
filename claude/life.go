// Conway's Game of Life on an N x N torus, bit-parallel: 64 cells per uint64.
package main

import (
	"fmt"
	"math/bits"
	"os"
	"strconv"
	"time"
)

// Horizontal 3-cell sum (left + self + right) of one row, as two bit planes.
func hsumRow(r, h0, h1 []uint64, lastbit uint) {
	w := len(r)
	h0 = h0[:w]
	h1 = h1[:w]
	if w == 1 {
		c := r[0]
		l := (c << 1) | ((c >> lastbit) & 1)
		rr := (c >> 1) | ((c & 1) << lastbit)
		x := l ^ c
		h0[0] = x ^ rr
		h1[0] = (l & c) | (x & rr)
		return
	}
	{
		c := r[0]
		l := (c << 1) | ((r[w-1] >> lastbit) & 1)
		rr := (c >> 1) | (r[1] << 63)
		x := l ^ c
		h0[0] = x ^ rr
		h1[0] = (l & c) | (x & rr)
	}
	prev, c := r[0], r[1]
	for i := 1; i < w-1; i++ {
		next := r[i+1]
		l := (c << 1) | (prev >> 63)
		rr := (c >> 1) | (next << 63)
		x := l ^ c
		h0[i] = x ^ rr
		h1[i] = (l & c) | (x & rr)
		prev, c = c, next
	}
	{
		c := r[w-1]
		l := (c << 1) | (r[w-2] >> 63)
		rr := (c >> 1) | ((r[0] & 1) << lastbit)
		x := l ^ c
		h0[w-1] = x ^ rr
		h1[w-1] = (l & c) | (x & rr)
	}
}

// Next state of one row from the 3-cell sums of the rows above, at and below.
// Total of the 3x3 block (self included): alive next iff total == 3, or total == 4 and alive.
func stepRow(a0, a1, b0, b1, c0, c1, cur, out []uint64) {
	w := len(out)
	a0, a1, b0, b1, c0, c1, cur = a0[:w], a1[:w], b0[:w], b1[:w], c0[:w], c1[:w], cur[:w]
	for i := range out {
		p := a0[i] ^ b0[i]
		ones := p ^ c0[i]
		carry := (a0[i] & b0[i]) | (p & c0[i])
		s := a1[i] ^ b1[i]
		sc := a1[i] & b1[i]
		t := c1[i] ^ carry
		tc := c1[i] & carry
		x := s ^ t
		eq3 := ones & x &^ (sc | tc)
		eq4 := ((s & t) | (sc ^ tc)) &^ (ones | x)
		out[i] = eq3 | (cur[i] & eq4)
	}
}

func main() {
	if len(os.Args) < 4 {
		fmt.Fprintf(os.Stderr, "usage: %s N GENS SEED_FILE\n", os.Args[0])
		os.Exit(1)
	}
	n, err1 := strconv.Atoi(os.Args[1])
	gens, err2 := strconv.Atoi(os.Args[2])
	data, err3 := os.ReadFile(os.Args[3])
	if err1 != nil || err2 != nil || err3 != nil {
		fmt.Fprintln(os.Stderr, "bad arguments or unreadable seed file")
		os.Exit(1)
	}

	w := (n + 63) / 64
	lastbit := uint((n - 1) & 63)
	lastmask := ^uint64(0)
	if n&63 != 0 {
		lastmask = (uint64(1) << uint(n&63)) - 1
	}
	cells := n * w
	g := make([]uint64, cells)
	ng := make([]uint64, cells)
	h0 := make([]uint64, cells)
	h1 := make([]uint64, cells)

	total := n * n
	k := 0
	for _, ch := range data {
		if k >= total {
			break
		}
		if ch == '0' || ch == '1' {
			if ch == '1' {
				y, x := k/n, k%n
				g[y*w+x/64] |= 1 << uint(x&63)
			}
			k++
		}
	}

	t0 := time.Now()
	for gen := 0; gen < gens; gen++ {
		for y := 0; y < n; y++ {
			o := y * w
			hsumRow(g[o:o+w], h0[o:o+w], h1[o:o+w], lastbit)
		}
		for y := 0; y < n; y++ {
			up := y - 1
			if y == 0 {
				up = n - 1
			}
			dn := y + 1
			if y == n-1 {
				dn = 0
			}
			up, mid, dn := up*w, y*w, dn*w
			out := ng[mid : mid+w]
			stepRow(h0[up:up+w], h1[up:up+w], h0[mid:mid+w], h1[mid:mid+w],
				h0[dn:dn+w], h1[dn:dn+w], g[mid:mid+w], out)
			out[w-1] &= lastmask
		}
		g, ng = ng, g
	}
	ms := float64(time.Since(t0).Nanoseconds()) / 1e6

	alive := 0
	for _, v := range g {
		alive += bits.OnesCount64(v)
	}
	fmt.Printf("alive=%d sim_ms=%.3f\n", alive, ms)
}
